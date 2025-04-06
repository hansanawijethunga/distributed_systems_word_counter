import math
from enum import Enum
import socket
import string
from collections import Counter
import json


TTL = 2

class Roles(Enum):
    PROPOSER = 1
    ACCEPTOR = 2
    LEANER = 3
    UNASSIGNED = 4


class Stage(Enum):
    PENDING = 0
    GO = 1
    NoGO = 2


class LogLevels(Enum):
    INFORMATION = 0
    WARNING = 1
    ERROR = 2
    DEBUG = 3



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
    if nodes[Roles.PROPOSER.name] < 2 * nodes[Roles.ACCEPTOR.name]:
        return Roles.PROPOSER
    # Only add a proposer if we have at least two acceptors for every proposer.
    return Roles.ACCEPTOR


def assign_ranges(nodes: dict ,replication_factor: int = 2) -> dict:
    """
    Given a dictionary of nodes (each with "other info"), assigns a letter range to each node.

    The letter range is determined by evenly splitting the alphabet (A-Z) into groups.
    Each group (or range) is then assigned to replication_factor number of nodes for fault tolerance.

    For example:
    Input nodes: {
        12: {"other info": "foo"},
        13: {"other info": "bar"},
        14: {"other info": "baz"},
        15: {"other info": "qux"}
    }
    With replication_factor=2, you would have 2 groups.

    Output might be:
    {
        12: {"other info": "foo", "range": ["A", "M"]},
        13: {"other info": "bar", "range": ["A", "M"]},
        14: {"other info": "baz", "range": ["N", "Z"]},
        15: {"other info": "qux", "range": ["N", "Z"]}
    }
    """
    letters = list(string.ascii_uppercase)
    total_letters = len(letters)

    total_nodes = len(nodes)
    if total_nodes == 0:
        return nodes

    # Calculate the number of groups (each group gets one unique range)
    num_groups = math.ceil(total_nodes / replication_factor)

    # Determine base size of each letter group and distribute extra letters
    base_group_size = total_letters // num_groups
    extra_letters = total_letters % num_groups

    # Create the list of letter groups (each group is a tuple: (first_letter, last_letter))
    groups = []
    start = 0
    for i in range(num_groups):
        # Distribute one extra letter to the first 'extra_letters' groups.
        current_group_size = base_group_size + (1 if i < extra_letters else 0)
        end = start + current_group_size
        if start < total_letters:
            groups.append([letters[start], letters[end-1]])
        else:
            groups.append([])
        start = end

    # Sort nodes by key to have a consistent order.
    sorted_node_ids = sorted(nodes.keys())

    # Assign groups to nodes. Each group gets replication_factor nodes.
    group_index = 0
    for i, node_id in enumerate(sorted_node_ids):
        # Determine which group this node should belong to.
        group_index = i // replication_factor
        # In case there are more nodes than groups * replication_factor,
        # assign extra nodes to the last group.
        if group_index >= len(groups):
            group_index = len(groups) - 1
        nodes[node_id]["range"] = groups[group_index]

    return nodes


def count_words_by_letter(letter_range, text):
    start_letter, end_letter = letter_range.split('-')
    start_letter, end_letter = start_letter.upper(), end_letter.upper()

    letter_counts = {chr(letter): 0 for letter in range(ord(start_letter), ord(end_letter) + 1)}
    letter_groups = {chr(letter): [] for letter in range(ord(start_letter), ord(end_letter) + 1)}

    words = text.split()

    for word in words:
        first_letter = word[0].upper()
        if start_letter <= first_letter <= end_letter:
            letter_counts[first_letter] += 1
            letter_groups[first_letter].append(word)

    return letter_counts, letter_groups

def get_most_common_value(values):
    counter = Counter(values)
    most_common = counter.most_common()
    if len(most_common) == 1:
        return most_common[0][0]
    max_count = most_common[0][1]
    top_values = [val for val, count in most_common if count == max_count]
    accepted_value = top_values[0] if len(top_values) == 1 else None
    return accepted_value


def get_most_present_value(values):
    """Aggregate letter counts from multiple proposals and return the final combined dictionary as JSON."""
    combined_counts = Counter()

    for value in values:
        for letter, count in value.items():
            combined_counts[letter] += count

    return json.dumps(dict(combined_counts))  # Convert Counter back to JSON



def get_most_voted_number(nums,total_voter_count):
    if total_voter_count < 2:
       return None
    candidate, count = None, 0
    for num in nums:
        if count == 0:
            candidate, count = num, 1
        elif num == candidate:
            count += 1
        else:
            count -= 1

    # Verify the candidate
    if nums.count(candidate) > total_voter_count // 2:
        return candidate
    return None  # No majority element

import string

def generate_alphabet_keys(prefix):
    return {f"{prefix}{letter}": False for letter in string.ascii_uppercase}


def all_values_true(dictionary):
    return all(dictionary.values())


def filter_exceeding_threshold(data: dict, threshold: int):
    result = {}
    # print(data)
    for proposal, value_dict in data.items():
        values = value_dict["values"]
        value,count =most_common_dict(values)
        if count > threshold:
            result[proposal] = value
        else:
            return False
    # print(result)
    return result

def has_negative_one(data: dict) -> bool:
    """
    Returns True if any value in the dictionary is -1, otherwise False.
    """
    return -1 in data.values()




def most_common_dict(dict_list):
    """
    Finds the most common dictionary in a list of dictionaries.

    Args:
        dict_list (list): A list of dictionaries.

    Returns:
        tuple: (most_common_dict, occurrence_count)
    """
    # Convert dictionaries to JSON strings (hashable format)
    dict_strings = [json.dumps(d, sort_keys=True) for d in dict_list]

    # Count occurrences
    counter = Counter(dict_strings)

    # Find the most common dictionary and its count
    most_common_str, most_common_count = counter.most_common(1)[0]

    # Convert back to dictionary
    most_common_dict = json.loads(most_common_str)

    return most_common_dict, most_common_count


def print_dict_table(data: dict):
    """Prints a dictionary in a tabular format with two columns: Keys and Values."""
    if not data:
        print("No data to display.")
        return

    key_width = max(len(str(k)) for k in data.keys()) + 2
    value_width = max(len(str(v)) for v in data.values()) + 2

    print(f"{'Key'.ljust(key_width)} | {'Value'.ljust(value_width)}")
    print("-" * (key_width + value_width + 3))

    for key, value in data.items():
        print(f"{str(key).ljust(key_width)} | {str(value).ljust(value_width)}")






if __name__ == "__main__":
    pass
    # nums1 = [4,3,3,3,3]
    # total_voter_count1 = 8
    # #print(get_most_voted_number(nums1, total_voter_count1))  # Output: 3
    #print(generate_alphabet_keys("10000000"))