import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path

st.set_page_config(page_title="FitApp • Workout Selector", page_icon="💪", layout="centered")

LOG_PATH = Path("workout_logs.csv")
COLUMNS = [
    "session_id","session_start","session_end","workout_name",
    "exercise_name","set_idx","is_warmup","weight_kg","added_load_kg",
    "reps","notes","est_1rm","volume_kg","total_reps"
]

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

WORKOUTS = {
    "Upper A": [
        {"Exercise": "Bench Press (BB/DB)", "Range": "6–8"},
        {"Exercise": "Pull-Ups (neutral/wide)", "Range": "6–8 (or rep-goal)"},
        {"Exercise": "Overhead Press (DB/bands)", "Range": "6–8"},
        {"Exercise": "Row (BB or 1-Arm DB)", "Range": "~8"},
        {"Exercise": "Dips (weighted if able)", "Range": "8–10"},
        {"Exercise": "EZ Bar Curl", "Range": "10–12"},
        {"Exercise": "Lateral Raise", "Range": "15–20"},
    ],
    "Lower": [
        {"Exercise": "Bulgarian Split Squat / Reverse Lunge", "Range": "6–8/leg"},
        {"Exercise": "Romanian Deadlift", "Range": "~8"},
        {"Exercise": "Step-Ups or Hip Thrusts", "Range": "10–12"},
        {"Exercise": "Calf Raise (BW + DB)", "Range": "12–15"},
        {"Exercise": "Core: Plank / Hollow / Side Plank", "Range": "circuit"},
    ],
    "Upper B": [
        {"Exercise": "Incline DB Press", "Range": "8–10"},
        {"Exercise": "Chin-Ups", "Range": "AMRAP/rep-goal"},
        {"Exercise": "Arnold Press / DB OHP", "Range": "10–12"},
        {"Exercise": "Skullcrusher (EZ Bar)", "Range": "12–15"},
        {"Exercise": "Incline DB Curl or Hammer Curl", "Range": "12–15"},
        {"Exercise": "Upright Row (EZ/Bands)", "Range": "10–12"},
        {"Exercise": "Lateral Raise (variation/giant set)", "Range": "15–20"},
    ],
}

WARMUP_BLUEPRINT = [
    "2–3 min light cardio to raise temp.",
    "Dynamic prep (8–12 reps): arm circles, band pull-aparts, hip-hinge swings, short 'world’s greatest' stretch, scap pull-ups/push-ups.",
    "Specific ramp-up: 2–3 lighter sets of FIRST lift (≈40–60–80%).",
]

RULEBOOK_NOTE = (
    "Autopilot: compounds use double progression (6–8), bodyweight uses rep-goal, isolations add reps then weight, deload after 2–3 stalls."
)

def last_load_for(exercise_name, logs):
    if logs.empty:
        return None
    df = logs[logs["exercise_name"] == exercise_name]
    if df.empty:
        return None
    df = df[df["is_warmup"] == False]
    if df.empty:
        return None
    row = df.sort_values("session_end").tail(1).iloc[0]
    return float(row.get("weight_kg", 0)) or None

def last_sets_count_for(exercise_name, logs, fallback=3):
    """Return number of working sets from the most recent session for this exercise."""
    if logs is None or logs.empty:
        return fallback
    df = logs[(logs["exercise_name"] == exercise_name) & (logs["is_warmup"] == False)].copy()
    if df.empty:
        return fallback
    # Identify last completed session for this exercise
    df = df.sort_values("session_end")
    last_session_id = df["session_id"].iloc[-1]
    n_sets = df[df["session_id"] == last_session_id]["set_idx"].nunique()
    try:
        return int(n_sets) if n_sets and n_sets > 0 else fallback
    except Exception:
        return fallback

st.title("Workout Selector")
st.caption("Pick your session and just enter reps. We’ll carry the weights.")

if "last_workout" not in st.session_state:
    st.session_state.last_workout = None
