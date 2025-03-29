import node_pb2
import node_pb2_grpc
from helpers import Roles


class LeaderElectionService(node_pb2_grpc.LeaderElectionServicer):
    def __init__(self, node):
        self.node = node

    def Challenge(self, request, context):
        # print("Setting is election to true")
        # self.node.start_election()
        self.node.is_should_start_election = True
        return node_pb2.ChallengeResponse(acknowledged=True)

    def UpdateRole(self, request, context):
        role = request.new_role
        if role == Roles.PROPOSER.name:
            self.node.role = Roles.PROPOSER
        if role == Roles.ACCEPTOR.name:
            self.node.role = Roles.ACCEPTOR
        if role == Roles.LEANER.name:
            self.node.start_redis()
            self.node.role = Roles.LEANER
        print(f"Node {self.node.id}I am a/an {self.node.role.name}")
        return node_pb2.UpdateRoleResponse(success=True)

    def QueueJob(self,request,context):
        page = request.page
        line = request.line
        letter_range = request.range
        text = request.text
        sequence = request.sequence
        self.node.jobs.put({"page":page,"line":line,"letter_range":letter_range,"text":text,"sequence":sequence})
        return node_pb2.AcknowledgementResponse(success=True)

    def PromiseProposal(self,request,context):
        node_id = request.node_id
        self.node.proposal_promises.append(node_id)
        return node_pb2.AcknowledgementResponse(success=True)


    def InformFinalResult(self,request,context):
        proposal_number = request.proposal_number
        status = request.status
        self.node.update_line_status(status)
        return node_pb2.AcknowledgementResponse(success=True)

    def InformLeanerRequest(self,request,context):
        # print(f"Request{request}")
        node_id = request.node_id
        proposal_number = request.proposal_number
        value = request.value
        data = request.data
        if proposal_number not in self.node.proposal_list:
            self.node.push_leander_queue(node_id,proposal_number,value,data)
        return node_pb2.AcknowledgementResponse(success=True)





