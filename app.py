import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path

st.set_page_config(page_title="FitApp • Workout Selector", page_icon="💪", layout="centered")

# ---------------------------------
# STORAGE
# ---------------------------------
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

# basic epley 1RM
def est_1rm(weight, reps):
    try:
        r = int(reps)
        w = float(weight)
        if r <= 1:
            return w
        return round(w * (1 + r/30), 2)
    except Exception:
        return None

# ---------------------------------
# DATA: Workouts & Rules (minimal)
# ---------------------------------
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

# ---------------------------------
# HISTORY & SUGGESTION HELPERS
# ---------------------------------

def last_load_for(exercise_name, logs):
    if logs.empty:
        return None
    df = logs[logs["exercise_name"] == exercise_name]
    if df.empty:
        return None
    # choose last non-warmup set weight
    df = df[df["is_warmup"] == False]
    if df.empty:
        return None
    row = df.sort_values("session_end").tail(1).iloc[0]
    return float(row.get("weight_kg", 0)) or None

# ---------------------------------
# UI: Header & Selector
# ---------------------------------
st.title("Workout Selector")
st.caption("Pick your session and just enter reps. We’ll carry the weights.")

if "last_workout" not in st.session_state:
    st.session_state.last_workout = None
if "session_start" not in st.session_state:
    st.session_state.session_start = None

rotation = ["Upper A", "Lower", "Upper B"]
if st.session_state.last_workout in rotation:
    idx = (rotation.index(st.session_state.last_workout) + 1) % len(rotation)
    suggested = rotation[idx]
else:
    suggested = rotation[0]

st.markdown(f"<div style='text-align:center;opacity:0.8'>Suggested next: <b>{suggested}</b> (override anytime)</div>", unsafe_allow_html=True)

cols = st.columns(3)
picked = None
if cols[0].button("Upper A", use_container_width=True):
    picked = "Upper A"
if cols[1].button("Lower", use_container_width=True):
    picked = "Lower"
if cols[2].button("Upper B", use_container_width=True):
    picked = "Upper B"

with st.expander("Warm-Up Blueprint (5–8 min)"):
    for step in WARMUP_BLUEPRINT:
        st.markdown(f"- {step}")

st.markdown("---")

# ---------------------------------
# MINIMAL LOGGER (Reps-only primary input)
# ---------------------------------
logs = load_logs()

if picked:
    st.session_state.last_workout = picked
    if not st.session_state.session_start:
        st.session_state.session_start = datetime.now().isoformat(timespec="seconds")

    st.subheader(f"{picked} – Quick Logger")
    st.caption(RULEBOOK_NOTE)

    # Session id
    session_id = f"{datetime.now().strftime('%Y%m%d-%H%M')}-{picked.replace(' ', '')}" 

    # build a reps-only logger: we prefill weights from last time and you mainly enter reps
    new_rows = []

    for ex in WORKOUTS[picked]:
        name = ex["Exercise"]
        with st.container():
            st.markdown(f"**{name}**  ")
            # last weight suggestion
            last_w = last_load_for(name, logs)
            suggested_w = st.number_input(
                f"Suggested weight (kg) — optional",
                value=float(last_w) if last_w is not None else 0.0,
                min_value=0.0, step=0.5, key=f"w_{name}"
            )
            st.caption("Leave as-is; you only need to enter reps below. Adjust weight only if you want.")

            # choose number of sets first (defaults sensible by category)
            default_sets = 4 if "Press" in name or "Deadlift" in name or "Squat" in name else 3
            carried_sets = last_sets_count_for(name, logs, fallback=default_sets)
            n_sets = st.number_input("Sets", min_value=1, max_value=8, value=carried_sets, step=1, key=f"sets_{name}")

            reps_inputs = []
            for s in range(1, int(n_sets)+1):
                reps_key = f"reps_{name}_{s}"
                reps = st.number_input(f"Reps – Set {s}", min_value=0, max_value=50, value=0, step=1, key=reps_key)
                reps_inputs.append(reps)

            # One-tap copy: duplicate the last non-zero set's reps into the next empty set
            def _copy_last_into_next_empty(prefix_name):
                last_val = None
                next_empty_idx = None
                for s in range(1, int(n_sets)+1):
                    val = st.session_state.get(f"reps_{prefix_name}_{s}", 0)
                    if val and val > 0:
                        last_val = val
                    if (next_empty_idx is None) and (not val or val == 0):
                        next_empty_idx = s
                if last_val is not None and next_empty_idx is not None:
                    st.session_state[f"reps_{prefix_name}_{next_empty_idx}"] = int(last_val)
                    st.toast(f"Copied {last_val} reps to Set {next_empty_idx}")

            if st.button("Copy last set → next empty", key=f"copybtn_{name}"):
                _copy_last_into_next_empty(name)

            # create rows (warmups excluded from this minimal logger)
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
        # finalize session end, append to CSV
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
            # Simple session summary
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

    # Reset/clear controls
    clr1, clr2 = st.columns(2)
    if clr1.button("🧹 Reset Current Inputs", use_container_width=True):
        # Clear reps widgets for this picked workout
        for ex in WORKOUTS[picked]:
            name = ex["Exercise"]
            default_sets = 4 if "Press" in name or "Deadlift" in name or "Squat" in name else 3
            for s in range(1, int(default_sets)+1):
                key = f"reps_{name}_{s}"
                if key in st.session_state:
                    st.session_state[key] = 0
        st.toast("Inputs reset.")
    if clr2.button("🔄 Start New Session", use_container_width=True):
        st.session_state.session_start = None
        st.experimental_rerun()

    # History preview for context
    with st.expander("Recent History (this workout)"):
        hist = logs[logs["workout_name"] == picked].sort_values("session_end").tail(50)
        if hist.empty:
            st.write("No history yet. Today sets your baseline.")
        else:
            st.dataframe(hist[["session_end","exercise_name","set_idx","weight_kg","reps","volume_kg"]], hide_index=True, use_container_width=True)