if "session_start" not in st.session_state:
    st.session_state.session_start = None
if "picked" not in st.session_state:
    st.session_state.picked = None
if "prefill_map" not in st.session_state:
    st.session_state.prefill_map = {}

rotation = ["Upper A", "Lower", "Upper B"]
if st.session_state.last_workout in rotation:
    idx = (rotation.index(st.session_state.last_workout) + 1) % len(rotation)
    suggested = rotation[idx]
else:
    suggested = rotation[0]

st.markdown(f"<div style='text-align:center;opacity:0.8'>Suggested next: <b>{suggested}</b> (override anytime)</div>", unsafe_allow_html=True)

cols = st.columns(3)
if cols[0].button("Upper A", use_container_width=True):
    st.session_state.picked = "Upper A"
if cols[1].button("Lower", use_container_width=True):
    st.session_state.picked = "Lower"
if cols[2].button("Upper B", use_container_width=True):
    st.session_state.picked = "Upper B"

picked = st.session_state.picked

with st.expander("Warm-Up Blueprint (5–8 min)"):
    for step in WARMUP_BLUEPRINT:
        st.markdown(f"- {step}")

st.markdown("---")

logs = load_logs()

if picked:
    st.session_state.last_workout = picked
    if not st.session_state.session_start:
        st.session_state.session_start = datetime.now().isoformat(timespec="seconds")

    st.subheader(f"{picked} – Quick Logger")
    st.caption(RULEBOOK_NOTE)

    session_id = f"{datetime.now().strftime('%Y%m%d-%H%M')}-{picked.replace(' ', '')}" 
    new_rows = []

    for ex in WORKOUTS[picked]:
        name = ex["Exercise"]
        with st.container():
            st.markdown(f"**{name}**  ")
            last_w = last_load_for(name, logs)
            suggested_w = st.number_input(
                f"Suggested weight (kg) — optional",
                value=float(last_w) if last_w is not None else 0.0,
                min_value=0.0, step=0.5, key=f"w_{name}"
            )
            st.caption("Weight carries over. You mainly enter reps.")

            df_ex = logs[logs["exercise_name"] == name]
            if not df_ex.empty:
                last_sess = df_ex.sort_values("session_end").tail(20)
                last_sets = last_sess[last_sess["session_id"] == last_sess["session_id"].iloc[-1]]
                prev_n_sets = last_sets["set_idx"].max()
                prev_reps = last_sets["reps"].tolist()
            else:
                prev_n_sets, prev_reps = None, []

            base_default = 4 if "Press" in name or "Deadlift" in name or "Squat" in name else 3
            carried_sets = last_sets_count_for(name, logs, fallback=(prev_n_sets if prev_n_sets else base_default))
            n_sets = st.number_input("Sets", min_value=1, max_value=8, value=int(carried_sets), step=1, key=f"sets_{name}")

            reps_inputs = []
            # Decide defaults: prefer prefill_map[name] if present, else last session reps
            prefill_list = st.session_state.prefill_map.get(name, None)
            for s in range(1, int(n_sets)+1):
                if prefill_list is not None and len(prefill_list) > 0:
                    default_rep = int(prefill_list[s-1]) if s-1 < len(prefill_list) else 0
                else:
                    default_rep = int(prev_reps[s-1]) if s-1 < len(prev_reps) else 0
                reps = st.number_input(f"Reps – Set {s}", min_value=0, max_value=50, value=default_rep, step=1, key=f"reps_{name}_{s}")
                reps_inputs.append(reps)

            c_copy, c_prefill = st.columns(2)
            if c_copy.button("Copy last set → all", key=f"copy_{name}"):
                try:
                    last_val = int(reps_inputs[-1]) if reps_inputs and reps_inputs[-1] else 0
                    if last_val <= 0:
                        st.warning("No reps in the last set to copy.")
                    else:
                        st.session_state.prefill_map[name] = [last_val] * int(n_sets)
                        st.rerun()
                except Exception as e:
                    st.error(f"Could not copy: {e}")

            if c_prefill.button("Prefill last session reps", key=f"prefill_{name}"):
                try:
                    if prev_reps:
                        vals = [int(prev_reps[i]) if i < len(prev_reps) else 0 for i in range(int(n_sets))]
                        st.session_state.prefill_map[name] = vals
                        st.rerun()
                    else:
                        st.info("No previous reps found for this exercise.")
                except Exception as e:
                    st.error(f"Could not prefill: {e}")

            for idx, reps in enumerate(reps_inputs, start=1):
                if reps > 0:
                    vol = (suggested_w) * reps if suggested_w else 0
                    row = {
                        "session_id": session_id,
                        "session_start": st.session_state.session_start,
                        "session_end": "",
                        "workout_name": picked,
                        "exercise_name": name,
                        "set_idx": idx,
                        "is_warmup": False,
                        "weight_kg": suggested_w,
                        "added_load_kg": 0,
                        "reps": reps,
                        "notes": "",
                        "est_1rm": est_1rm(suggested_w, reps) if suggested_w and reps else None,
                        "volume_kg": vol,
                        "total_reps": reps,
                    }
                    new_rows.append(row)

    st.markdown("---")
    save = st.button("✅ Finish Session & Save", use_container_width=True)
    if save:
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
            st.success(f"Saved {len(df_new)} sets to {LOG_PATH.name}.")
            by_ex = (df_new.groupby("exercise_name")
                            .agg(sets=("set_idx","count"),
                                 top_weight=("weight_kg","max"),
                                 total_reps=("reps","sum"),
                                 volume=("volume_kg","sum"))
                            .reset_index())
            st.markdown("#### Session Summary")
            st.dataframe(by_ex, hide_index=True, use_container_width=True)
        else:
            st.warning("No reps entered — nothing saved.")
        st.session_state.session_start = None

    clr1, clr2 = st.columns(2)
    if clr1.button("🧹 Reset Current Inputs", use_container_width=True):
        try:
            # Clear per-exercise state for the CURRENT workout
            for ex in WORKOUTS[picked]:
                name = ex["Exercise"]
                # Drop any prefill for this exercise
                if "prefill_map" in st.session_state and isinstance(st.session_state.prefill_map, dict):
                    st.session_state.prefill_map.pop(name, None)
                # Remove reps/sets/weight widget state keys safely
                for s in range(1, 13):  # up to 12 sets safety cap
                    rk = f"reps_{name}_{s}"
                    if rk in st.session_state:
                        del st.session_state[rk]
                sk = f"sets_{name}"
                if sk in st.session_state:
                    del st.session_state[sk]
                wk = f"w_{name}"
                if wk in st.session_state:
                    del st.session_state[wk]
            st.toast("Inputs reset.")
        except Exception as e:
            st.error(f"Could not reset inputs: {e}")
        st.rerun()

    if clr2.button("🔄 Start New Session", use_container_width=True):
        try:
            st.session_state.session_start = None
            # Clear all prefills for a clean slate
            st.session_state.prefill_map = {}
            # Optionally keep current 'picked' workout; do not change it.
            st.toast("New session started.")
        except Exception as e:
            st.error(f"Could not start new session: {e}")
        st.rerun()

    with st.expander("Recent History (this workout)"):
        hist = logs[logs["workout_name"] == picked].sort_values("session_end").tail(50)
        if hist.empty:
            st.write("No history yet. Today sets your baseline.")
        else:
            st.dataframe(hist[["session_end","exercise_name","set_idx","weight_kg","reps","volume_kg"]], hide_index=True, use_container_width=True)

st.markdown("""
<div style='text-align:center; opacity:0.6; font-size:0.9em;'>
  Minimal logging: reps + sets. We carry weights and history.
</div>
""", unsafe_allow_html=True)
