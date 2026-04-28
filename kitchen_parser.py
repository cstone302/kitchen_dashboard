"""
kitchen_parser.py
-----------------
Parses CASAS .csv files (comma-separated, no header) and extracts kitchen-focused
daily features for a Type 1 diabetic patient.

Handles both formats found in CASAS files:
  CSV format:  date,time,sensor,message[,label]     (atmo10.csv style)
  TXT format:  date  time  sensor  message  [label]  (space-separated, generated files)

Metrics derived:
  diet            - meal prep activity (stove + fridge + area sensors)
  blood_sugar     - from injected Glucometer events (mg/dL readings)
  medication      - insulin/MedBox opens (count-based)
  env_hygiene     - sink duration (dishwashing proxy)
  independence    - stove left on too long, fridge left open, tasks self-completed

Usage:
  from kitchen_parser import parse_kitchen_file, extract_daily_kitchen, aggregate_kitchen_week
  events = parse_kitchen_file("data/atmo10.csv")
  daily  = extract_daily_kitchen(events)
  weekly = aggregate_kitchen_week(daily)
"""

from datetime import datetime, date
from collections import defaultdict
from typing import Optional
import re


# ---------------------------------------------------------------------------
# Sensor classification for kitchen focus
# ---------------------------------------------------------------------------
KITCHEN_SENSORS = {
    # Sensor keyword → metric category
    "stove":         "cooking",
    "refrigerator":  "fridge",
    "fridge":        "fridge",
    "sink":          "sink",
    "kitchenarea":   "presence",
    "kitchena":      "presence",     # catches KitchenAArea, KitchenAMotion, etc.
    "diningchair":   "eating",
    "glucometer":    "blood_sugar",  # injected/synthetic sensor
    "glucose":       "blood_sugar",
    "medbox":        "medication",
    "insulin":       "medication",
}

def classify_sensor(sensor_id: str) -> str:
    """Return the metric category for a sensor, or 'other'."""
    s = sensor_id.lower()
    for keyword, cat in KITCHEN_SENSORS.items():
        if keyword in s:
            return cat
    return "other"


