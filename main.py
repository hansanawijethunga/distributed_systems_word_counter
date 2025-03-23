import socket
import threading
import time
import multiprocessing
import sys

import helpers
from helpers import Roles
from node import Node
from pdf_reader import PDFReader

PDF_PATH = 'Material/Document.pdf'


def start_threads(node):
    receiver_thread = threading.Thread(target=node.receive_messages, daemon=True)
    receiver_thread.start()
    #
    heartbeat_thread = threading.Thread(target=node.send_heartbeat, daemon=True)
    heartbeat_thread.start()
    #
    cleanup_thread = threading.Thread(target=node.check_inactive_nodes, daemon=True)
    cleanup_thread.start()
    #
    grpc_thread = threading.Thread(target=node.start_grpc_server, daemon=True)
    grpc_thread.start()


def leader(node):
    pdf_reader = PDFReader(PDF_PATH)
    page_count = pdf_reader.get_page_count()
    print("Document Ready")
    for i in range(0, page_count):
        # print(f"Reading page {i}")
        text_list = pdf_reader.get_page_text_lines(i)
        j = 0
        while j < len(text_list):  # loop will not increment if any one of the proposer nodes failed respond back
            node.manual_check_inactive_nodes() #remove inactive nodes
            node.check_unassigned_roles_roles() #assign roles in un assigned roles
            proposers = {n_id: info for n_id, info in node.nodes.items() if info.get('role') == Roles.PROPOSER.name}
            acceptor_count = len(node.get_nodes_by_role(Roles.ACCEPTOR))
            learner_count = len(node.get_nodes_by_role(Roles.LEANER))
            status = True
            if proposers and  learner_count == 1 and acceptor_count >1:
                ranges = helpers.assign_ranges(proposers)
                for key, data in ranges.items():
                    print(f"sending {text_list[j]} to proposer {key} to ")
                    status = status and node.queue_job(key, f'{data["range"][0]}-{data["range"][1]}', i, j,
                                                       text_list[j])
                    if not status:
                        print(f"FAIL sending {text_list[j]} to proposer {key} to ")
                        break
                if status:
                    j += 1
            else:
                print(f"Waiting for nodes system is in halt")
                print(f"found {len(proposers)} proposer nodes needs one minium")
                print(f"found {acceptor_count} Acceptors needs 2 minium")
                print(f"found {learner_count} Learners needs one")
                time.sleep(5)
        time.sleep(10)

def proposer(node):
        job = node.jobs.get()
        letters = helpers.count_words_by_letter(job['letter_range'], job['text'])
        for key, count in letters.items():
            node.send_proposal(f"{str(node.id)}{str(job['page']).zfill(4)}{str(job['line']).zfill(3)}{key}", count)
            start_time = time.time()
            node.manual_check_inactive_nodes()
            while len(node.proposal_promises) <= len(node.get_nodes_by_role(Roles.ACCEPTOR)) // 2:
                if time.time() - start_time >= 5: #if proposal was not accepted by majority retry until it get accepted
                    print(f"{node.id} resend proposal to Acceptors")
                    node.send_proposal(f"{str(node.id)}{str(job['page']).zfill(4)}{str(job['line']).zfill(3)}{key}",
                                       count)
                    start_time = time.time()
            node.proposal_promises = []

def acceptor(node):
        node.manual_check_inactive_nodes()
        n_id, proposal , value = node.proposals.get()
        if proposal not in node.proposal_log:
            node.proposal_log[proposal] = {"values": [value], "accepted": None}
        else:
            node.proposal_log[proposal]["values"].append(value)
        node.validate_proposal(proposal)

def learner(node):
        n_id, proposal, value , acceptor_node_count = node.accepted_proposals.get()
        if proposal not in node.result_log:
            node.result_log[proposal] = {"values": [value] , "acceptor_node_count":acceptor_node_count}
        else:
            node.result_log[proposal]["values"].append(value)
            node.result_log[proposal]["acceptor_node_count"] = acceptor_node_count
        node.process_leaning(proposal)
        time.sleep(5)

def start_node(n_id):
    node = Node(n_id)
    start_threads(node)
    try:
        print(f"Listening for other nodes")
        time.sleep(5)
        if not node.leader_id:
            print(f"Node {node.id}: Initiating leader election...")
            node.start_election()
        while True:
            node.manual_check_inactive_nodes()
            if node.is_election or not  node.leader_id:
                node.start_election()
            node.manual_check_inactive_nodes()
            if node.isLeader:
                leader(node) #infinite loop
            if node.role  == Roles.PROPOSER:
                proposer(node) #infinite loop
            if node.role == Roles.ACCEPTOR:
                acceptor(node) #infinite loop
            if node.role == Roles.LEANER:
                learner(node) #infinite loop


    except KeyboardInterrupt:
        print(f"Node {n_id}: Stopping...")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "single_run":
        if len(sys.argv) != 3:
            print("Usage: script.py single_run <node_id>")
            sys.exit(1)
        node_id = int(sys.argv[2])
        start_node(node_id)
    else:
        num_nodes = 20
        processes = []
        for node_id in range(1, num_nodes + 1):
            process = multiprocessing.Process(target=start_node, args=(node_id,))
            process.start()
            processes.append(process)

        for process in processes:
            process.join()
