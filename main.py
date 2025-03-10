import grpc
from concurrent import futures
import time
import argparse
import logging
import threading
import os

# Import the generated classes (make sure to generate these using grpcio-tools)
import node_pb2
import node_pb2_grpc

# ------------------------------------------------------------------------------
# Sidecar: encapsulates communication and logs all requests/responses.
# ------------------------------------------------------------------------------
class Sidecar:
    def __init__(self, node_address):
        self.node_address = node_address
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(self.node_address)

    def log(self, message):
        self.logger.info(message)

# ------------------------------------------------------------------------------
# Global coordinator state (for simulation purposes – in a real system this state is held by the coordinator)
# ------------------------------------------------------------------------------
coordinator_state = {
    'nodes': {},  # mapping: node_address -> role
    'letter_ranges': {}  # mapping: proposer node_address -> (start_letter, end_letter)
}

# Role constants
ROLE_COORDINATOR = 'coordinator'
ROLE_PROPOSER = 'proposer'
ROLE_ACCEPTOR = 'acceptor'
ROLE_LEARNER = 'learner'

# ------------------------------------------------------------------------------
# gRPC Servicer Implementation: defines how a node handles incoming gRPC calls.
# ------------------------------------------------------------------------------
class NodeServiceServicer(node_pb2_grpc.NodeServiceServicer):
    def __init__(self, node):
        self.node = node

    def Register(self, request, context):
        self.node.sidecar.log(f"Received registration from {request.node_address}")
        # Only the coordinator handles registration.
        if self.node.role != ROLE_COORDINATOR:
            return node_pb2.RegistrationResponse(
                assigned_role="unknown",
                message="Not the coordinator",
                all_nodes=[],
                roles={}
            )
        # Assign a role using a simple policy.
        assigned_role = assign_role_for_new_node(request.node_address)
        coordinator_state['nodes'][request.node_address] = assigned_role
        self.node.sidecar.log(f"Assigned role '{assigned_role}' to {request.node_address}")
        return node_pb2.RegistrationResponse(
            assigned_role=assigned_role,
            message="Registration successful",
            all_nodes=list(coordinator_state['nodes'].keys()),
            roles=coordinator_state['nodes']
        )

    def BroadcastRoles(self, request, context):
        self.node.sidecar.log("Broadcasting updated roles")
        self.node.update_roles(request.roles)
        return node_pb2.Ack(success=True, message="Roles updated")

    def ProcessLine(self, request, context):
        self.node.sidecar.log(f"Received document line: {request.line}")
        # Only proposer nodes process document lines.
        if self.node.role == ROLE_PROPOSER:
            self.node.process_line(request.line)
        return node_pb2.Ack(success=True, message="Line processed")

    def SendCount(self, request, context):
        self.node.sidecar.log(f"Received count from {request.node_address}")
        # Only the learner aggregates final counts.
        if self.node.role == ROLE_LEARNER:
            self.node.receive_count(request.counts)
        return node_pb2.Ack(success=True, message="Count received")

# ------------------------------------------------------------------------------
# Role Assignment Logic: the coordinator assigns roles as nodes register.
# ------------------------------------------------------------------------------
def assign_role_for_new_node(new_node_address):
    current_roles = list(coordinator_state['nodes'].values())
    if ROLE_LEARNER not in current_roles:
        return ROLE_LEARNER
    proposer_count = current_roles.count(ROLE_PROPOSER)
    acceptor_count = current_roles.count(ROLE_ACCEPTOR)
    if proposer_count <= acceptor_count:
        return ROLE_PROPOSER
    else:
        return ROLE_ACCEPTOR

