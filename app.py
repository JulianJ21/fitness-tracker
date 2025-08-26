import streamlit as st
from datetime import datetime

st.set_page_config(page_title="FitApp • Workout Selector", page_icon="💪", layout="centered")

# ---------------------------
# DATA: Workouts & Blueprints
# ---------------------------
WORKOUTS = {
    "Upper A": [
        {"Exercise": "Bench Press (BB/DB)", "Sets": 4, "Reps": "6–8", "Notes": "Double progression"},
        {"Exercise": "Pull-Ups (neutral/wide)", "Sets": 4, "Reps": "6–8", "Notes": "Rep goal if BW"},
        {"Exercise": "Overhead Press (DB/bands)", "Sets": 3, "Reps": "6–8", "Notes": "Keep reps crisp"},
        {"Exercise": "Row (BB or 1-Arm DB)", "Sets": 3, "Reps": "~8", "Notes": "Full range"},
        {"Exercise": "Dips (weighted if able)", "Sets": 3, "Reps": "8–10", "Notes": "Controlled depth"},
        {"Exercise": "EZ Bar Curl", "Sets": 3, "Reps": "10–12", "Notes": "Squeeze top"},
        {"Exercise": "Lateral Raise", "Sets": 3, "Reps": "15–20", "Notes": "Light, clean form"},
    ],
    "Lower": [
        {"Exercise": "Bulgarian Split Squat / Reverse Lunge", "Sets": 4, "Reps": "6–8/leg", "Notes": "Stay balanced"},
        {"Exercise": "Romanian Deadlift", "Sets": 4, "Reps": "~8", "Notes": "Hinge, lats tight"},
        {"Exercise": "Step-Ups or Hip Thrusts", "Sets": 3, "Reps": "10–12", "Notes": "Glutes focus"},
        {"Exercise": "Calf Raise (BW + DB)", "Sets": 4, "Reps": "12–15", "Notes": "Pause at stretch"},
        {"Exercise": "Core: Plank / Hollow / Side Plank", "Sets": 3, "Reps": "circuit", "Notes": "Solid bracing"},
    ],
    "Upper B": [
        {"Exercise": "Incline DB Press", "Sets": 3, "Reps": "8–10", "Notes": "Controlled tempo"},
        {"Exercise": "Chin-Ups", "Sets": 3, "Reps": "AMRAP", "Notes": "Rep goal if BW"},
        {"Exercise": "Arnold Press / DB OHP", "Sets": 3, "Reps": "10–12", "Notes": "Shoulder focus"},
        {"Exercise": "Skullcrusher (EZ Bar)", "Sets": 3, "Reps": "12–15", "Notes": "Elbows steady"},
        {"Exercise": "Incline DB Curl or Hammer Curl", "Sets": 3, "Reps": "12–15", "Notes": "No swinging"},
        {"Exercise": "Upright Row (EZ/Bands)", "Sets": 3, "Reps": "10–12", "Notes": "To mid-chest"},
        {"Exercise": "Lateral Raise (variation/giant set)", "Sets": 4, "Reps": "15–20", "Notes": "Pump work"},
    ],
}

WARMUP_BLUEPRINT = [
    "2–3 min light cardio (bike/jacks/shadowbox) to raise temp.",
    "Dynamic prep (8–12 reps each): arm circles, band pull-aparts, hip-hinge swings, short 'world’s greatest' stretch, scap pull-ups/push-ups.",
    "Specific ramp-up: 2–3 lighter sets of FIRST lift (≈40–60–80% of working load).",
]

PROGRESSION_RULES = [
    "Compounds (6–8 reps): Double progression — when you hit the top end across sets, add a small weight next time.",
    "Bodyweight (pull-ups/dips): Rep goal system — when total target is hit across sets, add weight.",
    "Isolation (10–15, laterals 15–20): Add reps week to week; when you reach the top end cleanly, bump weight and reset reps.",
    "Deload: If no progress for 2–3 sessions on a lift, drop 10–15% and rebuild.",
]

# ---------------------------
# UI: Header & Selector
# ---------------------------
st.title("Workout Selector")
st.caption("Pick your session for today. No calendar, no guilt — just train.")

if "last_workout" not in st.session_state:
    st.session_state.last_workout = None

# Suggest next in rotation (soft suggestion)
rotation = ["Upper A", "Lower", "Upper B"]
if st.session_state.last_workout in rotation:
    idx = (rotation.index(st.session_state.last_workout) + 1) % len(rotation)
    suggested = rotation[idx]
else:
    suggested = rotation[0]

with st.container():
    st.markdown("### Select a workout")
    c1, c2, c3 = st.columns(3)
    picked = None
    with c1:
        if st.button("Upper A", use_container_width=True):
            picked = "Upper A"
    with c2:
        if st.button("Lower", use_container_width=True):
            picked = "Lower"
    with c3:
        if st.button("Upper B", use_container_width=True):
            picked = "Upper B"

    st.markdown(f"<div style='text-align:center;opacity:0.8'>Suggested next: <b>{suggested}</b> (you can override)</div>", unsafe_allow_html=True)

# Warm-Up blueprint as reusable panel
with st.expander("Warm-Up Blueprint (5–8 min)", expanded=False):
    for step in WARMUP_BLUEPRINT:
        st.markdown(f"- {step}")
    st.info("Keep it lowkey: smooth reps, no fatigue before the main work.")

# Progression rules panel
with st.expander("Progression Rulebook", expanded=False):
    for rule in PROGRESSION_RULES:
        st.markdown(f"- {rule}")

# Render picked workout
if picked:
    st.session_state.last_workout = picked
    st.divider()
    st.subheader(f"{picked} – Session Plan")
    st.caption("Focus on quality reps. Log sets/reps/weights as you go (tracking comes next phase).")

    # Simple table
    import pandas as pd
    df = pd.DataFrame(WORKOUTS[picked])
    st.dataframe(df, hide_index=True, use_container_width=True)

    with st.container():
        st.markdown("#### Notes")
        if picked == "Upper A":
            st.markdown("- Heavy compounds first. Finish with arms/shoulders.")
        elif picked == "Lower":
            st.markdown("- Posterior-chain + unilateral focus. Manage soreness for BJJ.")
        elif picked == "Upper B":
            st.markdown("- Shoulder & arm volume emphasis. Chase the pump, not slop.")

    # Placeholder controls for future logging
    st.divider()
    st.caption("Coming soon: in-session logger, auto-progression suggestions, and export to CSV/SQLite.")

# Footer
st.markdown("""
<div style='text-align:center; opacity:0.6; font-size:0.9em;'>
  FitApp MVP • Build strength with simple rules and consistent execution.
</div>
""", unsafe_allow_html=True)
