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

WORKOUTS = {
    "Upper A": [
        {"Exercise": "Bench Press (BB/DB)", "Range": "6–8", "Info": "Main chest press. Focus on double progression."},
        {"Exercise": "Pull-Ups (neutral/wide)", "Range": "6–8 (or rep-goal)", "Info": "Back & biceps. Add load when rep goal reached."},
        {"Exercise": "Overhead Press (DB/bands)", "Range": "6–8", "Info": "Delts & triceps. Strict form."},
        {"Exercise": "Row (BB or 1-Arm DB)", "Range": "~8", "Info": "Back thickness. Full range."},
        {"Exercise": "Dips (weighted if able)", "Range": "8–10", "Info": "Chest & triceps. Keep shoulders safe."},
        {"Exercise": "EZ Bar Curl", "Range": "10–12", "Info": "Biceps isolation. Squeeze at top."},
        {"Exercise": "Lateral Raise", "Range": "15–20", "Info": "Shoulders. Controlled, light weight."},
    ],
}

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
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Compact Workout Logger")
st.caption("Minimal scrolling • Accordion cards • Sticky Save")

if st.button("Upper A", use_container_width=True):
    st.session_state.picked = "Upper A"

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
        last_avg_reps = int(round(sum(last["reps"])/last_sets)) if last_sets else 0
        cur_w = st.session_state.weights.get(name, last_w)

        header_html = f"<div class='header-row'><div class='hdr-left'><span class='hdr-title'>{name}</span><span class='hdr-meta'>• {cur_w:g} kg • Last: {last_sets}×{last_avg_reps if last_avg_reps else '-'} </span></div></div>"
        st.markdown(header_html, unsafe_allow_html=True)

        info = ex.get("Info", "")
        if info:
            st.markdown(f"<span class='info-chip'>{info}</span>", unsafe_allow_html=True)

        is_open = st.session_state.open_cards.get(name, False)
        btn_label = "📝 Log sets" if not is_open else "⬆️ Hide log"
        if st.button(btn_label, key=f"toggle_{name}"):
            st.session_state.open_cards[name] = not is_open
            st.rerun()

        if st.session_state.open_cards.get(name, False):
            with st.container():
                with st.expander("⚖️ Adjust weight", expanded=False):
                    cur_w = st.number_input("Weight (kg)", value=float(cur_w), min_value=0.0, step=0.5, key=f"w_{name}")
                    st.session_state.weights[name] = cur_w

                cA, cB = st.columns([1,1])
                if cA.button("📋 Prefill last", key=f"prefill_{name}"):
                    if last and last["reps"]:
                        st.session_state.sets_entered[name] = last["reps"].copy()
                    else:
                        st.session_state.sets_entered[name] = [0]
                    st.rerun()
                if cB.button("♻️ Reset", key=f"reset_{name}"):
                    st.session_state.sets_entered[name] = [0]
                    st.rerun()

                if name not in st.session_state.sets_entered:
                    st.session_state.sets_entered[name] = [0]
                reps_list = st.session_state.sets_entered[name]

                for i in range(len(reps_list)):
                    cols_row = st.columns([2,3])
                    cols_row[0].markdown(f"Set {i+1}")
                    rep_key = f"reps_{name}_{i+1}"
                    reps_val = cols_row[1].number_input("reps", min_value=0, max_value=50, value=int(reps_list[i]), step=1, key=rep_key, label_visibility="collapsed")
                    st.session_state.sets_entered[name][i] = int(reps_val)

                c1, c2 = st.columns([1,1])
                if c1.button("+ Add Set", key=f"add_{name}"):
                    reps_list.append(0)
                    st.session_state.sets_entered[name] = reps_list
                    st.rerun()
                if c2.button("Copy last set → all", key=f"copy_{name}"):
                    if reps_list:
                        last_val = int(reps_list[-1])
                        st.session_state.sets_entered[name] = [last_val for _ in reps_list]
                    st.rerun()

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

    st.markdown("<div class='footer-bar'><div class='footer-inner'>" 
                f"<div class='footer-title'>Session: {picked} <span class='pill'>{datetime.now().strftime('%H:%M')}</span></div>"
                "</div></div>", unsafe_allow_html=True)

    save_click = st.button("✅ Finish & Save", key="footer_save")
    if save_click:
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
            st.session_state.session_start = None
            st.session_state.sets_entered = {}
            st.session_state.weights = {}
        else:
            st.warning("No reps entered — nothing saved.")
else:
    st.info("Pick a workout to start: Upper A • Lower • Upper B")