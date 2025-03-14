from concurrent import futures
import grpc
import threading
import node_pb2
import node_pb2_grpc


class LeaderElectionServicer(node_pb2_grpc.LeaderElectionServicer):
    def Challenge(self, request, context):
        print(f"Received challenge from node {request.node_id}")
        return node_pb2.ChallengeResponse(acknowledged=True)  # Acknowledge the challenge


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    node_pb2_grpc.add_LeaderElectionServicer_to_server(LeaderElectionServicer(), server)
    server.add_insecure_port('[::]:60000')
    server.start()
    print("Server started. Listening on port 60000.")
    server.wait_for_termination()


def run_server_in_thread():
    server_thread = threading.Thread(target=serve, daemon=True)
    server_thread.start()
    return server_thread


if __name__ == '__main__':
    thread = run_server_in_thread()
    input("Press Enter to exit...\n")
