"""Reducing what the recorder keeps to what a chart can draw.

Home Assistant keeps two records: states, exact and purged after ten days, and
long-term statistics, hourly and kept forever for entities with a state_class.
A span up to two days is read from states so every wiggle is there; anything
longer is read from statistics, which is why the outdoor average and heat
demand exist as numbers at all.

The arithmetic lives apart from the reading. Bucketing a month of eight
sensors, working out where a heating line reaches zero — none of that needs a
recorder, a clock or a house, and all of it is worth being sure about.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

SPANS = {"24h": 86_400, "7d": 604_800, "30d": 2_592_000, "90d": 7_776_000}
# One point per bucket. Enough to see a night, few enough to send and draw.
BUCKETS = {"24h": 96, "7d": 168, "30d": 120, "90d": 90}
# Up to this much history comes from states; beyond it, from statistics.
STATES_LIMIT = 172_800


def bucket(
    points: list[tuple[float, float]], start: float, end: float, count: int
) -> list[float | None]:
    """Reduce a series to `count` means across the window.

    A bucket with nothing in it is None rather than zero: a sensor that was
    offline did not read zero degrees, and a chart that draws it as zero is
    worse than one that draws nothing.
    """
    if count <= 0 or end <= start:
        return []
    width = (end - start) / count
    sums = [0.0] * count
    counts = [0] * count
    for when, value in points:
        if when < start or when >= end:
            continue
        index = min(int((when - start) / width), count - 1)
        sums[index] += value
        counts[index] += 1
    return [sums[i] / counts[i] if counts[i] else None for i in range(count)]


def spans_of(
    points: list[tuple[float, float]], start: float, end: float
) -> list[tuple[float, float]]:
    """The intervals a 0/1 series spent on.

    A season that is still on when the window ends runs to the end of it,
    rather than disappearing for want of a closing edge.
    """
    spans: list[tuple[float, float]] = []
    opened: float | None = None
    for when, value in sorted(points):
        if when < start:
            opened = max(start, when) if value else None
            continue
        if when >= end:
            break
        if value and opened is None:
            opened = when
        elif not value and opened is not None:
            spans.append((opened, when))
            opened = None
    if opened is not None:
        spans.append((opened, end))
    return spans


def daily(
    outdoor_hours: dict[str, list[float]], demand_hours: dict[str, list[float]]
) -> list[dict[str, Any]]:
    """One dot per day: that day's mean outdoor temperature, and how many
    hours the heating ran.

    Demand is recorded as a fraction of each hour, so a day's hours is the sum
    of those fractions. A day with no outdoor reading is not a dot — there is
    nowhere to put it on the axis.
    """
    days = []
    for date in sorted(outdoor_hours):
        readings = outdoor_hours[date]
        if not readings:
            continue
        days.append({
            "date": date,
            "outdoor": sum(readings) / len(readings),
            "hours": sum(demand_hours.get(date, [])),
        })
    return days


def balance_point(days: list[dict[str, Any]]) -> float | None:
    """Where the heating line reaches zero.

    Every heated building draws a line: hours of heating against the day's
    mean outdoor temperature. Where it crosses zero is the temperature above
    which the house holds itself — the balance point, measured from days
    actually lived through rather than estimated from assumptions.

    Only days that used heat are fitted. Summer days sit flat on zero and
    would bend a line that is only meaningful where heating ran. Fewer than
    three such days is no answer rather than a wrong one, and so is a line
    with no slope, or one sloping the wrong way.
    """
    used = [day for day in days if day["hours"] > 0]
    if len(used) < 3:
        return None
    count = len(used)
    mean_x = sum(day["outdoor"] for day in used) / count
    mean_y = sum(day["hours"] for day in used) / count
    covariance = sum(
        (day["outdoor"] - mean_x) * (day["hours"] - mean_y) for day in used
    )
    variance = sum((day["outdoor"] - mean_x) ** 2 for day in used)
    if variance == 0:
        return None
    slope = covariance / variance
    if slope >= 0:
        # Heating that rises with the outdoor temperature is not a heating
        # line, whatever it is.
        return None
    intercept = mean_y - slope * mean_x
    return -intercept / slope


def day_key(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, timezone.utc).strftime("%Y-%m-%d")


def hourly_by_day(points: list[tuple[float, float]]) -> dict[str, list[float]]:
    """Group hourly values by the day they fall on, for the energy signature."""
    days: dict[str, list[float]] = {}
    for when, value in points:
        days.setdefault(day_key(when), []).append(value)
    return days


def _number(value: Any) -> float | None:
    """A state as a number, or None.

    'on' counts as one and 'off' as zero, so a binary sensor and its numeric
    twin bucket the same way.
    """
    if value in ("on", "off"):
        return 1.0 if value == "on" else 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


async def async_series(
    hass, entity_ids: list[str], start: float, end: float
) -> dict[str, list[tuple[float, float]]]:
    """Readings per entity across the window, from whichever record has them.

    Returns an empty series for anything the recorder cannot answer for,
    including when there is no recorder at all — a house without one still has
    a working thermostat, and the page should draw what it can.
    """
    if not entity_ids:
        return {}
    try:
        from homeassistant.components.recorder import get_instance, history, statistics
    except ImportError:
        return {entity_id: [] for entity_id in entity_ids}

    begin = datetime.fromtimestamp(start, timezone.utc)
    finish = datetime.fromtimestamp(end, timezone.utc)

    if end - start <= STATES_LIMIT:

        def _states() -> dict[str, list[tuple[float, float]]]:
            raw = history.get_significant_states(
                hass,
                begin,
                finish,
                entity_ids,
                include_start_time_state=True,
                significant_changes_only=False,
                minimal_response=False,
            )
            out: dict[str, list[tuple[float, float]]] = {}
            for entity_id in entity_ids:
                points = []
                for state in raw.get(entity_id, []):
                    value = _number(getattr(state, "state", None))
                    if value is not None:
                        points.append((state.last_updated_timestamp, value))
                out[entity_id] = points
            return out

        reader = _states
    else:

        def _stats() -> dict[str, list[tuple[float, float]]]:
            raw = statistics.statistics_during_period(
                hass, begin, finish, set(entity_ids), "hour", None, {"mean"}
            )
            out: dict[str, list[tuple[float, float]]] = {}
            for entity_id in entity_ids:
                out[entity_id] = [
                    (row["start"], row["mean"])
                    for row in raw.get(entity_id, [])
                    if row.get("mean") is not None
                ]
            return out

        reader = _stats

    try:
        return await get_instance(hass).async_add_executor_job(reader)
    except (KeyError, RuntimeError):
        # No recorder running. The thermostat works without one; the history
        # simply has nothing behind it.
        return {entity_id: [] for entity_id in entity_ids}
