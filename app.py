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

def est_1rm(weight, reps):
    try:
        r = int(reps)
        w = float(weight)
        if r <= 1:
            return w
        return round(w * (1 + r/30), 2)
    except Exception:
        return None

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

# ------------------ WORKOUTS ------------------
WORKOUTS = {
    "Upper (Strength)": [
        {"Exercise": "DB Bench Press", "Range": "6–8", "Info": "Main chest press. Double progression."},
        {"Exercise": "Wide Grip Pull-Ups", "Range": "6–8 (or rep-goal)", "Info": "Lats/biceps. Add load post-goal."},
        {"Exercise": "DB Overhead Press", "Range": "6–8", "Info": "Delts/triceps. Strict form."},
        {"Exercise": "Barbell Row", "Range": "~8", "Info": "Back thickness. Full range."},
        {"Exercise": "Weighted Dips", "Range": "8–10", "Info": "Chest/triceps. Shoulder-friendly depth."},
        {"Exercise": "EZ Bar Curl", "Range": "10–12", "Info": "Biceps isolation. Squeeze top."},
        {"Exercise": "Lateral Raise", "Range": "15–20", "Info": "Delts. Light, clean reps."},
    ],
    "Upper (Volume)": [
        {"Exercise": "Incline DB Press", "Range": "8–10", "Info": "Upper chest. Controlled tempo."},
        {"Exercise": "Neutral Grip Pull-ups", "Range": "AMRAP/rep-goal", "Info": "Back/biceps. Add load post-goal."},
        {"Exercise": "Arnold Press", "Range": "10–12", "Info": "Delts focus. Smooth rotation."},
        {"Exercise": "Skullcrusher", "Range": "12–15", "Info": "Elbows steady."},
        {"Exercise": "Hammer Curls", "Range": "12–15", "Info": "No swinging."},
        {"Exercise": "Upright Row", "Range": "10–12", "Info": "To mid-chest only."},
        {"Exercise": "Lateral Raise", "Range": "15–20", "Info": "Pump work, clean form."},
    ],
    "Lower": [
        {"Exercise": "Bulgarian Split Squat", "Range": "6–8/leg", "Info": "Quads/glutes. Balance + control."},
        {"Exercise": "Romanian Deadlift", "Range": "~8", "Info": "Hamstrings/glutes. Hinge tight."},
        {"Exercise": "Hip Thrusts", "Range": "10–12", "Info": "Glute focus. Full lockout."},
        {"Exercise": "Calf Raises", "Range": "12–15", "Info": "Pause at stretch."},
        {"Exercise": "Hanging Leg Raises", "Range": "8-10", "Info": "Slow eccentric."},
    ],
}

# ------------------ STATE ------------------
if "picked" not in st.session_state:
    st.session_state.picked = None
if "session_start" not in st.session_state:
    st.session_state.session_start = None
if "sets_entered" not in st.session_state:
    st.session_state.sets_entered = {}
if "weights" not in st.session_state:
    st.session_state.weights = {}
if "open_cards" not in st.session_state:
    st.session_state.open_cards = {}

