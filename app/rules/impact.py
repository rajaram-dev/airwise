"""Impact calculations. Methodology and sources: docs/ai-design.md#impact-methodology."""

from app.models.profile import CommuteMode, UserProfile

# kg CO2e per passenger-km.
# Car and two-wheeler: UK Government GHG conversion factors 2025 (average car ~0.177,
# small petrol car ~0.154, motorbike ~0.116), rounded.
# Bus and metro: approximate values from the same factor set's public transport tables;
# marked "estimated" in the UI.
EMISSION_FACTORS_KG_PER_KM: dict[CommuteMode, float] = {
    CommuteMode.CAR: 0.17,
    CommuteMode.TWO_WHEELER: 0.11,
    CommuteMode.BUS: 0.10,
    CommuteMode.METRO: 0.03,
    CommuteMode.WALK: 0.0,
    CommuteMode.CYCLE: 0.0,
    CommuteMode.WFH: 0.0,
}

# Assumption used to estimate distance when only commute time is given.
AVERAGE_URBAN_SPEED_KMH = 20.0

# Conservative real-world figures (lab filtration is higher; fit and use reduce it).
MASK_EXPOSURE_REDUCTION_PCT = 70
PURIFIER_INDOOR_REDUCTION_PCT = 50

TRIPS_PER_DAY = 2


def commute_km_one_way(profile: UserProfile) -> float:
    """Return the one-way commute distance, estimating from minutes if km is missing."""
    if profile.commute_km is not None:
        return profile.commute_km
    return profile.commute_minutes / 60 * AVERAGE_URBAN_SPEED_KMH


def co2_saved_per_day(current: CommuteMode, alternative: CommuteMode, km_one_way: float) -> float:
    """Return kg CO2e saved per day (round trip) by switching commute mode. Never negative."""
    difference = EMISSION_FACTORS_KG_PER_KM[current] - EMISSION_FACTORS_KG_PER_KM[alternative]
    return round(max(0.0, difference) * km_one_way * TRIPS_PER_DAY, 1)


def exposure_reduction_pct(usual_pm2_5: float, better_pm2_5: float) -> int:
    """Return the % drop in PM2.5 exposure from moving to a cleaner time, clamped to 0-100."""
    if usual_pm2_5 <= 0:
        return 0
    pct = (usual_pm2_5 - better_pm2_5) / usual_pm2_5 * 100
    return max(0, min(100, round(pct)))
