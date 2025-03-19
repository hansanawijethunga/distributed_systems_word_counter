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
                pdf_reader = PDFReader(PDF_PATH)
                page_count = pdf_reader.get_page_count()
                for i in range(0,page_count):
                    text_list = pdf_reader.get_page_text_lines(i)
                    for j in (0,len(text_list)):
                        proposers = {n_id: info for n_id, info in node.nodes.items() if info.get('role') == Roles.PROPOSER.name}
                        if  proposers :
                            ranges = helpers.assign_ranges(proposers)
                            for key , data in ranges.items():
                                node.queue_job(key,f'{data["range"][0]}-{data["range"][1]}',i,j,"My Sample Text")
                            i =+ 1
                            # print(f"Leader {ranges}")

            if node.role  == Roles.PROPOSER:
                job = node.jobs.get()
                letters = helpers.count_words_by_letter(job['letter_range'],job['text'])
                print(f"{node.id} page {job['page']} line {job['line']} {letters}")
            time.sleep(5)
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
