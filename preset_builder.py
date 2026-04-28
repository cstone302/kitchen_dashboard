"""
preset_builder.py
-----------------
Build dashboard JSON presets by hand — no sensor file needed.
Each preset fully specifies what the dashboard shows: metrics, readings,
notifications, and the patient's story.

This is Version 2 of the dashboard data layer. Instead of parsing a sensor
file, you define exactly what you want each view to say.

Usage:
    python3 preset_builder.py

This writes one JSON file per preset defined in the PRESETS dict at the bottom
of this file to the output/ directory.

Notification types:
    "red"    → danger alert  (immediate action needed)
    "orange" → warning       (pattern concern, monitor)
    "green"  → reinforcement (positive feedback)
    "blue"   → info          (neutral / scheduled reminder)

Metric scores are 0–100. Blood sugar is in mg/dL.
Set any metric to null to show it as "No data" in the dashboard.
"""

import json
import os


# ---------------------------------------------------------------------------
# Notification builder helpers
# ---------------------------------------------------------------------------

def alert(label: str, detail: str) -> dict:
    """Red — immediate danger. Use for: stove left on, critically low/high BG, missed insulin."""
    return {"type": "red", "label": label, "detail": detail}

def warning(label: str, detail: str) -> dict:
    """Orange — pattern concern. Use for: elevated BG trend, infrequent cooking, no dishes done."""
    return {"type": "orange", "label": label, "detail": detail}

def reinforcement(label: str, detail: str) -> dict:
    """Green — positive feedback. Use for: good BG control, meal cooked, medication taken on time."""
    return {"type": "green", "label": label, "detail": detail}

def info(label: str, detail: str) -> dict:
    """Blue — neutral info. Use for: reminders, scheduled events, informational updates."""
    return {"type": "blue", "label": label, "detail": detail}


# ---------------------------------------------------------------------------
# Preset definition function
# ---------------------------------------------------------------------------

def make_preset(
    name: str,
    description: str,

    # ---- Metric scores (0-100, or None for "no data") ----
    diet_score: int,
    blood_sugar_score: int,       # % of readings in range (70-180 mg/dL)
    medication_score: int,
    hygiene_score: int,
    independence_score: int,

    # ---- Raw readings ----
    current_bg: int,              # mg/dL, shown as the live reading
    bg_trend: str,                # "rising", "falling", "stable"
    last_meal_time: str,          # e.g. "8:30 AM"
    last_med_time: str,           # e.g. "8:45 AM" or "Not taken"
    stove_status: str,            # "off" or "on" or "left_on"

    # ---- Today's to-do list (patient view) ----
    # Each item: {"task": str, "done": bool, "time": str or None}
    todo_items: list,

    # ---- 7-day history for trend chart ----
    # Each: {"day": "Mon", "diet": 80, "blood_sugar": 70, "medication": 90,
    #         "hygiene": 60, "independence": 85}
    weekly_history: list,

    # ---- Notifications per audience ----
    # patient / family / care lists of alert()/warning()/reinforcement()/info() dicts
    patient_notifications: list,
    family_notifications: list,
    care_notifications: list,

    # ---- Timeline (shown in patient and care views) ----
    # Each: {"time": "8:30 AM", "label": str, "icon": str, "type": str}
    timeline: list,

) -> dict:
    """Assemble a complete preset dict that the dashboard HTML reads."""
    return {
        "meta": {
            "name":        name,
            "description": description,
        },
        "scores": {
            "diet":         diet_score,
            "blood_sugar":  blood_sugar_score,
            "medication":   medication_score,
            "env_hygiene":  hygiene_score,
            "independence": independence_score,
            "overall":      round(sum(
                s for s in [diet_score, blood_sugar_score,
                             medication_score, hygiene_score, independence_score]
                if s is not None
            ) / sum(1 for s in [diet_score, blood_sugar_score,
                                 medication_score, hygiene_score, independence_score]
                    if s is not None)),
        },
        "readings": {
            "current_bg":     current_bg,
            "bg_trend":       bg_trend,
            "last_meal_time": last_meal_time,
            "last_med_time":  last_med_time,
            "stove_status":   stove_status,
        },
        "todo":     todo_items,
        "history":  weekly_history,
        "alerts": {
            "patient": patient_notifications,
            "family":  family_notifications,
            "care":    care_notifications,
        },
        "timeline": timeline,
    }


# ---------------------------------------------------------------------------
# Weekly history helpers
# ---------------------------------------------------------------------------

def week_good() -> list:
    """7-day history for a healthy, well-managed week."""
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    return [
        {"day": d, "diet": 82 + i*2, "blood_sugar": 78 + i,
         "medication": 95, "hygiene": 80 + i*3, "independence": 90}
        for i, d in enumerate(days)
    ]

def week_declining() -> list:
    """7-day history showing a week-over-week decline."""
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    return [
        {"day": d, "diet": 75 - i*8, "blood_sugar": 65 - i*6,
         "medication": 80 - i*10, "hygiene": 70 - i*7, "independence": 85 - i*8}
        for i, d in enumerate(days)
    ]

def week_crisis() -> list:
    """7-day history showing an ongoing crisis."""
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    return [
        {"day": d, "diet": 30 + i*2, "blood_sugar": 20 + i*3,
         "medication": 25 + i*2, "hygiene": 15 + i, "independence": 40 + i*3}
        for i, d in enumerate(days)
    ]


# ===========================================================================
# PRESETS — define your scenarios here
# ===========================================================================
#
# This is the main section you edit. Copy a preset block, change the name,
# and adjust the values. The functions alert(), warning(), reinforcement(),
# and info() build the notifications for each audience.
#
# BLOOD SUGAR REFERENCE:
#   < 70 mg/dL  = hypoglycemia (dangerous low)
#   70-180      = target range for Type 1 diabetic
#   > 180       = hyperglycemia (high, needs correction)
#   > 250       = severely high (urgent)
#
# ===========================================================================

