import os
import threading
import grpc
import socket
from concurrent import futures
import node_pb2_grpc
from helpers import LogLevels
from leader_election_service import LeaderElectionService
from datetime import datetime
import time
from logging_service import LoginService

from redis_client import RedisClient

SIDE_CAR_PORT_OFFSET_GRPC = 7000
SIDE_CAR_PORT_OFFSET_UDP = 8000
MULTICAST_GROUP = "224.0.0.1"
BUFFER_SIZE = 1024


def start_grpc_server(id):
    side_car = SideCar(id)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=50))
    node_pb2_grpc.add_LoginServiceServicer_to_server(LoginService(side_car), server)
    port = SIDE_CAR_PORT_OFFSET_GRPC + id
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    # print(f"Side Car {id}: gRPC server started on port {port}")
    server.wait_for_termination()


def start_udp_listener(id):
    # print(f"Side Car {id}: UDP Listener started on port {SIDE_CAR_PORT_OFFSET_UDP + id}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", SIDE_CAR_PORT_OFFSET_UDP + id))
    mreq = socket.inet_aton(MULTICAST_GROUP) + socket.inet_aton("0.0.0.0")
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    try:
        while True:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            payload = data.decode()
            headers = payload.split("-")
            n_id = int(headers[0])

            if headers[1] == "Heartbeat":
                pass  # Handle heartbeat
            elif headers[1] == "LeaderHeartbeat":
                pass  # Handle leader heartbeat
            elif headers[1] == "I am the leader":
                pass  # Handle leader announcement
    except KeyboardInterrupt:
        print(f"Node Receiver {id} stopped.")
    finally:
        sock.close()


def start_side_car(id):
    grpc_thread = threading.Thread(target=start_grpc_server, args=(id,), daemon=True)
    udp_thread = threading.Thread(target=start_udp_listener, args=(id,), daemon=True)

    grpc_thread.start()
    udp_thread.start()

    while True:
        pass  # Keeps the main thread running

class SideCar:
    def __init__(self, n_id):
        self.id = n_id
        self.log_directory = "Logs"
        self.redis_client =  RedisClient(port=4380)
    def log(self,message,level= LogLevels.INFORMATION):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level.value}] {message}\n"
        print(log_entry)
        self.redis_client.set_value(f"{self.id,int(time.time())}-timestamp",log_entry)







