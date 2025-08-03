
import streamlit as st
import pandas as pd
import datetime
import os

# --- Workout Plan ---
workout_plan = {
    "Mon": [
        "Split Squat", "Bench Press", "Pull-Ups", "Close-Grip Push-Up", "EZ Curl", "Lateral Raise"
    ],
    "Wed": [
        "RDL", "Incline DB Press", "1-Arm Row", "Skullcrusher", "Incline Curl", "Lateral Raise"
    ],
    "Sat": [
        "Reverse Lunge", "Step-Up", "Chin-Ups", "Dips", "Shrugs / Carries", "Plank / Hollow Hold", "Lateral Raise"
    ]
}

# --- Load or create progress file ---
progress_file = "progress.csv"
if os.path.exists(progress_file):
    df = pd.read_csv(progress_file)
else:
    df = pd.DataFrame(columns=["Date", "Day", "Exercise", "Weight", "Reps", "Sets"])

# --- UI ---
st.title("🏋️ Workout Tracker")

today = datetime.date.today()
st.write(f"Date: {today}")

day = st.selectbox("Select workout day", list(workout_plan.keys()))
st.write(f"### Exercises for {day}")

for exercise in workout_plan[day]:
    st.subheader(exercise)
    prev = df[(df["Exercise"] == exercise) & (df["Day"] == day)].sort_values("Date", ascending=False).head(1)
    if not prev.empty:
        st.write(f"Last time: {prev['Weight'].values[0]} kg, {prev['Reps'].values[0]} reps × {prev['Sets'].values[0]} sets")
    else:
        st.write("No previous data")

    weight = st.number_input(f"Weight used for {exercise} (kg)", min_value=0.0, step=0.5, key=exercise+"w")
    reps = st.number_input(f"Reps per set for {exercise}", min_value=1, step=1, key=exercise+"r")
    sets = st.number_input(f"Number of sets for {exercise}", min_value=1, step=1, key=exercise+"s")

    if st.button(f"Save {exercise}", key=exercise):
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
        st.success(f"Saved {exercise}")
