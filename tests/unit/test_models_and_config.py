import pytest
from pydantic import SecretStr, ValidationError

from app.config import Settings
from tests.factories import make_profile


def test_profile_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        make_profile(is_admin=True)


@pytest.mark.parametrize(
    "overrides",
    [
        {"latitude": 999},
        {"longitude": -181},
        {"commute_mode": "rocket"},
        {"commute_minutes": 1000},
        {"location_name": "x" * 101},
    ],
)
def test_profile_validates_ranges_and_enums(overrides: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        make_profile(**overrides)


def test_profile_strips_whitespace() -> None:
    assert make_profile(location_name="  Delhi  ").location_name == "Delhi"


def test_settings_gemini_key_detection() -> None:
    assert not Settings(gemini_api_key=None).has_gemini_key
    assert not Settings(gemini_api_key=SecretStr("  ")).has_gemini_key
    assert Settings(gemini_api_key=SecretStr("abc")).has_gemini_key


def test_settings_gemini_models_order_and_dedup() -> None:
    settings = Settings(gemini_model="a", gemini_fallback_models=" b, a ,,c ")
    assert settings.gemini_models == ["a", "b", "c"]


def test_settings_origin_list() -> None:
    settings = Settings(allowed_origins="http://a.com, http://b.com,")
    assert settings.allowed_origin_list == ["http://a.com", "http://b.com"]
