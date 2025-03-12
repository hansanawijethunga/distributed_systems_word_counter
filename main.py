import socket
import threading
import time
import os
import multiprocessing

MULTICAST_GROUP = "224.1.1.1"
BASE_PORT = 5000  # Base port number for calculation
TTL = 2
BUFFER_SIZE = 1024


class Node:
    def __init__(self, id):
        self.id = id
        self.port = BASE_PORT
        self.nodes = []
        self.leader_id = None

    def _create_socket(self, is_receiver=False):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        if not is_receiver:
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, TTL)

        return sock

    def add_node(self, value):
        """Adds an integer to the array if it does not already exist."""
        if value not in self.nodes:
            self.nodes.append(value)

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
                print(f"Received from {addr}: {payload}")
                headers =  payload.split("-")

                if headers[1] == "Heartbeat":
                    self.add_node(int(headers[0]))




        except KeyboardInterrupt:
            print(f"Receiver stopped for node {self.id}.")
        finally:
            sock.close()

    def send_heartbeat(self):
        while True:
            heartbeat_message = f"{self.id}-Heartbeat-".encode()
            sock = self._create_socket(is_receiver=False)
            sock.sendto(heartbeat_message, (MULTICAST_GROUP, self.port))  # Use the node's port
            print(f"Sent heartbeat from node {self.id}")
            sock.close()
            time.sleep(10)  # Send heartbeat every 10 seconds


def start_node(n_id):
    node = Node(n_id)

    receiver_thread = threading.Thread(target=node.receive_messages, daemon=True)
    receiver_thread.start()

    heartbeat_thread = threading.Thread(target=node.send_heartbeat, daemon=True)
    heartbeat_thread.start()

    time.sleep(5)

    # node.broadcast_join_message()

    try:
        while True:
            time.sleep(10)
            print(f"From Node {node.id}  {node.nodes}")

    except KeyboardInterrupt:
        print(f"Stopping node {n_id}...")


def run_node(n_id):
    start_node(n_id)


if __name__ == "__main__":
    # Start two processes for two nodes
    num_nodes = 20

    for node_id in range(num_nodes):
        process = multiprocessing.Process(target=run_node, args=(node_id+1,))
        process.start()

    # process1.join()
    # process2.join()
