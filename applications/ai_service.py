"""Natural-language search and a recipe assistant.

An OpenAI-compatible chat (and, optionally, embeddings) endpoint is used when
``OPENAI_API_KEY`` is set. Any missing key, disabled flag, timeout, or HTTP
error falls back to a local parser plus TF-IDF, so the demo runs with no keys.
"""

import json
import math
import os
import re
import urllib.error
import urllib.request
from collections import Counter

from applications.catalog import list_products

STOPWORDS = {
    "a", "an", "the", "i", "me", "my", "want", "need", "some", "please", "for",
    "with", "and", "or", "of", "to", "buy", "get", "find", "show", "looking",
    "under", "below", "over", "above", "cheap", "budget", "affordable",
    "recipe", "make", "cook", "ingredients", "ingredient", "using",
}
UNDER_RE = re.compile(
    r"(?:under|below|less than|cheaper than|max|upto|up to)\s*₹?\s*(\d+(?:\.\d+)?)",
    re.IGNORECASE,
)
OVER_RE = re.compile(
    r"(?:over|above|more than|at least|min)\s*₹?\s*(\d+(?:\.\d+)?)",
    re.IGNORECASE,
)
CHEAP_RE = re.compile(r"\b(cheap|budget|affordable)\b", re.IGNORECASE)
TOKEN_RE = re.compile(r"[a-z0-9]+")

SYNONYMS = {
    "eggs": "egg",
    "noodle": "maggi",
    "noodles": "maggi",
    "ramen": "ramen",
    "soda": "pepsi",
    "cola": "pepsi",
    "loaf": "bread",
    "dahi": "yogurt",
    "curd": "yogurt",
}


def _tokens(text):
    return TOKEN_RE.findall((text or "").lower())


def interpret_locally(query):
    text = query or ""
    max_price = None
    min_price = None
    under = UNDER_RE.search(text)
    over = OVER_RE.search(text)
    if under:
        max_price = float(under.group(1))
    if over:
        min_price = float(over.group(1))
    if max_price is None and CHEAP_RE.search(text):
        max_price = 50.0
    cleaned = UNDER_RE.sub(" ", text)
    cleaned = OVER_RE.sub(" ", cleaned)
    cleaned = CHEAP_RE.sub(" ", cleaned)
    keywords = " ".join(token for token in _tokens(cleaned) if token not in STOPWORDS)
    return {"keywords": keywords, "min_price": min_price, "max_price": max_price}


def _openai_configured():
    return bool(os.environ.get("OPENAI_API_KEY"))


def _openai_json(path, payload):
    base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    request = urllib.request.Request(
        f"{base}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=float(os.environ.get("OPENAI_TIMEOUT", "20"))) as response:
        return json.loads(response.read().decode("utf-8"))


def _openai_interpret(query):
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    data = _openai_json(
        "/chat/completions",
        {
            "model": model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Extract grocery search filters. Reply with JSON "
                        '{"keywords": string, "min_price": number|null, "max_price": number|null}. '
                        "keywords are product words only. Prices are in INR."
                    ),
                },
                {"role": "user", "content": query},
            ],
        },
    )
    content = json.loads(data["choices"][0]["message"]["content"])
    return {
        "keywords": str(content.get("keywords") or ""),
        "min_price": content.get("min_price"),
        "max_price": content.get("max_price"),
    }


def _filter_price(products, interpreted):
    min_price = interpreted.get("min_price")
    max_price = interpreted.get("max_price")
    chosen = []
    for product in products:
        price = float(product["price"])
        if min_price is not None and price < float(min_price):
            continue
        if max_price is not None and price > float(max_price):
            continue
        chosen.append(product)
    return chosen


def _tfidf_scores(query, products):
    documents = []
    for product in products:
        text = " ".join(
            [
                product["name"],
                product.get("category_name") or "",
                product.get("description") or "",
                product.get("unit") or "",
            ]
        )
        documents.append(_tokens(text))
    document_frequency = Counter()
    for tokens in documents:
        for token in set(tokens):
            document_frequency[token] += 1
    total = max(len(documents), 1)
    query_tokens = [SYNONYMS.get(token, token) for token in _tokens(query)]
    scores = []
    for product, tokens in zip(products, documents):
        if not tokens or not query_tokens:
            scores.append(0.0)
            continue
        term_frequency = Counter(tokens)
        score = 0.0
        name_tokens = set(_tokens(product["name"]))
        for token in query_tokens:
            lexical = SYNONYMS.get(token, token)
            if lexical in name_tokens or token in name_tokens:
                score += 5.0
            in_document = term_frequency[lexical] or term_frequency[token]
            df = document_frequency[lexical] or document_frequency[token]
            if in_document and df:
                idf = math.log((total + 1) / (df + 1)) + 1
                score += (in_document / len(tokens)) * idf
        scores.append(score)
    return scores


