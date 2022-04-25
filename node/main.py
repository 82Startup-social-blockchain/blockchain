import os
from typing import Optional, Dict

from fastapi import FastAPI
from node.models import NodeAddress

# from models import TransactionRequest
from node.node import Node
from utils import constants

app = FastAPI()

assert "ADDRESS" in os.environ

node = Node(os.environ["ADDRESS"])
node.join_network()

### Endpoints that other nodes call ###


@app.post("/validation/block")
async def validate_block():
    # other nodes hit this endpoint to broadcast block to this node

    # 1. create block instance
    # 2. validate block
    # 3. add block to blockchain
    # 4. remove activities from activity pool
    pass


@app.post("/validation/transaction")
async def validate_activity():
    # other nodes hit this endpoint to broadcast transaction to this node

    # 1. create Activity instance
    # 2. add activity to activity pool
    pass


@app.post(constants.NODE_REQUEST_PATH)
async def accept_new_node(data: NodeAddress):
    # add the new node to known node address list
    node.accept_new_node(data.address)


@app.get(constants.KNOWN_NODES_PATH)
async def get_known_nodes():
    # return known nodes
    return list(node.known_node_address_set)


### Endpoints that services call ###

@app.post("/activity")
async def create_activity():
    # User-side API to create activity based on type and content

    # 1. create transaction instance and activity instance from activity request
    # 2. upload to s3
    # 3. add to activity pool and broadcast to other nodes
    pass


@app.get("/activity/{public_key}")
async def get_activities_by_public_key(
    public_key: str,
    tx_type: Optional[str] = None
):
    # get activities of a user with input public key - filter by multiple query paraemters
    pass
