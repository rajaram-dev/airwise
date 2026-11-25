"""Recommendation catalogue.

Each entry says when it applies, its default wording (used when AI is unavailable) and how its
impact is calculated. Gemini may reword entries but can never add new ones or change numbers.
"""

from collections.abc import Callable
from dataclasses import dataclass

from app.models.air import AqiCategory
from app.models.plan import Impact, ImpactBasis, RecommendationCategory
from app.models.profile import CommuteMode, CookingFuel, Heating, OutdoorActivity
from app.rules.context import (
    USUAL_ACTIVITY_HOUR,
    RuleContext,
    format_hour,
    format_window,
)
from app.rules.impact import (
    MASK_EXPOSURE_REDUCTION_PCT,
    PURIFIER_INDOOR_REDUCTION_PCT,
    co2_saved_per_day,
    commute_km_one_way,
    exposure_reduction_pct,
)
from app.rules.windows import cleanest_daytime_hour, dirtiest_daytime_hour, forecast_at_hour

Text = Callable[[RuleContext], str]
Rule = Callable[[RuleContext], bool]
ImpactFn = Callable[[RuleContext], Impact]

PRIVATE_MOTOR = {CommuteMode.CAR, CommuteMode.TWO_WHEELER}


@dataclass(frozen=True)
class CatalogItem:
    """A recommendation template."""

    id: str
    category: RecommendationCategory
    priority: int
    applies: Rule
    title: Text
    action: Text
    why: Text
    impact: ImpactFn


def _fixed(text: str) -> Text:
    return lambda _ctx: text


def _note(note: str) -> ImpactFn:
    return lambda _ctx: Impact(note=note, basis=ImpactBasis.ESTIMATED)


# ---------- routine ----------


def _usual_hour_pm(ctx: RuleContext) -> float | None:
    hour = USUAL_ACTIVITY_HOUR.get(ctx.profile.outdoor_activity)
    if hour is None:
        return None
    entry = forecast_at_hour(ctx.forecast, now=ctx.now, hour=hour)
    return entry.pm2_5 if entry else None


def _shift_applies(ctx: RuleContext) -> bool:
    usual = _usual_hour_pm(ctx)
    return bool(ctx.windows) and usual is not None and usual > ctx.windows[0].avg_pm2_5


def _shift_impact(ctx: RuleContext) -> Impact:
    usual = _usual_hour_pm(ctx) or 0.0
    return Impact(
        exposure_reduction_pct=exposure_reduction_pct(usual, ctx.windows[0].avg_pm2_5),
        basis=ImpactBasis.COMPUTED,
    )


def _indoor_exercise_applies(ctx: RuleContext) -> bool:
    return ctx.profile.outdoor_activity != OutdoorActivity.NONE and not ctx.windows


# ---------- indoor ----------


def _ventilate_impact(ctx: RuleContext) -> Impact:
    clean = cleanest_daytime_hour(ctx.forecast, ctx.now)
    dirty = dirtiest_daytime_hour(ctx.forecast, ctx.now)
    if clean is None or dirty is None:
        return Impact(note="Less smog enters your home", basis=ImpactBasis.ESTIMATED)
    return Impact(
        exposure_reduction_pct=exposure_reduction_pct(dirty.pm2_5, clean.pm2_5),
        basis=ImpactBasis.COMPUTED,
    )


def _ventilate_action(ctx: RuleContext) -> str:
    clean = cleanest_daytime_hour(ctx.forecast, ctx.now)
    when = f"around {format_hour(clean.time)}" if clean else "when the air is cleanest"
    return (
        "Keep windows shut most of the day. "
        f"Open them for 10–15 minutes {when} to let in fresh air."
    )


# ---------- alternatives ----------


def _commute_switch_applies(ctx: RuleContext) -> bool:
    return ctx.profile.commute_mode in PRIVATE_MOTOR and commute_km_one_way(ctx.profile) > 0


def _commute_switch_impact(ctx: RuleContext) -> Impact:
    saved = co2_saved_per_day(
        ctx.profile.commute_mode, CommuteMode.METRO, commute_km_one_way(ctx.profile)
    )
    return Impact(co2_kg_saved_per_day=saved, basis=ImpactBasis.ESTIMATED)


