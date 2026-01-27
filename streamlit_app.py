import csv
import json
import random
from datetime import date, datetime, time, timedelta
from pathlib import Path

import streamlit as st
import zen

BUSINESS_RULES_PATH = Path("rules/business_hours.jdm.json")
HOLIDAY_RULES_PATH = Path("rules/public_holidays.jdm.json")
LOOKUP_PATH = Path("data/business_hours.csv")
HOLIDAY_LOOKUP_PATH = Path("data/2026_pubhol_QLD.csv")
LOG_PATH = Path("data/decision_log.csv")


@st.cache_resource
def load_decision(path: Path):
    content = path.read_text(encoding="utf-8")
    engine = zen.ZenEngine()
    return engine.create_decision(content)


def random_datetime_2026():
    start = datetime(2026, 1, 1, 0, 0, 0)
    end = datetime(2026, 12, 31, 23, 59, 59)
    delta_seconds = int((end - start).total_seconds())
    return start + timedelta(seconds=random.randint(0, delta_seconds))


def ensure_log_header():
    if not LOG_PATH.exists():
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "generated_at_iso",
                    "date",
                    "time",
                    "day_of_week_name",
                    "day_of_week_num",
                    "minutes",
                    "gorules_input_json",
                    "gorules_output_message",
                ]
            )


def append_log_row(row):
    ensure_log_header()
    with LOG_PATH.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(row)


def load_lookup_rows(path: Path):
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def evaluate_and_render(dt, holiday_decision, business_decision):
    day_name = dt.strftime("%A")
    day_num = dt.isoweekday()
    date_str = dt.strftime("%Y-%m-%d")
    time_str = dt.strftime("%H:%M")
    minutes = dt.hour * 60 + dt.minute

    holiday_input = {"date": date_str}
    business_input = {"day_of_week": day_num, "minutes": minutes}

    holiday_message = ""
    holiday_name = ""
    holiday_day = ""
    holiday_location = ""
    try:
        holiday_result = holiday_decision.evaluate(holiday_input)
        holiday_message = holiday_result.get("result", {}).get("message", "")
        holiday_name = holiday_result.get("result", {}).get("holiday_name", "")
        holiday_day = holiday_result.get("result", {}).get("day_of_week", "")
        holiday_location = holiday_result.get("result", {}).get("location", "")
    except Exception as exc:
        st.error(f"GoRules holiday evaluation failed: {exc}")

    decision_used = "business-hours"
    final_message = ""

    if holiday_message:
        decision_used = "public-holiday"
        final_message = holiday_message
    else:
        try:
            result = business_decision.evaluate(business_input)
            final_message = result.get("result", {}).get("message", "")
        except Exception as exc:
            st.error(f"GoRules business hours evaluation failed: {exc}")

    st.subheader("Generated")
    st.write(f"Date: {date_str}")
    st.write(f"Time: {time_str}")
    st.write(f"Day: {day_name} (#{day_num})")
    st.write(f"Minutes since midnight: {minutes}")

    st.subheader("Decision")
    st.write(f"Path: {decision_used}")
    if holiday_message:
        if holiday_name:
            st.write(f"Holiday: {holiday_name}")
        if holiday_day:
            st.write(f"Holiday Day: {holiday_day}")
        if holiday_location:
            st.write(f"Location: {holiday_location}")
        st.error(final_message)
    else:
        if final_message:
            st.success(final_message)
        else:
            st.warning("No result returned from GoRules.")

    gorules_input = {
        "holiday": holiday_input,
        "business_hours": business_input,
    }

    append_log_row(
        [
            dt.isoformat(),
            date_str,
            time_str,
            day_name,
            day_num,
            minutes,
            json.dumps(gorules_input, separators=(",", ":")),
            final_message,
        ]
    )


st.set_page_config(page_title="GoRules Business Hours", layout="centered")

st.title("GoRules Business Hours PoC")
st.write("Evaluate a random or manual date/time against public holidays and business hours.")

try:
    holiday_decision = load_decision(HOLIDAY_RULES_PATH)
    business_decision = load_decision(BUSINESS_RULES_PATH)
except Exception as exc:
    st.error(f"Failed to load GoRules decision: {exc}")
    st.stop()

mode = st.radio("Input mode", ["Random (2026)", "Manual"], horizontal=True)

if mode == "Random (2026)":
    if st.button("Generate random date/time"):
        evaluate_and_render(random_datetime_2026(), holiday_decision, business_decision)
else:
    col_date, col_time = st.columns(2)
    with col_date:
        input_date = st.date_input(
            "Date",
            value=date(2026, 1, 27),
            min_value=date(2026, 1, 1),
            max_value=date(2026, 12, 31),
        )
    with col_time:
        input_time = st.time_input("Time", value=time(9, 0))

    if st.button("Evaluate manual date/time"):
        dt = datetime.combine(input_date, input_time)
        evaluate_and_render(dt, holiday_decision, business_decision)

st.subheader("Business Hours Lookup")
lookup_rows = load_lookup_rows(LOOKUP_PATH)
if lookup_rows:
    st.dataframe(lookup_rows, width='stretch')
else:
    st.info("Business hours lookup table not found.")

st.subheader("Public Holidays Lookup")
holiday_rows = load_lookup_rows(HOLIDAY_LOOKUP_PATH)
if holiday_rows:
    st.dataframe(holiday_rows, width='stretch')
else:
    st.info("Public holidays lookup table not found.")
