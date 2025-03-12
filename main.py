import socket
import threading
import time
import os
import multiprocessing
import sys


MULTICAST_GROUP = "224.1.1.1"
BASE_PORT = 5000  # Base port number for calculation
TTL = 2
BUFFER_SIZE = 1024


class Node:
    def __init__(self, id):
        self.id = id
        self.port = BASE_PORT
        self.nodes = {}
        self.leader_id = None

    def _create_socket(self, is_receiver=False):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        if not is_receiver:
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, TTL)

        return sock



    def broadcast_join_message(self):
        sock = self._create_socket(is_receiver=False)
        message = b"Hello, Docker Multicast!"
        sock.sendto(message, (MULTICAST_GROUP, self.port))  # Use the node's port
        # print(f"Sent message from node {self.id}: {message.decode()}")
        sock.close()

    def receive_messages(self):
        sock = self._create_socket(is_receiver=True)
        sock.bind(("", self.port))  # Bind to the node's fixed port
        mreq = socket.inet_aton(MULTICAST_GROUP) + socket.inet_aton("0.0.0.0")
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        print(f"Receiver started for node {self.id}, listening on port {self.port}...")

        try:
            while True:
                data, addr = sock.recvfrom(BUFFER_SIZE)
                payload = data.decode()
                # print(f"Received from {addr}: {payload}")
                headers =  payload.split("-")

                if headers[1] == "Heartbeat":
                    n_id = int(headers[0])
                    self.nodes[n_id] = time.time()
        except KeyboardInterrupt:
            print(f"Receiver stopped for node {self.id}.")
        finally:
            sock.close()

    def send_heartbeat(self):
        while True:
            heartbeat_message = f"{self.id}-Heartbeat-".encode()
            sock = self._create_socket(is_receiver=False)
            sock.sendto(heartbeat_message, (MULTICAST_GROUP, self.port))  # Use the node's port
            # print(f"Sent heartbeat from node {self.id}")
            sock.close()
            time.sleep(10)  # Send heartbeat every 10 seconds

    def check_inactive_nodes(self, timeout=30):
        while True:
            time.sleep(timeout / 2)  # Check more frequently than the timeout
            current_time = time.time()

            # Find inactive nodes
            inactive_nodes = [
                n_id for n_id, last_time in self.nodes.items()
                if current_time - last_time > timeout
            ]

            # Remove inactive nodes
            for n_id in inactive_nodes:
                self.nodes.pop(n_id, None)  # Use pop to avoid KeyError
                print(f"Node {n_id} removed due to inactivity")





def start_node(n_id):
    node = Node(n_id)

    receiver_thread = threading.Thread(target=node.receive_messages, daemon=True)
    receiver_thread.start()

    heartbeat_thread = threading.Thread(target=node.send_heartbeat, daemon=True)
    heartbeat_thread.start()

    cleanup_thread = threading.Thread(target=node.check_inactive_nodes, daemon=True)
    cleanup_thread.start()

    time.sleep(5)
    try:
        while True:
            time.sleep(10)
            print(f"From Node {node.id}  {node.nodes}")

    except KeyboardInterrupt:
        print(f"Stopping node {n_id}...")


def run_node(n_id):
    start_node(n_id)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "single_run":
        if len(sys.argv) != 3:
            print("Usage: script.py single_run <node_id>")
            sys.exit(1)
        node_id = int(sys.argv[2])
        run_node(node_id)
    else:
        num_nodes = 20
        processes = []
        for node_id in range(1, num_nodes + 1):
            process = multiprocessing.Process(target=run_node, args=(node_id,))
            process.start()
            processes.append(process)

        for process in processes:
            process.join()


