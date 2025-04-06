import streamlit as st
import redis
import pandas as pd
import time
import re
from helpers import LogLevels
import subprocess
import sys
import os

# Redis clients
redis_client = redis.StrictRedis(host="localhost", port=4380, db=0, decode_responses=True)
redis_client_proposal = redis.StrictRedis(host="localhost", port=4379, db=0, decode_responses=True)

# Init node state
if "next_node_id" not in st.session_state:
    st.session_state.next_node_id = 1

if "node_processes" not in st.session_state:
    st.session_state.node_processes = []

# -- Top Buttons --
col1, col2 = st.columns(2)

with col1:
    if st.button("🧹 Clear Redis DBs"):
        redis_client.flushdb()
        redis_client_proposal.flushdb()
        st.session_state.next_node_id = 1
        st.success("Redis databases cleared.")

with col2:
    if st.button("🚀 Start New Node"):
        node_id = st.session_state.next_node_id

        # Get the Python executable from the current environment
        python_exec = sys.executable

        # Build the command
        command = [python_exec, "main.py", "single_run", str(node_id)]

        # Run it in a separate subprocess (non-blocking)
        subprocess.Popen(command, cwd=os.getcwd())

        st.success(f"Node {node_id} started as a subprocess using main.py.")
        st.session_state.next_node_id += 1

# -- Helpers --

def parse_log_entry(log_entry):
    match = re.match(r"\[(\d+)] \[(.*?)\] \[(\d+)] (.*)", log_entry)
    if match:
        node_id, timestamp, log_level, message = match.groups()
        return {
            "Node ID": node_id,
            "Time": timestamp,
            "Log Level": LogLevels(int(log_level)).name,
            "Message": message,
        }
    return None

def read_logs_from_redis():
    keys = sorted(redis_client.keys("*-timestamp"))
    logs = [parse_log_entry(redis_client.get(key)) for key in keys]
    logs = [log for log in logs if log]
    df = pd.DataFrame(logs) if logs else pd.DataFrame(columns=["Node ID", "Time", "Log Level", "Message"])
    if not df.empty:
        df["Node ID"] = df["Node ID"].astype(int)
    return df

def get_node_activity():
    keys = redis_client.keys("*-node")
    current_time = time.time()
    nodes = []
    for key in keys:
        node_id = key.split("-node")[0]
        val = redis_client.get(key)
        if val:
            role, ts = val.split("-")
            ts = float(ts)
            status = "🟢 Active" if current_time - ts <= 6 else "🔴 Inactive"
            nodes.append({"Node ID": node_id, "Role": role, "Status": status})
    df = pd.DataFrame(nodes) if nodes else pd.DataFrame(columns=["Node ID", "Role", "Status"])
    if not df.empty:
        df["Node ID"] = df["Node ID"].astype(int)
    return df.sort_values(by="Node ID")

def get_current_page_and_line():
    val = redis_client_proposal.get("last_success_proposal")
    if val and len(val) == 7:
        return f"📄 Current Page: {val[:4]}, Line: {val[4:]}"
    return "📄 Current Page: N/A, Line: N/A"

def get_letter_word_counts():
    letters = [chr(i) for i in range(65, 91)]
    data = [{"Letter": l, "Word Count": int(redis_client_proposal.get(l) or 0)} for l in letters]
    return pd.DataFrame(data)

def get_letter_word_lists():
    letters = [chr(i) for i in range(65, 91)]
    data = []
    for l in letters:
        raw = redis_client_proposal.get(f"{l}_")
        words = raw.split(",") if raw else []
        data.append({"Letter": l, "Words": ", ".join(words)})
    return pd.DataFrame(data)

# -- Page Header --

logs_df = read_logs_from_redis()
error_count = (logs_df["Log Level"] == LogLevels.ERROR.name).sum()
st.markdown(
    f"<h3>❗ Errors: {error_count} | {get_current_page_and_line()}</h3>",
    unsafe_allow_html=True
)

# -- Main Data Display --

col1, col2 = st.columns(2)
with col1:
    st.subheader("Letter Word Counts")
    st.dataframe(get_letter_word_counts(), height=400, use_container_width=True)

with col2:
    st.subheader("Node Activity")
    st.dataframe(get_node_activity(), height=400, use_container_width=True)

st.subheader("Words by Letter")
st.dataframe(get_letter_word_lists(), height=400, use_container_width=True)

# -- Logs Filter & View --

unique_nodes = sorted(logs_df["Node ID"].unique()) if not logs_df.empty else []
levels = list(LogLevels.__members__.keys())

selected_node = st.selectbox("Filter by Node", ["All"] + unique_nodes)
selected_level = st.selectbox("Filter by Log Level", ["All"] + levels)

if selected_node != "All":
    logs_df = logs_df[logs_df["Node ID"] == selected_node]
if selected_level != "All":
    logs_df = logs_df[logs_df["Log Level"] == selected_level]

def color_logs(row):
    bg = {
        "INFORMATION": "#DFF0D8",
        "WARNING": "#FCF8E3",
        "ERROR": "#F2DEDE",
        "DEBUG": "#D9EDF7",
    }.get(row["Log Level"], "#FFFFFF")
    color = {
        "INFORMATION": "#3C763D",
        "WARNING": "#8A6D3B",
        "ERROR": "#A94442",
        "DEBUG": "#31708F",
    }.get(row["Log Level"], "#000000")
    return [f"background-color: {bg}; color: {color}"] * len(row)

st.subheader("Logs")
st.dataframe(logs_df.style.apply(color_logs, axis=1), height=500, use_container_width=True)

# -- Refresh Control --

if st.checkbox("Auto Refresh", value=True):
    time.sleep(2)
    st.rerun()
else:
    if st.button("🔄 Manual Refresh"):
        st.rerun()
