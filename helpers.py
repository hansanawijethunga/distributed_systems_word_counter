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


def count_words_by_letter(letter_range, text):
    start_letter, end_letter = letter_range.split('-')
    letter_counts = {chr(letter): 0 for letter in range(ord(start_letter), ord(end_letter) + 1)}

    words = text.split()
    for word in words:
        first_letter = word[0].upper()
        if start_letter <= first_letter <= end_letter:
            letter_counts[first_letter] += 1

    return {k: v for k, v in letter_counts.items() if v > 0}

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
    for proposal, value_dict in data.items():
        values = value_dict["values"]

        # Aggregate letter counts
        combined_counts = Counter()
        for value in values:
            for letter, count in value.items():
                combined_counts[letter] += count
        # Filter letters exceeding the threshold
        filtered_counts = {letter: count for letter, count in combined_counts.items() if count > threshold}

        result[proposal] = json.dumps(filtered_counts) if filtered_counts else "{}"  # Return JSON or empty dict
    return result

def has_negative_one(data: dict) -> bool:
    """
    Returns True if any value in the dictionary is -1, otherwise False.
    """
    return -1 in data.values()



if __name__ == "__main__":
    # nums1 = [4,3,3,3,3]
    # total_voter_count1 = 8
    # print(get_most_voted_number(nums1, total_voter_count1))  # Output: 3
    print(generate_alphabet_keys("10000000"))