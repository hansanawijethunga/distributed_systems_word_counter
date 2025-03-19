from enum import Enum
import socket
import string


TTL = 2

class Roles(Enum):
    PROPOSER = 1
    ACCEPTOR = 2
    LEANER = 3
    UNASSIGNED = 4


def create_socket(is_receiver=False):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    if not is_receiver:
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, TTL)

    return sock


def get_assign_role(nodes):
    # Only one learner should exist.
    # If no learner exists, assign the first new node as learner.
    if nodes[Roles.LEANER.name] == 0:
        return Roles.LEANER

    # Ensure at least one proposer.
    if nodes[Roles.PROPOSER.name] == 0:
        return Roles.PROPOSER

    # Ensure at least three acceptors.
    if nodes[Roles.ACCEPTOR.name] < 3:
        return Roles.ACCEPTOR

    # After the stable configuration (1 learner, 1 proposer, 3 acceptors),
    # we first add acceptors to the system.
    if nodes[Roles.ACCEPTOR.name] < 2 * nodes[Roles.PROPOSER.name]:
        return Roles.ACCEPTOR
    # Only add a proposer if we have at least two acceptors for every proposer.
    return Roles.PROPOSER


def assign_ranges(nodes: dict) -> dict:
    """
    Given a dictionary of nodes (each with "other info"),
    assigns a letter range to each node evenly from A to Z.

    Each node gets a contiguous block of letters. The assigned range
    is represented as a list containing the first and last letter of the block.

    Example:
    Input: {
        12: {"other info": "foo"},
        13: {"other info": "bar"}
    }
    Output: {
        12: {"other info": "foo", "range": ["A", "M"]},
        13: {"other info": "bar", "range": ["N", "Z"]}
    }
    """
    # Total letters (A-Z)
    letters = list(string.ascii_uppercase)  # ['A', 'B', ..., 'Z']
    total_letters = len(letters)

    # Total available nodes
    total_nodes = len(nodes)

    # Determine base size of each segment and the remainder
    base_size = total_letters // total_nodes  # integer division
    remainder = total_letters % total_nodes  # extra letters to distribute

    # Sort the nodes by key (assuming keys can be ordered)
    sorted_keys = sorted(nodes.keys())

    start = 0
    for i, key in enumerate(sorted_keys):
        # Distribute one extra letter to the first "remainder" nodes
        extra = 1 if i < remainder else 0
        end = start + base_size + extra

        # Get the assigned letters for this node
        assigned_letters = letters[start:end]
        if assigned_letters:
            # Represent range as [first_letter, last_letter]
            nodes[key]["range"] = [assigned_letters[0], assigned_letters[-1]]
        else:
            nodes[key]["range"] = []

        start = end  # Update starting index for next node

    return nodes