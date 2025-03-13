import socket
import threading
import time
import multiprocessing
import sys
from msilib.schema import ProgId

import grpc
import concurrent.futures

# gRPC Proto Definitions (Assume pre-generated from .proto file)
import node_pb2
import node_pb2_grpc

MULTICAST_GROUP = "224.1.1.1"
BASE_PORT = 5000  # Base port number for calculation
TTL = 2
BUFFER_SIZE = 1024
GRPC_PORT_OFFSET = 5050  # Offset for gRPC ports


def _create_socket(is_receiver=False):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    if not is_receiver:
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, TTL)

    return sock


class LeaderElectionService(node_pb2_grpc.LeaderElectionServicer):
    def __init__(self, node):
        self.node = node

    def Challenge(self, request, context):
        print("Request Found")
        return node_pb2.ChallengeResponse(acknowledged=True)



class Node:
    def __init__(self, id):
        self.id = id
        self.port = BASE_PORT
        self.grpc_port = GRPC_PORT_OFFSET + id
        self.nodes = {}
        self.leader_id = tuple()
        self.isLeader = False

    def start_grpc_server(self):
        """Starts the gRPC server for handling leader election challenges."""
        server = grpc.server(concurrent.futures.ThreadPoolExecutor(max_workers=10))
        node_pb2_grpc.add_LeaderElectionServicer_to_server(LeaderElectionService(self), server)
        server.add_insecure_port(f"[::]:{self.grpc_port}")
        server.start()
        print(f"Node {self.id}: gRPC server started on port {self.grpc_port}")
        server.wait_for_termination()

    def challenge_higher_nodes(self):
        """Sends a challenge request to higher nodes and waits for acknowledgment."""
        response = False
        for higher_id in sorted(self.nodes.keys(), reverse=True):
            if higher_id > self.id:
                try:
                    print(f"Node {self.id} chalanging node {higher_id}")
                    channel = grpc.insecure_channel(f"localhost:{GRPC_PORT_OFFSET + higher_id}")
                    stub = node_pb2_grpc.LeaderElectionStub(channel)
                    challenge_request = node_pb2.ChallengeRequest(node_id=self.id)
                    response = stub.Challenge(challenge_request)
                    if response.ack:
                        print(f"Node {self.id}: Acknowledgment received from {higher_id}")
                        response = response or True
                except Exception as e:
                    print(f"Node {self.id}: Failed to communicate with {higher_id} ({e})")

        return response

    def rpcCheck(self):
        print(f"node {self.id} Sending Request to {GRPC_PORT_OFFSET + 2}")
        channel = grpc.insecure_channel(f"localhost:{GRPC_PORT_OFFSET + 2}")
        stub = node_pb2_grpc.LeaderElectionStub(channel)
        challenge_request = node_pb2.ChallengeRequest(node_id=self.id)
        response = stub.Challenge(challenge_request)
        print(response)

    def announce_leadership(self):
        """Broadcasts that this node is the leader using UDP multicast."""
        sock = _create_socket(is_receiver=False)
        message = f"{self.id}-I am the leader".encode()
        sock.sendto(message, (MULTICAST_GROUP, self.port))
        sock.close()
        self.isLeader =True
        self.leader_id = (self.id,time.time())
        print(f"Node {self.id}: Broadcasted as leader")

    def receive_messages(self):
        """Listens for multicast messages from other nodes."""
        sock = _create_socket(is_receiver=True)
        sock.bind(("", self.port))
        mreq = socket.inet_aton(MULTICAST_GROUP) + socket.inet_aton("0.0.0.0")
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        print(f"Node {self.id}: Listening for multicast messages on port {self.port}...")

        try:
            while True:
                data, addr = sock.recvfrom(BUFFER_SIZE)
                payload = data.decode()
                headers = payload.split("-")
                n_id = int(headers[0])
                print(addr)
                if headers[1] == "Heartbeat" and n_id != self.id:
                    print(f"Node {self.id}:Receive Heartbeat from {n_id}")
                    self.nodes[n_id] = time.time()
                elif headers[1] == "LeaderHeartbeat" and n_id != self.id:
                    print(f"Node {self.id}:Receive Leader Heartbeat from {n_id}")
                    if not self.leader_id or self.leader_id[0] != n_id :
                        self.set_leader(n_id)
                elif headers[1] == "I am the leader" and n_id != self.id:
                    self.set_leader(n_id)

        except KeyboardInterrupt:
            print(f"Node {self.id}: Receiver stopped.")
        finally:
            sock.close()

    def set_leader(self,n_id):
        if self.isLeader:
            if self.id < n_id:
                self.leader_id = (n_id, time.time())
                print(f"Node {self.id}: Recognized leader {n_id}")
            else:
                print(f"Node {self.id}: Reject the Leadership offer form {n_id}")
        else:
            self.leader_id = (n_id, time.time())
            print(f"Node {self.id}: Recognized leader {n_id}")



    def send_heartbeat(self):
        """Sends a heartbeat message periodically."""
        while True:
            heartbeat_message = f"{self.id}-LeaderHeartbeat-".encode() if self.isLeader else f"{self.id}-Heartbeat-".encode()
            sock = _create_socket(is_receiver=False)
            sock.sendto(heartbeat_message, (MULTICAST_GROUP, self.port))
            sock.close()
            time.sleep(10)

    def check_inactive_nodes(self, timeout=30):
        """Checks for inactive nodes and triggers re-election if necessary."""
        while True:
            time.sleep(timeout / 2)
            current_time = time.time()

            inactive_nodes = [n_id for n_id, last_time in self.nodes.items() if current_time - last_time > timeout]
            for n_id in inactive_nodes:
                self.nodes.pop(n_id, None)
                print(f"Node {self.id}: Removed inactive node {n_id}")

            print(f"Leader Id {self.leader_id}")
            if self.leader_id :
                print(self.leader_id[1])
            if self.leader_id and current_time - self.leader_id[1] > timeout:
                self.leader_id = ()

    def start_election(self):
        """Initiates the leader election process."""
        print(f"Node {self.id}: Initiating leader election...")
        acknowledged = self.challenge_higher_nodes()

        if not acknowledged and not self.leader_id:
            self.announce_leadership()


def start_node(n_id):
    node = Node(n_id)


    # receiver_thread = threading.Thread(target=node.receive_messages, daemon=True)
    # receiver_thread.start()
    #
    # heartbeat_thread = threading.Thread(target=node.send_heartbeat, daemon=True)
    # heartbeat_thread.start()
    #
    # cleanup_thread = threading.Thread(target=node.check_inactive_nodes, daemon=True)
    # cleanup_thread.start()
    #
    grpc_thread = threading.Thread(target=node.start_grpc_server, daemon=True)
    grpc_thread.start()

    time.sleep(3)
    if node.id == 1 :
        node.rpcCheck()
    #
    # try:
    #     while True:
    #         if not node.leader_id :
    #             print(f"Node {node.id}: No leader found, waiting...")
    #             time.sleep(30)
    #             if not node.leader_id :
    #                 node.start_election()
    #
    #         time.sleep(5)
    #         print(f"Node {node.id}: Active nodes: {node.nodes}")
    #         print(f"Leader {node.leader_id}")
    #
    # except KeyboardInterrupt:
    #     print(f"Node {n_id}: Stopping...")


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
        num_nodes = 2
        processes = []
        for node_id in range(1, num_nodes + 1):
            process = multiprocessing.Process(target=run_node, args=(node_id,))
            process.start()
            processes.append(process)

        for process in processes:
            process.join()
