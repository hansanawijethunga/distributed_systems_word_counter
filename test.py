import psutil
import os
import signal

def kill_udp_process_on_port(n_id: int):
    """Kills the process listening on the given TCP port."""
    port = 60000 + n_id
    for conn in psutil.net_connections(kind='tcp'):
        if conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
            pid = conn.pid
            if pid:
                try:
                    print(f"Killing TCP process {pid} on port {port}...")
                    os.kill(pid, signal.SIGTERM)  # use SIGKILL to force
                    print("Process terminated.")
                    return True
                except Exception as e:
                    print(f"Error killing process: {e}")
                    return False
    print(f"No TCP process is listening on port {port}.")
    return False


kill_udp_process_on_port(12)
