"""Background e-mail tasks (SMTP mocked) and the production config check."""
import pytest

import applications.backend_tasks as tasks
from applications.config import DEV_SECRET_KEY, ConfigError, validate_config
from helpers import APPLE, APPLE_PRICE, bearer


@pytest.fixture
def sent(monkeypatch):
    messages = []
    monkeypatch.setattr(tasks, "send_message", lambda to, subject, body: messages.append((to, subject, body)))
    return messages


def test_daily_reminder_emails_every_user(app, sent):
    with app.app_context():
        assert tasks.daily_reminder.run() == "OK"
    assert sorted(to for to, _, _ in sent) == ["demo@grocery.app", "manager@grocery.app"]


def test_monthly_report_includes_recent_spend(app, client, shopper_token, sent):
    client.post("/api/add_to_cart", json={"product_id": APPLE, "quantity": 2}, headers=bearer(shopper_token))
    assert client.post("/api/shopping_cart/checkout", headers=bearer(shopper_token)).status_code == 200
    with app.app_context():
        assert tasks.monthly_report.run() == "OK"
    bodies = {to: body for to, _, body in sent}
    # orders.total_price is NUMERIC, so 360.0 is stored (and rendered) as 360.
    assert f"a total of {int(2 * APPLE_PRICE)} INR" in bodies["demo@grocery.app"]
    assert "a total of 0 INR" in bodies["manager@grocery.app"]


# --- validate_config (in-process; the subprocess tests are in test_infra.py) ---------

STRONG = {"SECRET_KEY": "s" * 40, "JWT_SECRET_KEY": "j" * 40, "ADMIN_PASSWORD": "long-enough-pw"}


def _config(monkeypatch, **env):
    for key in ("SECRET_KEY", "JWT_SECRET_KEY", "ADMIN_PASSWORD"):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    return {"IS_PRODUCTION": True, "SECRET_KEY": env.get("SECRET_KEY", DEV_SECRET_KEY),
            "JWT_SECRET_KEY": env.get("JWT_SECRET_KEY", DEV_SECRET_KEY)}


def test_validate_config_ignores_development():
    validate_config({"IS_PRODUCTION": False, "SECRET_KEY": DEV_SECRET_KEY})


def test_validate_config_accepts_strong_secrets(monkeypatch):
    validate_config(_config(monkeypatch, **STRONG))


@pytest.mark.parametrize("env,problem", [
    ({}, "SECRET_KEY is not set"),
    ({**STRONG, "SECRET_KEY": DEV_SECRET_KEY}, "SECRET_KEY uses the development default"),
    ({**STRONG, "JWT_SECRET_KEY": "x" * 31}, "JWT_SECRET_KEY is too short"),
    ({**STRONG, "ADMIN_PASSWORD": "password"}, 'must not be "password"'),
    ({**STRONG, "ADMIN_PASSWORD": "1234567"}, "at least 8 characters"),
])
def test_validate_config_rejects_weak_secrets(monkeypatch, env, problem):
    with pytest.raises(ConfigError, match=problem):
        validate_config(_config(monkeypatch, **env))
