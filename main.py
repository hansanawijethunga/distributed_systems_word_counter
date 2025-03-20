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
    for i in range(0, page_count):
        # print(f"Reading page {i}")
        text_list = pdf_reader.get_page_text_lines(i)
        j = 0
        while j < len(text_list):  # Use while loop for manual control
            status = True
            # print(text_list[j])
            print(f"Reading page {i} line {j} of {len(text_list)}")
            # print(f"Nodes {node.nodes}")
            proposers = {n_id: info for n_id, info in node.nodes.items() if info.get('role') == Roles.PROPOSER.name}
            # print(f"Proposers {proposers}")
            # time.sleep(5)
            if proposers:
                ranges = helpers.assign_ranges(proposers)
                # print(ranges)
                # time.sleep(10)
                for key, data in ranges.items():
                    status = status and node.queue_job(key, f'{data["range"][0]}-{data["range"][1]}', i, j,
                                                       text_list[j])
                    if not status:
                        break
                if status:
                    j += 1
        time.sleep(10)

def proposer(node):
    job = node.jobs.get()
    letters = helpers.count_words_by_letter(job['letter_range'], job['text'])
    print(f"{node.id} {job['text']} letters {letters}")
    time.sleep(5)
    for key, count in letters.items():
        node.send_proposal(f"{str(node.id)}{str(job['page']).zfill(4)}{str(job['line']).zfill(3)}{key}", count)
        start_time = time.time()
        # print(
        #     f"Promise Count {len(node.proposal_promises)} <= node count {len(node.get_nodes_by_role(Roles.ACCEPTOR)) // 2}")
        while len(node.proposal_promises) <= len(node.get_nodes_by_role(Roles.ACCEPTOR)) // 2:
            # print(
            #     f"Promise Count {len(node.proposal_promises)} <= node count {len(node.get_nodes_by_role(Roles.ACCEPTOR)) // 2}")
            if time.time() - start_time >= 5:
                print(f"{node.id} resend proposal to Acceptors")
                node.send_proposal(f"{str(node.id)}{str(job['page']).zfill(4)}{str(job['line']).zfill(3)}{key}",
                                   count)
                start_time = time.time()
        node.proposal_promises = []

def acceptor(node):
    pass



def start_node(n_id):
    node = Node(n_id)
    start_threads(node)
    try:
        while True:

            if not node.leader_id :
                print(f"Node {node.id}: No leader found, waiting...")
                time.sleep(30)
                if not node.leader_id :
                    print(f"Node {node.id}: Initiating leader election...")
                    node.start_election()

            if node.isLeader:
                leader(node)
            if node.role  == Roles.PROPOSER:
                proposer(node)
            if node.role == Roles.ACCEPTOR:
                acceptor(node)

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
