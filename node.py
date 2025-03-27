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
import json

from redis_client import RedisClient

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
        self.words_count ={}
        self.proposals = queue.Queue()
        self.proposal_promises = []
        self.proposal_log = {}
        self.accepted_proposals = queue.Queue()
        self.result_log = {}
        self.is_election = False
        self.is_should_start_election = False
        self.go_no_go_new_line = helpers.Stage.PENDING
        self.line_status = {}
        self.redis_client = None

    def start_redis(self):
        print("Starting Redis")
        self.redis_client = RedisClient()

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
                if headers[1] == "LeaderHeartbeat" and n_id != self.id:
                    # print(f"Node {self.id}:Receive Leader Heartbeat from {n_id}")
                    if not self.leader_id:
                        self.set_leader(n_id)  # set a leader if no leader found
                    elif self.leader_id[0] != n_id:
                        self.leader_id = ()  # set your leader id to empty when different  heartbeat
                    else:
                        self.leader_id = (n_id, time.time())  # update the timestamp if the leaderid is same
                if headers[1] == "I am the leader" and n_id != self.id:
                    self.set_leader(n_id)

                if self.role == Roles.ACCEPTOR and headers[1] == "Prepare":
                    self.proposals.put((n_id, headers[2], headers[3]))
                    self.promise_proposal(n_id, headers[2])

                if self.role == Roles.LEANER and headers[1] == "Learn":
                    self.accepted_proposals.put((n_id, headers[2], headers[3]))

        except KeyboardInterrupt:
            print(f"Node {self.id}: Receiver stopped.")
        finally:
            sock.close()


    def start_election(self):
        """Initiates the leader election process."""
        if not self.is_election:
            self.is_election = True
            time.sleep(5) #waiting for nodes
            self.update_node_status()
            print("Leader Election Started")
            acknowledged = self.challenge_higher_nodes()
            if not acknowledged and not self.isLeader:
                self.announce_leadership()
            else:
                time.sleep(10) #Waiitng for other nods annowsments
            print("Setting is election to false")
        self.is_election = False

    def challenge_higher_nodes(self):
        """Sends a challenge request to higher nodes and waits for acknowledgment."""
        response = False
        for higher_id in sorted(self.nodes.keys(), reverse=True):
            if higher_id > self.id:
                try:
                    print(f"Node {self.id} challenging node {higher_id} through port {GRPC_PORT_OFFSET + higher_id}")
                    channel = grpc.insecure_channel(f"localhost:{GRPC_PORT_OFFSET + higher_id}")
                    stub = node_pb2_grpc.LeaderElectionStub(channel)
                    challenge_request = node_pb2.ChallengeRequest(node_id=self.id)
                    response = stub.Challenge(challenge_request)
                    # print(response)
                    if response.acknowledged:
                        print(f"Node {self.id}: Acknowledgment received from {higher_id}")
                        response = response or True
                except Exception as e:
                    print(f"Node {self.id}: Failed to communicate with {higher_id} ({e})")

        return response

    def announce_leadership(self):
        """Broadcasts that this node is the leader using UDP multicast."""
        sock = helpers.create_socket(is_receiver=False)
        message = f"{self.id}-I am the leader".encode()
        sock.sendto(message, (MULTICAST_GROUP, self.port))
        sock.close()
        self.isLeader =True
        self.leader_id = (self.id,time.time())
        print(f"Node {self.id}: broadcasting as leader")

    def set_leader(self,n_id):
        if self.isLeader:
            if self.id < n_id:
                self.leader_id = (n_id, time.time())
                self.isLeader = False
                print(f"Node {self.id}: Handing over the leadership to {n_id}")
            else:
                self.isLeader = True
                print(f"Node {self.id}: Reject the Leadership offer form {n_id}")
        else:
            self.leader_id = (n_id, time.time())
            self.isLeader = False
            print(f"Node {self.id}: Recognized leader {n_id}")



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





    def promise_proposal(self,n_id,proposal_number):
        try:
            channel = grpc.insecure_channel(f"localhost:{GRPC_PORT_OFFSET + n_id}")
            stub = node_pb2_grpc.LeaderElectionStub(channel)
            promise_request = node_pb2.PromiseRequest(node_id=self.id, proposal_number=proposal_number, promise=True)
            response = stub.PromiseProposal(promise_request)
            # print(response)
            if response.success:
                return response.success
        except Exception as e:
            print(f"Node {self.id}: Failed to communicate with {n_id} ({e})")
            return False

    def get_nodes_by_role(self, node_role, max_retries=5, delay=0.1):
        for _ in range(max_retries):
            try:
                return {n_id: info for n_id, info in self.nodes.items() if info.get('role') == node_role.name}
            except RuntimeError:
                time.sleep(delay)  # Wait before retrying
        raise RuntimeError("Failed to retrieve nodes after multiple attempts due to concurrent modifications.")



    def send_heartbeat(self):
        """Sends a heartbeat message periodically."""
        while True:
            heartbeat_message = f"{self.id}-LeaderHeartbeat-".encode() if self.isLeader else f"{self.id}-Heartbeat-{self.role.name}".encode()
            sock = helpers.create_socket(is_receiver=False)
            sock.sendto(heartbeat_message, (MULTICAST_GROUP, self.port))
            sock.close()
            time.sleep(1)

    def assign_roles(self):
        # print(self.nodes)
        for n_id,node in self.nodes.items() :
            if node["role"] == Roles.UNASSIGNED.name :
                # print("Matched")
                nodes =self.gate_node_count()
                role = helpers.get_assign_role(nodes).name
                status = self.updater_role_in_nodes(n_id,role)
                if status :
                    self.nodes[n_id]["role"] = role

    def check_inactive_nodes(self, timeout=6):
        """Checks for inactive nodes and triggers re-election if necessary."""
        while True:
            if  self.role == Roles.ACCEPTOR or self.role == Roles.LEANER:
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


    def update_node_status(self, timeout = 3):
        time.sleep(timeout/2)
        current_time = time.time()
        inactive_nodes = [n_id for n_id, data in self.nodes.items() if current_time - data['time'] > timeout]
        for n_id in inactive_nodes:
            self.nodes.pop(n_id, None)
            print(f"Node {self.id}: Removed inactive node {n_id}")
        if not self.isLeader :
            if self.leader_id and current_time - self.leader_id[1] > timeout:
                self.leader_id = ()
                print(f"Node {self.id}: Removed Leader")
        # print(self.nodes)


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

    def queue_job(self,n_id,letter_range,page,line,text,sequence):
        try:
            new_text = text.replace("-", "") #remove the - in the text
            channel = grpc.insecure_channel(f"localhost:{GRPC_PORT_OFFSET + n_id}")
            stub = node_pb2_grpc.LeaderElectionStub(channel)
            job_request = node_pb2.JobRequest(range=letter_range,text=new_text,page=page,line=line,sequence=str(sequence))
            response = stub.QueueJob(job_request)
            # print(response)
            if response.success:
                return response.success
        except Exception as e:
            print(f"Node {self.id}: Failed to communicate with {n_id} ({e})")
            return False

    def send_proposal(self, proposal_number, value_dict):
        value_json = json.dumps(value_dict)  # Convert dict to a JSON string

        prepare_message = f"{self.id}-Prepare-{proposal_number}-{value_json}".encode()
        sock = helpers.create_socket(is_receiver=False)
        sock.sendto(prepare_message, (MULTICAST_GROUP, self.port))
        sock.close()

        print(f"Sent proposal: {prepare_message.decode()}")  # Debug output



    def validate_proposal(self,proposal):
        values = self.proposal_log[proposal]["values"]
        # print(f"The data type of 'value' is: {type(values)}")
        new_value = helpers.get_most_present_value(values)  # Use the external function for validation

        if self.proposal_log[proposal]["accepted"] is None or new_value != self.proposal_log[proposal]["accepted"]:
            self.proposal_log[proposal]["accepted"] = new_value
            print(f"The data type of 'value' is: {type( self.proposal_log[proposal]['accepted'])}")
            try:
                learner_id = next(iter(self.get_nodes_by_role(Roles.LEANER)), None)
                if learner_id:
                    channel = grpc.insecure_channel(f"localhost:{GRPC_PORT_OFFSET + learner_id}")
                    stub = node_pb2_grpc.LeaderElectionStub(channel)
                    learner_request = node_pb2.LeanerRequest(
                        proposal_number=proposal,
                        value=self.proposal_log[proposal]["accepted"],
                        node_id=self.id
                    )

                    response = stub.InformLeanerRequest(learner_request)

                    if response.success:
                        return response.success
                else:
                    print(f"{self.role.name} Learner Not Found")
                    return False
            except Exception as e:
                print(f"Node {self.role.name}: Failed to communicate with Learner ({e})")
                return False
        else:
            print(f"{self.role.name}: Same value, no need to update Learner {new_value}")
            return True


    def push_leander_queue(self,node_id,proposal_no,value):
        self.accepted_proposals.put((node_id, proposal_no, value))

    def process_learning(self, result):
        if helpers.has_negative_one(result):
            print(f"{self.role.name} Majority votes not found")
            self.inform_leader(False)
        else:
            line_numbers = ""
            for proposal, value in result.items():
                line_numbers = proposal[10:-1]  # Extracting line numbers from proposal
                print(f"Setting the final value for {proposal[10:]} value {value}")
                self.redis_client.set_value(proposal[10:], value)  # Store in Redis

            self.inform_leader(True)
            self.redis_client.set_value("last_success_proposal", line_numbers)  # Store last success

    def inform_leader(self,status):
        print("Informing Leader")
        if not self.leader_id:
            return
        try:
            channel = grpc.insecure_channel(f"localhost:{GRPC_PORT_OFFSET + self.leader_id[0]}")
            stub = node_pb2_grpc.LeaderElectionStub(channel)
            result_request = node_pb2.ResultRequest(proposal_number = "ABC",status=status)
            response = stub.InformFinalResult(result_request)
            # print(response)
            if response.success:
                return response.success
        except Exception as e:
            print(f"Node {self.id}: Failed to communicate with {self.leader_id[0]} ({e})")
            return False

    def initiate_new_line(self, page_no, line_no):
        self.go_no_go_new_line = helpers.Stage.PENDING
        proposal_number = f"{str(page_no).zfill(4)}{str(line_no).zfill(3)}"
        self.line_status = helpers.generate_alphabet_keys(proposal_number)



    def update_line_status(self,status):
        if status:
            print(f"{self.role.name} Validation Success")
            self.go_no_go_new_line = helpers.Stage.GO
        else:
            print(f"{self.role.name} Validation Fail")
            self.go_no_go_new_line = helpers.Stage.NoGO



    def start_grpc_server(self):
        """Starts the gRPC server for handling leader election challenges."""
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=50))
        node_pb2_grpc.add_LeaderElectionServicer_to_server(LeaderElectionService(self), server)
        server.add_insecure_port(f"[::]:{self.grpc_port}")
        server.start()
        print(f"Node {self.id}: gRPC server started on port {self.grpc_port}")
        server.wait_for_termination()


    def check_minium_requirement(self):
        proposer_count = len(self.get_nodes_by_role(Roles.PROPOSER))
        acceptor_count = len(self.get_nodes_by_role(Roles.ACCEPTOR))
        learner_count = len(self.get_nodes_by_role(Roles.LEANER))
        return  proposer_count >=1  and  learner_count == 1 and acceptor_count >1







