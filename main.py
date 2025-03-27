import queue
import socket
import threading
import time
import multiprocessing
import sys

import helpers
from helpers import Roles
from node import Node
from pdf_reader import PDFReader
import json

PDF_PATH = 'Material/Document.pdf'


def start_threads(node):
    receiver_thread = threading.Thread(target=node.receive_messages, daemon=True)
    receiver_thread.start()
    #
    heartbeat_thread = threading.Thread(target=node.send_heartbeat, daemon=True)
    heartbeat_thread.start()

    # cleanup_thread = threading.Thread(target=node.check_inactive_nodes, daemon=True)
    # cleanup_thread.start()

    grpc_thread = threading.Thread(target=node.start_grpc_server, daemon=True)
    grpc_thread.start()


def leader(node):
    pdf_reader = PDFReader(PDF_PATH)
    page_count = pdf_reader.get_page_count()
    print("Document Ready")
    node.start_redis()
    last_success_page_line = node.redis_client.get_value("last_success_proposal")
    page_start = 0
    line_start =0
    continue_flag = False
    if last_success_page_line is not None and last_success_page_line != "":
        print("Previous Procress Fond")
        continue_flag = True
        page_start = int(last_success_page_line[:4])
        line_start = int(last_success_page_line[4:7])

    for page_no in range(page_start, page_count):
        # print(f"Reading page {i}")
        text_list = pdf_reader.get_page_text_lines(page_no)
        if continue_flag:
            line_no = line_start
            continue_flag = False
        else:
            line_no = 0
        while line_no < len(text_list):  # loop will not increment if any one of the proposer nodes failed respond back
            if not node.isLeader:  # retuen to main loop if not a leader anymore
                print("Not the leader anymore stopping all operations")
                return
            node.initiate_new_line(page_no,line_no)
            node.update_node_status()
            node.assign_roles()
            proposers = node.get_nodes_by_role(Roles.PROPOSER)
            acceptor_count = len(node.get_nodes_by_role(Roles.ACCEPTOR))
            learner_count = len(node.get_nodes_by_role(Roles.LEANER))
            if node.check_minium_requirement(): #minimun nodes need to run the system
                letter_ranges = helpers.assign_ranges(proposers)
                for proposer_id, letter_range in letter_ranges.items():
                    print(f"sending page {page_no} line {line_no} {text_list[line_no]} to proposer {proposer_id}  assigned letter range  {letter_range['range'][0]}-{letter_range['range'][1]}")
                    proposer_feedback = node.queue_job(n_id= proposer_id,letter_range= f'{letter_range["range"][0]}-{letter_range["range"][1]}',page= page_no,line= line_no,
                                                       text= text_list[line_no],sequence=int(time.time()))

                    if not proposer_feedback: #if proposer return False stop the propose assignment and start form beginning
                        print(
                            f"FAIL sending page {page_no} line {line_no} {text_list[line_no]} to proposer {proposer_id} to")
                        break
                start_time = time.time()
                learner_id = next(iter(node.get_nodes_by_role(Roles.LEANER)))
                while  node.go_no_go_new_line == helpers.Stage.PENDING and learner_id:
                    node.update_node_status()  # remove inactive nodes
                    node.assign_roles() # assign un assigned nodes
                    leaner = node.get_nodes_by_role(Roles.LEANER)
                    if not leaner:
                        break
                    if time.time() - start_time >= 2 * 60:
                        print("All the votes not found, retrying line")
                        break
                if node.go_no_go_new_line == helpers.Stage.GO:
                    line_no += 1

            else:
                print(f"Waiting for nodes system is in halt")
                print(f"found {len(proposers)} proposer nodes needs one minium")
                print(f"found {acceptor_count} Acceptors needs 2 minium")
                print(f"found {learner_count} Learners needs one")
                time.sleep(5)
            # time.sleep(120)
    print("Document Completed")
    time.sleep(1000)

def proposer(node):
        if node.jobs.empty():
            print(f"{node.role.name} : Waiting for tasks")
            return

        job = node.jobs.get()
        print("Job Started")

        letter_counts = helpers.count_words_by_letter(job['letter_range'], job['text'])
        node.update_node_status()

        proposal_number = f"{job['sequence']}{str(job['page']).zfill(4)}{str(job['line']).zfill(3)}"
        print(f"Sending proposal {proposal_number} with counts {letter_counts} for text: {job['text']}")

        node.send_proposal(proposal_number, letter_counts)


def acceptor(node):
    if not node.proposals.empty():
            # Extract parts
            n_id, proposal, value_json = node.proposals.get()  # Allow for dictionary as last part
            print(value_json)
            value = json.loads(value_json)  # Convert JSON back to dictionary

            print(f"Validating Proposal {proposal} with values {value}")

            if proposal not in node.proposal_log:
                print("New Proposal")
                node.proposal_log[proposal] = {"values": [value], "accepted": None}
            else:
                print("Existing Proposal")
                node.proposal_log[proposal]["values"].append(value)

            node.validate_proposal(proposal)
    else:
        print("Acceptor Waiting for proposals")

def learner(node):
    if not node.accepted_proposals.empty():
        node.result_log = {}
        while True:
            try:
                n_id, proposal, value = node.accepted_proposals.get(timeout=5)
                print(f"{node.role.name} Received proposal: {n_id}, {proposal}, {value}")

                # Parse JSON value into a dictionary
                parsed_value = json.loads(value)

                if proposal not in node.result_log:
                    node.result_log[proposal] = {"values": [parsed_value]}
                else:
                    node.result_log[proposal]["values"].append(parsed_value)

            except queue.Empty:
                print(f"{node.role.name} No proposals received within 5 seconds.")
                break

        print(f"{node.role.name} Logged Proposals.")
        print(json.dumps(node.result_log, indent=2))  # Pretty-print the log

        # Process results based on threshold
        result = helpers.filter_exceeding_threshold(
            node.result_log,
            len(node.get_nodes_by_role(Roles.ACCEPTOR)) // 2
        )

        node.process_learning(result)  # Call process_learning with the final result
        node.result_log = {}  # Reset log after processing
    else:
        print(f"{node.role.name} Waiting for proposals")

def start_node(n_id):
    node = Node(n_id)
    start_threads(node)
    try:
        print(f"Listening for other nodes")
        time.sleep(5)
        if not node.leader_id:
            print(f"Node {node.id}: Initiating leader election...")
            node.start_election()
            # time.sleep(10)
        while True:
            # print(f"{node.role.name} {time.time()}" )
            node.update_node_status()
            if  not node.leader_id and not node.isLeader:
                print(f"Node {node.id}: Initiating leader election... inside while")
                node.start_election()
            if node.isLeader:
                leader(node)
            if node.role  == Roles.PROPOSER:
                proposer(node)
            if node.role == Roles.ACCEPTOR:
                acceptor(node)
            if node.role == Roles.LEANER:
                learner(node)


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
