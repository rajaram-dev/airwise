"""Select and rank the recommendations that apply to a user."""

from collections.abc import Iterable

from app.models.plan import Recommendation, RecommendationCategory
from app.rules.catalog import CATALOG, CatalogItem
from app.rules.context import RuleContext

MAX_PER_CATEGORY = 4
SENSITIVE_BOOST = 5

# Items that protect health get a boost when someone at home is sensitive.
HEALTH_ITEMS = frozenset(
    {"shift_activity_window", "exercise_indoors", "wear_n95", "run_purifier", "consider_purifier"}
)


def _priority(item: CatalogItem, ctx: RuleContext) -> int:
    boost = SENSITIVE_BOOST if ctx.profile.household.is_sensitive and item.id in HEALTH_ITEMS else 0
    return min(100, item.priority + boost)


def _render(item: CatalogItem, ctx: RuleContext) -> Recommendation:
    return Recommendation(
        id=item.id,
        category=item.category,
        title=item.title(ctx),
        action=item.action(ctx),
        why=item.why(ctx),
        impact=item.impact(ctx),
        priority=_priority(item, ctx),
    )


def select_recommendations(
    ctx: RuleContext, catalog: Iterable[CatalogItem] = CATALOG
) -> list[Recommendation]:
    """Return applicable recommendations, highest priority first, capped per category.

    Args:
        ctx: Rule context for this user and location.
        catalog: Catalogue to choose from (injectable for tests).

    Returns:
        Recommendations sorted by priority (descending), at most
        ``MAX_PER_CATEGORY`` per category.
    """
    applicable = [_render(item, ctx) for item in catalog if item.applies(ctx)]
    applicable.sort(key=lambda rec: (-rec.priority, rec.id))

    counts: dict[RecommendationCategory, int] = dict.fromkeys(RecommendationCategory, 0)
    selected: list[Recommendation] = []
    for rec in applicable:
        if counts[rec.category] < MAX_PER_CATEGORY:
            selected.append(rec)
            counts[rec.category] += 1
    return selected
