import socket
import threading
import time
import os


class Node:
    def __init__(self):
        self.id = os.getenv("NODE_ID", "Unknown")  # Get node ID from env variable
        self.api_address = self.get_local_ip()  # Get the local IP
        self.nodes = []  # List of all nodes in the network

    def get_local_ip(self):
        """Get the local IP address inside the Docker container."""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 80))  # Connect to an external address to fetch local IP
            local_ip = s.getsockname()[0]
        except Exception:
            local_ip = '127.0.0.1'
        finally:
            s.close()
        return local_ip

    def broadcast_join_message(self, multicast_group=("239.255.0.1", 9999)):
        """Broadcast a join message to the multicast group."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)  # TTL for multicast

        message = f"Node {self.id} has joined.".encode('utf-8')
        sock.sendto(message, multicast_group)
        print(f"[BROADCAST] Node {self.id} has joined")
        sock.close()

    def listen_for_new_nodes(self, multicast_group=("239.255.0.1", 9999)):
        """Listen for new nodes joining via multicast."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', multicast_group[1]))  # Bind to all interfaces

        # Join the multicast group
        group = socket.inet_aton(multicast_group[0])
        mreq = group + socket.inet_aton(self.get_local_ip())
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        print(f"[LISTENING] Node {self.id} is listening for new nodes...")

        while True:
            print("Listning...")
            data, addr = sock.recvfrom(1024)
            new_node_info = data.decode('utf-8')
            print("Listning...")
            if new_node_info.startswith("Node"):
                node_id = new_node_info.split()[1]
                sender_ip = addr[0]
                new_node_tuple = (node_id, sender_ip)
                if new_node_tuple not in self.nodes:
                    self.nodes.append(new_node_tuple)
                    print(f"[NEW NODE] {new_node_tuple}")


def listen_in_background(n):
    """Run the listener in a background thread."""
    listen_thread = threading.Thread(target=n.listen_for_new_nodes, daemon=True)
    listen_thread.start()


if __name__ == "__main__":
    node = Node()
    print("Staring")
    node.broadcast_join_message()
    print("Broad Cast Complete")
    listen_in_background(node)

    # Simulate other tasks running
    while True:
        pass

