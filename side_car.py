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
import helpers

SIDE_CAR_PORT_OFFSET_GRPC = 7000
SIDE_CAR_PORT_OFFSET_UDP = 8000
BASE_PORT = 5000
MULTICAST_GROUP = "224.1.1.1"

BUFFER_SIZE = 1024


def start_grpc_server(side_car):

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=50))
    node_pb2_grpc.add_LoginServiceServicer_to_server(LoginService(side_car), server)
    port = SIDE_CAR_PORT_OFFSET_GRPC + side_car.id
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    # print(f"Side Car {id}: gRPC server started on port {port}")
    server.wait_for_termination()


def start_udp_listener(side_car):
    sock = helpers.create_socket(is_receiver=True)
    sock.bind(("", BASE_PORT))
    mreq = socket.inet_aton(MULTICAST_GROUP) + socket.inet_aton("0.0.0.0")
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    try:
        while True:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            payload = data.decode()
            headers = payload.split("-")
            n_id = int(headers[0])
            if headers[1] == "Heartbeat" and n_id == side_car.id:
                side_car.set_availability(n_id,headers[2])
            elif headers[1] == "LeaderHeartbeat"and n_id == side_car.id:
                side_car.set_availability(n_id, "Leader")
    except KeyboardInterrupt:
        print(f"Node Receiver {id} stopped.")
    finally:
        sock.close()


def start_side_car(id):
    side_car = SideCar(id)
    grpc_thread = threading.Thread(target=start_grpc_server, args=(side_car,), daemon=True)
    udp_thread = threading.Thread(target=start_udp_listener, args=(side_car,), daemon=True)

    grpc_thread.start()
    udp_thread.start()

    while True:
        # side_car.set_availability(10,10,10)
        pass  # Keeps the main thread running

class SideCar:
    def __init__(self, n_id):
        self.id = n_id
        self.log_directory = "Logs"
        self.redis_client =  RedisClient(port=4380)
    def log(self,message,level= LogLevels.INFORMATION):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{self.id}] [{timestamp}] [{level.value}] {message}\n"
        self.redis_client.set_value(f"{self.id,int(time.time())}-timestamp",log_entry)

    def set_availability(self,node_id,role):
            self.redis_client.set_value(f"{node_id}-node",f"{role}-{time.time()}")
            print(self.redis_client.get_value(f"{node_id}-node"))