# ---------------------------------------------------------------------------
# Parser — handles both CSV and space-separated CASAS formats
# ---------------------------------------------------------------------------
def parse_kitchen_file(filepath: str) -> list[dict]:
    """
    Parse a CASAS file (CSV or space-separated) into event dicts.
    Automatically detects format from the first data line.
    Returns list of: {datetime, sensor, message, value, category}
    """
    events = []
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    # Detect format from first non-comment, non-empty line
    csv_format = False
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            csv_format = "," in stripped
            break

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Split based on detected format
        if csv_format:
            parts = [p.strip() for p in line.split(",")]
        else:
            parts = line.split()

        if len(parts) < 4:
            continue

        try:
            dt_str = parts[0] + " " + parts[1]
            try:
                dt = datetime.strptime(dt_str[:26], "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                dt = datetime.strptime(dt_str[:19], "%Y-%m-%d %H:%M:%S")

            sensor  = parts[2]
            message = parts[3]
            label   = parts[4].strip() if len(parts) > 4 else None
            cat     = classify_sensor(sensor)

            # Extract numeric value for glucometer (message = "mg/dL:142" or just "142")
            value = None
            if cat == "blood_sugar":
                num_match = re.search(r"\d+", message)
                if num_match:
                    value = int(num_match.group())

            events.append({
                "datetime": dt,
                "sensor":   sensor,
                "message":  message,
                "label":    label,
                "category": cat,
                "value":    value,
            })
        except Exception:
            continue

    return events


# ---------------------------------------------------------------------------
# Daily feature extraction
# ---------------------------------------------------------------------------
def extract_daily_kitchen(events: list[dict]) -> dict:
    """
    Group events by day and compute per-day kitchen features.
    Returns dict keyed by date.
    """
    by_day = defaultdict(list)
    for e in events:
        by_day[e["datetime"].date()].append(e)

    daily = {}
    for day in sorted(by_day.keys()):
        day_events = sorted(by_day[day], key=lambda x: x["datetime"])
        daily[day] = _features_for_day(day, day_events)
    return daily


def _features_for_day(day: date, evts: list[dict]) -> dict:
    """Compute all kitchen metrics for one day."""

    # --- Cooking duration (stove active minutes) ---------------------------
    stove_minutes, stove_long_sessions = _stove_analysis(evts)

    # --- Refrigerator opens -----------------------------------------------
    fridge_opens = sum(
        1 for e in evts
        if e["category"] == "fridge" and e["message"].upper() in ("ON", "OPEN")
    )

    # --- Sink duration (dishwashing / hygiene) ----------------------------
    sink_minutes = _dwell_minutes([e for e in evts if e["category"] == "sink"])

    # --- Kitchen presence (total time in kitchen) --------------------------
    presence_minutes = _dwell_minutes([e for e in evts if e["category"] == "presence"])

    # --- Blood sugar readings ----------------------------------------------
    bg_events = [e for e in evts if e["category"] == "blood_sugar" and e["value"]]
    bg_readings  = [e["value"] for e in bg_events]
    bg_avg       = round(sum(bg_readings) / len(bg_readings)) if bg_readings else None
    bg_high      = sum(1 for v in bg_readings if v > 180)
    bg_low       = sum(1 for v in bg_readings if v < 70)

    # --- Medication (insulin/MedBox opens) --------------------------------
    med_events = sum(
        1 for e in evts
        if e["category"] == "medication" and e["message"].upper() in ("ON", "OPEN")
    )

    # --- Independence signals ---------------------------------------------
    # Stove left on > 20 min = safety concern
    independence_issues = len([d for d in stove_long_sessions if d > 20])

    # --- Diet score (0-100) -----------------------------------------------
    # Based on: stove use (cooking), fridge access (eating), presence in kitchen
    diet_score = _diet_score(stove_minutes, fridge_opens, presence_minutes)

    # --- Environmental hygiene score (0-100) ------------------------------
    hygiene_score = min(100, int((sink_minutes / 15.0) * 100))  # 15 min/day = 100%

    # --- Medication score (0-100) -----------------------------------------
    # 3 expected doses/day for T1D (breakfast, lunch, dinner insulin + possible corrections)
    med_score = min(100, int((med_events / 3.0) * 100))

    # --- Blood sugar score (0-100, where 100 = all readings in range) -----
    total_readings = len(bg_readings)
    in_range = sum(1 for v in bg_readings if 70 <= v <= 180)
    bg_score = int((in_range / total_readings) * 100) if total_readings > 0 else None

    # --- Independence score (0-100) ---------------------------------------
    # Penalise for stove issues; reward for completing tasks
    independence_score = max(0, 100 - (independence_issues * 25))

    # --- Timeline (notable events) ----------------------------------------
    timeline = _build_kitchen_timeline(evts)

    return {
        "date":               day,
        "stove_minutes":      stove_minutes,
        "stove_long_sessions":stove_long_sessions,
        "fridge_opens":       fridge_opens,
        "sink_minutes":       sink_minutes,
        "presence_minutes":   presence_minutes,
        "bg_readings":        bg_readings,
        "bg_avg":             bg_avg,
        "bg_high":            bg_high,
        "bg_low":             bg_low,
        "med_events":         med_events,
        "independence_issues":independence_issues,
        "scores": {
            "diet":         diet_score,
            "blood_sugar":  bg_score,
            "medication":   med_score,
            "env_hygiene":  hygiene_score,
            "independence": independence_score,
        },
        "timeline":           timeline,
    }


def _dwell_minutes(evts: list[dict], cap_min: float = 30.0) -> float:
    """Sum dwell time from consecutive sensor activations, capped per gap."""
    if not evts:
        return 0.0
    total = 0.0
    prev = None
    for e in sorted(evts, key=lambda x: x["datetime"]):
        if prev:
            gap = (e["datetime"] - prev).total_seconds() / 60.0
            total += min(gap, cap_min)
        prev = e["datetime"]
    return round(total, 1)


def _stove_analysis(evts: list[dict]) -> tuple[float, list[float]]:
    """
    Return (total_on_minutes, list_of_long_session_minutes).
    A long session is any stove ON period > 20 minutes.
    """
    stove = sorted(
        [e for e in evts if e["category"] == "cooking"],
        key=lambda x: x["datetime"]
    )
    total_min   = 0.0
    long_sessions = []
    on_time = None
    for e in stove:
        if e["message"].upper() == "ON":
            on_time = e["datetime"]
        elif e["message"].upper() == "OFF" and on_time:
            dur = (e["datetime"] - on_time).total_seconds() / 60.0
            total_min += dur
            if dur > 20:
                long_sessions.append(round(dur, 1))
            on_time = None
    return round(total_min, 1), long_sessions


def _diet_score(stove_min: float, fridge_opens: int, presence_min: float) -> int:
    """
    0-100 score based on meal activity signals.
    Expected healthy day: ~25 min stove, 8+ fridge opens, ~45 min presence.
    """
    stove_s    = min(100, int((stove_min / 25.0)    * 40))  # up to 40 pts
    fridge_s   = min(100, int((fridge_opens / 8.0)   * 30))  # up to 30 pts
    presence_s = min(100, int((presence_min / 45.0)  * 30))  # up to 30 pts
    return min(100, stove_s + fridge_s + presence_s)


def _build_kitchen_timeline(evts: list[dict]) -> list[dict]:
    """Key kitchen events for the timeline view."""
    timeline = []
    stove_on = None
    for e in sorted(evts, key=lambda x: x["datetime"]):
        t = e["datetime"].strftime("%H:%M")
        cat = e["category"]

        if cat == "cooking" and e["message"].upper() == "ON":
            stove_on = e["datetime"]
            timeline.append({"time": t, "label": "Stove turned on",    "type": "cooking", "icon": "🔥"})
        elif cat == "cooking" and e["message"].upper() == "OFF" and stove_on:
            dur = (e["datetime"] - stove_on).total_seconds() / 60.0
            label = f"Stove off ({dur:.0f} min)" if dur > 1 else "Stove off"
            icon  = "⚠️" if dur > 20 else "✓"
            timeline.append({"time": t, "label": label, "type": "stove_off", "icon": icon})
            stove_on = None
        elif cat == "blood_sugar" and e["value"]:
            v = e["value"]
            status = "high" if v > 180 else "low" if v < 70 else "ok"
            timeline.append({"time": t, "label": f"Blood sugar: {v} mg/dL",
                              "type": f"bg_{status}", "icon": "🩸"})
        elif cat == "medication":
            timeline.append({"time": t, "label": "Medication taken", "type": "medication", "icon": "💊"})
        elif cat == "fridge" and e["message"].upper() in ("ON", "OPEN"):
            # Only log first open of each cluster (avoid spam)
            if not timeline or timeline[-1]["type"] != "fridge" or \
               (int(t.replace(":", "")) - int(timeline[-1]["time"].replace(":", "")) > 5):
                timeline.append({"time": t, "label": "Fridge opened", "type": "fridge", "icon": "🧊"})
        elif cat == "sink" and e["message"].upper() == "ON":
            if not timeline or timeline[-1]["type"] != "dishes":
                timeline.append({"time": t, "label": "Sink activity", "type": "dishes", "icon": "🫧"})

    return timeline[:10]


# ---------------------------------------------------------------------------
# Weekly aggregation
# ---------------------------------------------------------------------------
def aggregate_kitchen_week(daily: dict) -> dict:
    """
    Aggregate the most recent 7 days.
    Returns a summary dict consumed by build_dashboard_data.py.
    """
    recent = sorted(daily.keys())[-7:]
    days   = [daily[d] for d in recent]

    def avg(key: str) -> float:
        vals = [d[key] for d in days if d.get(key) is not None]
        return round(sum(vals) / len(vals), 1) if vals else 0

    def score_avg(cat: str) -> int:
        vals = [d["scores"].get(cat) for d in days if d["scores"].get(cat) is not None]
        return round(sum(vals) / len(vals)) if vals else 0

    bg_all = [v for d in days for v in d["bg_readings"]]
    bg_avg = round(sum(bg_all) / len(bg_all)) if bg_all else None

    return {
        "independence_score":  score_avg("independence"),
        "scores": {
            "diet":         score_avg("diet"),
            "blood_sugar":  score_avg("blood_sugar") if bg_all else None,
            "medication":   score_avg("medication"),
            "env_hygiene":  score_avg("env_hygiene"),
            "independence": score_avg("independence"),
        },
        "avg_stove_min":       avg("stove_minutes"),
        "avg_fridge_opens":    avg("fridge_opens"),
        "avg_sink_min":        avg("sink_minutes"),
        "avg_bg":              bg_avg,
        "bg_in_range_pct":     (
            round(100 * sum(1 for v in bg_all if 70 <= v <= 180) / len(bg_all))
            if bg_all else None
        ),
        "latest_timeline":     days[-1]["timeline"] if days else [],
        "daily_score_series":  [
            {"date": str(d), "score": round(sum(
                v for v in daily[d]["scores"].values() if v is not None
            ) / sum(1 for v in daily[d]["scores"].values() if v is not None))}
            for d in recent
        ],
    }