# ------------------ STYLES ------------------
st.markdown(
    """
    <style>
      .header-row {display:flex; gap:8px; align-items:center; justify-content:space-between;}
      .hdr-left {display:flex; gap:10px; align-items:baseline;}
      .hdr-title {font-weight:600;}
      .hdr-meta {opacity:0.75; font-size:0.9em;}
      .footer-bar {position:fixed; left:0; right:0; bottom:0; padding:10px 16px; backdrop-filter: blur(8px); background: rgba(255,255,255,0.9); border-top:1px solid rgba(0,0,0,0.08); z-index:9999;}
      .footer-inner {display:flex; gap:10px; align-items:center; justify-content:space-between; max-width: 900px; margin: 0 auto;}
      .footer-title {font-weight:600; opacity:0.8}
      .pill {display:inline-block; padding:2px 8px; border-radius:999px; background:rgba(0,0,0,0.06); font-size:12px; margin-left:6px}
      .info-chip {display:inline-block; padding:2px 6px; border-radius:8px; background:rgba(0,0,0,0.05); font-size:12px; margin-left:6px}
      /* pill radio styling */
      div[role="radiogroup"] > label {border:1px solid rgba(0,0,0,0.12); padding:8px 14px; border-radius:999px; margin-right:8px; margin-bottom:8px; background:rgba(0,0,0,0.03);} 
      div[role="radiogroup"] > label:hover {background: rgba(0,0,0,0.06)}
      div[role="radiogroup"] input:checked + div {font-weight:600}
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------ HEADER ------------------
st.title("SpeedyTraining")

# Tabs: Workouts, Progression Guide, Warm-up
work_tab, rules_tab, warm_tab = st.tabs(["🏋️ Workouts", "📈 Progression Guide", "🔥 Warm-up"])

with rules_tab:
    st.subheader("How to Progress in Weights")
    st.markdown(
        "- **Double progression rule:** Stay in the rep range. When you hit the top end on all sets, increase the weight next session.\n"
        "- **Upper (Strength):** Add ~2.5 kg once you reach top reps in all sets.\n"
        "- **Upper (Volume):** Push for more reps first; add weight when you comfortably exceed the top of the range.\n"
        "- **Lower:** Focus on form. Add 2.5–5 kg cautiously when rep targets are hit with clean execution.\n"
        "- **Isolation lifts:** Prefer adding reps before weight."
    )

with warm_tab:
    st.subheader("Warm-up Routine")
    st.markdown(
        "Keep it lowkey and efficient:\n"
        "- 3–5 min cardio bike\n"
        "- Band pull-aparts ×15\n"
        "- Shoulder dislocates ×10\n"
        "- Bodyweight squats ×15\n"
        "- Push-ups ×10–15\n"
        "- Light warm-up sets of your first lift (≈40–60–80% of working weight)"
    )

with work_tab:
    # Aesthetic pill radio selector
    options = ["Upper (Strength)", "Upper (Volume)", "Lower"]
    default_idx = options.index(st.session_state.picked) if st.session_state.picked in options else 0
    choice = st.radio("Choose workout", options, index=default_idx, horizontal=True)
    st.session_state.picked = choice

picked = st.session_state.picked
logs = load_logs()

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
        last_avg_reps = int(round(sum(last["reps"])/max(1,last_sets))) if last_sets else 0
        cur_w = st.session_state.weights.get(name, last_w)

        # Header row
        st.markdown(
            f"<div class='header-row'><div class='hdr-left'><span class='hdr-title'>{name}</span><span class='hdr-meta'>• {cur_w:g} kg • Last: {last_sets}×{last_avg_reps if last_avg_reps else '-'} </span></div></div>",
            unsafe_allow_html=True,
        )
        info = ex.get("Info", "")
        if info:
            st.markdown(f"<span class='info-chip'>{info}</span>", unsafe_allow_html=True)

        is_open = st.session_state.open_cards.get(name, False)
        btn_label = "⬇️ Log sets" if not is_open else "⬆️ Hide log"
        if st.button(btn_label, key=f"toggle_{name}"):
            st.session_state.open_cards[name] = not is_open
            st.rerun()

        if st.session_state.open_cards.get(name, False):
            with st.container():
                with st.expander("⚖️ Adjust weight", expanded=False):
                    cur_w = st.number_input("Weight (kg)", value=float(cur_w), min_value=0.0, step=0.5, key=f"w_{name}")
                    st.session_state.weights[name] = cur_w

                # Prefill/Reset
                cA, cB = st.columns([1,1])
                if cA.button("📋 Prefill last", key=f"prefill_{name}"):
                    st.session_state.sets_entered[name] = last["reps"].copy() if last and last["reps"] else [0]
                    st.rerun()
                if cB.button("♻️ Reset", key=f"reset_{name}"):
                    st.session_state.sets_entered[name] = [0]
                    st.rerun()

                if name not in st.session_state.sets_entered:
                    st.session_state.sets_entered[name] = [0]

                reps_list = st.session_state.sets_entered[name]
                # ---- FORM to avoid reruns on each keypress ----
                with st.form(f"form_{name}", clear_on_submit=False):
                    for i in range(len(reps_list)):
                        colL, colR = st.columns([2,3])
                        colL.markdown(f"Set {i+1}")
                        rep_key = f"reps_{name}_{i+1}"
                        val = colR.number_input("reps", min_value=0, max_value=50, value=int(reps_list[i]), step=1, key=rep_key, label_visibility="collapsed")
                    c1, c2, c3 = st.columns([1,1,2])
                    add_clicked = c1.form_submit_button("+ Add Set")
                    copy_clicked = c2.form_submit_button("Copy last set → all")
                    save_changes = c3.form_submit_button("Apply changes")

                # After form submit: sync inputs back to sets_entered
                updated = []
                for i in range(len(reps_list)):
                    rep_key = f"reps_{name}_{i+1}"
                    updated.append(int(st.session_state.get(rep_key, reps_list[i])))
                st.session_state.sets_entered[name] = updated

                if add_clicked:
                    st.session_state.sets_entered[name].append(0)
                    st.rerun()
                if copy_clicked:
                    rl = st.session_state.sets_entered[name]
                    if rl:
                        last_val = int(rl[-1])
                        st.session_state.sets_entered[name] = [last_val for _ in rl]
                    st.rerun()

                # Collect rows for save
                for idx, reps in enumerate(st.session_state.sets_entered[name], start=1):
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

    # Sticky footer UI + real save button
    st.markdown(
        f"<div class='footer-bar'><div class='footer-inner'><div class='footer-title'>Session: {picked} <span class='pill'>{datetime.now().strftime('%H:%M')}</span></div></div></div>",
        unsafe_allow_html=True,
    )
    save_click = st.button("✅ Finish & Save", key="footer_save")
    if save_click:
        end_ts = datetime.now().isoformat(timespec="seconds")
        if new_rows:
            for r in new_rows:
                r["session_end"] = end_ts
            df_new = save_rows(new_rows)
            st.success(f"Saved {len(df_new)} sets to {LOG_PATH.name}.")
            by_ex = (
                df_new.groupby("exercise_name")
                .agg(sets=("set_idx","count"), top_weight=("weight_kg","max"), total_reps=("reps","sum"), volume=("volume_kg","sum"))
                .reset_index()
            )
            st.markdown("#### Session Summary")
            st.dataframe(by_ex, hide_index=True, use_container_width=True)
            st.session_state.session_start = None
            st.session_state.sets_entered = {}
            st.session_state.weights = {}
        else:
            st.warning("No reps entered — nothing saved.")
else:
    st.info("Pick a workout to start: Upper (Strength) • Upper (Volume) • Lower")