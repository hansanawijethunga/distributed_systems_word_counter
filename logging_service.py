import node_pb2
import node_pb2_grpc
from helpers import Roles
from helpers import LogLevels


class LoginService(node_pb2_grpc.LoginServiceServicer):
    def __init__(self, side_car):
        self.side_car = side_car

    def LogMessageRequest(self, request, context):
        # print(f"Log Level: {request.log_level}, Message: {request.message}")
        log_level_message = request.log_level
        log_level = LogLevels.INFORMATION
        if log_level_message == LogLevels.WARNING.value:
            log_level = LogLevels.WARNING
        if log_level_message == LogLevels.ERROR.value:
            log_level = LogLevels.ERROR
        if log_level_message == LogLevels.DEBUG.value:
            log_level = LogLevels.DEBUG
        message = request.message
        self.side_car.log(message,log_level)
        return node_pb2.AcknowledgementResponse(success=True)