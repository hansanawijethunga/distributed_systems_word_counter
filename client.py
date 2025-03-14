import grpc
import node_pb2
import node_pb2_grpc


def run():
    # Step 1: Set up the gRPC channel to connect to the server.
    channel = grpc.insecure_channel('localhost:60000')  # Update the server address if needed

    # Step 2: Create a stub (client).
    stub = node_pb2_grpc.LeaderElectionStub(channel)

    # Step 3: Create a request message for the 'Challenge' method.
    challenge_request = node_pb2.ChallengeRequest(node_id=1)  # Pass the appropriate node ID

    # Step 4: Call the remote procedure (the 'Challenge' method) and get the response.
    response = stub.Challenge(challenge_request)

    # Step 5: Print the response.
    if response.acknowledged:
        print("Challenge acknowledged!")
    else:
        print("Challenge not acknowledged.")


if __name__ == '__main__':
    run()