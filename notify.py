import streamlit as st
import time
import redis
import pandas as pd
from helpers import LogLevels
import re
from datetime import datetime

# Initialize Redis (Ensure it's synchronous)
redis_client = redis.StrictRedis(host="localhost", port=4380, db=0, decode_responses=True)
redis_client_proposal = redis.StrictRedis(host="localhost", port=4379, db=0, decode_responses=True)

st.title("Real-time Log Viewer")

LOG_COLORS = {
    LogLevels.INFORMATION.name: "#DFF0D8",  # Light green
    LogLevels.WARNING.name: "#FCF8E3",  # Light yellow
    LogLevels.ERROR.name: "#F2DEDE",  # Light red
    LogLevels.DEBUG.name: "#D9EDF7",  # Light blue
}

TEXT_COLORS = {
    LogLevels.INFORMATION.name: "#3C763D",  # Dark green for information
    LogLevels.WARNING.name: "#8A6D3B",  # Dark yellow for warning
    LogLevels.ERROR.name: "#A94442",  # Dark red for error
    LogLevels.DEBUG.name: "#31708F",  # Dark blue for debug
}


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
    keys = redis_client.keys("*-timestamp")
    keys.sort()
    logs = [parse_log_entry(redis_client.get(key)) for key in keys]
    logs = [log for log in logs if log]
    logs_df = pd.DataFrame(logs) if logs else pd.DataFrame(columns=["Node ID", "Time", "Log Level", "Message"])

    # Sort Node IDs as integers
    if not logs_df.empty:
        logs_df["Node ID"] = logs_df["Node ID"].astype(int)
    return logs_df


def get_node_activity():
    keys = redis_client.keys("*-node")
    node_status = []
    current_time = time.time()

    for key in keys:
        node_id = key.split("-node")[0]
        value = redis_client.get(key)
        if value:
            value = str(value)
            role, timestamp = value.split("-")
            timestamp = float(timestamp)
            is_active = (current_time - timestamp) <= 6
            node_status.append({
                "Node ID": node_id,
                "Role": role,
                "Status": "🟢 Active" if is_active else "🔴 Inactive"
            })

    df = pd.DataFrame(node_status) if node_status else pd.DataFrame(columns=["Node ID", "Role", "Status"])

    # Sort Node IDs as integers
    if not df.empty:
        df["Node ID"] = df["Node ID"].astype(int)
    return df.sort_values(by=["Node ID"])


def get_current_page_and_line():
    value = redis_client_proposal.get("last_success_proposal")
    if value and len(value) == 7:
        page_number = value[:4]
        line_number = value[4:]
        return f"📄 Current Page: {page_number}, Line: {line_number}"
    return "📄 Current Page: N/A, Line: N/A"


def get_letter_word_counts():
    letters = [chr(i) for i in range(65, 91)]
    word_counts = [{"Letter": letter, "Word Count": int(redis_client_proposal.get(letter) or 0)} for letter in letters]
    return pd.DataFrame(word_counts)


logs_df = read_logs_from_redis()

error_count = (logs_df["Log Level"] == LogLevels.ERROR.name).sum()
st.markdown(
    f"<div style='display: flex; justify-content: space-between;'>"
    f"<h3>❗ Errors: {error_count} | {get_current_page_and_line()}</h3>"
    f"</div>",
    unsafe_allow_html=True,
)

col1, col2 = st.columns(2)
with col1:
    st.subheader("Letter Word Counts")
    st.dataframe(get_letter_word_counts(), height=600, use_container_width=True)
with col2:
    st.subheader("Node Activity")
    st.dataframe(get_node_activity(), height=600, use_container_width=True)

total_nodes = logs_df["Node ID"].unique().tolist() if not logs_df.empty else []
total_log_levels = list(LogLevels.__members__.keys())

selected_node = st.selectbox("Filter by Node ID", ["All"] + total_nodes)
selected_log_level = st.selectbox("Filter by Log Level", ["All"] + total_log_levels)

if selected_node != "All":
    logs_df = logs_df[logs_df["Node ID"] == selected_node]
if selected_log_level != "All":
    logs_df = logs_df[logs_df["Log Level"] == selected_log_level]


def style_row(row):
    color = LOG_COLORS[row["Log Level"]]
    text_color = TEXT_COLORS[row["Log Level"]]
    return [f'background-color: {color}; color: {text_color}'] * len(row)


styled_df = logs_df.style.apply(style_row, axis=1)

st.subheader("Logs")
st.dataframe(styled_df, height=500, use_container_width=True)

# Auto-refresh mechanism
refresh_interval = 2
if st.checkbox("Auto Refresh", value=True):
    time.sleep(refresh_interval)
    st.rerun()
else:
    if st.button("Manual Refresh"):
        st.rerun()
