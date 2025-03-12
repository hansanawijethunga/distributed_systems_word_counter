import socket
import threading
import time
import os

MULTICAST_GROUP = "224.1.1.1"
PORT = 5007
TTL = 2
BUFFER_SIZE = 1024


class Node:
    def __init__(self):
        self.id = os.getenv("NODE_ID", "Unknown")
        self.nodes = []

    def _create_socket(self, is_receiver=False):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        if not is_receiver:
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, TTL)

        return sock

    def broadcast_join_message(self):
        sock = self._create_socket(is_receiver=False)
        message = b"Hello, Docker Multicast!"
        sock.sendto(message, (MULTICAST_GROUP, PORT))
        print(f"Sent message: {message.decode()}")
        sock.close()

    def receive_messages(self):
        sock = self._create_socket(is_receiver=True)
        sock.bind(("", PORT))
        mreq = socket.inet_aton(MULTICAST_GROUP) + socket.inet_aton("0.0.0.0")
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        print("Receiver started, listening for messages...")

        try:
            while True:
                data, addr = sock.recvfrom(BUFFER_SIZE)
                print(f"Received from {addr}: {data.decode()}")
        except KeyboardInterrupt:
            print("Receiver stopped.")
        finally:
            sock.close()


def start_node():
    node = Node()

    receiver_thread = threading.Thread(target=node.receive_messages, daemon=True)
    receiver_thread.start()

    time.sleep(5)

    node.broadcast_join_message()

    try:
        while True:
            time.sleep(10)

    except KeyboardInterrupt:
        print("Stopping node...")


if __name__ == "__main__":
    start_node()