def _wfh_impact(ctx: RuleContext) -> Impact:
    saved = co2_saved_per_day(
        ctx.profile.commute_mode, CommuteMode.WFH, commute_km_one_way(ctx.profile)
    )
    return Impact(
        co2_kg_saved_per_day=saved,
        note="No time spent in traffic smog",
        basis=ImpactBasis.ESTIMATED,
    )


CATALOG: tuple[CatalogItem, ...] = (
    # Routine
    CatalogItem(
        id="shift_activity_window",
        category=RecommendationCategory.ROUTINE,
        priority=90,
        applies=_shift_applies,
        title=lambda ctx: f"Move your outdoor time to {format_window(ctx.windows[0])}",
        action=_fixed("Plan walks, play or sport for this window and keep it light."),
        why=_fixed(
            "Smog is usually worst at night and early morning when cool air traps pollution."
        ),
        impact=_shift_impact,
    ),
    CatalogItem(
        id="exercise_indoors",
        category=RecommendationCategory.ROUTINE,
        priority=88,
        applies=_indoor_exercise_applies,
        title=_fixed("Exercise indoors today"),
        action=_fixed("Swap your outdoor workout for yoga, stretching or a home workout."),
        why=_fixed("No hour today is clean enough for safe outdoor exercise for your household."),
        impact=_note("Avoids breathing hard in polluted air"),
    ),
    CatalogItem(
        id="protect_sensitive",
        category=RecommendationCategory.ROUTINE,
        priority=85,
        applies=lambda ctx: (
            ctx.profile.household.is_sensitive and ctx.air_at_least(AqiCategory.UNHEALTHY_SENSITIVE)
        ),
        title=_fixed("Keep sensitive family members indoors"),
        action=_fixed(
            "Children, older adults and anyone with asthma should skip outdoor play and walks."
        ),
        why=_fixed("Their lungs are more easily harmed by fine particles."),
        impact=_note("Lowers risk of asthma attacks and breathing problems"),
    ),
    CatalogItem(
        id="wear_n95",
        category=RecommendationCategory.ROUTINE,
        priority=80,
        applies=lambda ctx: ctx.air_at_least(AqiCategory.UNHEALTHY_SENSITIVE),
        title=_fixed("Wear an N95 mask outdoors"),
        action=_fixed(
            "Use a well-fitted N95 or FFP2 mask. Cloth and surgical masks do little against smog."
        ),
        why=_fixed("N95 masks filter the fine PM2.5 particles that reach deep into the lungs."),
        impact=lambda _ctx: Impact(
            exposure_reduction_pct=MASK_EXPOSURE_REDUCTION_PCT, basis=ImpactBasis.ESTIMATED
        ),
    ),
    # Indoor
    CatalogItem(
        id="run_purifier",
        category=RecommendationCategory.INDOOR,
        priority=78,
        applies=lambda ctx: ctx.profile.has_air_purifier and ctx.air_at_least(AqiCategory.MODERATE),
        title=_fixed("Run your air purifier in the bedroom"),
        action=_fixed(
            "Keep the door closed and run it on high for an hour, then on auto through the night."
        ),
        why=_fixed("A purifier works best in a closed room where people spend the most time."),
        impact=lambda _ctx: Impact(
            exposure_reduction_pct=PURIFIER_INDOOR_REDUCTION_PCT, basis=ImpactBasis.ESTIMATED
        ),
    ),
    CatalogItem(
        id="consider_purifier",
        category=RecommendationCategory.INDOOR,
        priority=70,
        applies=lambda ctx: (
            not ctx.profile.has_air_purifier and ctx.air_at_least(AqiCategory.UNHEALTHY_SENSITIVE)
        ),
        title=_fixed("Get a HEPA air purifier for one room"),
        action=_fixed(
            "Choose a HEPA purifier sized for your bedroom, "
            "or build a low-cost fan-and-filter unit."
        ),
        why=_fixed("Cleaning the air in one room gives your family a safe place to sleep."),
        impact=lambda _ctx: Impact(
            exposure_reduction_pct=PURIFIER_INDOOR_REDUCTION_PCT, basis=ImpactBasis.ESTIMATED
        ),
    ),
    CatalogItem(
        id="ventilate_clean_hour",
        category=RecommendationCategory.INDOOR,
        priority=65,
        applies=lambda ctx: ctx.air_at_least(AqiCategory.MODERATE),
        title=_fixed("Air out your home at the cleanest hour"),
        action=_ventilate_action,
        why=_fixed(
            "Short airing at the cleanest time refreshes indoor air without letting smog in."
        ),
        impact=_ventilate_impact,
    ),
    CatalogItem(
        id="avoid_indoor_smoke",
        category=RecommendationCategory.INDOOR,
        priority=60,
        applies=lambda ctx: ctx.air_at_least(AqiCategory.MODERATE),
        title=_fixed("Avoid indoor smoke"),
        action=_fixed(
            "Skip incense, candles, mosquito coils and smoking indoors. "
            "Use the exhaust fan when cooking."
        ),
        why=_fixed("These add fine particles to air that is already polluted."),
        impact=_note("Removes avoidable indoor PM2.5 sources"),
    ),
    CatalogItem(
        id="wet_cleaning",
        category=RecommendationCategory.INDOOR,
        priority=50,
        applies=lambda ctx: ctx.air_at_least(AqiCategory.UNHEALTHY_SENSITIVE),
        title=_fixed("Mop instead of sweeping"),
        action=_fixed("Wet-mop floors and wipe surfaces with a damp cloth."),
        why=_fixed("Dry sweeping throws settled dust back into the air."),
        impact=_note("Less dust in the air you breathe"),
    ),
    CatalogItem(
        id="gas_heater_safety",
        category=RecommendationCategory.INDOOR,
        priority=75,
        applies=lambda ctx: ctx.profile.heating == Heating.GAS,
        title=_fixed("Use your gas heater safely"),
        action=_fixed("Never sleep with it on, and keep a door slightly open while it runs."),
        why=_fixed("Gas heaters release nitrogen dioxide and can build up carbon monoxide."),
        impact=_note("Prevents harmful gas build-up indoors"),
    ),
    # Alternatives
    CatalogItem(
        id="commute_metro",
        category=RecommendationCategory.ALTERNATIVE,
        priority=72,
        applies=_commute_switch_applies,
        title=_fixed("Take the metro or bus instead of driving"),
        action=_fixed(
            "Try public transport for your daily commute, at least on the worst smog days."
        ),
        why=_fixed(
            "Vehicle exhaust is a major source of city smog, "
            "and fewer cars means cleaner air for all."
        ),
        impact=_commute_switch_impact,
    ),
    CatalogItem(
        id="work_from_home",
        category=RecommendationCategory.ALTERNATIVE,
        priority=74,
        applies=lambda ctx: (
            _commute_switch_applies(ctx) and ctx.air_at_least(AqiCategory.VERY_UNHEALTHY)
        ),
        title=_fixed("Work from home on severe smog days"),
        action=_fixed("Ask if you can work remotely today to skip the commute entirely."),
        why=_fixed("You avoid traffic smog and your trip's emissions at the same time."),
        impact=_wfh_impact,
    ),
    CatalogItem(
        id="clean_cooking_fuel",
        category=RecommendationCategory.ALTERNATIVE,
        priority=86,
        applies=lambda ctx: ctx.profile.cooking_fuel in {CookingFuel.BIOMASS, CookingFuel.KEROSENE},
        title=_fixed("Switch to LPG or electric cooking"),
        action=_fixed(
            "Use LPG, piped gas or an induction stove instead of wood, dung or kerosene."
        ),
        why=_fixed("Solid fuels and kerosene fill the kitchen with smoke and fine particles."),
        impact=_note("Large reduction in indoor smoke"),
    ),
    CatalogItem(
        id="clean_heating",
        category=RecommendationCategory.ALTERNATIVE,
        priority=84,
        applies=lambda ctx: ctx.profile.heating in {Heating.WOOD, Heating.COAL},
        title=_fixed("Heat with electricity instead of wood or coal"),
        action=_fixed("Use an electric heater or warm layers instead of burning wood or coal."),
        why=_fixed("Burning solid fuel indoors adds heavy smoke and adds to outdoor smog."),
        impact=_note("Large reduction in indoor and outdoor smoke"),
    ),
    CatalogItem(
        id="no_open_burning",
        category=RecommendationCategory.ALTERNATIVE,
        priority=55,
        applies=lambda ctx: ctx.air_at_least(AqiCategory.UNHEALTHY_SENSITIVE),
        title=_fixed("Say no to burning waste or leaves"),
        action=_fixed(
            "Compost leaves, use waste collection, and ask neighbours to avoid bonfires."
        ),
        why=_fixed("Open burning is a major winter smog source in many cities."),
        impact=_note("Cleaner air for your whole neighbourhood"),
    ),
)
