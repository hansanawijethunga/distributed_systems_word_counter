import streamlit as st
import time
import redis
import pandas as pd
from helpers import LogLevels
import re
from datetime import datetime

# Initialize Redis (Ensure it's synchronous)
redis_client = redis.StrictRedis(host="localhost", port=4380, db=0, decode_responses=True)

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
    """Parses a log entry and extracts Node ID, Time, Log Level, and Message."""
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
    """Fetches all logs from Redis and returns a DataFrame."""
    keys = redis_client.keys("*-timestamp")  # Get all timestamped log keys
    keys.sort()
    logs = [parse_log_entry(redis_client.get(key)) for key in keys]
    logs = [log for log in logs if log]  # Remove None values
    return pd.DataFrame(logs) if logs else pd.DataFrame(columns=["Node ID", "Time", "Log Level", "Message"])


def get_node_activity():
    """Fetches node activity data from Redis."""
    keys = redis_client.keys("*-node")
    node_status = []
    current_time = time.time()

    for key in keys:
        print(key)
        node_id = key.split("-node")[0]  # Extract Node ID
        value = redis_client.get(key)
        if value:
            value = str(value)  # Ensure it's a string
            print(value)
            role, timestamp = value.split("-")
            timestamp = float(timestamp)
            is_active = (current_time - timestamp) <= 6
            node_status.append({
                "Node ID": node_id,
                "Role": role,
                "Status": "🟢 Active" if is_active else "🔴 Inactive"
            })

    return pd.DataFrame(node_status) if node_status else pd.DataFrame(columns=["Node ID", "Role", "Status"])


# UI for logs
logs_df = read_logs_from_redis()

total_nodes = logs_df["Node ID"].unique().tolist() if not logs_df.empty else []
total_log_levels = list(LogLevels.__members__.keys())

selected_node = st.selectbox("Filter by Node ID", ["All"] + total_nodes)
selected_log_level = st.selectbox("Filter by Log Level", ["All"] + total_log_levels)

# Apply filters
if selected_node != "All":
    logs_df = logs_df[logs_df["Node ID"] == selected_node]

if selected_log_level != "All":
    logs_df = logs_df[logs_df["Log Level"] == selected_log_level]


# Display logs with coloring
def style_row(row):
    color = LOG_COLORS[row["Log Level"]]
    text_color = TEXT_COLORS[row["Log Level"]]
    return [
        f'background-color: {color}; color: {text_color}'  # Set both background and text color
    ] * len(row)


styled_df = logs_df.style.apply(style_row, axis=1)

st.subheader("Logs")
st.dataframe(styled_df, height=400)

# Display node activity
st.subheader("Node Activity")
st.dataframe(get_node_activity(), height=200)

time.sleep(2)
st.rerun()