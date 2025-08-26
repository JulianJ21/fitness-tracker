import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
import math

st.set_page_config(page_title="FitApp • Compact Mode", page_icon="💪", layout="centered")

# ------------------ STORAGE ------------------
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

def save_rows(rows: list):
    df_new = pd.DataFrame(rows, columns=COLUMNS)
    if LOG_PATH.exists():
        try:
            df_old = pd.read_csv(LOG_PATH)
            df_out = pd.concat([df_old, df_new], ignore_index=True)
        except Exception:
            df_out = df_new
    else:
        df_out = df_new
    df_out.to_csv(LOG_PATH, index=False)
    return df_new

# Epley 1RM
def est_1rm(weight, reps):
    try:
        r = int(reps)
        w = float(weight)
        if r <= 1:
            return w
        return round(w * (1 + r/30), 2)
    except Exception:
        return None

# Last session summary & suggestions
def last_summary(logs, ex_name):
    if logs.empty:
        return {"weight": 0.0, "reps": [], "n_sets": 0}
    df = logs[(logs["exercise_name"] == ex_name) & (logs["is_warmup"] == False)].copy()
    if df.empty:
        return {"weight": 0.0, "reps": [], "n_sets": 0}
    df = df.sort_values("session_end")
    last_id = df["session_id"].iloc[-1]
    last_df = df[df["session_id"] == last_id].sort_values("set_idx")
    weight = float(last_df["weight_kg"].max()) if not last_df.empty else 0.0
    reps = last_df["reps"].astype(int).tolist()
    return {"weight": weight, "reps": reps, "n_sets": len(reps)}

# ------------------ WORKOUT DATA ------------------
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

# ------------------ SESSION STATE ------------------
if "picked" not in st.session_state:
    st.session_state.picked = None
if "session_start" not in st.session_state:
    st.session_state.session_start = None
if "sets_entered" not in st.session_state:
    st.session_state.sets_entered = {}  # {exercise: [reps,...]}
if "weights" not in st.session_state:
    st.session_state.weights = {}       # {exercise: weight}

# ------------------ STYLES ------------------
st.markdown(
    """
    <style>
      .header-row {display:flex; gap:8px; align-items:center; justify-content:space-between;}
      .hdr-left {display:flex; gap:10px; align-items:baseline;}
      .hdr-title {font-weight:600;}
      .hdr-meta {opacity:0.75; font-size:0.9em;}
      .tiny-btn button {padding:2px 6px; font-size:0.85em;}
      .footer-bar {position:fixed; left:0; right:0; bottom:0; padding:10px 16px; backdrop-filter: blur(8px); background: rgba(255,255,255,0.75); border-top:1px solid rgba(0,0,0,0.08); z-index:9999;}
      .footer-inner {display:flex; gap:10px; align-items:center; justify-content:space-between; max-width: 900px; margin: 0 auto;}
      .footer-title {font-weight:600; opacity:0.8}
      .pill {display:inline-block; padding:2px 8px; border-radius:999px; background:rgba(0,0,0,0.06); font-size:12px; margin-left:6px}
      .info-chip {display:inline-block; padding:2px 6px; border-radius:8px; background:rgba(0,0,0,0.05); font-size:12px; margin-left:6px}
      .card {padding:8px 6px; border-radius:12px; border:1px solid rgba(0,0,0,0.08); margin-bottom:8px}
    </style>
    """,
    unsafe_allow_html=True,
)
# ------------------ UI: HEADER ------------------
st.title("Compact Workout Logger")
st.caption("Minimal scrolling • Dynamic rows • Accordion cards • Sticky Save")

cols = st.columns(3)
if cols[0].button("Upper A", use_container_width=True):
    st.session_state.picked = "Upper A"
if cols[1].button("Lower", use_container_width=True):
    st.session_state.picked = "Lower"
if cols[2].button("Upper B", use_container_width=True):
    st.session_state.picked = "Upper B"

picked = st.session_state.picked
logs = load_logs()

