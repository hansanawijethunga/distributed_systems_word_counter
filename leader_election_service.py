import node_pb2
import node_pb2_grpc
from helpers import Roles


class LeaderElectionService(node_pb2_grpc.LeaderElectionServicer):
    def __init__(self, node):
        self.node = node

    def Challenge(self, request, context):
        # self.node.start_election()
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