# ---------------------------------
# PROGRESS GRAPHS (Beta)
# ---------------------------------
with st.expander("📈 Progress (Beta)", expanded=False):
    if LOG_PATH.exists():
        logs = load_logs()
        # exclude warmups
        data = logs.copy()
        if not data.empty:
            data["session_end"] = pd.to_datetime(data["session_end"], errors="coerce")
            data = data[data["is_warmup"] == False]
            data = data.dropna(subset=["session_end"])  # only finalized sets

            # exercise picker
            exercises = sorted(data["exercise_name"].dropna().unique().tolist())
            if exercises:
                ex_pick = st.selectbox("Exercise", exercises, index=0)
                metric = st.selectbox("Metric", ["Top Set Weight (kg)", "Estimated 1RM", "Total Volume (kg) per Session", "Total Reps per Session"], index=0)

                # aggregate by session for chosen exercise
                d_ex = data[data["exercise_name"] == ex_pick]
                by_sess = (d_ex.groupby(["session_id", "session_end"]) 
                                .agg(top_weight=("weight_kg", "max"),
                                     est1rm=("est_1rm", "max"),
                                     total_volume=("volume_kg", "sum"),
                                     total_reps=("reps", "sum"))
                                .reset_index()
                                .sort_values("session_end"))
                if not by_sess.empty:
                    if metric.startswith("Top Set"):
                        y = by_sess[["session_end", "top_weight"]].set_index("session_end")
                        st.line_chart(y)
                        st.caption("Shows heaviest working set each session.")
                    elif metric.startswith("Estimated 1RM"):
                        y = by_sess[["session_end", "est1rm"]].set_index("session_end")
                        st.line_chart(y)
                        st.caption("Epley estimate from your best set per session.")
                    elif metric.startswith("Total Volume"):
                        y = by_sess[["session_end", "total_volume"]].set_index("session_end")
                        st.line_chart(y)
                        st.caption("Sum of (weight × reps) across sets per session.")
                    else:
                        y = by_sess[["session_end", "total_reps"]].set_index("session_end")
                        st.line_chart(y)
                        st.caption("Total reps logged for this exercise per session.")

                    # quick PR badges
                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        st.metric("Top Set (kg)", value=(by_sess["top_weight"].max() if not by_sess["top_weight"].isna().all() else 0))
                    with c2:
                        st.metric("Best est 1RM", value=(by_sess["est1rm"].max() if not by_sess["est1rm"].isna().all() else 0))
                    with c3:
                        st.metric("Best Volume (kg)", value=int(by_sess["total_volume"].max() if not by_sess["total_volume"].isna().all() else 0))
                    with c4:
                        st.metric("Best Total Reps", value=int(by_sess["total_reps"].max() if not by_sess["total_reps"].isna().all() else 0))

            st.markdown("---")
            # Weekly training frequency (all workouts)
            wk = (logs.dropna(subset=["session_end"]).copy())
            wk["session_end"] = pd.to_datetime(wk["session_end"], errors="coerce")
            wk = wk.dropna(subset=["session_end"]) 
            wk = wk.groupby(["session_id", "session_end"]).size().reset_index(name="sets")
            if not wk.empty:
                wk["week"] = wk["session_end"].dt.to_period("W").dt.start_time
                freq = wk.groupby("week").agg(sessions=("session_id", "nunique")).reset_index().set_index("week").sort_index()
                st.subheader("Weekly Sessions")
                st.line_chart(freq)
                st.caption("How many training sessions you completed each week.")
        else:
            st.info("No data yet. Log a session to unlock progress graphs.")
    else:
        st.info("No logs found yet. After saving your first workout, graphs will appear here.")

# Footer
st.markdown("""
<div style='text-align:center; opacity:0.6; font-size:0.9em;'>
  Minimal logging + Progress (Beta). Build history first; insights compound over time.
</div>
""", unsafe_allow_html=True)