def _embed_scores(query, products):
    model = os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    texts = [query] + [
        f"{product['name']}. {product.get('description') or ''} {product.get('category_name') or ''}"
        for product in products
    ]
    data = _openai_json("/embeddings", {"model": model, "input": texts})
    vectors = [item["embedding"] for item in data["data"]]
    query_vector = vectors[0]
    scores = []
    for vector in vectors[1:]:
        scores.append(_cosine(query_vector, vector))
    return scores


def _cosine(left, right):
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left)) or 1.0
    right_norm = math.sqrt(sum(b * b for b in right)) or 1.0
    return dot / (left_norm * right_norm)


def smart_search(query):
    products = [product for product in list_products() if product["quantity"] > 0]
    provider = "local"
    interpreted = interpret_locally(query)
    if _openai_configured():
        try:
            interpreted = _openai_interpret(query)
            provider = "openai"
        except (urllib.error.URLError, TimeoutError, KeyError, ValueError, json.JSONDecodeError):
            interpreted = interpret_locally(query)
            provider = "local"
    filtered = _filter_price(products, interpreted)
    keywords = interpreted.get("keywords") or ""
    if not keywords:
        ranked = sorted(filtered, key=lambda product: product["name"])
    else:
        use_embeddings = provider == "openai" and os.environ.get("OPENAI_USE_EMBEDDINGS", "1") != "0"
        try:
            scores = _embed_scores(keywords, filtered) if use_embeddings else _tfidf_scores(keywords, filtered)
            if use_embeddings:
                provider = "openai"
        except (urllib.error.URLError, TimeoutError, KeyError, ValueError, json.JSONDecodeError):
            scores = _tfidf_scores(keywords, filtered)
        paired = [pair for pair in zip(scores, filtered) if pair[0] > 0]
        paired.sort(key=lambda pair: (-pair[0], pair[1]["name"]))
        ranked = [product for _score, product in paired]
    return {
        "products": ranked,
        "provider": provider,
        "interpreted": interpreted,
        "no_results": len(ranked) == 0,
    }


def _local_ingredient_names(message, products):
    text_tokens = set(_tokens(message))
    text_tokens |= {SYNONYMS.get(token, token) for token in list(text_tokens)}
    matched = []
    lowered_message = (message or "").lower()
    for product in products:
        name_tokens = set(_tokens(product["name"]))
        name = product["name"].lower()
        if name in lowered_message or name_tokens & text_tokens:
            matched.append(product["name"])
    return matched


def _openai_ingredients(message, products):
    names = [product["name"] for product in products]
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    data = _openai_json(
        "/chat/completions",
        {
            "model": model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Pick grocery products from the catalog that the shopper needs. "
                        'Reply with JSON {"product_names": [string], "reply": string}. '
                        "product_names must be copied from the catalog."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Catalog: {', '.join(names)}\n\nRequest: {message}",
                },
            ],
        },
    )
    content = json.loads(data["choices"][0]["message"]["content"])
    return content.get("product_names") or [], content.get("reply") or ""


def shopping_assistant(message):
    products = list_products()
    provider = "local"
    reply = ""
    names = []
    if _openai_configured():
        try:
            names, reply = _openai_ingredients(message, products)
            provider = "openai"
        except (urllib.error.URLError, TimeoutError, KeyError, ValueError, json.JSONDecodeError):
            names = []
            provider = "local"
    if not names:
        names = _local_ingredient_names(message, products)
    wanted = {name.lower() for name in names}
    matched = []
    for product in products:
        if product["name"].lower() in wanted or any(
            product["name"].lower() in name.lower() or name.lower() in product["name"].lower()
            for name in names
        ):
            matched.append(
                {
                    **product,
                    "reason": f"Matches your request for {product['name']}",
                }
            )
    in_stock = [product for product in matched if product["quantity"] > 0]
    if not reply:
        if in_stock:
            listed = ", ".join(product["name"] for product in in_stock)
            reply = f"I can add these from the shelves: {listed}."
        else:
            reply = "I couldn't match that to anything in stock. Try naming ingredients, like milk and bread."
    return {"reply": reply, "products": in_stock, "provider": provider}
