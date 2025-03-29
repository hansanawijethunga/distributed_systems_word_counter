import grpc
import node_pb2
import node_pb2_grpc
from concurrent import futures

from leader_election_service import LeaderElectionService


def start_side_car(id):
        side_car = SideCar()
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=50))
        node_pb2_grpc.add_LeaderElectionServicer_to_server(LeaderElectionService(side_car), server)
        server.add_insecure_port(f"[::]:{id}")
        server.start()
        ##print(f"Node {self.id}: gRPC server started on port {self.grpc_port}")
        server.wait_for_termination()
        while True:
            pass



class SideCar:
    pass


