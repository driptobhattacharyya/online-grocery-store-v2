from applications.ai_service import interpret_locally
from tests.conftest import auth


def test_local_parser_understands_a_price_phrase():
    parsed = interpret_locally("cheap milk under 50")
    assert parsed["max_price"] == 50
    assert "milk" in parsed["keywords"]
    assert "cheap" not in parsed["keywords"]
    assert "under" not in parsed["keywords"]


def test_smart_search_and_assistant_work_without_an_api_key(client, app, catalog, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    found = client.post("/api/search/smart", json={"query": "milk under 150"})
    body = found.get_json()
    assert found.status_code == 200, body
    assert body["provider"] == "local"
    assert [product["name"] for product in body["products"]] == ["Milk"]

    cheap = client.post("/api/search/smart", json={"query": "cheap bread under 50"})
    assert [product["name"] for product in cheap.get_json()["products"]] == ["Bread"]

    pricey = client.post("/api/search/smart", json={"query": "milk under 10"})
    assert pricey.get_json()["products"] == []

    assistant = client.post(
        "/api/assistant",
        json={"message": "I want a recipe with milk and bread"},
    )
    answer = assistant.get_json()
    assert assistant.status_code == 200, answer
    assert answer["provider"] == "local"
    assert {product["name"] for product in answer["products"]} == {"Milk", "Bread"}

    # The endpoint is public so the homepage can demo it before login.
    assert client.get("/api/recommendations/popular").status_code == 200
    headers, _ = auth(client, app, "ada@example.com")
    personal = client.get("/api/recommendations/for-you", headers=headers)
    assert personal.status_code == 200
