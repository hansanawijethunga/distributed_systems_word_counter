from concurrent import futures
import grpc
import node_pb2
import node_pb2_grpc


class LeaderElectionServicer(node_pb2_grpc.LeaderElectionServicer):
    def Challenge(self, request, context):
        print(f"Received challenge from node {request.node_id}")
        return node_pb2.ChallengeResponse(acknowledged=True)  # Acknowledge the challenge


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    node_pb2_grpc.add_LeaderElectionServicer_to_server(LeaderElectionServicer(), server)

    server.add_insecure_port('[::]:50051')  # The server listens on port 50051
    server.start()
    print("Server started. Listening on port 50051.")
    server.wait_for_termination()


if __name__ == '__main__':
    serve()
