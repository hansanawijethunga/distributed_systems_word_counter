# Distributed Word Count System

## Overview
This project implements a distributed system for counting words in a document based on their starting letters. The system follows the **Paxos algorithm** for distributed consensus and automatically assigns roles (Coordinator, Proposer, Acceptor, Learner) to nodes as they join the cluster. The implementation uses **Docker** to manage independent processes and enables seamless scaling of nodes.

## Architecture
- **Coordinator Node**: Manages the cluster, assigns letter ranges to proposers, and handles failure recovery.
- **Proposer Nodes**: Receives document lines, counts words within their assigned letter range, and proposes results to Acceptors.
- **Acceptor Nodes**: Validates word counts from Proposers and reaches a consensus before forwarding to the Learner.
- **Learner Node**: Aggregates validated word counts and produces the final result.
- **Sidecar Proxy**: Handles logging and inter-node communication using appropriate protocols.

## Technologies Used
- **Programming Language**: Python
- **Communication Protocols**:
  - **gRPC**: For efficient inter-node communication
  - **MQTT**: For lightweight message passing
  - **HTTP (FastAPI)**: For exposing external APIs
- **Docker**: To containerize nodes and scale dynamically
- **Paxos Algorithm**: For consensus handling in a distributed system

## Installation
### Prerequisites
Ensure you have the following installed:
- Python 3.9+
- Docker & Docker Compose

### Clone the Repository
```sh
git clone https://github.com/your-repo/distributed-word-count.git
cd distributed-word-count
```

### Install Dependencies
Create a virtual environment and install dependencies:
```sh
python -m venv venv
source venv/bin/activate  # On Windows, use 'venv\Scripts\activate'
pip install -r requirements.txt
```

## Running the System
### Using Docker Compose
Start all nodes:
```sh
docker-compose up --build
```
This will automatically spawn Coordinator, Proposer(s), Acceptor(s), and the Learner node.

### Without Docker
Run each node manually in separate terminals:
```sh
python coordinator.py  # Start the Coordinator Node
python proposer.py  # Start Proposer Nodes
python acceptor.py  # Start Acceptor Nodes
python learner.py  # Start the Learner Node
```

## Configuration
- Nodes automatically discover each other without requiring environment variables.
- Logging and inter-node communication are handled via the Sidecar Proxy.
- If the **Coordinator Node fails**, another node will automatically take over.

## Testing
Run unit tests:
```sh
pytest
```

## Future Enhancements
- Implement dynamic rebalancing of workloads if nodes leave or join the network.
- Optimize the Paxos implementation for high-performance word counting.
- Improve fault tolerance using persistent storage.

## License
MIT License

## Contact
For any queries, reach out to **your-email@example.com**.


