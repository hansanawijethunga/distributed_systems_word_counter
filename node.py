import socket
import time
from concurrent import futures
import grpc
import node_pb2
import node_pb2_grpc
import helpers
from helpers import Roles
from leader_election_service import LeaderElectionService
import queue


MULTICAST_GROUP = "224.1.1.1"
BASE_PORT = 5000  # Base port number for calculation
BUFFER_SIZE = 1024
GRPC_PORT_OFFSET = 60000



class Node:
    def __init__(self, id):
        self.id = id
        self.port = BASE_PORT
        self.grpc_port = GRPC_PORT_OFFSET + id
        self.nodes = {}
        self.role = Roles.UNASSIGNED
        self.leader_id = tuple()
        self.isLeader = False
        self.jobs = queue.Queue()

    def start_grpc_server(self):
        """Starts the gRPC server for handling leader election challenges."""
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=50))
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
                    # print(f"Node {self.id} challenging node {higher_id} through port {GRPC_PORT_OFFSET + higher_id}")
                    channel = grpc.insecure_channel(f"localhost:{GRPC_PORT_OFFSET + higher_id}")
                    stub = node_pb2_grpc.LeaderElectionStub(channel)
                    challenge_request = node_pb2.ChallengeRequest(node_id=self.id)
                    response = stub.Challenge(challenge_request)
                    # print(response)
                    if response.acknowledged:
                        # print(f"Node {self.id}: Acknowledgment received from {higher_id}")
                        response = response or True
                except Exception as e:
                    print(f"Node {self.id}: Failed to communicate with {higher_id} ({e})")

        return response



    def updater_role_in_nodes(self,n_id,role):
        try:
            # print(f"Leader  Setting Role of the node {n_id} through port {GRPC_PORT_OFFSET + n_id}")
            channel = grpc.insecure_channel(f"localhost:{GRPC_PORT_OFFSET + n_id}")
            stub = node_pb2_grpc.LeaderElectionStub(channel)
            update_role_request = node_pb2.UpdateRoleRequest(new_role=role)
            response = stub.UpdateRole(update_role_request)
            # print(response)
            if response.success:
                return response.success
        except Exception as e:
            print(f"Node {self.id}: Failed to communicate with {n_id} ({e})")
            return False



    def rpcCheck(self):
        print(f"node {self.id} Sending Request to {GRPC_PORT_OFFSET + 2}")
        channel = grpc.insecure_channel(f"localhost:{GRPC_PORT_OFFSET + 2}")
        stub = node_pb2_grpc.LeaderElectionStub(channel)
        challenge_request = node_pb2.ChallengeRequest(node_id=self.id)
        response = stub.Challenge(challenge_request)
        print(response)

    def announce_leadership(self):
        """Broadcasts that this node is the leader using UDP multicast."""
        sock = helpers.create_socket(is_receiver=False)
        message = f"{self.id}-I am the leader".encode()
        sock.sendto(message, (MULTICAST_GROUP, self.port))
        sock.close()
        self.isLeader =True
        self.leader_id = (self.id,time.time())
        print(f"Node {self.id}: Broadcasted as leader")

    def receive_messages(self):
        """Listens for multicast messages from other nodes."""
        sock = helpers.create_socket(is_receiver=True)
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
                # print(addr)
                if headers[1] == "Heartbeat" and n_id != self.id:
                    # print(f"Node {self.id}:Receive Heartbeat from {n_id}")
                    self.nodes[n_id] = {'time': time.time(), 'role': headers[2]}
                elif headers[1] == "LeaderHeartbeat" and n_id != self.id:
                    # print(f"Node {self.id}:Receive Leader Heartbeat from {n_id}")
                    if not self.leader_id:
                        self.set_leader(n_id) #set a leader if no leader found
                    elif self.leader_id[0] != n_id:
                        self.leader_id = ()  #set your leader id to empty when different  heartbeat
                    else:
                        self.leader_id = (n_id, time.time()) # update the timestamp if the leaderid is same
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
            heartbeat_message = f"{self.id}-LeaderHeartbeat-".encode() if self.isLeader else f"{self.id}-Heartbeat-{self.role.name}".encode()
            sock = helpers.create_socket(is_receiver=False)
            sock.sendto(heartbeat_message, (MULTICAST_GROUP, self.port))
            sock.close()
            time.sleep(10)

    def check_unassigned_roles_roles(self):
        # print(self.nodes)
        for n_id,node in self.nodes.items() :
            if node["role"] == Roles.UNASSIGNED.name :
                # print("Matched")
                nodes =self.gate_node_count()
                role = helpers.get_assign_role(nodes).name
                status = self.updater_role_in_nodes(n_id,role)
                if status :
                    self.nodes[n_id]["role"] = role

    def check_inactive_nodes(self, timeout=30):
        """Checks for inactive nodes and triggers re-election if necessary."""
        while True:
            time.sleep(timeout / 2)
            current_time = time.time()
            inactive_nodes = [n_id for n_id, data in self.nodes.items() if current_time - data['time'] > timeout]
            for n_id in inactive_nodes:
                self.nodes.pop(n_id, None)
                print(f"Node {self.id}: Removed inactive node {n_id}")
            if not self.isLeader :
                if self.leader_id and current_time - self.leader_id[1] > timeout:
                    self.leader_id = ()
                    print(f"Node {self.id}: Removed Leader")
            if self.isLeader:
                self.check_unassigned_roles_roles()

    def start_election(self):
        """Initiates the leader election process."""
        acknowledged = self.challenge_higher_nodes()
        if not acknowledged and not self.isLeader:
            self.announce_leadership()


    def gate_node_count(self):
        nodes = {Roles.PROPOSER.name : 0 , Roles.ACCEPTOR.name:0 , Roles.LEANER.name:0}
        for _,node in self.nodes.items():
            if node["role"] == Roles.PROPOSER.name:
                nodes[ Roles.PROPOSER.name]+= 1
            if node["role"] == Roles.ACCEPTOR.name:
                nodes[Roles.ACCEPTOR.name] += 1
            if node["role"] == Roles.LEANER.name:
                nodes[Roles.LEANER.name] += 1
        return  nodes

    def queue_job(self,n_id,letter_range,page,line,text):
        try:
            # print(f"Leader  queuing jobs to {n_id} through port {GRPC_PORT_OFFSET + n_id}")
            channel = grpc.insecure_channel(f"localhost:{GRPC_PORT_OFFSET + n_id}")
            stub = node_pb2_grpc.LeaderElectionStub(channel)
            job_request = node_pb2.JobRequest(range=letter_range,text=text,page=page,line=line)
            response = stub.QueueJob(job_request)
            # print(response)
            if response.success:
                return response.success
        except Exception as e:
            print(f"Node {self.id}: Failed to communicate with {n_id} ({e})")
            return False
