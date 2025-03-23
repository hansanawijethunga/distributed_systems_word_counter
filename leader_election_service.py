import node_pb2
import node_pb2_grpc
from helpers import Roles


class LeaderElectionService(node_pb2_grpc.LeaderElectionServicer):
    def __init__(self, node):
        self.node = node

    def Challenge(self, request, context):
        self.node.is_election = True
        return node_pb2.ChallengeResponse(acknowledged=True)

    def UpdateRole(self, request, context):
        role = request.new_role
        if role == Roles.PROPOSER.name:
            self.node.role = Roles.PROPOSER
        if role == Roles.ACCEPTOR.name:
            self.node.role = Roles.ACCEPTOR
        if role == Roles.LEANER.name:
            self.node.role = Roles.LEANER
        return node_pb2.UpdateRoleResponse(success=True)

    def QueueJob(self,request,context):
        page = request.page
        line = request.line
        letter_range = request.range
        text = request.text
        self.node.jobs.put({"page":page,"line":line,"letter_range":letter_range,"text":text})
        return node_pb2.AcknowledgementResponse(success=True)

    def PromiseProposal(self,request,context):
        node_id = request.node_id
        self.node.proposal_promises.append(node_id)
        return node_pb2.AcknowledgementResponse(success=True)



