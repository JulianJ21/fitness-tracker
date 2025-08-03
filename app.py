
import streamlit as st
import pandas as pd
import datetime
import os

# --- Workout Plan with new labels ---
workout_plan = {
    "Strength (Mon)": [
        "Split Squat", "Bench Press", "Pull-Ups", "Close-Grip Push-Up", "EZ Curl", "Lateral Raise"
    ],
    "Volume (Wed)": [
        "RDL", "Incline DB Press", "1-Arm Row", "Skullcrusher", "Incline Curl", "Lateral Raise"
    ],
    "Athleticism (Sat)": [
        "Reverse Lunge", "Step-Up", "Chin-Ups", "Dips", "Shrugs / Carries", "Plank / Hollow Hold", "Lateral Raise"
    ]
}

# Load or create progress file
progress_file = "progress.csv"
if os.path.exists(progress_file):
    df = pd.read_csv(progress_file)
else:
    df = pd.DataFrame(columns=["Date", "Day", "Exercise", "Weight", "Reps", "Sets"])

# --- Page config ---
st.set_page_config(page_title="Julian's Workout Tracker", layout="centered")

# --- Style ---
st.markdown("""
    <style>
        .title { font-size: 2.2em; font-weight: bold; text-align: center; margin-bottom: 0.5em; }
        .subtitle { font-size: 1.4em; font-weight: 600; margin-top: 1.5em; color: #333; }
        .last-session { color: #888; font-size: 0.9em; }
        .stButton>button { width: 100%; margin-top: 0.3em; background-color: #4CAF50; color: white; border-radius: 8px; }
        .stNumberInput input { border-radius: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- UI ---
st.markdown('<div class="title">🏋️ Julian's Workout Tracker</div>', unsafe_allow_html=True)

today = datetime.date.today()
st.write(f"📅 **Date:** {today}")

day = st.selectbox("🏷️ Select workout type", list(workout_plan.keys()))
st.markdown(f'<div class="subtitle">Exercises for {day}</div>', unsafe_allow_html=True)

for exercise in workout_plan[day]:
    st.markdown(f"#### {exercise}")
    prev = df[(df["Exercise"] == exercise) & (df["Day"] == day)].sort_values("Date", ascending=False).head(1)
    if not prev.empty:
        st.markdown(f'<div class="last-session">Last: {prev["Weight"].values[0]} kg, {prev["Reps"].values[0]} reps × {prev["Sets"].values[0]} sets</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="last-session">No previous data</div>', unsafe_allow_html=True)

    weight = st.number_input(f"Weight (kg)", min_value=0.0, step=0.5, key=exercise+"w")
    reps = st.number_input(f"Reps", min_value=1, step=1, key=exercise+"r")
    sets = st.number_input(f"Sets", min_value=1, step=1, key=exercise+"s")

    if st.button(f"💾 Save {exercise}", key=exercise):
        new_entry = pd.DataFrame({
            "Date": [str(today)],
            "Day": [day],
            "Exercise": [exercise],
            "Weight": [weight],
            "Reps": [reps],
            "Sets": [sets]
        })
        df = pd.concat([df, new_entry], ignore_index=True)
        df.to_csv(progress_file, index=False)
        st.success(f"Saved: {exercise}")
