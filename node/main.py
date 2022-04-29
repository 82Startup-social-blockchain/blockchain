import binascii
import json
import os
import logging
from typing import List, Optional, Dict

from fastapi import FastAPI, HTTPException

# from models import TransactionRequest
from block.block import Block, create_block_from_dict
from block.blockchain import Blockchain
from node.models import BlockValidationRequest, NodeAddress, TransactionValidationRequest
from node.node import Node
from transaction.transaction import create_transaction_from_dict
from utils import constants

FORMAT = "%(levelname)s:     %(message)s"
logging.basicConfig(format=FORMAT, level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

assert "ADDRESS" in os.environ

node = Node(os.environ["ADDRESS"])

if "INIT_BLOCKCHAIN_FILE_NAME" in os.environ:
    with open(os.path.join(constants.EXAMPLE_DATA_DIR, os.environ["INIT_BLOCKCHAIN_FILE_NAME"]), 'r') as fp:
        blockchain_dict_list = json.load(fp)
    blockchain = Blockchain()
    blockchain.from_dict_list(blockchain_dict_list)
    node.blockchain = blockchain

node.join_network()


### Endpoints that other nodes call ###

@app.post(constants.BLOCK_VALIDATION_PATH, response_model=None)
async def validate_block(blockRequest: BlockValidationRequest):
    # other nodes hit this endpoint to broadcast block to this node

    # 1. create block instance
    previous_block = None
    if blockRequest.previous_block_hash_hex is not None:
        # TODO: what if the block does not reach this node in order?
        # make a block pool to store candidate blocks
        # for now, just check if the previous block is head
        if node.blockchain.head.block_hash != binascii.unhexlify(blockRequest.previous_block_hash_hex.encode('utf-8')):
            logger.error("Requested block is not linked to the current head")
            raise HTTPException(
                status_code=409,
                detail="Requested block is not linked to the current head"
            )
        previous_block = node.blockchain.head

    block_dict = blockRequest.dict()
    origin = block_dict["origin"]
    del block_dict["origin"]
    block = create_block_from_dict(blockRequest.dict(), previous_block)

    # 2. add block to blockchain
    logger.info("Adding new block to blockchain")
    await node.accept_new_block(block, origin)


@app.post(constants.TRANSACTION_VALIDATION_PATH, response_model=None)
async def validate_transaction(transactionRequest: TransactionValidationRequest):
    # other nodes hit this endpoint to broadcast transaction to this node

    # 1. create Transaction instance
    transaction_dict = transactionRequest.dict()
    origin = transaction_dict["origin"]
    del transaction_dict["origin"]
    transaction = create_transaction_from_dict(transactionRequest.dict())

    # 2. add transaction to transaction pool
    await node.accept_new_transaction(transaction, origin)


@app.post(constants.NODE_REQUEST_PATH, response_model=None)
async def accept_new_node(data: NodeAddress):
    # add the new node to known node address list
    node.accept_new_node(data.address)


@app.get(constants.KNOWN_NODES_PATH, response_model=List[str])
async def get_known_nodes():
    # return known nodes
    return list(node.known_node_address_set)


@app.get(constants.BLOCKCHAIN_REQUEST_PATH)
async def get_blockchain():
    # return the current state of blockchain that the node has
    if node.blockchain is None:
        return []

    return node.blockchain.to_dict_list()


@app.get("/transaction-pool")
async def get_transaction_pool():
    return {tx_hash_hex.decode('utf-8'): tx.to_dict()
            for tx_hash_hex, tx in node.transaction_pool.items()}


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