PRESETS = {

    # ------------------------------------------------------------------
    # PRESET 1: Well-managed day
    # Patient is doing well. Good BG control, ate breakfast, took meds.
    # ------------------------------------------------------------------
    "well_managed": make_preset(
        name="Well-managed day",
        description="Patient is managing well — BG in range, ate breakfast, took insulin on time.",

        diet_score=88,
        blood_sugar_score=92,
        medication_score=100,
        hygiene_score=85,
        independence_score=95,

        current_bg=112,
        bg_trend="stable",
        last_meal_time="8:15 AM",
        last_med_time="8:30 AM",
        stove_status="off",

        todo_items=[
            {"task": "Take morning insulin",       "done": True,  "time": "8:30 AM"},
            {"task": "Eat breakfast",              "done": True,  "time": "8:15 AM"},
            {"task": "Check blood sugar",          "done": True,  "time": "9:00 AM"},
            {"task": "Prepare lunch",              "done": False, "time": "12:00 PM"},
            {"task": "Take midday reading",        "done": False, "time": "12:30 PM"},
            {"task": "Do the dishes",              "done": True,  "time": "9:30 AM"},
        ],

        weekly_history=week_good(),

        timeline=[
            {"time": "7:30 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "7:45 AM", "label": "Blood sugar: 98 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "8:10 AM", "label": "Stove turned on",       "icon": "🔥",  "type": "cooking"},
            {"time": "8:15 AM", "label": "Fridge opened",         "icon": "🧊",  "type": "fridge"},
            {"time": "8:30 AM", "label": "Stove off (20 min)",    "icon": "✓",   "type": "stove_off"},
            {"time": "8:32 AM", "label": "Medication taken",      "icon": "💊",  "type": "medication"},
            {"time": "9:20 AM", "label": "Sink activity (dishes)","icon": "🫧",  "type": "dishes"},
            {"time": "9:00 AM", "label": "Blood sugar: 112 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[
            reinforcement("Great morning!",
                "You took your insulin on time and your blood sugar is right where it should be."),
            info("Lunch reminder",
                "It's almost noon. Time to prepare lunch and take your midday reading."),
            reinforcement("Kitchen's clean",
                "You did the dishes after breakfast — nice work keeping your space tidy."),
        ],

        family_notifications=[
            reinforcement("Johnny is having a good day",
                "Blood sugar is 112 mg/dL (in target range), morning insulin taken at 8:30 AM."),
            info("No concerns this morning",
                "Ate breakfast, stove turned off properly, dishes done. Everything looks on track."),
        ],

        care_notifications=[
            reinforcement("All morning targets met",
                "BG 112 mg/dL at 9:00 AM (target 70–180). Morning insulin confirmed 8:32 AM. "
                "Stove on 20 min (within normal). Sink active 18 min (dishes completed)."),
            info("Afternoon check pending",
                "Next expected glucometer reading: 12:30 PM before lunch."),
        ],
    ),


    # ------------------------------------------------------------------
    # PRESET 2: Missed medication, elevated blood sugar
    # Patient forgot morning insulin, BG rising.
    # ------------------------------------------------------------------
    "missed_insulin": make_preset(
        name="Missed morning insulin",
        description="Patient skipped morning insulin. Blood sugar is elevated and rising.",

        diet_score=72,
        blood_sugar_score=38,
        medication_score=33,
        hygiene_score=60,
        independence_score=80,

        current_bg=247,
        bg_trend="rising",
        last_meal_time="8:45 AM",
        last_med_time="Yesterday 8:00 PM",
        stove_status="off",

        todo_items=[
            {"task": "Take morning insulin",       "done": False, "time": "8:30 AM"},
            {"task": "Eat breakfast",              "done": True,  "time": "8:45 AM"},
            {"task": "Check blood sugar",          "done": True,  "time": "10:00 AM"},
            {"task": "Prepare lunch",              "done": False, "time": "12:00 PM"},
            {"task": "Do the dishes",              "done": False, "time": None},
        ],

        weekly_history=week_declining(),

        timeline=[
            {"time": "8:30 AM", "label": "Fridge opened",          "icon": "🧊",  "type": "fridge"},
            {"time": "8:40 AM", "label": "Stove turned on",        "icon": "🔥",  "type": "cooking"},
            {"time": "8:52 AM", "label": "Stove off (12 min)",     "icon": "✓",   "type": "stove_off"},
            {"time": "8:55 AM", "label": "No medication recorded", "icon": "⚠️",  "type": "med_missed"},
            {"time": "10:00 AM","label": "Blood sugar: 247 mg/dL — HIGH","icon": "🩸", "type": "bg_high"},
        ],

        patient_notifications=[
            alert("Take your insulin now",
                "Your blood sugar is 247 mg/dL and rising. You haven't taken your morning "
                "insulin yet. Take it now and check again in 2 hours."),
            warning("Blood sugar has been elevated this week",
                "Your readings have been above 180 mg/dL on most mornings. "
                "Your care team has been notified."),
            info("Reminder: dishes still need to be done",
                "Sink hasn't been active since breakfast."),
        ],

        family_notifications=[
            alert("Johnny missed her morning insulin",
                "Blood sugar is 247 mg/dL (target: 70–180) and still rising. "
                "She has not taken insulin since last night. A check-in call is recommended."),
            warning("This is the third time this week",
                "Insulin has been missed on Monday, Wednesday, and today (Friday). "
                "A pattern is forming — her care team has been alerted."),
        ],

        care_notifications=[
            alert("Critical: Morning insulin not administered",
                "BG 247 mg/dL at 10:00 AM, trend rising. No MedBox activity since 8:00 PM "
                "yesterday. Breakfast consumed (stove active 8:40–8:52 AM) without insulin. "
                "Third missed morning dose this week (Monday, Wednesday, Friday)."),
            warning("Hyperglycemia pattern — 5 of 7 days above 200 mg/dL",
                "Weekly BG average: 218 mg/dL. Recommend insulin regimen review and "
                "possible dose adjustment at next visit."),
            info("Sink inactive since breakfast",
                "Dishes not done. Minor hygiene concern — monitor for pattern."),
        ],
    ),


    # ------------------------------------------------------------------
    # PRESET 3: Stove left on, low blood sugar
    # Patient shows signs of hypoglycemia and left the stove on.
    # ------------------------------------------------------------------
    "hypoglycemia_stove": make_preset(
        name="Hypoglycemia + stove safety",
        description="Blood sugar critically low. Stove was left on for 45 minutes.",

        diet_score=55,
        blood_sugar_score=20,
        medication_score=90,
        hygiene_score=40,
        independence_score=35,

        current_bg=58,
        bg_trend="falling",
        last_meal_time="7:00 AM",
        last_med_time="7:15 AM",
        stove_status="left_on",

        todo_items=[
            {"task": "Take morning insulin",       "done": True,  "time": "7:15 AM"},
            {"task": "Eat breakfast",              "done": True,  "time": "7:00 AM"},
            {"task": "Check blood sugar",          "done": True,  "time": "8:00 AM"},
            {"task": "Turn off stove",             "done": False, "time": None},
            {"task": "Eat something (BG low)",     "done": False, "time": "Now"},
            {"task": "Do the dishes",              "done": False, "time": None},
        ],

        weekly_history=week_crisis(),

        timeline=[
            {"time": "7:00 AM", "label": "Fridge opened",             "icon": "🧊",  "type": "fridge"},
            {"time": "7:05 AM", "label": "Stove turned on",           "icon": "🔥",  "type": "cooking"},
            {"time": "7:15 AM", "label": "Medication taken",          "icon": "💊",  "type": "medication"},
            {"time": "7:10 AM", "label": "Blood sugar: 82 mg/dL — OK","icon": "🩸",  "type": "bg_ok"},
            {"time": "7:45 AM", "label": "⚠️ Stove still on (40 min)","icon": "⚠️",  "type": "stove_warning"},
            {"time": "8:00 AM", "label": "Blood sugar: 58 mg/dL — LOW","icon": "🩸", "type": "bg_low"},
        ],

        patient_notifications=[
            alert("Your blood sugar is dangerously low",
                "58 mg/dL — this is too low. Eat 15g of fast-acting carbs right now "
                "(juice, glucose tablets, or candy). Do NOT wait. Check again in 15 minutes."),
            alert("The stove may still be on",
                "The stove has been on for over 45 minutes. Please check it now."),
            info("Your care team has been notified",
                "Both of these alerts have been sent to your family and your care team."),
        ],

        family_notifications=[
            alert("URGENT: Johnny's blood sugar is critically low",
                "58 mg/dL at 8:00 AM (dangerous — below 70). She took insulin at 7:15 AM "
                "but BG is still falling. Please call her immediately."),
            alert("Stove has been on for 45+ minutes",
                "The stove sensor has not detected an OFF event since 7:05 AM. "
                "This is a safety risk — please verify she is okay."),
        ],

        care_notifications=[
            alert("Hypoglycemia: BG 58 mg/dL at 8:00 AM",
                "Patient took morning insulin (MedBox 7:15 AM). BG was 82 at 7:10 AM, "
                "dropped to 58 by 8:00 AM — falling trend. No glucometer activity in past 30 min. "
                "Family has been notified. Consider insulin dose review."),
            alert("Independence concern: stove left on 45+ minutes",
                "KitchenAStove ON at 7:05 AM, no OFF event recorded. Patient may have left "
                "the kitchen while experiencing hypoglycemia."),
            warning("Third hypoglycemic episode this week",
                "Occurrences: Monday 7:30 AM (BG 61), Wednesday 2:00 PM (BG 64), "
                "Friday 8:00 AM (BG 58). Pattern suggests possible over-bolusing. "
                "Carb ratio and correction factor review recommended."),
        ],
    ),


    # ------------------------------------------------------------------
    # PRESET 4: Full crisis — no cooking, no meds, high BG for days
    # This is the "bad outcome" of the choose-your-own-adventure
    # ------------------------------------------------------------------
    "full_crisis": make_preset(
        name="Full crisis",
        description="Multiple days of missed insulin, no meal prep, and severely elevated BG.",

        diet_score=12,
        blood_sugar_score=5,
        medication_score=10,
        hygiene_score=8,
        independence_score=20,

        current_bg=312,
        bg_trend="rising",
        last_meal_time="Yesterday 6:00 PM",
        last_med_time="2 days ago",
        stove_status="off",

        todo_items=[
            {"task": "Take insulin immediately",   "done": False, "time": "Now"},
            {"task": "Eat something",              "done": False, "time": "Now"},
            {"task": "Check blood sugar",          "done": False, "time": "Now"},
            {"task": "Call your care team",        "done": False, "time": "Now"},
        ],

        weekly_history=week_crisis(),

        timeline=[
            {"time": "Yesterday", "label": "Last meal recorded",  "icon": "🍽️", "type": "meal"},
            {"time": "2 days ago","label": "Last insulin taken",  "icon": "💊",  "type": "medication"},
            {"time": "This AM",   "label": "Blood sugar: 312 mg/dL — CRITICAL", "icon": "🩸", "type": "bg_high"},
            {"time": "This AM",   "label": "No kitchen activity today", "icon": "⚠️", "type": "inactive"},
        ],

        patient_notifications=[
            alert("You need help right now",
                "Your blood sugar is 312 mg/dL. You haven't taken insulin in 2 days. "
                "Please call your care team or go to the emergency room. "
                "Your family has already been called."),
        ],

        family_notifications=[
            alert("Johnny needs immediate assistance",
                "Blood sugar is 312 mg/dL (critically high). No insulin in 2 days, "
                "no food today, no kitchen activity. Please go to her or call emergency services."),
            alert("5 consecutive days of missed medication",
                "This is not a one-time lapse. Immediate intervention is needed."),
        ],

        care_notifications=[
            alert("DKA risk: BG 312 mg/dL, insulin withheld 48+ hours",
                "No MedBox activity in 48 hours. BG rising: 198 (Mon), 241 (Tue), "
                "278 (Wed), 312 (Thu). No kitchen sensor activity today. "
                "Patient may be experiencing diabetic ketoacidosis. Emergency contact recommended."),
            alert("Nutritional and safety collapse",
                "Stove: zero sessions in 3 days. Fridge: <3 opens/day (was 45 avg). "
                "Sink: no activity in 4 days. Patient is not eating, cooking, or maintaining hygiene."),
            alert("Immediate intervention required",
                "Family has been notified. Consider emergency wellness check."),
        ],
    ),
    "baseline": make_preset(
        name="baseline",
        description="Basic Assumptions",

        diet_score=74,
        blood_sugar_score=74,
        medication_score=74,
        hygiene_score=74,
        independence_score=74,

        current_bg=103,
        bg_trend="stable",
        last_meal_time="9:00 AM",
        last_med_time="9:15 AM",
        stove_status="off",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": True,  "time": "8:10 AM"},
            {"task": "Eat breakfast",              "done": True,  "time": "9:00 AM"},
            {"task": "Take Medication",          "done": True,  "time": "9:15 AM"},
            {"task": "Do the Dishes",              "done": True, "time": "9:20 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "10:00 AM"},
            {"task": "Call Family",              "done": False,  "time": "12:30 PM"},
        ],

        weekly_history=week_good(),

        timeline=[
            {"time": "7:30 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "7:45 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "8:10 AM", "label": "Made Coffee",       "icon": "☕️",  "type": "cooking"},
            {"time": "8:30 AM", "label": "Stove on",    "icon": "🔥",   "type": "stove_on"},
            {"time": "8:35 AM", "label": "Fridge opened",         "icon": "🧊",  "type": "fridge"},
            {"time": "8:50 AM", "label": "Stove off (20 min)",    "icon": "✓",   "type": "stove_off"},
            {"time": "9:15 AM", "label": "Medication taken",      "icon": "💊",  "type": "medication"},
            {"time": "9:20 AM", "label": "Sink activity (dishes)","icon": "🫧",  "type": "dishes"},
            {"time": "9:30 AM", "label": "Blood sugar: 112 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[],

        family_notifications=[],

        care_notifications=[],
    ),
    "LEKFMD": make_preset(
        name="LEKFMD",
        description="Sleep, Eat, Cook, Turn Off, Meds, Dishes",

        diet_score=99,
        blood_sugar_score=83,
        medication_score=95,
        hygiene_score=87,
        independence_score=86,

        current_bg=105,
        bg_trend="stable",
        last_meal_time="10:30 AM",
        last_med_time="10:45 AM",
        stove_status="off",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": False,  "time": "9:40 AM"},
            {"task": "Eat breakfast",              "done": True,  "time": "10:30 AM"},
            {"task": "Take Medication",          "done": True,  "time": "10:45 AM"},
            {"task": "Do the Dishes",              "done": True, "time": "10:50 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "11:30 AM"},
            {"task": "Call Family",              "done": False,  "time": "2:00 PM"},
        ],

        weekly_history=[
            {"day": "Mon", "diet":95, "blood_sugar":78, "medication":98, "hygiene":91, "independence":86},
            {"day": "Tue", "diet":98, "blood_sugar":81, "medication":97, "hygiene":88, "independence":84},
            {"day": "Wed", "diet":97, "blood_sugar":87, "medication":92, "hygiene":92, "independence":83},
            {"day": "Thu", "diet":94, "blood_sugar":84, "medication":95, "hygiene":85, "independence":88},
            {"day": "Fri", "diet":91, "blood_sugar":88, "medication":96, "hygiene":83, "independence":87},
            {"day": "Sat", "diet":95, "blood_sugar":87, "medication":94, "hygiene":87, "independence":86},
            {"day": "Sun", "diet":96, "blood_sugar":82, "medication":97, "hygiene":88, "independence":86},
        ],

        timeline=[
            {"time": "9:00 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "9:15 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "10:00 AM", "label": "Stove on",    "icon": "🔥",   "type": "stove_on"},
            {"time": "10:05 AM", "label": "Fridge opened",         "icon": "🧊",  "type": "fridge"},
            {"time": "10:20 AM", "label": "Stove off (20 min)",    "icon": "✓",   "type": "stove_off"},
            {"time": "10:45 AM", "label": "Medication taken",      "icon": "💊",  "type": "medication"},
            {"time": "10:50 AM", "label": "Sink activity (dishes)","icon": "🫧",  "type": "dishes"},
            {"time": "11:00 AM", "label": "Blood sugar: 115 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[info("Easy Morning", "You slept well last night - let's start the day!"),
                                reinforcement("Breakfast", "Nicely done, chef Johnny! How was breakfast?")],

        family_notifications=[info("Well-Rested", "Johnny got extra sleep last night.")],

        care_notifications=[],
    ),
    "LEKFMT": make_preset(
        name="LEKFMT",
        description="Sleep, Eat, Cook, Turn Off, Meds, TV",

        diet_score=99,
        blood_sugar_score=83,
        medication_score=95,
        hygiene_score=49,
        independence_score=70,

        current_bg=105,
        bg_trend="stable",
        last_meal_time="10:30 AM",
        last_med_time="10:45 AM",
        stove_status="off",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": False,  "time": "9:40 AM"},
            {"task": "Eat breakfast",              "done": True,  "time": "10:30 AM"},
            {"task": "Take Medication",          "done": True,  "time": "10:45 AM"},
            {"task": "Do the Dishes",              "done": False, "time": "10:50 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "11:30 AM"},
            {"task": "Call Family",              "done": False,  "time": "2:00 PM"},
        ],

        weekly_history=[
            {"day": "Mon", "diet":95, "blood_sugar":78, "medication":98, "hygiene":61, "independence":71},
            {"day": "Tue", "diet":98, "blood_sugar":81, "medication":97, "hygiene":58, "independence":69},
            {"day": "Wed", "diet":97, "blood_sugar":87, "medication":92, "hygiene":62, "independence":68},
            {"day": "Thu", "diet":94, "blood_sugar":84, "medication":95, "hygiene":55, "independence":73},
            {"day": "Fri", "diet":91, "blood_sugar":88, "medication":96, "hygiene":53, "independence":72},
            {"day": "Sat", "diet":95, "blood_sugar":87, "medication":94, "hygiene":57, "independence":71},
            {"day": "Sun", "diet":96, "blood_sugar":82, "medication":97, "hygiene":58, "independence":71},
        ],

        timeline=[
            {"time": "9:00 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "9:15 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "10:00 AM", "label": "Stove on",    "icon": "🔥",   "type": "stove_on"},
            {"time": "10:05 AM", "label": "Fridge opened",         "icon": "🧊",  "type": "fridge"},
            {"time": "10:20 AM", "label": "Stove off (20 min)",    "icon": "✓",   "type": "stove_off"},
            {"time": "10:45 AM", "label": "Medication taken",      "icon": "💊",  "type": "medication"},
            {"time": "11:00 AM", "label": "Blood sugar: 115 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[info("Easy Morning", "You slept well last night - let's start the day!"),
                                reinforcement("Breakfast", "Nicely done, chef Johnny! How was breakfast?")],

        family_notifications=[info("Well-Rested", "Johnny got extra sleep last night.")],

        care_notifications=[warning("Clutter Warning", "Johnny didn't do the dishes after cooking - environmental cluttering is possible.")],
    ),
    "LEKFND": make_preset(
        name="LEKFND",
        description="Sleep, Eat, Cook, Turn Off, No Meds, Dishes",

        diet_score=99,
        blood_sugar_score=64,
        medication_score=43,
        hygiene_score=87,
        independence_score=63,

        current_bg=168,
        bg_trend="stable",
        last_meal_time="10:30 AM",
        last_med_time="Yesterday, 8:00 PM",
        stove_status="off",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": False,  "time": "9:40 AM"},
            {"task": "Eat breakfast",              "done": True,  "time": "10:30 AM"},
            {"task": "Take Medication",          "done": False,  "time": "10:45 AM"},
            {"task": "Do the Dishes",              "done": True, "time": "10:50 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "11:30 AM"},
            {"task": "Call Family",              "done": False,  "time": "2:00 PM"},
        ],

        weekly_history=[
            {"day": "Mon", "diet":95, "blood_sugar":58, "medication":48, "hygiene":91, "independence":66},
            {"day": "Tue", "diet":98, "blood_sugar":61, "medication":47, "hygiene":88, "independence":64},
            {"day": "Wed", "diet":97, "blood_sugar":67, "medication":42, "hygiene":92, "independence":63},
            {"day": "Thu", "diet":94, "blood_sugar":64, "medication":45, "hygiene":85, "independence":68},
            {"day": "Fri", "diet":91, "blood_sugar":68, "medication":46, "hygiene":83, "independence":67},
            {"day": "Sat", "diet":95, "blood_sugar":67, "medication":44, "hygiene":87, "independence":66},
            {"day": "Sun", "diet":96, "blood_sugar":62, "medication":47, "hygiene":88, "independence":66},
        ],

        timeline=[
            {"time": "9:00 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "9:15 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "10:00 AM", "label": "Stove on",    "icon": "🔥",   "type": "stove_on"},
            {"time": "10:05 AM", "label": "Fridge opened",         "icon": "🧊",  "type": "fridge"},
            {"time": "10:20 AM", "label": "Stove off (20 min)",    "icon": "✓",   "type": "stove_off"},
            {"time": "10:50 AM", "label": "Sink activity (dishes)","icon": "🫧",  "type": "dishes"},
            {"time": "11:00 AM", "label": "Blood sugar: 178 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[info("Easy Morning", "You slept well last night - let's start the day!"),
                                reinforcement("Breakfast", "Nicely done, chef Johnny! How was breakfast?"),
                                warning("Medication", "Don't forget to take your medication, Johnny")],

        family_notifications=[info("Well-Rested", "Johnny got extra sleep last night."),
                                warning("Medication", "Johnny forgot to take his medication today, want to check in?")],

        care_notifications=[warning("Medication", "Johnny displayed reduced medication adherence, reflected in his blood glucose.")],
    ),
    "LEKFNT": make_preset(
        name="LEKFNT",
        description="Sleep, Eat, Cook, Turn Off, No Meds, TV",

        diet_score=99,
        blood_sugar_score=64,
        medication_score=43,
        hygiene_score=51,
        independence_score=40,

        current_bg=161,
        bg_trend="stable",
        last_meal_time="10:30 AM",
        last_med_time="Yesterday, 8:00 PM",
        stove_status="off",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": False,  "time": "9:40 AM"},
            {"task": "Eat breakfast",              "done": True,  "time": "10:30 AM"},
            {"task": "Take Medication",          "done": False,  "time": "10:45 AM"},
            {"task": "Do the Dishes",              "done": False, "time": "10:50 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "11:30 AM"},
            {"task": "Call Family",              "done": False,  "time": "2:00 PM"},
        ],

        weekly_history=[
            {"day": "Mon", "diet":95, "blood_sugar":58, "medication":48, "hygiene":61, "independence":46},
            {"day": "Tue", "diet":98, "blood_sugar":61, "medication":47, "hygiene":58, "independence":44},
            {"day": "Wed", "diet":97, "blood_sugar":67, "medication":42, "hygiene":62, "independence":43},
            {"day": "Thu", "diet":94, "blood_sugar":64, "medication":45, "hygiene":55, "independence":48},
            {"day": "Fri", "diet":91, "blood_sugar":68, "medication":46, "hygiene":53, "independence":47},
            {"day": "Sat", "diet":95, "blood_sugar":67, "medication":44, "hygiene":57, "independence":46},
            {"day": "Sun", "diet":96, "blood_sugar":62, "medication":47, "hygiene":58, "independence":46},
        ],

        timeline=[
            {"time": "9:00 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "9:15 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "10:00 AM", "label": "Stove on",    "icon": "🔥",   "type": "stove_on"},
            {"time": "10:05 AM", "label": "Fridge opened",         "icon": "🧊",  "type": "fridge"},
            {"time": "10:20 AM", "label": "Stove off (20 min)",    "icon": "✓",   "type": "stove_off"},
            {"time": "11:00 AM", "label": "Blood sugar: 171 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[info("Easy Morning", "You slept well last night - let's start the day!"),
                                reinforcement("Breakfast", "Nicely done, chef Johnny! How was breakfast?"),
                                warning("Medication", "Don't forget to take your medication, Johnny")],

        family_notifications=[info("Well-Rested", "Johnny got extra sleep last night."),
                                warning("Medication", "Johnny forgot to take his medication today, want to check in?")],

        care_notifications=[warning("Medication", "Johnny displayed reduced medication adherence, reflected in his blood glucose."),
                        warning("Clutter Warning", "Johnny didn't do the dishes after cooking - environmental cluttering is possible.")],
    ),
    "LEKOMD": make_preset(
        name="LEKOMD",
        description="Sleep, Eat, Cook, Turn On, Meds, Dishes",

        diet_score=99,
        blood_sugar_score=83,
        medication_score=95,
        hygiene_score=87,
        independence_score=49,

        current_bg=105,
        bg_trend="stable",
        last_meal_time="10:30 AM",
        last_med_time="10:45 AM",
        stove_status="on",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": False,  "time": "9:40 AM"},
            {"task": "Eat breakfast",              "done": True,  "time": "10:30 AM"},
            {"task": "Take Medication",          "done": True,  "time": "10:45 AM"},
            {"task": "Do the Dishes",              "done": True, "time": "10:50 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "11:30 AM"},
            {"task": "Call Family",              "done": False,  "time": "2:00 PM"},
        ],

        weekly_history=[
            {"day": "Mon", "diet":95, "blood_sugar":78, "medication":98, "hygiene":91, "independence":51},
            {"day": "Tue", "diet":98, "blood_sugar":81, "medication":97, "hygiene":88, "independence":49},
            {"day": "Wed", "diet":97, "blood_sugar":87, "medication":92, "hygiene":92, "independence":48},
            {"day": "Thu", "diet":94, "blood_sugar":84, "medication":95, "hygiene":85, "independence":53},
            {"day": "Fri", "diet":91, "blood_sugar":88, "medication":96, "hygiene":83, "independence":52},
            {"day": "Sat", "diet":95, "blood_sugar":87, "medication":94, "hygiene":87, "independence":51},
            {"day": "Sun", "diet":96, "blood_sugar":82, "medication":97, "hygiene":88, "independence":51},
        ],

        timeline=[
            {"time": "9:00 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "9:15 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "10:00 AM", "label": "Stove on",    "icon": "🔥",   "type": "stove_on"},
            {"time": "10:05 AM", "label": "Fridge opened",         "icon": "🧊",  "type": "fridge"},
            {"time": "10:45 AM", "label": "Medication taken",      "icon": "💊",  "type": "medication"},
            {"time": "10:50 AM", "label": "Sink activity (dishes)","icon": "🫧",  "type": "dishes"},
            {"time": "11:00 AM", "label": "Blood sugar: 115 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[info("Easy Morning", "You slept well last night - let's start the day!"),
                                reinforcement("Breakfast", "Nicely done, chef Johnny! How was breakfast?"),
                                alert("Stove", "The stove has been left on, don't forget to turn it off.")],

        family_notifications=[info("Well-Rested", "Johnny got extra sleep last night."),
                                alert("Stove", "Johnny has left the stove on for 20 minutes and not responded.")],

        care_notifications=[alert("Stove Awareness", "Johnny failed to turn the stove off after cooking.")],
    ),
    "LEKOMT": make_preset(
        name="LEKOMT",
        description="Sleep, Eat, Cook, Turn On, Meds, TV",

        diet_score=99,
        blood_sugar_score=83,
        medication_score=95,
        hygiene_score=49,
        independence_score=31,

        current_bg=105,
        bg_trend="stable",
        last_meal_time="10:30 AM",
        last_med_time="10:45 AM",
        stove_status="on",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": False,  "time": "9:40 AM"},
            {"task": "Eat breakfast",              "done": True,  "time": "10:30 AM"},
            {"task": "Take Medication",          "done": True,  "time": "10:45 AM"},
            {"task": "Do the Dishes",              "done": False, "time": "10:50 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "11:30 AM"},
            {"task": "Call Family",              "done": False,  "time": "2:00 PM"},
        ],

        weekly_history=[
            {"day": "Mon", "diet":95, "blood_sugar":78, "medication":98, "hygiene":58, "independence":31},
            {"day": "Tue", "diet":98, "blood_sugar":81, "medication":97, "hygiene":55, "independence":29},
            {"day": "Wed", "diet":97, "blood_sugar":87, "medication":92, "hygiene":59, "independence":28},
            {"day": "Thu", "diet":94, "blood_sugar":84, "medication":95, "hygiene":52, "independence":33},
            {"day": "Fri", "diet":91, "blood_sugar":88, "medication":96, "hygiene":50, "independence":32},
            {"day": "Sat", "diet":95, "blood_sugar":87, "medication":94, "hygiene":54, "independence":31},
            {"day": "Sun", "diet":96, "blood_sugar":82, "medication":97, "hygiene":55, "independence":31},
        ],

        timeline=[
            {"time": "9:00 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "9:15 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "10:00 AM", "label": "Stove on",    "icon": "🔥",   "type": "stove_on"},
            {"time": "10:05 AM", "label": "Fridge opened",         "icon": "🧊",  "type": "fridge"},
            {"time": "10:45 AM", "label": "Medication taken",      "icon": "💊",  "type": "medication"},
            {"time": "11:00 AM", "label": "Blood sugar: 115 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[info("Easy Morning", "You slept well last night - let's start the day!"),
                                reinforcement("Breakfast", "Nicely done, chef Johnny! How was breakfast?"),
                                alert("Stove", "The stove has been left on, don't forget to turn it off.")],

        family_notifications=[info("Well-Rested", "Johnny got extra sleep last night."),
                                alert("Stove", "Johnny has left the stove on for 20 minutes and not responded.")],

        care_notifications=[warning("Clutter Warning", "Johnny didn't do the dishes after cooking - environmental cluttering is possible."),
                            alert("Stove Awareness", "Johnny failed to turn the stove off after cooking.")],
    ),
    "LEKOND": make_preset(
        name="LEKOND",
        description="Sleep, Eat, Cook, Turn On, No Meds, Dishes",

        diet_score=99,
        blood_sugar_score=64,
        medication_score=43,
        hygiene_score=87,
        independence_score=28,

        current_bg=173,
        bg_trend="rising",
        last_meal_time="10:30 AM",
        last_med_time="Yesterday, 8:00 PM",
        stove_status="on",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": False,  "time": "9:40 AM"},
            {"task": "Eat breakfast",              "done": True,  "time": "10:30 AM"},
            {"task": "Take Medication",          "done": False,  "time": "10:45 AM"},
            {"task": "Do the Dishes",              "done": True, "time": "10:50 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "11:30 AM"},
            {"task": "Call Family",              "done": False,  "time": "2:00 PM"},
        ],

        weekly_history=[
            {"day": "Mon", "diet":95, "blood_sugar":56, "medication":44, "hygiene":91, "independence":35},
            {"day": "Tue", "diet":98, "blood_sugar":59, "medication":43, "hygiene":88, "independence":33},
            {"day": "Wed", "diet":97, "blood_sugar":65, "medication":38, "hygiene":92, "independence":32},
            {"day": "Thu", "diet":94, "blood_sugar":62, "medication":41, "hygiene":85, "independence":37},
            {"day": "Fri", "diet":91, "blood_sugar":66, "medication":42, "hygiene":83, "independence":32},
            {"day": "Sat", "diet":95, "blood_sugar":65, "medication":40, "hygiene":87, "independence":31},
            {"day": "Sun", "diet":96, "blood_sugar":60, "medication":43, "hygiene":88, "independence":31},
        ],

        timeline=[
            {"time": "9:00 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "9:15 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "10:00 AM", "label": "Stove on",    "icon": "🔥",   "type": "stove_on"},
            {"time": "10:05 AM", "label": "Fridge opened",         "icon": "🧊",  "type": "fridge"},
            {"time": "10:50 AM", "label": "Sink activity (dishes)","icon": "🫧",  "type": "dishes"},
            {"time": "11:00 AM", "label": "Blood sugar: 183 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[info("Easy Morning", "You slept well last night - let's start the day!"),
                                reinforcement("Breakfast", "Nicely done, chef Johnny! How was breakfast?"),
                                warning("Medication", "Don't forget to take your medication, Johnny"),
                                alert("Stove", "The stove has been left on, don't forget to turn it off.")],

        family_notifications=[info("Well-Rested", "Johnny got extra sleep last night."),
                                warning("Medication", "Johnny forgot to take his medication today, want to check in?"),
                                alert("Stove", "Johnny has left the stove on for 20 minutes and not responded.")],

        care_notifications=[warning("Medication", "Johnny displayed reduced medication adherence, reflected in his blood glucose."),
                            alert("Stove Awareness", "Johnny failed to turn the stove off after cooking.")],
    ),
    "LEKONT": make_preset(
        name="LEKONT",
        description="Sleep, Eat, Cook, Turn On, No Meds, TV",

        diet_score=99,
        blood_sugar_score=58,
        medication_score=50,
        hygiene_score=49,
        independence_score=13,

        current_bg=171,
        bg_trend="rising",
        last_meal_time="10:30 AM",
        last_med_time="Yesterday, 8:00 PM",
        stove_status="on",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": False,  "time": "9:40 AM"},
            {"task": "Eat breakfast",              "done": True,  "time": "10:30 AM"},
            {"task": "Take Medication",          "done": False,  "time": "10:45 AM"},
            {"task": "Do the Dishes",              "done": False, "time": "10:50 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "11:30 AM"},
            {"task": "Call Family",              "done": False,  "time": "2:00 PM"},
        ],

        weekly_history=[
            {"day": "Mon", "diet":95, "blood_sugar":79, "medication":52, "hygiene":53, "independence":21},
            {"day": "Tue", "diet":98, "blood_sugar":52, "medication":51, "hygiene":50, "independence":19},
            {"day": "Wed", "diet":97, "blood_sugar":58, "medication":46, "hygiene":54, "independence":18},
            {"day": "Thu", "diet":94, "blood_sugar":55, "medication":49, "hygiene":47, "independence":23},
            {"day": "Fri", "diet":91, "blood_sugar":59, "medication":50, "hygiene":45, "independence":18},
            {"day": "Sat", "diet":95, "blood_sugar":58, "medication":48, "hygiene":42, "independence":17},
            {"day": "Sun", "diet":96, "blood_sugar":53, "medication":51, "hygiene":53, "independence":17},
        ],

        timeline=[
            {"time": "9:00 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "9:15 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "10:00 AM", "label": "Stove on",    "icon": "🔥",   "type": "stove_on"},
            {"time": "10:05 AM", "label": "Fridge opened",         "icon": "🧊",  "type": "fridge"},
            {"time": "11:00 AM", "label": "Blood sugar: 181 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[info("Easy Morning", "You slept well last night - let's start the day!"),
                                reinforcement("Breakfast", "Nicely done, chef Johnny! How was breakfast?"),
                                alert("Stove", "The stove has been left on, don't forget to turn it off."),
                                warning("Medication", "Don't forget to take your medication, Johnny")],

        family_notifications=[info("Well-Rested", "Johnny got extra sleep last night."),
                                alert("Stove", "Johnny has left the stove on for 20 minutes and not responded."),
                                warning("Medication", "Johnny forgot to take his medication today, want to check in?")],

        care_notifications=[warning("Clutter Warning", "Johnny didn't do the dishes after cooking - environmental cluttering is possible."),
                            alert("Stove Awareness", "Johnny failed to turn the stove off after cooking."),
                            warning("Medication", "Johnny displayed reduced medication adherence, reflected in his blood glucose.")],
    ),
    "LEJMD": make_preset(
        name="LEJMD",
        description="Sleep, Eat, Junk Food, Meds, Dishes",

        diet_score=35,
        blood_sugar_score=63,
        medication_score=94,
        hygiene_score=87,
        independence_score=74,

        current_bg=129,
        bg_trend="stable",
        last_meal_time="10:30 AM",
        last_med_time="10:45 AM",
        stove_status="off",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": False,  "time": "9:40 AM"},
            {"task": "Eat breakfast",              "done": True,  "time": "10:30 AM"},
            {"task": "Take Medication",          "done": True,  "time": "10:45 AM"},
            {"task": "Do the Dishes",              "done": True, "time": "10:50 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "11:30 AM"},
            {"task": "Call Family",              "done": False,  "time": "2:00 PM"},
        ],

        weekly_history=[
            {"day": "Mon", "diet":34, "blood_sugar":61, "medication":98, "hygiene":91, "independence":78},
            {"day": "Tue", "diet":37, "blood_sugar":64, "medication":97, "hygiene":88, "independence":76},
            {"day": "Wed", "diet":36, "blood_sugar":70, "medication":92, "hygiene":92, "independence":75},
            {"day": "Thu", "diet":33, "blood_sugar":67, "medication":95, "hygiene":85, "independence":80},
            {"day": "Fri", "diet":30, "blood_sugar":71, "medication":96, "hygiene":83, "independence":79},
            {"day": "Sat", "diet":34, "blood_sugar":70, "medication":94, "hygiene":87, "independence":78},
            {"day": "Sun", "diet":32, "blood_sugar":65, "medication":97, "hygiene":88, "independence":78},
        ],

        timeline=[
            {"time": "9:00 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "9:15 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "10:05 AM", "label": "Pantry opened",         "icon": "🚪",  "type": "pantry"},
            {"time": "10:45 AM", "label": "Medication taken",      "icon": "💊",  "type": "medication"},
            {"time": "10:50 AM", "label": "Sink activity (dishes)","icon": "🫧",  "type": "dishes"},
            {"time": "11:00 AM", "label": "Blood sugar: 138 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[info("Easy Morning", "You slept well last night - let's start the day!")],

        family_notifications=[info("Well-Rested", "Johnny got extra sleep last night."),
                                info("Breakfast", "Johnny ate but didn't cook - a grocery trip could be helpful.")],

        care_notifications=[warning("Breakfast", "Johnny hasn't cooked recently - ask him about his diet.")],
    ),
    "LEJMT": make_preset(
        name="LEJMT",
        description="Sleep, Eat, Junk Food, Meds, TV",

        diet_score=35,
        blood_sugar_score=63,
        medication_score=94,
        hygiene_score=48,
        independence_score=53,

        current_bg=129,
        bg_trend="stable",
        last_meal_time="10:30 AM",
        last_med_time="10:45 AM",
        stove_status="off",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": False,  "time": "9:40 AM"},
            {"task": "Eat breakfast",              "done": True,  "time": "10:30 AM"},
            {"task": "Take Medication",          "done": True,  "time": "10:45 AM"},
            {"task": "Do the Dishes",              "done": False, "time": "10:50 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "11:30 AM"},
            {"task": "Call Family",              "done": False,  "time": "2:00 PM"},
        ],

        weekly_history=[
            {"day": "Mon", "diet":35, "blood_sugar":58, "medication":98, "hygiene":51, "independence":56},
            {"day": "Tue", "diet":38, "blood_sugar":61, "medication":97, "hygiene":48, "independence":54},
            {"day": "Wed", "diet":37, "blood_sugar":67, "medication":92, "hygiene":52, "independence":53},
            {"day": "Thu", "diet":34, "blood_sugar":64, "medication":95, "hygiene":45, "independence":58},
            {"day": "Fri", "diet":31, "blood_sugar":68, "medication":96, "hygiene":53, "independence":57},
            {"day": "Sat", "diet":35, "blood_sugar":67, "medication":94, "hygiene":57, "independence":56},
            {"day": "Sun", "diet":36, "blood_sugar":62, "medication":97, "hygiene":58, "independence":56},
        ],

        timeline=[
            {"time": "9:00 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "9:15 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "10:05 AM", "label": "Pantry opened",         "icon": "🚪",  "type": "pantry"},
            {"time": "10:45 AM", "label": "Medication taken",      "icon": "💊",  "type": "medication"},
            {"time": "11:00 AM", "label": "Blood sugar: 138 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[info("Easy Morning", "You slept well last night - let's start the day!")],

        family_notifications=[info("Well-Rested", "Johnny got extra sleep last night."),
                                info("Breakfast", "Johnny ate but didn't cook - a grocery trip could be helpful.")],

        care_notifications=[warning("Breakfast", "Johnny hasn't cooked recently - ask him about his diet."),
                            warning("Clutter Warning", "Johnny didn't do the dishes after cooking - environmental cluttering is possible.")],
    ),
    "LEJND": make_preset(
        name="LEJND",
        description="Sleep, Eat, Junk Food, No Meds, Dishes",

        diet_score=35,
        blood_sugar_score=40,
        medication_score=51,
        hygiene_score=87,
        independence_score=52,

        current_bg=199,
        bg_trend="rising",
        last_meal_time="10:30 AM",
        last_med_time="Yesterday, 8:00 PM",
        stove_status="off",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": False,  "time": "9:40 AM"},
            {"task": "Eat breakfast",              "done": True,  "time": "10:30 AM"},
            {"task": "Take Medication",          "done": False,  "time": "10:45 AM"},
            {"task": "Do the Dishes",              "done": True, "time": "10:50 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "11:30 AM"},
            {"task": "Call Family",              "done": False,  "time": "2:00 PM"},
        ],

        weekly_history=[
            {"day": "Mon", "diet":35, "blood_sugar":33, "medication":53, "hygiene":91, "independence":56},
            {"day": "Tue", "diet":38, "blood_sugar":36, "medication":52, "hygiene":88, "independence":54},
            {"day": "Wed", "diet":37, "blood_sugar":42, "medication":47, "hygiene":92, "independence":53},
            {"day": "Thu", "diet":34, "blood_sugar":39, "medication":50, "hygiene":85, "independence":58},
            {"day": "Fri", "diet":31, "blood_sugar":43, "medication":51, "hygiene":83, "independence":57},
            {"day": "Sat", "diet":35, "blood_sugar":42, "medication":49, "hygiene":87, "independence":56},
            {"day": "Sun", "diet":36, "blood_sugar":37, "medication":52, "hygiene":88, "independence":56},
        ],

        timeline=[
            {"time": "9:00 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "9:15 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "10:05 AM", "label": "Pantry opened",         "icon": "🚪",  "type": "pantry"},
            {"time": "10:50 AM", "label": "Sink activity (dishes)","icon": "🫧",  "type": "dishes"},
            {"time": "11:00 AM", "label": "Blood sugar: 208 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[info("Easy Morning", "You slept well last night - let's start the day!"),
                                warning("Medication", "Don't forget to take your medication, Johnny")],

        family_notifications=[info("Well-Rested", "Johnny got extra sleep last night."),
                                info("Breakfast", "Johnny ate but didn't cook - a grocery trip could be helpful."),
                                warning("Medication", "Johnny forgot to take his medication today, want to check in?")],

        care_notifications=[warning("Breakfast", "Johnny hasn't cooked recently - ask him about his diet."),
                            warning("Medication", "Johnny displayed reduced medication adherence, reflected in his blood glucose.")],
    ),
    "LEJNT": make_preset(
        name="LEJNT",
        description="Sleep, Eat, Junk Food, No Meds, TV",

        diet_score=35,
        blood_sugar_score=40,
        medication_score=51,
        hygiene_score=50,
        independence_score=30,

        current_bg=167,
        bg_trend="stable",
        last_meal_time="10:30 AM",
        last_med_time="Yesterday, 8:00 PM",
        stove_status="off",

        todo_items=[
            {"day": "Mon", "diet":35, "blood_sugar":33, "medication":53, "hygiene":56, "independence":36},
            {"day": "Tue", "diet":38, "blood_sugar":36, "medication":52, "hygiene":53, "independence":34},
            {"day": "Wed", "diet":37, "blood_sugar":42, "medication":47, "hygiene":57, "independence":33},
            {"day": "Thu", "diet":34, "blood_sugar":39, "medication":50, "hygiene":50, "independence":38},
            {"day": "Fri", "diet":31, "blood_sugar":43, "medication":51, "hygiene":47, "independence":37},
            {"day": "Sat", "diet":35, "blood_sugar":42, "medication":49, "hygiene":52, "independence":36},
            {"day": "Sun", "diet":36, "blood_sugar":37, "medication":52, "hygiene":53, "independence":36},
        ],

        weekly_history=week_good(),

        timeline=[
            {"time": "9:00 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "9:15 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "10:05 AM", "label": "Pantry opened",         "icon": "🚪",  "type": "pantry"},
            {"time": "11:00 AM", "label": "Blood sugar: 176 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[info("Easy Morning", "You slept well last night - let's start the day!"),
                                warning("Medication", "Don't forget to take your medication, Johnny")],

        family_notifications=[info("Well-Rested", "Johnny got extra sleep last night."),
                                info("Breakfast", "Johnny ate but didn't cook - a grocery trip could be helpful."),
                                warning("Medication", "Johnny forgot to take his medication today, want to check in?")],

        care_notifications=[warning("Breakfast", "Johnny hasn't cooked recently - ask him about his diet."),
                            warning("Medication", "Johnny displayed reduced medication adherence, reflected in his blood glucose."),
                            warning("Clutter Warning", "Johnny didn't do the dishes after cooking - environmental cluttering is possible.")],
    ),
    "LAMD": make_preset(
        name="LAMD",
        description="Sleep, No Eat, Meds, Dishes",

        diet_score=58,
        blood_sugar_score=51,
        medication_score=98,
        hygiene_score=88,
        independence_score=57,

        current_bg=31,
        bg_trend="falling",
        last_meal_time="Yesterday, 6:30 PM",
        last_med_time="10:45 AM",
        stove_status="off",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": False,  "time": "9:40 AM"},
            {"task": "Eat breakfast",              "done": False,  "time": "10:30 AM"},
            {"task": "Take Medication",          "done": True,  "time": "10:45 AM"},
            {"task": "Do the Dishes",              "done": True, "time": "10:50 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "11:30 AM"},
            {"task": "Call Family",              "done": False,  "time": "2:00 PM"},
        ],

        weekly_history=[
            {"day": "Mon", "diet":55, "blood_sugar":48, "medication":98, "hygiene":91, "independence":56},
            {"day": "Tue", "diet":58, "blood_sugar":51, "medication":97, "hygiene":88, "independence":54},
            {"day": "Wed", "diet":57, "blood_sugar":57, "medication":92, "hygiene":92, "independence":53},
            {"day": "Thu", "diet":54, "blood_sugar":54, "medication":95, "hygiene":85, "independence":58},
            {"day": "Fri", "diet":51, "blood_sugar":58, "medication":96, "hygiene":83, "independence":57},
            {"day": "Sat", "diet":55, "blood_sugar":57, "medication":94, "hygiene":87, "independence":56},
            {"day": "Sun", "diet":56, "blood_sugar":52, "medication":97, "hygiene":88, "independence":56},
        ],

        timeline=[
            {"time": "9:00 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "9:15 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "10:45 AM", "label": "Medication taken",      "icon": "💊",  "type": "medication"},
            {"time": "10:50 AM", "label": "Sink activity (dishes)","icon": "🫧",  "type": "dishes"},
            {"time": "11:00 AM", "label": "Blood sugar: 40 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[info("Easy Morning", "You slept well last night - let's start the day!"),
                                warning("Breakfast", "It looks like you haven't made breakfast yet. Make sure to eat at some point.")],

        family_notifications=[info("Well-Rested", "Johnny got extra sleep last night."),
                                warning("Breakfast", "Johnny has not made breakfast, would you like to call to check in?")],

        care_notifications=[warning("Inconsistent Diet", "Johnny has skipped eating breakfast, creating volatile BG readings.")],
    ),
    "LAMT": make_preset(
        name="LAMT",
        description="Sleep, No Eat, Meds, TV",

        diet_score=58,
        blood_sugar_score=51,
        medication_score=98,
        hygiene_score=50,
        independence_score=41,

        current_bg=31,
        bg_trend="falling",
        last_meal_time="Yesterday, 6:30 PM",
        last_med_time="10:45 AM",
        stove_status="off",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": False,  "time": "9:40 AM"},
            {"task": "Eat breakfast",              "done": False,  "time": "10:30 AM"},
            {"task": "Take Medication",          "done": True,  "time": "10:45 AM"},
            {"task": "Do the Dishes",              "done": False, "time": "10:50 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "11:30 AM"},
            {"task": "Call Family",              "done": False,  "time": "2:00 PM"},
        ],

        weekly_history=[
            {"day": "Mon", "diet":65, "blood_sugar":53, "medication":98, "hygiene":56, "independence":46},
            {"day": "Tue", "diet":68, "blood_sugar":56, "medication":97, "hygiene":58, "independence":44},
            {"day": "Wed", "diet":67, "blood_sugar":62, "medication":92, "hygiene":57, "independence":43},
            {"day": "Thu", "diet":64, "blood_sugar":59, "medication":95, "hygiene":50, "independence":48},
            {"day": "Fri", "diet":61, "blood_sugar":63, "medication":96, "hygiene":48, "independence":47},
            {"day": "Sat", "diet":65, "blood_sugar":62, "medication":94, "hygiene":52, "independence":46},
            {"day": "Sun", "diet":66, "blood_sugar":57, "medication":97, "hygiene":53, "independence":46},
        ],

        timeline=[
            {"time": "9:00 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "9:15 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "10:45 AM", "label": "Medication taken",      "icon": "💊",  "type": "medication"},
            {"time": "11:00 AM", "label": "Blood sugar: 40 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[info("Easy Morning", "You slept well last night - let's start the day!"),
                                warning("Breakfast", "It looks like you haven't made breakfast yet. Make sure to eat at some point.")],

        family_notifications=[info("Well-Rested", "Johnny got extra sleep last night."),
                                warning("Breakfast", "Johnny has not made breakfast, would you like to call to check in?")],

        care_notifications=[warning("Inconsistent Diet", "Johnny has skipped eating breakfast, creating volatile BG readings."),
                            warning("Clutter Warning", "Johnny didn't do the dishes after cooking - environmental cluttering is possible.")],
    ),
    "LAND": make_preset(
        name="LAND",
        description="Sleep, No Eat, No Meds, Dishes",

        diet_score=58,
        blood_sugar_score=31,
        medication_score=47,
        hygiene_score=88,
        independence_score=39,

        current_bg=82,
        bg_trend="stable",
        last_meal_time="Yesterday, 6:30 PM",
        last_med_time="Yesterday, 8:00 PM",
        stove_status="off",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": False,  "time": "9:40 AM"},
            {"task": "Eat breakfast",              "done": False,  "time": "10:30 AM"},
            {"task": "Take Medication",          "done": False,  "time": "10:45 AM"},
            {"task": "Do the Dishes",              "done": True, "time": "10:50 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "11:30 AM"},
            {"task": "Call Family",              "done": False,  "time": "2:00 PM"},
        ],

        weekly_history=[
            {"day": "Mon", "diet":55, "blood_sugar":28, "medication":48, "hygiene":91, "independence":36},
            {"day": "Tue", "diet":58, "blood_sugar":31, "medication":47, "hygiene":88, "independence":34},
            {"day": "Wed", "diet":57, "blood_sugar":37, "medication":42, "hygiene":92, "independence":33},
            {"day": "Thu", "diet":54, "blood_sugar":34, "medication":45, "hygiene":85, "independence":38},
            {"day": "Fri", "diet":51, "blood_sugar":38, "medication":46, "hygiene":83, "independence":37},
            {"day": "Sat", "diet":55, "blood_sugar":37, "medication":44, "hygiene":87, "independence":36},
            {"day": "Sun", "diet":56, "blood_sugar":32, "medication":47, "hygiene":88, "independence":36},
        ],


        timeline=[
            {"time": "9:00 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "9:15 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "10:50 AM", "label": "Sink activity (dishes)","icon": "🫧",  "type": "dishes"},
            {"time": "11:00 AM", "label": "Blood sugar: 91 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[info("Easy Morning", "You slept well last night - let's start the day!"),
                                warning("Breakfast", "It looks like you haven't made breakfast yet. Make sure to eat at some point."),
                                warning("Medication", "Don't forget to take your medication, Johnny")],

        family_notifications=[info("Well-Rested", "Johnny got extra sleep last night."),
                                warning("Breakfast", "Johnny has not made breakfast, would you like to call to check in?"),
                                warning("Medication", "Johnny forgot to take his medication today, want to check in?")],

        care_notifications=[warning("Inconsistent Diet", "Johnny has skipped eating breakfast, creating volatile BG readings."),
                            warning("Medication", "Johnny displayed reduced medication adherence, reflected in his blood glucose.")],
    ),
    "LANT": make_preset(
        name="LANT",
        description="Sleep, No Eat, No Meds, TV",

        diet_score=58,
        blood_sugar_score=31,
        medication_score=47,
        hygiene_score=41,
        independence_score=15,

        current_bg=82,
        bg_trend="stable",
        last_meal_time="Yesterday, 6:30 PM",
        last_med_time="Yesterday, 8:00 PM",
        stove_status="off",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": False,  "time": "9:40 AM"},
            {"task": "Eat breakfast",              "done": False,  "time": "10:30 AM"},
            {"task": "Take Medication",          "done": False,  "time": "10:45 AM"},
            {"task": "Do the Dishes",              "done": False, "time": "10:50 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "11:30 AM"},
            {"task": "Call Family",              "done": False,  "time": "2:00 PM"},
        ],

        weekly_history=[
            {"day": "Mon", "diet":55, "blood_sugar":28, "medication":48, "hygiene":46, "independence":11},
            {"day": "Tue", "diet":58, "blood_sugar":31, "medication":47, "hygiene":43, "independence":9},
            {"day": "Wed", "diet":57, "blood_sugar":37, "medication":42, "hygiene":47, "independence":7},
            {"day": "Thu", "diet":54, "blood_sugar":34, "medication":45, "hygiene":40, "independence":13},
            {"day": "Fri", "diet":51, "blood_sugar":38, "medication":46, "hygiene":38, "independence":12},
            {"day": "Sat", "diet":55, "blood_sugar":37, "medication":44, "hygiene":42, "independence":11},
            {"day": "Sun", "diet":56, "blood_sugar":32, "medication":47, "hygiene":43, "independence":11},
        ],

        timeline=[
            {"time": "9:00 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "9:15 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "11:00 AM", "label": "Blood sugar: 91 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[info("Easy Morning", "You slept well last night - let's start the day!"),
                                warning("Breakfast", "It looks like you haven't made breakfast yet. Make sure to eat at some point."),
                                warning("Medication", "Don't forget to take your medication, Johnny")],

        family_notifications=[info("Well-Rested", "Johnny got extra sleep last night."),
                                warning("Breakfast", "Johnny has not made breakfast, would you like to call to check in?"),
                                warning("Medication", "Johnny forgot to take his medication today, want to check in?")],

        care_notifications=[warning("Inconsistent Diet", "Johnny has skipped eating breakfast, creating volatile BG readings."),
                            warning("Medication", "Johnny displayed reduced medication adherence, reflected in his blood glucose."),
                            warning("Clutter Warning", "Johnny didn't do the dishes after cooking - environmental cluttering is possible.")],
    ),
    "SUEKFMD": make_preset(
        name="SUEKFMD",
        description="Start, No Coffee, Eat, Cook, Turn Off, Meds, Dishes",

        diet_score=97,
        blood_sugar_score=100,
        medication_score=98,
        hygiene_score=99,
        independence_score=98,

        current_bg=132,
        bg_trend="stable",
        last_meal_time="9:00 AM",
        last_med_time="9:15 AM",
        stove_status="off",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": False,  "time": "8:10 AM"},
            {"task": "Eat breakfast",              "done": True,  "time": "9:00 AM"},
            {"task": "Take Medication",          "done": True,  "time": "9:15 AM"},
            {"task": "Do the Dishes",              "done": True, "time": "9:20 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "10:00 AM"},
            {"task": "Call Family",              "done": False,  "time": "12:30 PM"},
        ],

        weekly_history=[
            {"day": "Mon", "diet":95, "blood_sugar":98, "medication":98, "hygiene":91, "independence":96},
            {"day": "Tue", "diet":98, "blood_sugar":100, "medication":97, "hygiene":98, "independence":94},
            {"day": "Wed", "diet":97, "blood_sugar":97, "medication":92, "hygiene":92, "independence":93},
            {"day": "Thu", "diet":94, "blood_sugar":94, "medication":95, "hygiene":95, "independence":98},
            {"day": "Fri", "diet":91, "blood_sugar":98, "medication":96, "hygiene":93, "independence":97},
            {"day": "Sat", "diet":95, "blood_sugar":97, "medication":94, "hygiene":97, "independence":96},
            {"day": "Sun", "diet":96, "blood_sugar":92, "medication":97, "hygiene":98, "independence":96},
        ],

        timeline=[
            {"time": "7:30 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "7:45 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "8:30 AM", "label": "Stove on",    "icon": "🔥",   "type": "stove_on"},
            {"time": "8:35 AM", "label": "Fridge opened",         "icon": "🧊",  "type": "fridge"},
            {"time": "8:50 AM", "label": "Stove off (20 min)",    "icon": "✓",   "type": "stove_off"},
            {"time": "9:15 AM", "label": "Medication taken",      "icon": "💊",  "type": "medication"},
            {"time": "9:20 AM", "label": "Sink activity (dishes)","icon": "🫧",  "type": "dishes"},
            {"time": "9:30 AM", "label": "Blood sugar: 141 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[reinforcement("Rise and Shine!", "Good morning Johnny! Ready to start the day?"),
                                reinforcement("Breakfast", "Nicely done, chef Johnny! How was breakfast?")],

        family_notifications=[info("Rise and Shine!", "Johnny is awake. Want to say good morning?")],

        care_notifications=[],
    ),
    "SUEKFMT": make_preset(
        name="SUEKFMT",
        description="Start, No Coffee, Eat, Cook, Turn Off, Meds, TV",

        diet_score=97,
        blood_sugar_score=100,
        medication_score=98,
        hygiene_score=56,
        independence_score=77,

        current_bg=132,
        bg_trend="stable",
        last_meal_time="9:00 AM",
        last_med_time="9:15 AM",
        stove_status="off",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": False,  "time": "8:10 AM"},
            {"task": "Eat breakfast",              "done": True,  "time": "9:00 AM"},
            {"task": "Take Medication",          "done": True,  "time": "9:15 AM"},
            {"task": "Do the Dishes",              "done": False, "time": "9:20 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "10:00 AM"},
            {"task": "Call Family",              "done": False,  "time": "12:30 PM"},
        ],

        weekly_history=[
            {"day": "Mon", "diet":95, "blood_sugar":98, "medication":98, "hygiene":51, "independence":76},
            {"day": "Tue", "diet":98, "blood_sugar":100, "medication":97, "hygiene":58, "independence":74},
            {"day": "Wed", "diet":97, "blood_sugar":97, "medication":92, "hygiene":52, "independence":73},
            {"day": "Thu", "diet":94, "blood_sugar":94, "medication":95, "hygiene":55, "independence":78},
            {"day": "Fri", "diet":91, "blood_sugar":98, "medication":96, "hygiene":53, "independence":77},
            {"day": "Sat", "diet":95, "blood_sugar":97, "medication":94, "hygiene":57, "independence":76},
            {"day": "Sun", "diet":96, "blood_sugar":92, "medication":97, "hygiene":58, "independence":76},
        ],

        timeline=[
            {"time": "7:30 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "7:45 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "8:30 AM", "label": "Stove on",    "icon": "🔥",   "type": "stove_on"},
            {"time": "8:35 AM", "label": "Fridge opened",         "icon": "🧊",  "type": "fridge"},
            {"time": "8:50 AM", "label": "Stove off (20 min)",    "icon": "✓",   "type": "stove_off"},
            {"time": "9:15 AM", "label": "Medication taken",      "icon": "💊",  "type": "medication"},
            {"time": "9:30 AM", "label": "Blood sugar: 141 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[reinforcement("Rise and Shine!", "Good morning Johnny! Ready to start the day?"),
                                reinforcement("Breakfast", "Nicely done, chef Johnny! How was breakfast?")],

        family_notifications=[info("Rise and Shine!", "Johnny is awake. Want to say good morning?")],

        care_notifications=[warning("Clutter Warning", "Johnny didn't do the dishes after cooking - environmental cluttering is possible.")],
    ),
    "SUEKFND": make_preset(
        name="SUEKFND",
        description="Start, No Coffee, Eat, Cook, Turn Off, No Meds, Dishes",

        diet_score=97,
        blood_sugar_score=78,
        medication_score=54,
        hygiene_score=99,
        independence_score=81,

        current_bg=198,
        bg_trend="rising",
        last_meal_time="9:00 AM",
        last_med_time="Yesterday, 8:00 PM",
        stove_status="off",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": False,  "time": "8:10 AM"},
            {"task": "Eat breakfast",              "done": True,  "time": "9:00 AM"},
            {"task": "Take Medication",          "done": False,  "time": "9:15 AM"},
            {"task": "Do the Dishes",              "done": True, "time": "9:20 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "10:00 AM"},
            {"task": "Call Family",              "done": False,  "time": "12:30 PM"},
        ],

        weekly_history=[
            {"day": "Mon", "diet":95, "blood_sugar":78, "medication":58, "hygiene":91, "independence":86},
            {"day": "Tue", "diet":98, "blood_sugar":80, "medication":57, "hygiene":98, "independence":84},
            {"day": "Wed", "diet":97, "blood_sugar":77, "medication":52, "hygiene":92, "independence":83},
            {"day": "Thu", "diet":94, "blood_sugar":74, "medication":55, "hygiene":95, "independence":88},
            {"day": "Fri", "diet":91, "blood_sugar":78, "medication":56, "hygiene":93, "independence":87},
            {"day": "Sat", "diet":95, "blood_sugar":77, "medication":54, "hygiene":97, "independence":86},
            {"day": "Sun", "diet":96, "blood_sugar":72, "medication":57, "hygiene":98, "independence":86},
        ],

        timeline=[
            {"time": "7:30 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "7:45 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "8:30 AM", "label": "Stove on",    "icon": "🔥",   "type": "stove_on"},
            {"time": "8:35 AM", "label": "Fridge opened",         "icon": "🧊",  "type": "fridge"},
            {"time": "8:50 AM", "label": "Stove off (20 min)",    "icon": "✓",   "type": "stove_off"},
            {"time": "9:20 AM", "label": "Sink activity (dishes)","icon": "🫧",  "type": "dishes"},
            {"time": "9:30 AM", "label": "Blood sugar: 207 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[reinforcement("Rise and Shine!", "Good morning Johnny! Ready to start the day?"),
                                reinforcement("Breakfast", "Nicely done, chef Johnny! How was breakfast?"),
                                warning("Medication", "Don't forget to take your medication, Johnny")],

        family_notifications=[info("Rise and Shine!", "Johnny is awake. Want to say good morning?"),
                                warning("Medication", "Johnny forgot to take his medication today, want to check in?")],

        care_notifications=[warning("Medication", "Johnny displayed reduced medication adherence, reflected in his blood glucose.")],
    ),
    "SUEKFNT": make_preset(
        name="SUEKFNT",
        description="Start, No Coffee, Eat, Cook, Turn Off, No Meds, TV",

        diet_score=97,
        blood_sugar_score=78,
        medication_score=54,
        hygiene_score=53,
        independence_score=61,

        current_bg=198,
        bg_trend="rising",
        last_meal_time="9:00 AM",
        last_med_time="Yesterday, 8:00 PM",
        stove_status="off",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": False,  "time": "8:10 AM"},
            {"task": "Eat breakfast",              "done": True,  "time": "9:00 AM"},
            {"task": "Take Medication",          "done": False,  "time": "9:15 AM"},
            {"task": "Do the Dishes",              "done": False, "time": "9:20 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "10:00 AM"},
            {"task": "Call Family",              "done": False,  "time": "12:30 PM"},
        ],

        weekly_history=[
            {"day": "Mon", "diet":95, "blood_sugar":78, "medication":58, "hygiene":51, "independence":66},
            {"day": "Tue", "diet":98, "blood_sugar":80, "medication":57, "hygiene":58, "independence":64},
            {"day": "Wed", "diet":97, "blood_sugar":77, "medication":52, "hygiene":52, "independence":63},
            {"day": "Thu", "diet":94, "blood_sugar":74, "medication":55, "hygiene":55, "independence":68},
            {"day": "Fri", "diet":91, "blood_sugar":78, "medication":56, "hygiene":53, "independence":67},
            {"day": "Sat", "diet":95, "blood_sugar":77, "medication":54, "hygiene":57, "independence":66},
            {"day": "Sun", "diet":96, "blood_sugar":72, "medication":57, "hygiene":58, "independence":66},
        ],

        timeline=[
            {"time": "7:30 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "7:45 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "8:30 AM", "label": "Stove on",    "icon": "🔥",   "type": "stove_on"},
            {"time": "8:35 AM", "label": "Fridge opened",         "icon": "🧊",  "type": "fridge"},
            {"time": "8:50 AM", "label": "Stove off (20 min)",    "icon": "✓",   "type": "stove_off"},
            {"time": "9:30 AM", "label": "Blood sugar: 207 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[reinforcement("Rise and Shine!", "Good morning Johnny! Ready to start the day?"),
                                reinforcement("Breakfast", "Nicely done, chef Johnny! How was breakfast?"),
                                warning("Medication", "Don't forget to take your medication, Johnny")],

        family_notifications=[info("Rise and Shine!", "Johnny is awake. Want to say good morning?"),
                                warning("Medication", "Johnny forgot to take his medication today, want to check in?")],

        care_notifications=[warning("Medication", "Johnny displayed reduced medication adherence, reflected in his blood glucose."),
                            warning("Clutter Warning", "Johnny didn't do the dishes after cooking - environmental cluttering is possible.")],
    ),
    "SUEKOMD": make_preset(
        name="SUEKOMD",
        description="Start, No Coffee, Eat, Cook, Turn On, Meds, Dishes",

        diet_score=97,
        blood_sugar_score=100,
        medication_score=98,
        hygiene_score=99,
        independence_score=62,

        current_bg=132,
        bg_trend="stable",
        last_meal_time="9:00 AM",
        last_med_time="9:15 AM",
        stove_status="on",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": False,  "time": "8:10 AM"},
            {"task": "Eat breakfast",              "done": True,  "time": "9:00 AM"},
            {"task": "Take Medication",          "done": True,  "time": "9:15 AM"},
            {"task": "Do the Dishes",              "done": True, "time": "9:20 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "10:00 AM"},
            {"task": "Call Family",              "done": False,  "time": "12:30 PM"},
        ],

        weekly_history=[
            {"day": "Mon", "diet":95, "blood_sugar":98, "medication":98, "hygiene":91, "independence":66},
            {"day": "Tue", "diet":98, "blood_sugar":100, "medication":97, "hygiene":98, "independence":64},
            {"day": "Wed", "diet":97, "blood_sugar":97, "medication":92, "hygiene":92, "independence":63},
            {"day": "Thu", "diet":94, "blood_sugar":94, "medication":95, "hygiene":95, "independence":68},
            {"day": "Fri", "diet":91, "blood_sugar":98, "medication":96, "hygiene":93, "independence":67},
            {"day": "Sat", "diet":95, "blood_sugar":97, "medication":94, "hygiene":97, "independence":66},
            {"day": "Sun", "diet":96, "blood_sugar":92, "medication":97, "hygiene":98, "independence":66},
        ],

        timeline=[
            {"time": "7:30 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "7:45 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "8:30 AM", "label": "Stove on",    "icon": "🔥",   "type": "stove_on"},
            {"time": "8:35 AM", "label": "Fridge opened",         "icon": "🧊",  "type": "fridge"},
            {"time": "9:15 AM", "label": "Medication taken",      "icon": "💊",  "type": "medication"},
            {"time": "9:20 AM", "label": "Sink activity (dishes)","icon": "🫧",  "type": "dishes"},
            {"time": "9:30 AM", "label": "Blood sugar: 141 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[reinforcement("Rise and Shine!", "Good morning Johnny! Ready to start the day?"),
                                reinforcement("Breakfast", "Nicely done, chef Johnny! How was breakfast?"),
                                alert("Stove", "The stove has been left on, don't forget to turn it off.")],

        family_notifications=[info("Rise and Shine!", "Johnny is awake. Want to say good morning?"),
                                alert("Stove", "Johnny has left the stove on for 20 minutes and not responded.")],

        care_notifications=[alert("Stove Awareness", "Johnny failed to turn the stove off after cooking.")],
    ),
    "SUEKOMT": make_preset(
        name="SUEKOMT",
        description="Start, No Coffee, Eat, Cook, Turn On, Meds, TV",

        diet_score=97,
        blood_sugar_score=100,
        medication_score=98,
        hygiene_score=56,
        independence_score=37,

        current_bg=132,
        bg_trend="stable",
        last_meal_time="9:00 AM",
        last_med_time="9:15 AM",
        stove_status="on",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": False,  "time": "8:10 AM"},
            {"task": "Eat breakfast",              "done": True,  "time": "9:00 AM"},
            {"task": "Take Medication",          "done": True,  "time": "9:15 AM"},
            {"task": "Do the Dishes",              "done": False, "time": "9:20 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "10:00 AM"},
            {"task": "Call Family",              "done": False,  "time": "12:30 PM"},
        ],

        weekly_history=[
            {"day": "Mon", "diet":95, "blood_sugar":98, "medication":98, "hygiene":51, "independence":36},
            {"day": "Tue", "diet":98, "blood_sugar":100, "medication":97, "hygiene":58, "independence":34},
            {"day": "Wed", "diet":97, "blood_sugar":97, "medication":92, "hygiene":52, "independence":33},
            {"day": "Thu", "diet":94, "blood_sugar":94, "medication":95, "hygiene":55, "independence":38},
            {"day": "Fri", "diet":91, "blood_sugar":98, "medication":96, "hygiene":53, "independence":37},
            {"day": "Sat", "diet":95, "blood_sugar":97, "medication":94, "hygiene":57, "independence":36},
            {"day": "Sun", "diet":96, "blood_sugar":92, "medication":97, "hygiene":58, "independence":36},
        ],

        timeline=[
            {"time": "7:30 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "7:45 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "8:30 AM", "label": "Stove on",    "icon": "🔥",   "type": "stove_on"},
            {"time": "8:35 AM", "label": "Fridge opened",         "icon": "🧊",  "type": "fridge"},
            {"time": "9:15 AM", "label": "Medication taken",      "icon": "💊",  "type": "medication"},
            {"time": "9:30 AM", "label": "Blood sugar: 141 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[reinforcement("Rise and Shine!", "Good morning Johnny! Ready to start the day?"),
                                reinforcement("Breakfast", "Nicely done, chef Johnny! How was breakfast?"),
                                alert("Stove", "The stove has been left on, don't forget to turn it off.")],

        family_notifications=[info("Rise and Shine!", "Johnny is awake. Want to say good morning?"),
                                alert("Stove", "Johnny has left the stove on for 20 minutes and not responded.")],

        care_notifications=[alert("Stove Awareness", "Johnny failed to turn the stove off after cooking."),
                            warning("Clutter Warning", "Johnny didn't do the dishes after cooking - environmental cluttering is possible.")],
    ),
    "SUEKOND": make_preset(
        name="SUEKOND",
        description="Start, No Coffee, Eat, Cook, Turn On, No Meds, Dishes",

        diet_score=97,
        blood_sugar_score=74,
        medication_score=48,
        hygiene_score=99,
        independence_score=42,

        current_bg=191,
        bg_trend="rising",
        last_meal_time="9:00 AM",
        last_med_time="Yesterday, 8:00 PM",
        stove_status="on",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": False,  "time": "8:10 AM"},
            {"task": "Eat breakfast",              "done": True,  "time": "9:00 AM"},
            {"task": "Take Medication",          "done": False,  "time": "9:15 AM"},
            {"task": "Do the Dishes",              "done": True, "time": "9:20 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "10:00 AM"},
            {"task": "Call Family",              "done": False,  "time": "12:30 PM"},
        ],

        weekly_history=[
            {"day": "Mon", "diet":95, "blood_sugar":78, "medication":48, "hygiene":91, "independence":46},
            {"day": "Tue", "diet":98, "blood_sugar":80, "medication":47, "hygiene":98, "independence":44},
            {"day": "Wed", "diet":97, "blood_sugar":77, "medication":42, "hygiene":92, "independence":43},
            {"day": "Thu", "diet":94, "blood_sugar":74, "medication":45, "hygiene":95, "independence":48},
            {"day": "Fri", "diet":91, "blood_sugar":78, "medication":46, "hygiene":93, "independence":47},
            {"day": "Sat", "diet":95, "blood_sugar":77, "medication":44, "hygiene":97, "independence":46},
            {"day": "Sun", "diet":96, "blood_sugar":72, "medication":47, "hygiene":98, "independence":46},
        ],

        timeline=[
            {"time": "7:30 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "7:45 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "8:30 AM", "label": "Stove on",    "icon": "🔥",   "type": "stove_on"},
            {"time": "8:35 AM", "label": "Fridge opened",         "icon": "🧊",  "type": "fridge"},
            {"time": "9:20 AM", "label": "Sink activity (dishes)","icon": "🫧",  "type": "dishes"},
            {"time": "9:30 AM", "label": "Blood sugar: 200 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[reinforcement("Rise and Shine!", "Good morning Johnny! Ready to start the day?"),
                                reinforcement("Breakfast", "Nicely done, chef Johnny! How was breakfast?"),
                                alert("Stove", "The stove has been left on, don't forget to turn it off."),
                                warning("Medication", "Don't forget to take your medication, Johnny")],

        family_notifications=[info("Rise and Shine!", "Johnny is awake. Want to say good morning?"),
                                alert("Stove", "Johnny has left the stove on for 20 minutes and not responded."),
                                warning("Medication", "Johnny forgot to take his medication today, want to check in?")],

        care_notifications=[alert("Stove Awareness", "Johnny failed to turn the stove off after cooking."),
                            warning("Medication", "Johnny displayed reduced medication adherence, reflected in his blood glucose.")],
    ),
    "SUEKONT": make_preset(
        name="SUEKONT",
        description="Start, No Coffee, Eat, Cook, Turn On, No Meds, TV",

        diet_score=97,
        blood_sugar_score=74,
        medication_score=48,
        hygiene_score=61,
        independence_score=21,

        current_bg=191,
        bg_trend="rising",
        last_meal_time="9:00 AM",
        last_med_time="Yesterday, 8:00 PM",
        stove_status="on",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": False,  "time": "8:10 AM"},
            {"task": "Eat breakfast",              "done": True,  "time": "9:00 AM"},
            {"task": "Take Medication",          "done": False,  "time": "9:15 AM"},
            {"task": "Do the Dishes",              "done": False, "time": "9:20 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "10:00 AM"},
            {"task": "Call Family",              "done": False,  "time": "12:30 PM"},
        ],

        weekly_history=[
            {"day": "Mon", "diet":95, "blood_sugar":78, "medication":48, "hygiene":61, "independence":26},
            {"day": "Tue", "diet":98, "blood_sugar":80, "medication":47, "hygiene":68, "independence":24},
            {"day": "Wed", "diet":97, "blood_sugar":77, "medication":42, "hygiene":62, "independence":23},
            {"day": "Thu", "diet":94, "blood_sugar":74, "medication":45, "hygiene":65, "independence":28},
            {"day": "Fri", "diet":91, "blood_sugar":78, "medication":46, "hygiene":63, "independence":27},
            {"day": "Sat", "diet":95, "blood_sugar":77, "medication":44, "hygiene":67, "independence":26},
            {"day": "Sun", "diet":96, "blood_sugar":72, "medication":47, "hygiene":68, "independence":26},
        ],

        timeline=[
            {"time": "7:30 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "7:45 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "8:30 AM", "label": "Stove on",    "icon": "🔥",   "type": "stove_on"},
            {"time": "8:35 AM", "label": "Fridge opened",         "icon": "🧊",  "type": "fridge"},
            {"time": "9:30 AM", "label": "Blood sugar: 200 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[reinforcement("Rise and Shine!", "Good morning Johnny! Ready to start the day?"),
                                reinforcement("Breakfast", "Nicely done, chef Johnny! How was breakfast?"),
                                alert("Stove", "The stove has been left on, don't forget to turn it off."),
                                warning("Medication", "Don't forget to take your medication, Johnny")],

        family_notifications=[info("Rise and Shine!", "Johnny is awake. Want to say good morning?"),
                                alert("Stove", "Johnny has left the stove on for 20 minutes and not responded."),
                                warning("Medication", "Johnny forgot to take his medication today, want to check in?")],

        care_notifications=[alert("Stove Awareness", "Johnny failed to turn the stove off after cooking."),
                            warning("Medication", "Johnny displayed reduced medication adherence, reflected in his blood glucose."),
                            warning("Clutter Warning", "Johnny didn't do the dishes after cooking - environmental cluttering is possible.")],
    ),
    "SUEJMD": make_preset(
        name="SUEJMD",
        description="Start, No Coffee, Eat, Junk Food, Meds, Dishes",

        diet_score=38,
        blood_sugar_score=80,
        medication_score=98,
        hygiene_score=99,
        independence_score=82,

        current_bg=152,
        bg_trend="stable",
        last_meal_time="9:00 AM",
        last_med_time="9:15 AM",
        stove_status="off",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": False,  "time": "8:10 AM"},
            {"task": "Eat breakfast",              "done": True,  "time": "9:00 AM"},
            {"task": "Take Medication",          "done": True,  "time": "9:15 AM"},
            {"task": "Do the Dishes",              "done": True, "time": "9:20 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "10:00 AM"},
            {"task": "Call Family",              "done": False,  "time": "12:30 PM"},
        ],

        weekly_history=[
            {"day": "Mon", "diet":35, "blood_sugar":88, "medication":98, "hygiene":91, "independence":86},
            {"day": "Tue", "diet":38, "blood_sugar":80, "medication":97, "hygiene":98, "independence":84},
            {"day": "Wed", "diet":37, "blood_sugar":87, "medication":92, "hygiene":92, "independence":83},
            {"day": "Thu", "diet":34, "blood_sugar":84, "medication":95, "hygiene":95, "independence":88},
            {"day": "Fri", "diet":31, "blood_sugar":88, "medication":96, "hygiene":93, "independence":87},
            {"day": "Sat", "diet":35, "blood_sugar":87, "medication":94, "hygiene":97, "independence":86},
            {"day": "Sun", "diet":36, "blood_sugar":82, "medication":97, "hygiene":98, "independence":86},
        ],

        timeline=[
            {"time": "7:30 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "7:45 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "8:30 AM", "label": "Pantry opened",         "icon": "🚪",  "type": "pantry"},
            {"time": "9:15 AM", "label": "Medication taken",      "icon": "💊",  "type": "medication"},
            {"time": "9:20 AM", "label": "Sink activity (dishes)","icon": "🫧",  "type": "dishes"},
            {"time": "9:30 AM", "label": "Blood sugar: 161 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[reinforcement("Rise and Shine!", "Good morning Johnny! Ready to start the day?")],

        family_notifications=[info("Rise and Shine!", "Johnny is awake. Want to say good morning?"),
                                info("Breakfast", "Johnny ate but didn't cook - a grocery trip could be helpful.")],

        care_notifications=[warning("Breakfast", "Johnny hasn't cooked recently - ask him about his diet.")],
    ),
    "SUEJMT": make_preset(
        name="SUEJMT",
        description="Start, No Coffee, Eat, Junk Food, Meds, TV",

        diet_score=38,
        blood_sugar_score=80,
        medication_score=98,
        hygiene_score=64,
        independence_score=62,

        current_bg=152,
        bg_trend="stable",
        last_meal_time="9:00 AM",
        last_med_time="9:15 AM",
        stove_status="off",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": False,  "time": "8:10 AM"},
            {"task": "Eat breakfast",              "done": True,  "time": "9:00 AM"},
            {"task": "Take Medication",          "done": True,  "time": "9:15 AM"},
            {"task": "Do the Dishes",              "done": False, "time": "9:20 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "10:00 AM"},
            {"task": "Call Family",              "done": False,  "time": "12:30 PM"},
        ],

        weekly_history=[
            {"day": "Mon", "diet":35, "blood_sugar":88, "medication":98, "hygiene":61, "independence":66},
            {"day": "Tue", "diet":38, "blood_sugar":80, "medication":97, "hygiene":68, "independence":64},
            {"day": "Wed", "diet":37, "blood_sugar":87, "medication":92, "hygiene":62, "independence":63},
            {"day": "Thu", "diet":34, "blood_sugar":84, "medication":95, "hygiene":65, "independence":68},
            {"day": "Fri", "diet":31, "blood_sugar":88, "medication":96, "hygiene":63, "independence":67},
            {"day": "Sat", "diet":35, "blood_sugar":87, "medication":94, "hygiene":67, "independence":66},
            {"day": "Sun", "diet":36, "blood_sugar":82, "medication":97, "hygiene":68, "independence":66},
        ],

        timeline=[
            {"time": "7:30 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "7:45 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "8:30 AM", "label": "Pantry opened",         "icon": "🚪",  "type": "pantry"},
            {"time": "9:15 AM", "label": "Medication taken",      "icon": "💊",  "type": "medication"},
            {"time": "9:30 AM", "label": "Blood sugar: 161 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[reinforcement("Rise and Shine!", "Good morning Johnny! Ready to start the day?")],

        family_notifications=[info("Rise and Shine!", "Johnny is awake. Want to say good morning?"),
                                info("Breakfast", "Johnny ate but didn't cook - a grocery trip could be helpful.")],

        care_notifications=[warning("Breakfast", "Johnny hasn't cooked recently - ask him about his diet."),
                            warning("Clutter Warning", "Johnny didn't do the dishes after cooking - environmental cluttering is possible.")],
    ),
    "SUEJND": make_preset(
        name="SUEJND",
        description="Start, No Coffee, Eat, Junk Food, No Meds, Dishes",

        diet_score=38,
        blood_sugar_score=60,
        medication_score=52,
        hygiene_score=99,
        independence_score=65,

        current_bg=214,
        bg_trend="rising",
        last_meal_time="9:00 AM",
        last_med_time="Yesterday, 8:00 PM",
        stove_status="off",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": False,  "time": "8:10 AM"},
            {"task": "Eat breakfast",              "done": True,  "time": "9:00 AM"},
            {"task": "Take Medication",          "done": False,  "time": "9:15 AM"},
            {"task": "Do the Dishes",              "done": True, "time": "9:20 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "10:00 AM"},
            {"task": "Call Family",              "done": False,  "time": "12:30 PM"},
        ],

        weekly_history=[
            {"day": "Mon", "diet":35, "blood_sugar":68, "medication":58, "hygiene":91, "independence":66},
            {"day": "Tue", "diet":38, "blood_sugar":60, "medication":57, "hygiene":98, "independence":64},
            {"day": "Wed", "diet":37, "blood_sugar":67, "medication":52, "hygiene":92, "independence":63},
            {"day": "Thu", "diet":34, "blood_sugar":64, "medication":55, "hygiene":95, "independence":68},
            {"day": "Fri", "diet":31, "blood_sugar":68, "medication":56, "hygiene":93, "independence":67},
            {"day": "Sat", "diet":35, "blood_sugar":67, "medication":54, "hygiene":97, "independence":66},
            {"day": "Sun", "diet":36, "blood_sugar":62, "medication":57, "hygiene":98, "independence":66},
        ],

        timeline=[
            {"time": "7:30 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "7:45 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "8:30 AM", "label": "Pantry opened",         "icon": "🚪",  "type": "pantry"},
            {"time": "9:20 AM", "label": "Sink activity (dishes)","icon": "🫧",  "type": "dishes"},
            {"time": "9:30 AM", "label": "Blood sugar: 223 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[reinforcement("Rise and Shine!", "Good morning Johnny! Ready to start the day?"),
                                warning("Medication", "Don't forget to take your medication, Johnny")],

        family_notifications=[info("Rise and Shine!", "Johnny is awake. Want to say good morning?"),
                                info("Breakfast", "Johnny ate but didn't cook - a grocery trip could be helpful."),
                                warning("Medication", "Johnny forgot to take his medication today, want to check in?")],

        care_notifications=[warning("Breakfast", "Johnny hasn't cooked recently - ask him about his diet."),
                            warning("Medication", "Johnny displayed reduced medication adherence, reflected in his blood glucose.")],
    ),
    "SUEJNT": make_preset(
        name="SUEJNT",
        description="Start, No Coffee, Eat, Junk Food, No Meds, TV",

        diet_score=38,
        blood_sugar_score=60,
        medication_score=52,
        hygiene_score=59,
        independence_score=43,

        current_bg=214,
        bg_trend="rising",
        last_meal_time="9:00 AM",
        last_med_time="Yesterday, 8:00 PM",
        stove_status="off",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": False,  "time": "8:10 AM"},
            {"task": "Eat breakfast",              "done": True,  "time": "9:00 AM"},
            {"task": "Take Medication",          "done": False,  "time": "9:15 AM"},
            {"task": "Do the Dishes",              "done": False, "time": "9:20 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "10:00 AM"},
            {"task": "Call Family",              "done": False,  "time": "12:30 PM"},
        ],

        weekly_history=[
            {"day": "Mon", "diet":35, "blood_sugar":68, "medication":58, "hygiene":51, "independence":46},
            {"day": "Tue", "diet":38, "blood_sugar":60, "medication":57, "hygiene":58, "independence":44},
            {"day": "Wed", "diet":37, "blood_sugar":67, "medication":52, "hygiene":52, "independence":43},
            {"day": "Thu", "diet":34, "blood_sugar":64, "medication":52, "hygiene":55, "independence":48},
            {"day": "Fri", "diet":31, "blood_sugar":68, "medication":56, "hygiene":53, "independence":47},
            {"day": "Sat", "diet":35, "blood_sugar":67, "medication":54, "hygiene":57, "independence":46},
            {"day": "Sun", "diet":36, "blood_sugar":62, "medication":57, "hygiene":58, "independence":46},
        ],

        timeline=[
            {"time": "7:30 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "7:45 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "8:30 AM", "label": "Pantry opened",         "icon": "🚪",  "type": "pantry"},
            {"time": "9:30 AM", "label": "Blood sugar: 223 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[reinforcement("Rise and Shine!", "Good morning Johnny! Ready to start the day?"),
                                warning("Medication", "Don't forget to take your medication, Johnny")],

        family_notifications=[info("Rise and Shine!", "Johnny is awake. Want to say good morning?"),
                                info("Breakfast", "Johnny ate but didn't cook - a grocery trip could be helpful."),
                                warning("Medication", "Johnny forgot to take his medication today, want to check in?")],

        care_notifications=[warning("Breakfast", "Johnny hasn't cooked recently - ask him about his diet."),
                            warning("Medication", "Johnny displayed reduced medication adherence, reflected in his blood glucose."),
                            warning("Clutter Warning", "Johnny didn't do the dishes after cooking - environmental cluttering is possible.")],
    ),
    "SUAMD": make_preset(
        name="SUAMD",
        description="Start, No Coffee, No Eat, Meds, Dishes",

        diet_score=63,
        blood_sugar_score=66,
        medication_score=98,
        hygiene_score=99,
        independence_score=73,

        current_bg=56,
        bg_trend="falling",
        last_meal_time="Yesterday, 6:30 PM",
        last_med_time="9:15 AM",
        stove_status="off",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": False,  "time": "8:10 AM"},
            {"task": "Eat breakfast",              "done": True,  "time": "9:00 AM"},
            {"task": "Take Medication",          "done": True,  "time": "9:15 AM"},
            {"task": "Do the Dishes",              "done": True, "time": "9:20 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "10:00 AM"},
            {"task": "Call Family",              "done": False,  "time": "12:30 PM"},
        ],

        weekly_history=[
            {"day": "Mon", "diet":65, "blood_sugar":68, "medication":98, "hygiene":91, "independence":76},
            {"day": "Tue", "diet":68, "blood_sugar":60, "medication":97, "hygiene":98, "independence":74},
            {"day": "Wed", "diet":67, "blood_sugar":67, "medication":92, "hygiene":92, "independence":73},
            {"day": "Thu", "diet":64, "blood_sugar":64, "medication":92, "hygiene":95, "independence":78},
            {"day": "Fri", "diet":61, "blood_sugar":68, "medication":96, "hygiene":93, "independence":77},
            {"day": "Sat", "diet":65, "blood_sugar":67, "medication":94, "hygiene":97, "independence":76},
            {"day": "Sun", "diet":66, "blood_sugar":62, "medication":97, "hygiene":98, "independence":76},
        ],

        timeline=[
            {"time": "7:30 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "7:45 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "9:15 AM", "label": "Medication taken",      "icon": "💊",  "type": "medication"},
            {"time": "9:20 AM", "label": "Sink activity (dishes)","icon": "🫧",  "type": "dishes"},
            {"time": "9:30 AM", "label": "Blood sugar: 65 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[reinforcement("Rise and Shine!", "Good morning Johnny! Ready to start the day?"),
                                warning("Breakfast", "It looks like you haven't made breakfast yet. Make sure to eat at some point.")],

        family_notifications=[info("Rise and Shine!", "Johnny is awake. Want to say good morning?"),
                                warning("Breakfast", "Johnny has not made breakfast, would you like to call to check in?")],

        care_notifications=[warning("Inconsistent Diet", "Johnny has skipped eating breakfast, creating volatile BG readings.")],
    ),
    "SUAMT": make_preset(
        name="SUAMT",
        description="Start, No Coffee, No Eat, Meds, TV",

        diet_score=63,
        blood_sugar_score=66,
        medication_score=98,
        hygiene_score=55,
        independence_score=49,

        current_bg=56,
        bg_trend="falling",
        last_meal_time="Yesterday, 6:30 PM",
        last_med_time="9:15 AM",
        stove_status="off",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": False,  "time": "8:10 AM"},
            {"task": "Eat breakfast",              "done": True,  "time": "9:00 AM"},
            {"task": "Take Medication",          "done": True,  "time": "9:15 AM"},
            {"task": "Do the Dishes",              "done": False, "time": "9:20 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "10:00 AM"},
            {"task": "Call Family",              "done": False,  "time": "12:30 PM"},
        ],

        weekly_history=[
            {"day": "Mon", "diet":65, "blood_sugar":68, "medication":98, "hygiene":51, "independence":46},
            {"day": "Tue", "diet":68, "blood_sugar":60, "medication":97, "hygiene":58, "independence":44},
            {"day": "Wed", "diet":67, "blood_sugar":67, "medication":92, "hygiene":52, "independence":43},
            {"day": "Thu", "diet":64, "blood_sugar":64, "medication":92, "hygiene":55, "independence":48},
            {"day": "Fri", "diet":61, "blood_sugar":68, "medication":96, "hygiene":53, "independence":47},
            {"day": "Sat", "diet":65, "blood_sugar":67, "medication":94, "hygiene":57, "independence":46},
            {"day": "Sun", "diet":66, "blood_sugar":62, "medication":97, "hygiene":58, "independence":46},
        ],

        timeline=[
            {"time": "7:30 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "7:45 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "9:15 AM", "label": "Medication taken",      "icon": "💊",  "type": "medication"},
            {"time": "9:30 AM", "label": "Blood sugar: 65 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[reinforcement("Rise and Shine!", "Good morning Johnny! Ready to start the day?"),
                                warning("Breakfast", "It looks like you haven't made breakfast yet. Make sure to eat at some point.")],

        family_notifications=[info("Rise and Shine!", "Johnny is awake. Want to say good morning?"),
                                warning("Breakfast", "Johnny has not made breakfast, would you like to call to check in?")],

        care_notifications=[warning("Inconsistent Diet", "Johnny has skipped eating breakfast, creating volatile BG readings."),
                            warning("Clutter Warning", "Johnny didn't do the dishes after cooking - environmental cluttering is possible.")],
    ),
    "SUAND": make_preset(
        name="SUAND",
        description="Start, No Coffee, No Eat, No Meds, Dishes",

        diet_score=63,
        blood_sugar_score=47,
        medication_score=53,
        hygiene_score=99,
        independence_score=53,

        current_bg=125,
        bg_trend="stable",
        last_meal_time="Yesterday, 6:30 PM",
        last_med_time="Yesterday, 8:00 PM",
        stove_status="off",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": False,  "time": "8:10 AM"},
            {"task": "Eat breakfast",              "done": True,  "time": "9:00 AM"},
            {"task": "Take Medication",          "done": False,  "time": "9:15 AM"},
            {"task": "Do the Dishes",              "done": True, "time": "9:20 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "10:00 AM"},
            {"task": "Call Family",              "done": False,  "time": "12:30 PM"},
        ],

        weekly_history=[
            {"day": "Mon", "diet":65, "blood_sugar":48, "medication":58, "hygiene":91, "independence":56},
            {"day": "Tue", "diet":68, "blood_sugar":40, "medication":57, "hygiene":98, "independence":54},
            {"day": "Wed", "diet":67, "blood_sugar":47, "medication":52, "hygiene":92, "independence":53},
            {"day": "Thu", "diet":64, "blood_sugar":44, "medication":52, "hygiene":95, "independence":58},
            {"day": "Fri", "diet":61, "blood_sugar":48, "medication":56, "hygiene":93, "independence":57},
            {"day": "Sat", "diet":65, "blood_sugar":47, "medication":54, "hygiene":97, "independence":56},
            {"day": "Sun", "diet":66, "blood_sugar":42, "medication":57, "hygiene":98, "independence":56},
        ],

        timeline=[
            {"time": "7:30 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "7:45 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "9:20 AM", "label": "Sink activity (dishes)","icon": "🫧",  "type": "dishes"},
            {"time": "9:30 AM", "label": "Blood sugar: 97 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[reinforcement("Rise and Shine!", "Good morning Johnny! Ready to start the day?"),
                                warning("Breakfast", "It looks like you haven't made breakfast yet. Make sure to eat at some point."),
                                warning("Medication", "Don't forget to take your medication, Johnny")],

        family_notifications=[info("Rise and Shine!", "Johnny is awake. Want to say good morning?"),
                                warning("Breakfast", "Johnny has not made breakfast, would you like to call to check in?"),
                                warning("Medication", "Johnny forgot to take his medication today, want to check in?")],

        care_notifications=[warning("Inconsistent Diet", "Johnny has skipped eating breakfast, creating volatile BG readings."),
                            warning("Medication", "Johnny displayed reduced medication adherence, reflected in his blood glucose.")],
    ),
    "SUANT": make_preset(
        name="SUANT",
        description="Start, No Coffee, No Eat, No Meds, TV",

        diet_score=63,
        blood_sugar_score=47,
        medication_score=53,
        hygiene_score=63,
        independence_score=30,

        current_bg=125,
        bg_trend="stable",
        last_meal_time="Yesterday, 6:30 PM",
        last_med_time="Yesterday, 8:00 PM",
        stove_status="off",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": False,  "time": "8:10 AM"},
            {"task": "Eat breakfast",              "done": False,  "time": "9:00 AM"},
            {"task": "Take Medication",          "done": False,  "time": "9:15 AM"},
            {"task": "Do the Dishes",              "done": False, "time": "9:20 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "10:00 AM"},
            {"task": "Call Family",              "done": False,  "time": "12:30 PM"},
        ],

        weekly_history=[
            {"day": "Mon", "diet":65, "blood_sugar":48, "medication":58, "hygiene":61, "independence":36},
            {"day": "Tue", "diet":68, "blood_sugar":40, "medication":57, "hygiene":68, "independence":34},
            {"day": "Wed", "diet":67, "blood_sugar":47, "medication":52, "hygiene":62, "independence":33},
            {"day": "Thu", "diet":64, "blood_sugar":44, "medication":52, "hygiene":65, "independence":38},
            {"day": "Fri", "diet":61, "blood_sugar":48, "medication":56, "hygiene":63, "independence":37},
            {"day": "Sat", "diet":65, "blood_sugar":47, "medication":54, "hygiene":67, "independence":36},
            {"day": "Sun", "diet":66, "blood_sugar":42, "medication":57, "hygiene":68, "independence":36},
        ],

        timeline=[
            {"time": "7:30 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "7:45 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "9:30 AM", "label": "Blood sugar: 97 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[reinforcement("Rise and Shine!", "Good morning Johnny! Ready to start the day?"),
                                warning("Breakfast", "It looks like you haven't made breakfast yet. Make sure to eat at some point."),
                                warning("Medication", "Don't forget to take your medication, Johnny")],

        family_notifications=[info("Rise and Shine!", "Johnny is awake. Want to say good morning?"),
                                warning("Breakfast", "Johnny has not made breakfast, would you like to call to check in?"),
                                warning("Medication", "Johnny forgot to take his medication today, want to check in?")],

        care_notifications=[warning("Inconsistent Diet", "Johnny has skipped eating breakfast, creating volatile BG readings."),
                            warning("Medication", "Johnny displayed reduced medication adherence, reflected in his blood glucose."),
                            warning("Clutter Warning", "Johnny didn't do the dishes after cooking - environmental cluttering is possible.")],
    ),
    "SCEKFMD": make_preset(
        name="SCEKFMD",
        description="Start, Coffee, Eat, Cook, Turn Off, Meds, Dishes",

        diet_score=97,
        blood_sugar_score=100,
        medication_score=98,
        hygiene_score=99,
        independence_score=100,

        current_bg=159,
        bg_trend="stable",
        last_meal_time="9:00 AM",
        last_med_time="9:15 AM",
        stove_status="off",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": True,  "time": "8:10 AM"},
            {"task": "Eat breakfast",              "done": True,  "time": "9:00 AM"},
            {"task": "Take Medication",          "done": True,  "time": "9:15 AM"},
            {"task": "Do the Dishes",              "done": True, "time": "9:20 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "10:00 AM"},
            {"task": "Call Family",              "done": False,  "time": "12:30 PM"},
        ],

        weekly_history=[
            {"day": "Mon", "diet":95, "blood_sugar":98, "medication":98, "hygiene":91, "independence":96},
            {"day": "Tue", "diet":98, "blood_sugar":100, "medication":97, "hygiene":98, "independence":94},
            {"day": "Wed", "diet":97, "blood_sugar":97, "medication":92, "hygiene":92, "independence":93},
            {"day": "Thu", "diet":94, "blood_sugar":94, "medication":95, "hygiene":95, "independence":98},
            {"day": "Fri", "diet":91, "blood_sugar":98, "medication":96, "hygiene":93, "independence":97},
            {"day": "Sat", "diet":95, "blood_sugar":97, "medication":94, "hygiene":97, "independence":96},
            {"day": "Sun", "diet":96, "blood_sugar":92, "medication":97, "hygiene":98, "independence":96},
        ],

        timeline=[
            {"time": "7:30 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "7:45 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "8:10 AM", "label": "Made Coffee",       "icon": "☕️",  "type": "cooking"},
            {"time": "8:30 AM", "label": "Stove on",    "icon": "🔥",   "type": "stove_on"},
            {"time": "8:35 AM", "label": "Fridge opened",         "icon": "🧊",  "type": "fridge"},
            {"time": "8:50 AM", "label": "Stove off (20 min)",    "icon": "✓",   "type": "stove_off"},
            {"time": "9:15 AM", "label": "Medication taken",      "icon": "💊",  "type": "medication"},
            {"time": "9:20 AM", "label": "Sink activity (dishes)","icon": "🫧",  "type": "dishes"},
            {"time": "9:30 AM", "label": "Blood sugar: 168 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[reinforcement("Rise and Shine!", "Good morning Johnny! Ready to start the day?"),
                                reinforcement("Breakfast", "Nicely done, chef Johnny! How was breakfast?")],

        family_notifications=[info("Rise and Shine!", "Johnny is awake. Want to say good morning?")],

        care_notifications=[],
    ),
    "SCEKFMT": make_preset(
        name="SCEKFMT",
        description="Start, Coffee, Eat, Cook, Turn Off, Meds, TV",

        diet_score=97,
        blood_sugar_score=100,
        medication_score=98,
        hygiene_score=59,
        independence_score=74,

        current_bg=159,
        bg_trend="stable",
        last_meal_time="9:00 AM",
        last_med_time="9:15 AM",
        stove_status="off",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": True,  "time": "8:10 AM"},
            {"task": "Eat breakfast",              "done": True,  "time": "9:00 AM"},
            {"task": "Take Medication",          "done": True,  "time": "9:15 AM"},
            {"task": "Do the Dishes",              "done": False, "time": "9:20 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "10:00 AM"},
            {"task": "Call Family",              "done": False,  "time": "12:30 PM"},
        ],

        weekly_history=[
            {"day": "Mon", "diet":95, "blood_sugar":98, "medication":98, "hygiene":51, "independence":76},
            {"day": "Tue", "diet":98, "blood_sugar":100, "medication":97, "hygiene":58, "independence":74},
            {"day": "Wed", "diet":97, "blood_sugar":97, "medication":92, "hygiene":52, "independence":73},
            {"day": "Thu", "diet":94, "blood_sugar":94, "medication":95, "hygiene":55, "independence":78},
            {"day": "Fri", "diet":91, "blood_sugar":98, "medication":96, "hygiene":53, "independence":77},
            {"day": "Sat", "diet":95, "blood_sugar":97, "medication":94, "hygiene":57, "independence":76},
            {"day": "Sun", "diet":96, "blood_sugar":92, "medication":97, "hygiene":58, "independence":76},
        ],

        timeline=[
            {"time": "7:30 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "7:45 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "8:10 AM", "label": "Made Coffee",       "icon": "☕️",  "type": "cooking"},
            {"time": "8:30 AM", "label": "Stove on",    "icon": "🔥",   "type": "stove_on"},
            {"time": "8:35 AM", "label": "Fridge opened",         "icon": "🧊",  "type": "fridge"},
            {"time": "8:50 AM", "label": "Stove off (20 min)",    "icon": "✓",   "type": "stove_off"},
            {"time": "9:15 AM", "label": "Medication taken",      "icon": "💊",  "type": "medication"},
            {"time": "9:30 AM", "label": "Blood sugar: 168 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[reinforcement("Rise and Shine!", "Good morning Johnny! Ready to start the day?"),
                                reinforcement("Breakfast", "Nicely done, chef Johnny! How was breakfast?")],

        family_notifications=[info("Rise and Shine!", "Johnny is awake. Want to say good morning?")],

        care_notifications=[warning("Clutter Warning", "Johnny didn't do the dishes after cooking - environmental cluttering is possible.")],
    ),
    "SCEKFND": make_preset(
        name="SCEKFND",
        description="Start, Coffee, Eat, Cook, Turn Off, Meds, Dishes",

        diet_score=97,
        blood_sugar_score=80,
        medication_score=56,
        hygiene_score=99,
        independence_score=81,

        current_bg=214,
        bg_trend="rising",
        last_meal_time="9:00 AM",
        last_med_time="Yesterday, 8:00 PM",
        stove_status="off",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": True,  "time": "8:10 AM"},
            {"task": "Eat breakfast",              "done": True,  "time": "9:00 AM"},
            {"task": "Take Medication",          "done": False,  "time": "9:15 AM"},
            {"task": "Do the Dishes",              "done": True, "time": "9:20 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "10:00 AM"},
            {"task": "Call Family",              "done": False,  "time": "12:30 PM"},
        ],

        weekly_history=[
            {"day": "Mon", "diet":95, "blood_sugar":88, "medication":58, "hygiene":91, "independence":86},
            {"day": "Tue", "diet":98, "blood_sugar":80, "medication":57, "hygiene":98, "independence":84},
            {"day": "Wed", "diet":97, "blood_sugar":87, "medication":52, "hygiene":92, "independence":83},
            {"day": "Thu", "diet":94, "blood_sugar":84, "medication":55, "hygiene":95, "independence":88},
            {"day": "Fri", "diet":91, "blood_sugar":88, "medication":56, "hygiene":93, "independence":87},
            {"day": "Sat", "diet":95, "blood_sugar":87, "medication":54, "hygiene":97, "independence":86},
            {"day": "Sun", "diet":96, "blood_sugar":82, "medication":57, "hygiene":98, "independence":86},
        ],

        timeline=[
            {"time": "7:30 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "7:45 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "8:10 AM", "label": "Made Coffee",       "icon": "☕️",  "type": "cooking"},
            {"time": "8:30 AM", "label": "Stove on",    "icon": "🔥",   "type": "stove_on"},
            {"time": "8:35 AM", "label": "Fridge opened",         "icon": "🧊",  "type": "fridge"},
            {"time": "8:50 AM", "label": "Stove off (20 min)",    "icon": "✓",   "type": "stove_off"},
            {"time": "9:20 AM", "label": "Sink activity (dishes)","icon": "🫧",  "type": "dishes"},
            {"time": "9:30 AM", "label": "Blood sugar: 223 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[reinforcement("Rise and Shine!", "Good morning Johnny! Ready to start the day?"),
                                reinforcement("Breakfast", "Nicely done, chef Johnny! How was breakfast?"),
                                warning("Medication", "Don't forget to take your medication, Johnny")],

        family_notifications=[info("Rise and Shine!", "Johnny is awake. Want to say good morning?"),
                                warning("Medication", "Johnny forgot to take his medication today, want to check in?")],

        care_notifications=[warning("Medication", "Johnny displayed reduced medication adherence, reflected in his blood glucose.")],
    ),
    "SCEKFNT": make_preset(
        name="SCEKFNT",
        description="Start, Coffee, Eat, Cook, Turn Off, Meds, TV",

        diet_score=97,
        blood_sugar_score=80,
        medication_score=56,
        hygiene_score=65,
        independence_score=57,

        current_bg=214,
        bg_trend="rising",
        last_meal_time="9:00 AM",
        last_med_time="Yesterday, 8:00 PM",
        stove_status="off",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": True,  "time": "8:10 AM"},
            {"task": "Eat breakfast",              "done": True,  "time": "9:00 AM"},
            {"task": "Take Medication",          "done": False,  "time": "9:15 AM"},
            {"task": "Do the Dishes",              "done": False, "time": "9:20 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "10:00 AM"},
            {"task": "Call Family",              "done": False,  "time": "12:30 PM"},
        ],

        weekly_history=[
            {"day": "Mon", "diet":95, "blood_sugar":88, "medication":58, "hygiene":61, "independence":56},
            {"day": "Tue", "diet":98, "blood_sugar":80, "medication":57, "hygiene":68, "independence":54},
            {"day": "Wed", "diet":97, "blood_sugar":87, "medication":52, "hygiene":62, "independence":53},
            {"day": "Thu", "diet":94, "blood_sugar":84, "medication":55, "hygiene":65, "independence":58},
            {"day": "Fri", "diet":91, "blood_sugar":88, "medication":56, "hygiene":63, "independence":57},
            {"day": "Sat", "diet":95, "blood_sugar":87, "medication":54, "hygiene":67, "independence":56},
            {"day": "Sun", "diet":96, "blood_sugar":82, "medication":57, "hygiene":68, "independence":56},
        ],

        timeline=[
            {"time": "7:30 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "7:45 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "8:10 AM", "label": "Made Coffee",       "icon": "☕️",  "type": "cooking"},
            {"time": "8:30 AM", "label": "Stove on",    "icon": "🔥",   "type": "stove_on"},
            {"time": "8:35 AM", "label": "Fridge opened",         "icon": "🧊",  "type": "fridge"},
            {"time": "8:50 AM", "label": "Stove off (20 min)",    "icon": "✓",   "type": "stove_off"},
            {"time": "9:30 AM", "label": "Blood sugar: 223 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[reinforcement("Rise and Shine!", "Good morning Johnny! Ready to start the day?"),
                                reinforcement("Breakfast", "Nicely done, chef Johnny! How was breakfast?"),
                                warning("Medication", "Don't forget to take your medication, Johnny")],

        family_notifications=[info("Rise and Shine!", "Johnny is awake. Want to say good morning?"),
                                warning("Medication", "Johnny forgot to take his medication today, want to check in?")],

        care_notifications=[warning("Medication", "Johnny displayed reduced medication adherence, reflected in his blood glucose."),
                            warning("Clutter Warning", "Johnny didn't do the dishes after cooking - environmental cluttering is possible.")],
    ),
    "SCEKOMD": make_preset(
        name="SCEKOMD",
        description="Start, Coffee, Eat, Cook, Turn On, Meds, Dishes",

        diet_score=97,
        blood_sugar_score=100,
        medication_score=98,
        hygiene_score=99,
        independence_score=60,

        current_bg=159,
        bg_trend="stable",
        last_meal_time="9:00 AM",
        last_med_time="9:15 AM",
        stove_status="on",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": True,  "time": "8:10 AM"},
            {"task": "Eat breakfast",              "done": True,  "time": "9:00 AM"},
            {"task": "Take Medication",          "done": True,  "time": "9:15 AM"},
            {"task": "Do the Dishes",              "done": True, "time": "9:20 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "10:00 AM"},
            {"task": "Call Family",              "done": False,  "time": "12:30 PM"},
        ],

        weekly_history=[
            {"day": "Mon", "diet":95, "blood_sugar":98, "medication":98, "hygiene":91, "independence":66},
            {"day": "Tue", "diet":98, "blood_sugar":100, "medication":97, "hygiene":98, "independence":64},
            {"day": "Wed", "diet":97, "blood_sugar":97, "medication":92, "hygiene":92, "independence":63},
            {"day": "Thu", "diet":94, "blood_sugar":94, "medication":95, "hygiene":95, "independence":68},
            {"day": "Fri", "diet":91, "blood_sugar":98, "medication":96, "hygiene":93, "independence":67},
            {"day": "Sat", "diet":95, "blood_sugar":97, "medication":94, "hygiene":97, "independence":66},
            {"day": "Sun", "diet":96, "blood_sugar":92, "medication":97, "hygiene":98, "independence":66},
        ],

        timeline=[
            {"time": "7:30 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "7:45 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "8:10 AM", "label": "Made Coffee",       "icon": "☕️",  "type": "cooking"},
            {"time": "8:30 AM", "label": "Stove on",    "icon": "🔥",   "type": "stove_on"},
            {"time": "8:35 AM", "label": "Fridge opened",         "icon": "🧊",  "type": "fridge"},
            {"time": "9:15 AM", "label": "Medication taken",      "icon": "💊",  "type": "medication"},
            {"time": "9:20 AM", "label": "Sink activity (dishes)","icon": "🫧",  "type": "dishes"},
            {"time": "9:30 AM", "label": "Blood sugar: 168 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[reinforcement("Rise and Shine!", "Good morning Johnny! Ready to start the day?"),
                                reinforcement("Breakfast", "Nicely done, chef Johnny! How was breakfast?"),
                                alert("Stove", "The stove has been left on, don't forget to turn it off.")],

        family_notifications=[info("Rise and Shine!", "Johnny is awake. Want to say good morning?"),
                                alert("Stove", "Johnny has left the stove on for 20 minutes and not responded.")],

        care_notifications=[alert("Stove Awareness", "Johnny failed to turn the stove off after cooking.")],
    ),
    "SCEKOMT": make_preset(
        name="SCEKOMT",
        description="Start, Coffee, Eat, Cook, Turn On, Meds, TV",

        diet_score=97,
        blood_sugar_score=100,
        medication_score=98,
        hygiene_score=58,
        independence_score=40,

        current_bg=159,
        bg_trend="stable",
        last_meal_time="9:00 AM",
        last_med_time="9:15 AM",
        stove_status="on",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": True,  "time": "8:10 AM"},
            {"task": "Eat breakfast",              "done": True,  "time": "9:00 AM"},
            {"task": "Take Medication",          "done": True,  "time": "9:15 AM"},
            {"task": "Do the Dishes",              "done": False, "time": "9:20 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "10:00 AM"},
            {"task": "Call Family",              "done": False,  "time": "12:30 PM"},
        ],

        weekly_history=[
            {"day": "Mon", "diet":95, "blood_sugar":98, "medication":98, "hygiene":51, "independence":46},
            {"day": "Tue", "diet":98, "blood_sugar":100, "medication":97, "hygiene":58, "independence":44},
            {"day": "Wed", "diet":97, "blood_sugar":97, "medication":92, "hygiene":52, "independence":43},
            {"day": "Thu", "diet":94, "blood_sugar":94, "medication":95, "hygiene":55, "independence":48},
            {"day": "Fri", "diet":91, "blood_sugar":98, "medication":96, "hygiene":53, "independence":47},
            {"day": "Sat", "diet":95, "blood_sugar":97, "medication":94, "hygiene":57, "independence":46},
            {"day": "Sun", "diet":96, "blood_sugar":92, "medication":97, "hygiene":58, "independence":46},
        ],

        timeline=[
            {"time": "7:30 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "7:45 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "8:10 AM", "label": "Made Coffee",       "icon": "☕️",  "type": "cooking"},
            {"time": "8:30 AM", "label": "Stove on",    "icon": "🔥",   "type": "stove_on"},
            {"time": "8:35 AM", "label": "Fridge opened",         "icon": "🧊",  "type": "fridge"},
            {"time": "9:15 AM", "label": "Medication taken",      "icon": "💊",  "type": "medication"},
            {"time": "9:30 AM", "label": "Blood sugar: 168 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[reinforcement("Rise and Shine!", "Good morning Johnny! Ready to start the day?"),
                                reinforcement("Breakfast", "Nicely done, chef Johnny! How was breakfast?"),
                                alert("Stove", "The stove has been left on, don't forget to turn it off.")],

        family_notifications=[info("Rise and Shine!", "Johnny is awake. Want to say good morning?"),
                                alert("Stove", "Johnny has left the stove on for 20 minutes and not responded.")],

        care_notifications=[alert("Stove Awareness", "Johnny failed to turn the stove off after cooking."),
                            warning("Clutter Warning", "Johnny didn't do the dishes after cooking - environmental cluttering is possible.")],
    ),
    "SCEKOND": make_preset(
        name="SCEKOND",
        description="Start, Coffee, Eat, Cook, Turn On, No Meds, Dishes",

        diet_score=97,
        blood_sugar_score=73,
        medication_score=54,
        hygiene_score=99,
        independence_score=43,

        current_bg=222,
        bg_trend="rising",
        last_meal_time="9:00 AM",
        last_med_time="Yesterday, 8:00 PM",
        stove_status="on",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": True,  "time": "8:10 AM"},
            {"task": "Eat breakfast",              "done": True,  "time": "9:00 AM"},
            {"task": "Take Medication",          "done": False,  "time": "9:15 AM"},
            {"task": "Do the Dishes",              "done": True, "time": "9:20 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "10:00 AM"},
            {"task": "Call Family",              "done": False,  "time": "12:30 PM"},
        ],

        weekly_history=[
            {"day": "Mon", "diet":95, "blood_sugar":78, "medication":58, "hygiene":91, "independence":46},
            {"day": "Tue", "diet":98, "blood_sugar":80, "medication":57, "hygiene":98, "independence":44},
            {"day": "Wed", "diet":97, "blood_sugar":77, "medication":52, "hygiene":92, "independence":43},
            {"day": "Thu", "diet":94, "blood_sugar":74, "medication":55, "hygiene":95, "independence":48},
            {"day": "Fri", "diet":91, "blood_sugar":78, "medication":56, "hygiene":93, "independence":47},
            {"day": "Sat", "diet":95, "blood_sugar":77, "medication":54, "hygiene":97, "independence":46},
            {"day": "Sun", "diet":96, "blood_sugar":72, "medication":57, "hygiene":98, "independence":46},
        ],

        timeline=[
            {"time": "7:30 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "7:45 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "8:10 AM", "label": "Made Coffee",       "icon": "☕️",  "type": "cooking"},
            {"time": "8:30 AM", "label": "Stove on",    "icon": "🔥",   "type": "stove_on"},
            {"time": "8:35 AM", "label": "Fridge opened",         "icon": "🧊",  "type": "fridge"},
            {"time": "9:20 AM", "label": "Sink activity (dishes)","icon": "🫧",  "type": "dishes"},
            {"time": "9:30 AM", "label": "Blood sugar: 231 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[reinforcement("Rise and Shine!", "Good morning Johnny! Ready to start the day?"),
                                reinforcement("Breakfast", "Nicely done, chef Johnny! How was breakfast?"),
                                alert("Stove", "The stove has been left on, don't forget to turn it off."),
                                warning("Medication", "Don't forget to take your medication, Johnny")],

        family_notifications=[info("Rise and Shine!", "Johnny is awake. Want to say good morning?"),
                                alert("Stove", "Johnny has left the stove on for 20 minutes and not responded."),
                                warning("Medication", "Johnny forgot to take his medication today, want to check in?")],

        care_notifications=[alert("Stove Awareness", "Johnny failed to turn the stove off after cooking."),
                            warning("Medication", "Johnny displayed reduced medication adherence, reflected in his blood glucose.")],
    ),
    "SCEKONT": make_preset(
        name="SCEKONT",
        description="Start, Coffee, Eat, Cook, Turn On, No Meds, TV",

        diet_score=97,
        blood_sugar_score=73,
        medication_score=54,
        hygiene_score=54,
        independence_score=18,

        current_bg=222,
        bg_trend="rising",
        last_meal_time="9:00 AM",
        last_med_time="Yesterday, 8:00 PM",
        stove_status="on",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": True,  "time": "8:10 AM"},
            {"task": "Eat breakfast",              "done": True,  "time": "9:00 AM"},
            {"task": "Take Medication",          "done": False,  "time": "9:15 AM"},
            {"task": "Do the Dishes",              "done": False, "time": "9:20 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "10:00 AM"},
            {"task": "Call Family",              "done": False,  "time": "12:30 PM"},
        ],

        weekly_history=[
            {"day": "Mon", "diet":95, "blood_sugar":78, "medication":58, "hygiene":51, "independence":16},
            {"day": "Tue", "diet":98, "blood_sugar":80, "medication":57, "hygiene":58, "independence":14},
            {"day": "Wed", "diet":97, "blood_sugar":77, "medication":52, "hygiene":52, "independence":13},
            {"day": "Thu", "diet":94, "blood_sugar":74, "medication":55, "hygiene":55, "independence":18},
            {"day": "Fri", "diet":91, "blood_sugar":78, "medication":56, "hygiene":53, "independence":17},
            {"day": "Sat", "diet":95, "blood_sugar":77, "medication":54, "hygiene":57, "independence":16},
            {"day": "Sun", "diet":96, "blood_sugar":72, "medication":57, "hygiene":58, "independence":16},
        ],

        timeline=[
            {"time": "7:30 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "7:45 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "8:10 AM", "label": "Made Coffee",       "icon": "☕️",  "type": "cooking"},
            {"time": "8:30 AM", "label": "Stove on",    "icon": "🔥",   "type": "stove_on"},
            {"time": "8:35 AM", "label": "Fridge opened",         "icon": "🧊",  "type": "fridge"},
            {"time": "9:30 AM", "label": "Blood sugar: 231 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[reinforcement("Rise and Shine!", "Good morning Johnny! Ready to start the day?"),
                                reinforcement("Breakfast", "Nicely done, chef Johnny! How was breakfast?"),
                                alert("Stove", "The stove has been left on, don't forget to turn it off."),
                                warning("Medication", "Don't forget to take your medication, Johnny")],

        family_notifications=[info("Rise and Shine!", "Johnny is awake. Want to say good morning?"),
                                alert("Stove", "Johnny has left the stove on for 20 minutes and not responded."),
                                warning("Medication", "Johnny forgot to take his medication today, want to check in?")],

        care_notifications=[alert("Stove Awareness", "Johnny failed to turn the stove off after cooking."),
                            warning("Medication", "Johnny displayed reduced medication adherence, reflected in his blood glucose."),
                            warning("Clutter Warning", "Johnny didn't do the dishes after cooking - environmental cluttering is possible.")],
    ),
    "SCEJMD": make_preset(
        name="SCEJMD",
        description="Start, Coffee, Eat, Junk Food, Meds, Dishes",

        diet_score=30,
        blood_sugar_score=82,
        medication_score=98,
        hygiene_score=99,
        independence_score=86,

        current_bg=177,
        bg_trend="rising",
        last_meal_time="9:00 AM",
        last_med_time="9:15 AM",
        stove_status="off",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": True,  "time": "8:10 AM"},
            {"task": "Eat breakfast",              "done": True,  "time": "9:00 AM"},
            {"task": "Take Medication",          "done": True,  "time": "9:15 AM"},
            {"task": "Do the Dishes",              "done": True, "time": "9:20 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "10:00 AM"},
            {"task": "Call Family",              "done": False,  "time": "12:30 PM"},
        ],

        weekly_history=[
            {"day": "Mon", "diet":35, "blood_sugar":88, "medication":98, "hygiene":91, "independence":86},
            {"day": "Tue", "diet":38, "blood_sugar":80, "medication":97, "hygiene":98, "independence":84},
            {"day": "Wed", "diet":37, "blood_sugar":87, "medication":92, "hygiene":92, "independence":83},
            {"day": "Thu", "diet":34, "blood_sugar":84, "medication":95, "hygiene":95, "independence":88},
            {"day": "Fri", "diet":31, "blood_sugar":88, "medication":96, "hygiene":93, "independence":87},
            {"day": "Sat", "diet":35, "blood_sugar":87, "medication":94, "hygiene":97, "independence":86},
            {"day": "Sun", "diet":36, "blood_sugar":82, "medication":97, "hygiene":98, "independence":86},
        ],

        timeline=[
            {"time": "7:30 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "7:45 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "8:10 AM", "label": "Made Coffee",       "icon": "☕️",  "type": "cooking"},
            {"time": "8:30 AM", "label": "Pantry opened",         "icon": "🚪",  "type": "pantry"},
            {"time": "9:15 AM", "label": "Medication taken",      "icon": "💊",  "type": "medication"},
            {"time": "9:20 AM", "label": "Sink activity (dishes)","icon": "🫧",  "type": "dishes"},
            {"time": "9:30 AM", "label": "Blood sugar: 186 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[reinforcement("Rise and Shine!", "Good morning Johnny! Ready to start the day?")],

        family_notifications=[info("Rise and Shine!", "Johnny is awake. Want to say good morning?"),
                                info("Breakfast", "Johnny ate but didn't cook - a grocery trip could be helpful.")],

        care_notifications=[warning("Breakfast", "Johnny hasn't cooked recently - ask him about his diet.")],
    ),
    "SCEJMT": make_preset(
        name="SCEJMT",
        description="Start, Coffee, Eat, Junk Food, Meds, TV",

        diet_score=30,
        blood_sugar_score=82,
        medication_score=98,
        hygiene_score=53,
        independence_score=64,

        current_bg=177,
        bg_trend="rising",
        last_meal_time="9:00 AM",
        last_med_time="9:15 AM",
        stove_status="off",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": True,  "time": "8:10 AM"},
            {"task": "Eat breakfast",              "done": True,  "time": "9:00 AM"},
            {"task": "Take Medication",          "done": True,  "time": "9:15 AM"},
            {"task": "Do the Dishes",              "done": False, "time": "9:20 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "10:00 AM"},
            {"task": "Call Family",              "done": False,  "time": "12:30 PM"},
        ],

        weekly_history=[
            {"day": "Mon", "diet":35, "blood_sugar":88, "medication":98, "hygiene":51, "independence":66},
            {"day": "Tue", "diet":38, "blood_sugar":80, "medication":97, "hygiene":58, "independence":64},
            {"day": "Wed", "diet":37, "blood_sugar":87, "medication":92, "hygiene":52, "independence":63},
            {"day": "Thu", "diet":34, "blood_sugar":84, "medication":95, "hygiene":55, "independence":68},
            {"day": "Fri", "diet":31, "blood_sugar":88, "medication":96, "hygiene":53, "independence":67},
            {"day": "Sat", "diet":35, "blood_sugar":87, "medication":94, "hygiene":57, "independence":66},
            {"day": "Sun", "diet":36, "blood_sugar":82, "medication":97, "hygiene":58, "independence":66},
        ],

        timeline=[
            {"time": "7:30 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "7:45 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "8:10 AM", "label": "Made Coffee",       "icon": "☕️",  "type": "cooking"},
            {"time": "8:30 AM", "label": "Pantry opened",         "icon": "🚪",  "type": "pantry"},
            {"time": "9:15 AM", "label": "Medication taken",      "icon": "💊",  "type": "medication"},
            {"time": "9:30 AM", "label": "Blood sugar: 186 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[reinforcement("Rise and Shine!", "Good morning Johnny! Ready to start the day?")],

        family_notifications=[info("Rise and Shine!", "Johnny is awake. Want to say good morning?"),
                                info("Breakfast", "Johnny ate but didn't cook - a grocery trip could be helpful.")],

        care_notifications=[warning("Breakfast", "Johnny hasn't cooked recently - ask him about his diet."),
                            warning("Clutter Warning", "Johnny didn't do the dishes after cooking - environmental cluttering is possible.")],
    ),
    "SCEJND": make_preset(
        name="SCEJND",
        description="Start, Coffee, Eat, Junk Food, No Meds, Dishes",

        diet_score=30,
        blood_sugar_score=61,
        medication_score=52,
        hygiene_score=99,
        independence_score=65,

        current_bg=241,
        bg_trend="rising",
        last_meal_time="9:00 AM",
        last_med_time="Yesterday, 8:00 PM",
        stove_status="off",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": True,  "time": "8:10 AM"},
            {"task": "Eat breakfast",              "done": True,  "time": "9:00 AM"},
            {"task": "Take Medication",          "done": False,  "time": "9:15 AM"},
            {"task": "Do the Dishes",              "done": True, "time": "9:20 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "10:00 AM"},
            {"task": "Call Family",              "done": False,  "time": "12:30 PM"},
        ],

        weekly_history=[
            {"day": "Mon", "diet":35, "blood_sugar":58, "medication":58, "hygiene":91, "independence":66},
            {"day": "Tue", "diet":38, "blood_sugar":60, "medication":57, "hygiene":98, "independence":64},
            {"day": "Wed", "diet":37, "blood_sugar":57, "medication":52, "hygiene":92, "independence":63},
            {"day": "Thu", "diet":34, "blood_sugar":54, "medication":55, "hygiene":95, "independence":68},
            {"day": "Fri", "diet":31, "blood_sugar":58, "medication":56, "hygiene":93, "independence":67},
            {"day": "Sat", "diet":35, "blood_sugar":57, "medication":54, "hygiene":97, "independence":66},
            {"day": "Sun", "diet":36, "blood_sugar":52, "medication":57, "hygiene":98, "independence":66},
        ],

        timeline=[
            {"time": "7:30 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "7:45 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "8:10 AM", "label": "Made Coffee",       "icon": "☕️",  "type": "cooking"},
            {"time": "8:30 AM", "label": "Pantry opened",         "icon": "🚪",  "type": "pantry"},
            {"time": "9:20 AM", "label": "Sink activity (dishes)","icon": "🫧",  "type": "dishes"},
            {"time": "9:30 AM", "label": "Blood sugar: 250 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[reinforcement("Rise and Shine!", "Good morning Johnny! Ready to start the day?"),
                                warning("Medication", "Don't forget to take your medication, Johnny")],

        family_notifications=[info("Rise and Shine!", "Johnny is awake. Want to say good morning?"),
                                info("Breakfast", "Johnny ate but didn't cook - a grocery trip could be helpful."),
                                warning("Medication", "Johnny forgot to take his medication today, want to check in?")],

        care_notifications=[warning("Breakfast", "Johnny hasn't cooked recently - ask him about his diet."),
                            warning("Medication", "Johnny displayed reduced medication adherence, reflected in his blood glucose.")],
    ),
    "SCEJNT": make_preset(
        name="SCEJNT",
        description="Start, Coffee, Eat, Junk Food, No Meds, TV",

        diet_score=30,
        blood_sugar_score=61,
        medication_score=52,
        hygiene_score=52,
        independence_score=45,

        current_bg=241,
        bg_trend="rising",
        last_meal_time="9:00 AM",
        last_med_time="Yesterday, 8:00 PM",
        stove_status="off",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": True,  "time": "8:10 AM"},
            {"task": "Eat breakfast",              "done": True,  "time": "9:00 AM"},
            {"task": "Take Medication",          "done": False,  "time": "9:15 AM"},
            {"task": "Do the Dishes",              "done": False, "time": "9:20 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "10:00 AM"},
            {"task": "Call Family",              "done": False,  "time": "12:30 PM"},
        ],

        weekly_history=[
            {"day": "Mon", "diet":35, "blood_sugar":68, "medication":58, "hygiene":51, "independence":46},
            {"day": "Tue", "diet":38, "blood_sugar":70, "medication":57, "hygiene":58, "independence":44},
            {"day": "Wed", "diet":37, "blood_sugar":67, "medication":52, "hygiene":52, "independence":43},
            {"day": "Thu", "diet":34, "blood_sugar":64, "medication":55, "hygiene":55, "independence":48},
            {"day": "Fri", "diet":31, "blood_sugar":68, "medication":56, "hygiene":53, "independence":47},
            {"day": "Sat", "diet":35, "blood_sugar":67, "medication":54, "hygiene":57, "independence":46},
            {"day": "Sun", "diet":36, "blood_sugar":62, "medication":57, "hygiene":58, "independence":46},
        ],

        timeline=[
            {"time": "7:30 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "7:45 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "8:10 AM", "label": "Made Coffee",       "icon": "☕️",  "type": "cooking"},
            {"time": "8:30 AM", "label": "Pantry opened",         "icon": "🚪",  "type": "pantry"},
            {"time": "9:30 AM", "label": "Blood sugar: 250 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[reinforcement("Rise and Shine!", "Good morning Johnny! Ready to start the day?"),
                                warning("Medication", "Don't forget to take your medication, Johnny")],

        family_notifications=[info("Rise and Shine!", "Johnny is awake. Want to say good morning?"),
                                info("Breakfast", "Johnny ate but didn't cook - a grocery trip could be helpful."),
                                warning("Medication", "Johnny forgot to take his medication today, want to check in?")],

        care_notifications=[warning("Breakfast", "Johnny hasn't cooked recently - ask him about his diet."),
                            warning("Medication", "Johnny displayed reduced medication adherence, reflected in his blood glucose."),
                            warning("Clutter Warning", "Johnny didn't do the dishes after cooking - environmental cluttering is possible.")],
    ),
    "SCAMD": make_preset(
        name="SCAMD",
        description="Start, Coffee, No Eat, Meds, Dishes",

        diet_score=63,
        blood_sugar_score=66,
        medication_score=98,
        hygiene_score=99,
        independence_score=76,

        current_bg=83,
        bg_trend="stable",
        last_meal_time="Yesterday, 6:30 PM",
        last_med_time="9:15 AM",
        stove_status="off",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": True,  "time": "8:10 AM"},
            {"task": "Eat breakfast",              "done": True,  "time": "9:00 AM"},
            {"task": "Take Medication",          "done": True,  "time": "9:15 AM"},
            {"task": "Do the Dishes",              "done": True, "time": "9:20 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "10:00 AM"},
            {"task": "Call Family",              "done": False,  "time": "12:30 PM"},
        ],

        weekly_history=[
            {"day": "Mon", "diet":65, "blood_sugar":68, "medication":98, "hygiene":91, "independence":76},
            {"day": "Tue", "diet":68, "blood_sugar":70, "medication":97, "hygiene":98, "independence":74},
            {"day": "Wed", "diet":67, "blood_sugar":67, "medication":92, "hygiene":92, "independence":73},
            {"day": "Thu", "diet":64, "blood_sugar":64, "medication":95, "hygiene":95, "independence":78},
            {"day": "Fri", "diet":61, "blood_sugar":68, "medication":96, "hygiene":93, "independence":77},
            {"day": "Sat", "diet":65, "blood_sugar":67, "medication":94, "hygiene":97, "independence":76},
            {"day": "Sun", "diet":66, "blood_sugar":62, "medication":97, "hygiene":98, "independence":76},
        ],

        timeline=[
            {"time": "7:30 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "7:45 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "8:10 AM", "label": "Made Coffee",       "icon": "☕️",  "type": "cooking"},
            {"time": "9:15 AM", "label": "Medication taken",      "icon": "💊",  "type": "medication"},
            {"time": "9:20 AM", "label": "Sink activity (dishes)","icon": "🫧",  "type": "dishes"},
            {"time": "9:30 AM", "label": "Blood sugar: 94 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[reinforcement("Rise and Shine!", "Good morning Johnny! Ready to start the day?"),
                                warning("Breakfast", "It looks like you haven't made breakfast yet. Make sure to eat at some point.")],

        family_notifications=[info("Rise and Shine!", "Johnny is awake. Want to say good morning?"),
                                warning("Breakfast", "Johnny has not made breakfast, would you like to call to check in?")],

        care_notifications=[warning("Inconsistent Diet", "Johnny has skipped eating breakfast, creating volatile BG readings.")],
    ),
    "SCAMT": make_preset(
        name="SCAMT",
        description="Start, Coffee, No Eat, Meds, TV",

        diet_score=63,
        blood_sugar_score=66,
        medication_score=98,
        hygiene_score=57,
        independence_score=50,

        current_bg=83,
        bg_trend="stable",
        last_meal_time="Yesterday, 6:30 PM",
        last_med_time="9:15 AM",
        stove_status="off",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": True,  "time": "8:10 AM"},
            {"task": "Eat breakfast",              "done": True,  "time": "9:00 AM"},
            {"task": "Take Medication",          "done": True,  "time": "9:15 AM"},
            {"task": "Do the Dishes",              "done": False, "time": "9:20 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "10:00 AM"},
            {"task": "Call Family",              "done": False,  "time": "12:30 PM"},
        ],

        weekly_history=[
            {"day": "Mon", "diet":65, "blood_sugar":68, "medication":98, "hygiene":61, "independence":46},
            {"day": "Tue", "diet":68, "blood_sugar":70, "medication":97, "hygiene":58, "independence":44},
            {"day": "Wed", "diet":67, "blood_sugar":67, "medication":92, "hygiene":62, "independence":43},
            {"day": "Thu", "diet":64, "blood_sugar":64, "medication":95, "hygiene":65, "independence":48},
            {"day": "Fri", "diet":61, "blood_sugar":68, "medication":96, "hygiene":63, "independence":47},
            {"day": "Sat", "diet":65, "blood_sugar":67, "medication":94, "hygiene":57, "independence":46},
            {"day": "Sun", "diet":66, "blood_sugar":62, "medication":97, "hygiene":68, "independence":46},
        ],

        timeline=[
            {"time": "7:30 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "7:45 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "8:10 AM", "label": "Made Coffee",       "icon": "☕️",  "type": "cooking"},
            {"time": "9:15 AM", "label": "Medication taken",      "icon": "💊",  "type": "medication"},
            {"time": "9:30 AM", "label": "Blood sugar: 94 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[reinforcement("Rise and Shine!", "Good morning Johnny! Ready to start the day?"),
                                warning("Breakfast", "It looks like you haven't made breakfast yet. Make sure to eat at some point.")],

        family_notifications=[info("Rise and Shine!", "Johnny is awake. Want to say good morning?"),
                                warning("Breakfast", "Johnny has not made breakfast, would you like to call to check in?")],

        care_notifications=[warning("Inconsistent Diet", "Johnny has skipped eating breakfast, creating volatile BG readings."),
                            warning("Clutter Warning", "Johnny didn't do the dishes after cooking - environmental cluttering is possible.")],
    ),
    "SCAND": make_preset(
        name="SCAND",
        description="Start, Coffee, No Eat, No Meds, Dishes",

        diet_score=63,
        blood_sugar_score=47,
        medication_score=47,
        hygiene_score=99,
        independence_score=57,

        current_bg=135,
        bg_trend="stable",
        last_meal_time="Yesterday, 6:30 PM",
        last_med_time="Yesterday, 8:00 PM",
        stove_status="off",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": True,  "time": "8:10 AM"},
            {"task": "Eat breakfast",              "done": True,  "time": "9:00 AM"},
            {"task": "Take Medication",          "done": False,  "time": "9:15 AM"},
            {"task": "Do the Dishes",              "done": True, "time": "9:20 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "10:00 AM"},
            {"task": "Call Family",              "done": False,  "time": "12:30 PM"},
        ],

        weekly_history=[
            {"day": "Mon", "diet":65, "blood_sugar":48, "medication":48, "hygiene":91, "independence":56},
            {"day": "Tue", "diet":68, "blood_sugar":50, "medication":47, "hygiene":98, "independence":54},
            {"day": "Wed", "diet":67, "blood_sugar":47, "medication":42, "hygiene":92, "independence":53},
            {"day": "Thu", "diet":64, "blood_sugar":44, "medication":45, "hygiene":95, "independence":58},
            {"day": "Fri", "diet":61, "blood_sugar":48, "medication":46, "hygiene":93, "independence":57},
            {"day": "Sat", "diet":65, "blood_sugar":47, "medication":44, "hygiene":97, "independence":56},
            {"day": "Sun", "diet":66, "blood_sugar":42, "medication":47, "hygiene":98, "independence":56},
        ],

        timeline=[
            {"time": "7:30 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "7:45 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "8:10 AM", "label": "Made Coffee",       "icon": "☕️",  "type": "cooking"},
            {"time": "9:20 AM", "label": "Sink activity (dishes)","icon": "🫧",  "type": "dishes"},
            {"time": "9:30 AM", "label": "Blood sugar: 144 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[reinforcement("Rise and Shine!", "Good morning Johnny! Ready to start the day?"),
                                warning("Breakfast", "It looks like you haven't made breakfast yet. Make sure to eat at some point."),
                                warning("Medication", "Don't forget to take your medication, Johnny")],

        family_notifications=[info("Rise and Shine!", "Johnny is awake. Want to say good morning?"),
                                warning("Breakfast", "Johnny has not made breakfast, would you like to call to check in?"),
                                warning("Medication", "Johnny forgot to take his medication today, want to check in?")],

        care_notifications=[warning("Inconsistent Diet", "Johnny has skipped eating breakfast, creating volatile BG readings."),
                            warning("Medication", "Johnny displayed reduced medication adherence, reflected in his blood glucose.")],
    ),
    "SCANT": make_preset(
        name="SCAND",
        description="Start, Coffee, No Eat, No Meds, TV",

        diet_score=63,
        blood_sugar_score=47,
        medication_score=47,
        hygiene_score=55,
        independence_score=33,

        current_bg=135,
        bg_trend="stable",
        last_meal_time="Yesterday, 6:30 PM",
        last_med_time="Yesterday, 8:00 PM",
        stove_status="off",

        todo_items=[
            {"task": "Make a Cup of Coffee",       "done": True,  "time": "8:10 AM"},
            {"task": "Eat breakfast",              "done": True,  "time": "9:00 AM"},
            {"task": "Take Medication",          "done": False,  "time": "9:15 AM"},
            {"task": "Do the Dishes",              "done": False, "time": "9:20 AM"},
            {"task": "Check Blood Sugar",        "done": False, "time": "10:00 AM"},
            {"task": "Call Family",              "done": False,  "time": "12:30 PM"},
        ],

        weekly_history=[
            {"day": "Mon", "diet":65, "blood_sugar":48, "medication":48, "hygiene":51, "independence":36},
            {"day": "Tue", "diet":68, "blood_sugar":50, "medication":47, "hygiene":58, "independence":34},
            {"day": "Wed", "diet":67, "blood_sugar":47, "medication":42, "hygiene":52, "independence":33},
            {"day": "Thu", "diet":64, "blood_sugar":44, "medication":45, "hygiene":55, "independence":38},
            {"day": "Fri", "diet":61, "blood_sugar":48, "medication":46, "hygiene":53, "independence":37},
            {"day": "Sat", "diet":65, "blood_sugar":47, "medication":44, "hygiene":57, "independence":36},
            {"day": "Sun", "diet":66, "blood_sugar":42, "medication":47, "hygiene":58, "independence":36},
        ],

        timeline=[
            {"time": "7:30 AM", "label": "Woke up",              "icon": "☀️",  "type": "wake"},
            {"time": "7:45 AM", "label": "Blood sugar: 103 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
            {"time": "8:10 AM", "label": "Made Coffee",       "icon": "☕️",  "type": "cooking"},
            {"time": "9:30 AM", "label": "Blood sugar: 144 mg/dL — in range", "icon": "🩸", "type": "bg_ok"},
        ],

        patient_notifications=[reinforcement("Rise and Shine!", "Good morning Johnny! Ready to start the day?"),
                                warning("Breakfast", "It looks like you haven't made breakfast yet. Make sure to eat at some point."),
                                warning("Medication", "Don't forget to take your medication, Johnny")],

        family_notifications=[info("Rise and Shine!", "Johnny is awake. Want to say good morning?"),
                                warning("Breakfast", "Johnny has not made breakfast, would you like to call to check in?"),
                                warning("Medication", "Johnny forgot to take his medication today, want to check in?")],

        care_notifications=[warning("Inconsistent Diet", "Johnny has skipped eating breakfast, creating volatile BG readings."),
                            warning("Medication", "Johnny displayed reduced medication adherence, reflected in his blood glucose."),
                            warning("Clutter Warning", "Johnny didn't do the dishes after cooking - environmental cluttering is possible.")],
    ),
}


# ---------------------------------------------------------------------------
# Write output files
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(out_dir, exist_ok=True)

    for name, preset in PRESETS.items():
        path = os.path.join(out_dir, f"{name}.json")
        with open(path, "w") as f:
            json.dump(preset, f, indent=2)
        print(f"Written → {path}")

    print(f"\nDone. {len(PRESETS)} presets written to output/")
    print("\nTo add a new preset:")
    print("  1. Copy one of the preset blocks above")
    print("  2. Give it a new key in the PRESETS dict")
    print("  3. Change the values and notifications")
    print("  4. Run: python3 preset_builder.py")
