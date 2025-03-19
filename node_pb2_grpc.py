# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings

import node_pb2 as node__pb2

GRPC_GENERATED_VERSION = '1.64.0'
GRPC_VERSION = grpc.__version__
EXPECTED_ERROR_RELEASE = '1.65.0'
SCHEDULED_RELEASE_DATE = 'June 25, 2024'
_version_not_supported = False

try:
    from grpc._utilities import first_version_is_lower
    _version_not_supported = first_version_is_lower(GRPC_VERSION, GRPC_GENERATED_VERSION)
except ImportError:
    _version_not_supported = True

if _version_not_supported:
    warnings.warn(
        f'The grpc package installed is at version {GRPC_VERSION},'
        + f' but the generated code in node_pb2_grpc.py depends on'
        + f' grpcio>={GRPC_GENERATED_VERSION}.'
        + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}'
        + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.'
        + f' This warning will become an error in {EXPECTED_ERROR_RELEASE},'
        + f' scheduled for release on {SCHEDULED_RELEASE_DATE}.',
        RuntimeWarning
    )


class LeaderElectionStub(object):
    """Service for leader election
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Challenge = channel.unary_unary(
                '/leader_election.LeaderElection/Challenge',
                request_serializer=node__pb2.ChallengeRequest.SerializeToString,
                response_deserializer=node__pb2.ChallengeResponse.FromString,
                _registered_method=True)
        self.UpdateRole = channel.unary_unary(
                '/leader_election.LeaderElection/UpdateRole',
                request_serializer=node__pb2.UpdateRoleRequest.SerializeToString,
                response_deserializer=node__pb2.UpdateRoleResponse.FromString,
                _registered_method=True)
        self.QueueJob = channel.unary_unary(
                '/leader_election.LeaderElection/QueueJob',
                request_serializer=node__pb2.JobRequest.SerializeToString,
                response_deserializer=node__pb2.AcknowledgementResponse.FromString,
                _registered_method=True)


class LeaderElectionServicer(object):
    """Service for leader election
    """

    def Challenge(self, request, context):
        """A node challenges a higher node
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def UpdateRole(self, request, context):
        """Method to update the role of a node
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def QueueJob(self, request, context):
        """Queue a job to be processed
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_LeaderElectionServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'Challenge': grpc.unary_unary_rpc_method_handler(
                    servicer.Challenge,
                    request_deserializer=node__pb2.ChallengeRequest.FromString,
                    response_serializer=node__pb2.ChallengeResponse.SerializeToString,
            ),
            'UpdateRole': grpc.unary_unary_rpc_method_handler(
                    servicer.UpdateRole,
                    request_deserializer=node__pb2.UpdateRoleRequest.FromString,
                    response_serializer=node__pb2.UpdateRoleResponse.SerializeToString,
            ),
            'QueueJob': grpc.unary_unary_rpc_method_handler(
                    servicer.QueueJob,
                    request_deserializer=node__pb2.JobRequest.FromString,
                    response_serializer=node__pb2.AcknowledgementResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'leader_election.LeaderElection', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('leader_election.LeaderElection', rpc_method_handlers)


 # This class is part of an EXPERIMENTAL API.
class LeaderElection(object):
    """Service for leader election
    """

    @staticmethod
    def Challenge(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/leader_election.LeaderElection/Challenge',
            node__pb2.ChallengeRequest.SerializeToString,
            node__pb2.ChallengeResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def UpdateRole(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/leader_election.LeaderElection/UpdateRole',
            node__pb2.UpdateRoleRequest.SerializeToString,
            node__pb2.UpdateRoleResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def QueueJob(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/leader_election.LeaderElection/QueueJob',
            node__pb2.JobRequest.SerializeToString,
            node__pb2.AcknowledgementResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)
