import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path

st.set_page_config(page_title="FitApp • Compact Mode", page_icon="💪", layout="centered")

LOG_PATH = Path("workout_logs.csv")
COLUMNS = [
    "session_id","session_start","session_end","workout_name",
    "exercise_name","set_idx","is_warmup","weight_kg","added_load_kg",
    "reps","notes","est_1rm","volume_kg","total_reps"
]

# ------------------ HELPERS ------------------
def load_logs():
    if LOG_PATH.exists():
        try:
            return pd.read_csv(LOG_PATH)
        except Exception:
            return pd.DataFrame(columns=COLUMNS)
    return pd.DataFrame(columns=COLUMNS)

def est_1rm(weight, reps):
    try:
        r = int(reps)
        w = float(weight)
        if r <= 1:
            return w
        return round(w * (1 + r/30), 2)
    except Exception:
        return None

def last_session_for_ex(logs, ex_name):
    if logs.empty:
        return None
    df = logs[logs["exercise_name"] == ex_name]
    if df.empty:
        return None
    df = df[df["is_warmup"] == False]
    if df.empty:
        return None
    last_sess = df.sort_values("session_end").tail(1)
    return last_sess

# ------------------ WORKOUT DATA ------------------
WORKOUTS = {
    "Upper A": [
        {"Exercise": "Bench Press (BB/DB)", "Range": "6–8"},
        {"Exercise": "Pull-Ups (neutral/wide)", "Range": "6–8 (or rep-goal)"},
    ],
}

# ------------------ SESSION STATE ------------------
if "picked" not in st.session_state:
    st.session_state.picked = None
if "session_start" not in st.session_state:
    st.session_state.session_start = None
if "sets_entered" not in st.session_state:
    st.session_state.sets_entered = {}

# ------------------ UI ------------------
st.title("Compact Workout Logger")
st.caption("Minimal scrolling • Dynamic rows • Accordion cards")

cols = st.columns(3)
if cols[0].button("Upper A", use_container_width=True):
    st.session_state.picked = "Upper A"

picked = st.session_state.picked
logs = load_logs()

if picked:
    if not st.session_state.session_start:
        st.session_state.session_start = datetime.now().isoformat(timespec="seconds")
    session_id = f"{datetime.now().strftime('%Y%m%d-%H%M')}-{picked}"

    st.subheader(f"{picked} – Compact Session")

    new_rows = []

    for ex in WORKOUTS[picked]:
        name = ex["Exercise"]
        last_sess = last_session_for_ex(logs, name)
        suggested_w = float(last_sess["weight_kg"].max()) if last_sess is not None else 0.0

        # Accordion per exercise
        with st.expander(f"{name} | Last: {suggested_w}kg", expanded=False):
            weight = st.number_input("Weight (kg)", value=suggested_w, step=0.5, key=f"w_{name}")
            
            # dynamic rows
            if name not in st.session_state.sets_entered:
                st.session_state.sets_entered[name] = [0]

            reps_list = st.session_state.sets_entered[name]

            for i, reps in enumerate(reps_list, start=1):
                reps_val = st.number_input(f"Set {i} reps", min_value=0, max_value=50, value=reps, key=f"reps_{name}_{i}")
                reps_list[i-1] = reps_val

            c1, c2 = st.columns(2)
            if c1.button("+ Add Set", key=f"add_{name}"):
                reps_list.append(0)
                st.rerun()
            if c2.button("🗑 Reset", key=f"reset_{name}"):
                st.session_state.sets_entered[name] = [0]
                st.rerun()

            # save rows
            for idx, reps in enumerate(reps_list, start=1):
                if reps > 0:
                    vol = weight * reps
                    row = {
                        "session_id": session_id,
                        "session_start": st.session_state.session_start,
                        "session_end": "",
                        "workout_name": picked,
                        "exercise_name": name,
                        "set_idx": idx,
                        "is_warmup": False,
                        "weight_kg": weight,
                        "added_load_kg": 0,
                        "reps": reps,
                        "notes": "",
                        "est_1rm": est_1rm(weight, reps),
                        "volume_kg": vol,
                        "total_reps": reps,
                    }
                    new_rows.append(row)

    st.markdown("---")
    if st.button("✅ Finish & Save", use_container_width=True):
        end_ts = datetime.now().isoformat(timespec="seconds")
        if new_rows:
            for r in new_rows:
                r["session_end"] = end_ts
            df_new = pd.DataFrame(new_rows, columns=COLUMNS)
            if LOG_PATH.exists():
                try:
                    df_old = pd.read_csv(LOG_PATH)
                    df_out = pd.concat([df_old, df_new], ignore_index=True)
                except Exception:
                    df_out = df_new
            else:
                df_out = df_new
            df_out.to_csv(LOG_PATH, index=False)
            st.success("Session saved.")
        else:
            st.warning("No reps entered.")