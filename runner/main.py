from datetime import datetime
import os
import logging
import time
from typing import Optional

from fastapi import APIRouter, Depends, FastAPI
from fastapi_utils.tasks import repeat_every

from node.node import Node
from runner.deps import get_node, get_public_key_hex
from runner.routes import p2p
from utils import constants

FORMAT = "%(levelname)s:     %(message)s"
logging.basicConfig(format=FORMAT, level=logging.INFO)
logger = logging.getLogger(__name__)

assert "ADDRESS" in os.environ
assert "ACCOUNT_KEY_FILE_NAME" in os.environ

app = FastAPI()


@app.on_event("startup")
@repeat_every(seconds=1, raise_exceptions=True)  # turn on raise_exceptions True for debugging
async def choose_validator():
    # TODO: make it so that node validation can be asynchronous (?)
    # TODO: add retry mechanism to deal with temporary network down issue?
    node = get_node()

    # Broadcast validator rand every 10 seconds when the last digit of the second is 0
    if int(time.time()) % 6 == 0:
        # every 10 seconds with the last digit of 0 (0, 10, 20, ...), broadcast validator rand
        validator_rand = node.create_validator_rand()
        await node.broadcast_validator_rand(validator_rand)

    # Create and broadcast block every 10 seconds when the last digit of the second is 5
    if int(time.time()) % 6 == 3:
        if node.is_validator():
            print(f"[INFO {datetime.now().isoformat()}] Chosen as the validator - creating block")
            block = node.create_block()
            await node.broadcast_block(block, os.environ["ADDRESS"])


##### Endpoints that services call #####

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


##### Endpoints to show data - useful for development #####

@app.get(constants.BLOCKCHAIN_REQUEST_PATH)
async def get_blockchain(node: Node = Depends(get_node)):
    # return the current state of blockchain that the node has
    if node.blockchain is None:
        return []

    return node.blockchain.to_dict_list()


@app.get(constants.ACCOUNTS_PATH)
async def get_accounts(node: Node = Depends(get_node)):
    # return account data that the node holds
    return {
        public_key_hex: account.to_dict()
        for public_key_hex, account in node.account_dict.items()
    }


@app.get("/transaction-pool")
async def get_transaction_pool(node: Node = Depends(get_node)):
    return {
        tx_hash_hex.decode('utf-8'): tx.to_dict()
        for tx_hash_hex, tx in node.transaction_pool.items()
    }

api_router = APIRouter()

api_router.include_router(p2p.router)

app.include_router(api_router)