# ------------------------------------------------------------------------------
# DistributedNode Class: encapsulates node behavior (coordinator, proposer, etc.).
# ------------------------------------------------------------------------------
class DistributedNode:
    def __init__(self, node_id):
        self.node_id = node_id
        # Use the container's hostname (set by Docker) for addressing; fallback to 'localhost'
        self.address = f"{os.environ.get('HOSTNAME', 'localhost')}:{5000 + int(node_id)}"
        if int(node_id) == 1:
            self.coordinator_address = None
        else:
            # Use the provided COORDINATOR_ADDRESS or default to "node1:5001"
            self.coordinator_address = os.environ.get('COORDINATOR_ADDRESS', "node1:5001")
        self.role = None
        self.all_nodes = {}
        self.letter_range = None  # For proposer nodes: (start_letter, end_letter)
        self.sidecar = Sidecar(self.address)
        self.counts = {}  # Local word counts (for proposer)
        self.final_counts = {}  # Aggregated counts (for learner)

    def start_server(self):
        # Start the gRPC server.
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        node_pb2_grpc.add_NodeServiceServicer_to_server(NodeServiceServicer(self), self.server)
        self.server.add_insecure_port(self.address)
        self.server.start()
        self.sidecar.log(f"Server started on {self.address}")
        threading.Thread(target=self.server.wait_for_termination, daemon=True).start()

    def register_with_coordinator(self):
        # If a coordinator address is available, register via gRPC.
        if self.coordinator_address:
            try:
                with grpc.insecure_channel(self.coordinator_address) as channel:
                    stub = node_pb2_grpc.NodeServiceStub(channel)
                    response = stub.Register(node_pb2.NodeInfo(node_address=self.address))
                    self.role = response.assigned_role
                    self.all_nodes = {node: role for node, role in response.roles.items()}
                    self.sidecar.log(f"Registered with coordinator at {self.coordinator_address}. My role: {self.role}")
            except Exception as e:
                self.sidecar.log(f"Registration failed: {e}. Becoming coordinator.")
                self.role = ROLE_COORDINATOR
                coordinator_state['nodes'][self.address] = ROLE_COORDINATOR

    def update_roles(self, roles):
        self.all_nodes = roles
        self.sidecar.log(f"Updated cluster roles: {roles}")

    def assign_letter_ranges(self):
        # Only the coordinator assigns letter ranges among proposer nodes.
        proposers = [node for node, role in coordinator_state['nodes'].items() if role == ROLE_PROPOSER]
        if not proposers:
            self.sidecar.log("No proposer nodes available for assignment.")
            return
        letters = [chr(c) for c in range(ord('A'), ord('Z') + 1)]
        n = len(proposers)
        size = len(letters) // n
        for i, proposer in enumerate(proposers):
            start = i * size
            end = len(letters) if i == n - 1 else (i + 1) * size
            letter_range = letters[start:end]
            coordinator_state['letter_ranges'][proposer] = (letter_range[0], letter_range[-1])
            if proposer == self.address:
                self.letter_range = (letter_range[0], letter_range[-1])
        self.sidecar.log(f"Assigned letter ranges: {coordinator_state['letter_ranges']}")
        self.broadcast_roles()

    def broadcast_roles(self):
        # Coordinator broadcasts updated roles.
        for node_address in coordinator_state['nodes']:
            if node_address == self.address:
                continue
            with grpc.insecure_channel(node_address) as channel:
                stub = node_pb2_grpc.NodeServiceStub(channel)
                stub.BroadcastRoles(node_pb2.RolesInfo(roles=coordinator_state['nodes']))
                self.sidecar.log(f"Broadcasted roles to {node_address}")

    def process_document(self, document_path):
        # Only the coordinator reads the document and multicasts lines to proposer nodes.
        self.sidecar.log(f"Reading document: {document_path}")
        with open(document_path, 'r') as f:
            for line in f:
                self.multicast_line(line.strip())
                time.sleep(0.1)  # simulate slight delay

    def multicast_line(self, line):
        # Send the document line to all proposer nodes.
        for node_address, role in self.all_nodes.items():
            if role == ROLE_PROPOSER:
                with grpc.insecure_channel(node_address) as channel:
                    stub = node_pb2_grpc.NodeServiceStub(channel)
                    stub.ProcessLine(node_pb2.LineRequest(line=line))
                    self.sidecar.log(f"Sent line to proposer {node_address}")

    def process_line(self, line):
        # Proposer nodes count words starting with letters in their assigned range.
        if not self.letter_range:
            self.sidecar.log("No letter range assigned; cannot process line.")
            return
        start_letter, end_letter = self.letter_range
        self.sidecar.log(f"Processing line for range {start_letter}-{end_letter}: {line}")
        words = line.split()
        for word in words:
            if word and start_letter <= word[0].upper() <= end_letter:
                self.counts[word[0].upper()] = self.counts.get(word[0].upper(), 0) + 1
        self.sidecar.log(f"Local counts: {self.counts}")
        # After processing, send counts to all acceptor nodes.
        for node_address, role in self.all_nodes.items():
            if role == ROLE_ACCEPTOR:
                with grpc.insecure_channel(node_address) as channel:
                    stub = node_pb2_grpc.NodeServiceStub(channel)
                    stub.SendCount(node_pb2.CountRequest(node_address=self.address, counts=self.counts))
                    self.sidecar.log(f"Sent counts to acceptor {node_address}")

    def receive_count(self, counts):
        # The learner node aggregates counts received from acceptor nodes.
        self.sidecar.log(f"Received counts: {counts}")
        for letter, count in counts.items():
            self.final_counts[letter] = self.final_counts.get(letter, 0) + count
        self.sidecar.log(f"Updated final counts: {self.final_counts}")
        print("\nFinal Word Counts by Starting Letter:")
        for letter, count in sorted(self.final_counts.items()):
            print(f"{letter}: {count}")

# ------------------------------------------------------------------------------
# Main entry point
# ------------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Distributed Node for Word Count")
    parser.add_argument('--node_id', type=int, required=False,
                        help='Unique node ID (e.g., 1, 2, 3). The node will listen on port (5000 + node_id)')
    args = parser.parse_args()

    # Allow node_id to be set via environment variable if not passed as an argument
    node_id = args.node_id if args.node_id is not None else int(os.environ.get('NODE_ID', '1'))

    node = DistributedNode(node_id)
    node.start_server()
    time.sleep(1)  # Allow time for the server to start

    # If this node has node_id 1, it becomes the coordinator.
    if node_id == 1:
        node.role = ROLE_COORDINATOR
        coordinator_state['nodes'][node.address] = ROLE_COORDINATOR
        node.sidecar.log("I am the coordinator.")
    else:
        node.register_with_coordinator()

    # If this node is the coordinator, assign letter ranges and process the document.
    if node.role == ROLE_COORDINATOR:
        time.sleep(2)  # Wait for potential node registrations
        node.assign_letter_ranges()
        # Hard-coded document path; ensure that document.txt is available in the container
        document_path = "document.txt"
        node.process_document(document_path)

    # Keep the node running.
    while True:
        time.sleep(10)

if __name__ == '__main__':
    main()
