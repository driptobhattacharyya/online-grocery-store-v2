"""Explainable cart recommendations.

Data
----
Past purchases in ``orders`` and ``order_items`` (product id, order id, and
the email of the buyer). Current cart rows decide the anchor products. Stock
comes from ``inventory`` so out-of-stock items are never suggested.

Algorithm
---------
1. Item-based collaborative filtering (co-purchase).
   Each product is the set of orders that contain it. Similarity of an anchor
   ``c`` and a candidate ``p`` is the conditional probability

       |orders containing both| / |orders containing c|

   The item score of ``p`` is the sum of those similarities over every anchor
   currently in the cart. The anchor with the largest raw overlap is kept so
   the UI can say "Because you added {that product}".

2. Similar shoppers.
   Neighbours are other customers who bought at least one anchor. A neighbour
   who shares ``k`` anchor products contributes ``k`` to every other product
   they bought. That is a small item-based collaborative filter: people whose
   baskets overlap the cart vote for what else they purchased.

3. Blend.
   Each of those two scores is divided by its own maximum (so neither swamps
   the other), then combined as

       0.6 * normalised co-purchase + 0.4 * normalised similar-shopper score

4. Fallback.
   Items already in the cart and items with no remaining stock are removed.
   If nothing has a positive score (an empty cart, or a product nobody has
   bought with anything), the remaining slots are filled by popularity: how
   many past order lines contain the product. With no orders at all, any
   in-stock product is listed and labelled as popular.

The same function serves the product page by treating that product as the
only anchor, and the "for you" row by using the signed-in customer's past
purchases as anchors.
"""

from collections import Counter

from applications.database import get_db

ITEM_WEIGHT = 0.6
USER_WEIGHT = 0.4


def recommend_for_cart(email, limit=6):
    db = get_db()
    anchors = [
        row["product_id"]
        for row in db.execute("SELECT product_id FROM cart WHERE email = ?", (email,)).fetchall()
    ]
    return recommend(anchors, limit=limit, context="cart")


def recommend_for_user(email, limit=6):
    db = get_db()
    anchors = [
        row["product_id"]
        for row in db.execute(
            """
            SELECT DISTINCT oi.product_id
            FROM order_items oi
            JOIN orders o ON o.orderID = oi.orderID
            WHERE o.email = ? AND oi.product_id IS NOT NULL
            """,
            (email,),
        ).fetchall()
    ]
    return recommend(anchors, limit=limit, context="history")


def recommend(anchor_product_ids, limit=6, context="cart"):
    db = get_db()
    anchors = []
    for value in anchor_product_ids or []:
        try:
            anchors.append(int(value))
        except (TypeError, ValueError):
            continue
    anchor_set = set(anchors)

    purchase_rows = db.execute(
        """
        SELECT o.orderID AS order_id, o.email AS email, oi.product_id AS product_id
        FROM orders o
        JOIN order_items oi ON oi.orderID = o.orderID
        WHERE oi.product_id IS NOT NULL
        """
    ).fetchall()

    user_items = {}
    item_orders = {}
    popularity = Counter()
    for row in purchase_rows:
        product_id = int(row["product_id"])
        user_items.setdefault(row["email"], set()).add(product_id)
        item_orders.setdefault(product_id, set()).add(row["order_id"])
        popularity[product_id] += 1

    catalog = db.execute(
        """
        SELECT p.productID, p.name, p.price, p.unit, IFNULL(i.quantity, 0) AS quantity
        FROM products p
        LEFT JOIN inventory i ON i.productID = p.productID
        """
    ).fetchall()
    products = {row["productID"]: row for row in catalog}

    def eligible(product_id):
        row = products.get(product_id)
        return row is not None and product_id not in anchor_set and row["quantity"] > 0

    item_scores = {}
    best_anchor = {}
    best_overlap = {}
    for candidate in products:
        if not eligible(candidate):
            continue
        score = 0.0
        top_anchor = None
        top_overlap = 0
        for anchor in anchors:
            anchor_orders = item_orders.get(anchor, set())
            if not anchor_orders:
                continue
            overlap = len(anchor_orders & item_orders.get(candidate, set()))
            if overlap <= 0:
                continue
            score += overlap / len(anchor_orders)
            if overlap > top_overlap:
                top_overlap = overlap
                top_anchor = anchor
        if score > 0:
            item_scores[candidate] = score
            best_anchor[candidate] = top_anchor
            best_overlap[candidate] = top_overlap

    neighbour_weight = Counter()
    if anchors:
        for email, items in user_items.items():
            overlap = len(anchor_set & items)
            if overlap:
                for product_id in items:
                    if eligible(product_id):
                        neighbour_weight[product_id] += overlap

    normalised_items = _normalise(item_scores)
    normalised_users = _normalise(neighbour_weight)
    ranked = []
    for product_id in set(normalised_items) | set(normalised_users):
        score = (ITEM_WEIGHT * normalised_items.get(product_id, 0.0)) + (
            USER_WEIGHT * normalised_users.get(product_id, 0.0)
        )
        ranked.append((score, product_id))
    ranked.sort(key=lambda pair: (-pair[0], products[pair[1]]["name"]))

    results = []
    used = set()
    for score, product_id in ranked:
        if len(results) >= limit:
            break
        reason, strategy = _reason(
            product_id, best_anchor, products, normalised_users, context
        )
        results.append(_pack(products[product_id], score, reason, strategy))
        used.add(product_id)

    if len(results) < limit:
        popular_ids = [product_id for product_id, _count in popularity.most_common()]
        if not popular_ids:
            popular_ids = sorted(products, key=lambda product_id: products[product_id]["name"])
        for product_id in popular_ids:
            if len(results) >= limit:
                break
            if not eligible(product_id) or product_id in used:
                continue
            results.append(
                _pack(
                    products[product_id],
                    0,
                    "Popular with other shoppers",
                    "popularity",
                )
            )
            used.add(product_id)
    return results


def _normalise(scores):
    if not scores:
        return {}
    peak = max(scores.values())
    if peak <= 0:
        return {}
    return {key: value / peak for key, value in scores.items()}


def _reason(product_id, best_anchor, products, user_scores, context):
    anchor = best_anchor.get(product_id)
    if anchor and anchor in products:
        anchor_name = products[anchor]["name"]
        if context == "product":
            return f"Frequently bought with {anchor_name}", "cooccurrence"
        if context == "history":
            return f"Because you bought {anchor_name}", "cooccurrence"
        return f"Because you added {anchor_name}", "cooccurrence"
    if user_scores.get(product_id, 0) > 0:
        return "Shoppers with similar baskets also bought this", "similar_users"
    return "Popular with other shoppers", "popularity"


def _pack(row, score, reason, strategy):
    return {
        "productID": row["productID"],
        "name": row["name"],
        "price": row["price"],
        "unit": row["unit"],
        "quantity": row["quantity"],
        "score": round(float(score), 4),
        "reason": reason,
        "strategy": strategy,
    }
