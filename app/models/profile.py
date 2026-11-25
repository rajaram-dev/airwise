"""User profile models. Profiles are request input only and are never stored."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class CommuteMode(StrEnum):
    """How the user usually travels to work or school."""

    CAR = "car"
    TWO_WHEELER = "two_wheeler"
    BUS = "bus"
    METRO = "metro"
    WALK = "walk"
    CYCLE = "cycle"
    WFH = "wfh"


class CookingFuel(StrEnum):
    """Main cooking fuel at home."""

    LPG = "lpg"
    PNG = "png"
    ELECTRIC = "electric"
    BIOMASS = "biomass"
    KEROSENE = "kerosene"


class Heating(StrEnum):
    """Main heating source at home."""

    NONE = "none"
    ELECTRIC = "electric"
    GAS = "gas"
    WOOD = "wood"
    COAL = "coal"


class OutdoorActivity(StrEnum):
    """Usual outdoor exercise habit."""

    NONE = "none"
    MORNING_WALK = "morning_walk"
    EVENING_WALK = "evening_walk"
    SPORTS = "sports"


class Language(StrEnum):
    """Language for AI-generated text."""

    EN = "en"
    HI = "hi"


class Household(BaseModel):
    """Who lives at home. Used only to judge sensitivity to pollution."""

    model_config = ConfigDict(extra="forbid")

    children: bool = False
    elderly: bool = False
    respiratory_condition: bool = False
    pregnant: bool = False

    @property
    def is_sensitive(self) -> bool:
        """Return True if anyone at home belongs to a sensitive group."""
        return self.children or self.elderly or self.respiratory_condition or self.pregnant


class UserProfile(BaseModel):
    """Location, household and lifestyle details used to personalise the plan."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    location_name: str = Field(default="", max_length=100)
    household: Household = Field(default_factory=Household)
    commute_mode: CommuteMode = CommuteMode.WFH
    commute_minutes: int = Field(default=0, ge=0, le=240)
    commute_km: float | None = Field(default=None, ge=0, le=150)
    cooking_fuel: CookingFuel = CookingFuel.LPG
    heating: Heating = Heating.NONE
    has_air_purifier: bool = False
    outdoor_activity: OutdoorActivity = OutdoorActivity.NONE
    language: Language = Language.EN