# Remove sidebar save; we'll add a sticky footer bar instead
if picked:
    if not st.session_state.session_start:
        st.session_state.session_start = datetime.now().isoformat(timespec="seconds")
    session_id = f"{datetime.now().strftime('%Y%m%d-%H%M')}-{picked.replace(' ', '')}"

    st.subheader(f"{picked} – Compact Session")

    new_rows = []

    for ex in WORKOUTS[picked]:
        name = ex["Exercise"]
        last = last_summary(logs, name)
        last_w = float(last["weight"]) if last else 0.0
        last_sets = last["n_sets"] if last else 0
        last_avg_reps = int(round(sum(last["reps"])/last_sets)) if last_sets else 0

        # Carry current weight from state or last session
        cur_w = st.session_state.weights.get(name, last_w)

        # Accordion header with meta + actions
        header = st.container()
        with header:
            st.markdown(
                f"<div class='header-row'>"
                f"  <div class='hdr-left'>"
                f"    <span class='hdr-title'>{name}</span>"
                f"    <span class='hdr-meta'>• {cur_w:g} kg • Last: {last_sets}×{last_avg_reps if last_avg_reps else '-'} </span>"
                f"  </div>"
                f"  <div class='hdr-actions'>"
                f"  </div>"
                f"</div>",
                unsafe_allow_html=True,
            )
        with st.expander("Log sets", expanded=False):
            # Adjust weight (hidden by default)
            with st.expander("⚖️ Adjust weight", expanded=False):
                cur_w = st.number_input("Weight (kg)", value=float(cur_w), min_value=0.0, step=0.5, key=f"w_{name}")
                st.session_state.weights[name] = cur_w

            # Prefill controls (icons in a small row)
            cA, cB, cC = st.columns([1,1,6])
            if cA.button("📋 Prefill last", key=f"prefill_{name}"):
                if last and last["reps"]:
                    st.session_state.sets_entered[name] = last["reps"].copy()
                else:
                    st.session_state.sets_entered[name] = [0]
                st.rerun()
            if cB.button("♻️ Reset", key=f"reset_{name}"):
                st.session_state.sets_entered[name] = [0]
                st.rerun()

            # Dynamic rows (start minimal)
            if name not in st.session_state.sets_entered:
                st.session_state.sets_entered[name] = [0]
            reps_list = st.session_state.sets_entered[name]

            # Render rows with small +/- steppers
            for i in range(len(reps_list)):
                cols_row = st.columns([2,1,1,1])
                cols_row[0].markdown(f"Set {i+1}")
                rep_key = f"reps_{name}_{i+1}"
                # Number input (compact)
                reps_val = cols_row[1].number_input("reps", min_value=0, max_value=50, value=int(reps_list[i]), step=1, key=rep_key, label_visibility="collapsed")
                # Quick - / +
                if cols_row[2].button("-", key=f"minus_{name}_{i}"):
                    reps_val = max(0, int(reps_val) - 1)
                    st.session_state.sets_entered[name][i] = reps_val
                    st.rerun()
                if cols_row[3].button("+", key=f"plus_{name}_{i}"):
                    reps_val = int(reps_val) + 1
                    st.session_state.sets_entered[name][i] = reps_val
                    st.rerun()
                # Save back current value
                st.session_state.sets_entered[name][i] = int(reps_val)

            c1, c2, c3 = st.columns(3)
            if c1.button("+ Add Set", key=f"add_{name}"):
                reps_list.append(0)
                st.session_state.sets_entered[name] = reps_list
                st.rerun()
            if c2.button("Copy last set → all", key=f"copy_{name}"):
                if reps_list:
                    last_val = int(reps_list[-1])
                    st.session_state.sets_entered[name] = [last_val for _ in reps_list]
                st.rerun()
            # minimal per-exercise totals
            total_reps = sum(int(x) for x in reps_list)
            c3.markdown(f"**Total reps:** {total_reps}")

            # Collect rows (only >0 reps)
            for idx, reps in enumerate(reps_list, start=1):
                reps = int(reps)
                if reps > 0:
                    vol = float(cur_w) * reps
                    new_rows.append({
                        "session_id": session_id,
                        "session_start": st.session_state.session_start,
                        "session_end": "",
                        "workout_name": picked,
                        "exercise_name": name,
                        "set_idx": idx,
                        "is_warmup": False,
                        "weight_kg": float(cur_w),
                        "added_load_kg": 0,
                        "reps": reps,
                        "notes": "",
                        "est_1rm": est_1rm(cur_w, reps),
                        "volume_kg": vol,
                        "total_reps": reps,
                    })

    # Sticky/Sidebar Save actions
    # Floating visual button (non-functional anchor for aesthetics)
    st.markdown("<div class='sticky-save'>""</div>", unsafe_allow_html=True)

    # Real save lives in sidebar (always visible)
    if sidebar_save:
        end_ts = datetime.now().isoformat(timespec="seconds")
        if new_rows:
            for r in new_rows:
                r["session_end"] = end_ts
            df_new = save_rows(new_rows)
            st.success(f"Saved {len(df_new)} sets to {LOG_PATH.name}.")
            by_ex = (df_new.groupby("exercise_name")
                        .agg(sets=("set_idx","count"), top_weight=("weight_kg","max"), total_reps=("reps","sum"), volume=("volume_kg","sum"))
                        .reset_index())
            st.markdown("#### Session Summary")
            st.dataframe(by_ex, hide_index=True, use_container_width=True)
            # Reset after save
            st.session_state.session_start = None
            st.session_state.sets_entered = {}
            st.session_state.weights = {}
        else:
            st.warning("No reps entered — nothing saved.")
else:
    st.info("Pick a workout to start: Upper A • Lower • Upper B")
