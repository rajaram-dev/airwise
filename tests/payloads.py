"""Fake upstream payloads and a fake AI generator for tests."""

import json
from typing import Any

from app.core.errors import AIUnavailableError
from tests.factories import NOW, make_forecast

GEOCODE_PAYLOAD: dict[str, Any] = {
    "results": [
        {
            "name": "Delhi",
            "country": "India",
            "admin1": "Delhi",
            "latitude": 28.65,
            "longitude": 77.23,
            "timezone": "Asia/Kolkata",
        }
    ]
}


REVERSE_PAYLOAD: dict[str, Any] = {
    "address": {
        "city": "Lucknow",
        "state_district": "Lucknow District",
        "state": "Uttar Pradesh",
        "country": "India",
    }
}


def air_payload(
    current_aqi: int = 287, aqi_by_hour: dict[int, int] | None = None
) -> dict[str, Any]:
    """Open-Meteo shaped response built from the test forecast factory."""
    forecast = make_forecast(aqi_by_hour, default_aqi=current_aqi)
    return {
        "timezone": "Asia/Kolkata",
        "utc_offset_seconds": 19800,
        "current": {
            "time": NOW.strftime("%Y-%m-%dT%H:%M"),
            "us_aqi": current_aqi,
            "pm2_5": current_aqi / 2,
            "pm10": current_aqi * 0.75,
            "nitrogen_dioxide": 50.0,
            "ozone": 10.0,
            "us_aqi_pm2_5": current_aqi,
            "us_aqi_pm10": current_aqi // 2,
            "us_aqi_nitrogen_dioxide": 30,
            "us_aqi_ozone": 10,
        },
        "hourly": {
            "time": [h.time.strftime("%Y-%m-%dT%H:%M") for h in forecast],
            "us_aqi": [h.aqi for h in forecast],
            "pm2_5": [h.pm2_5 for h in forecast],
        },
    }


class FakeGenerator:
    """Records prompts and returns canned output (or raises)."""

    def __init__(
        self,
        plan_reply: str | None = None,
        chat_reply: str = "Stay indoors at 5 pm.",
        fail: bool = False,
    ) -> None:
        self.plan_reply = plan_reply
        self.chat_reply = chat_reply
        self.fail = fail
        self.plan_prompts: list[str] = []
        self.chat_prompts: list[str] = []

    async def generate_plan(self, system: str, prompt: str) -> str:
        self.plan_prompts.append(prompt)
        if self.fail:
            raise AIUnavailableError("fake failure")
        if self.plan_reply is not None:
            return self.plan_reply
        payload = json.loads(prompt.split("\n", 1)[1])
        return json.dumps(
            {
                "summary": f"AI summary for {payload['location']}.",
                "items": [
                    {
                        "id": item["id"],
                        "title": f"AI {item['id']}",
                        "action": "Do it.",
                        "why": "Because.",
                    }
                    for item in payload["items"]
                ],
            }
        )

    async def generate_chat(self, system: str, prompt: str) -> str:
        self.chat_prompts.append(prompt)
        if self.fail:
            raise AIUnavailableError("fake failure")
        return self.chat_reply
