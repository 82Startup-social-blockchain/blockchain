from datetime import datetime
import os
import logging
import time

from fastapi import APIRouter, FastAPI
from fastapi_utils.tasks import repeat_every

from runner.deps import get_node
from runner.routes import p2p as p2p_route, data as data_route
from runner.routes.service import transaction as transaction_route, account as account_route

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
    if int(time.time()) % 8 == 0:
        # every 10 seconds with the last digit of 0 (0, 10, 20, ...), broadcast validator rand
        validator_rand = node.create_validator_rand()
        await node.broadcast_validator_rand(validator_rand)

    # Create and broadcast block every 10 seconds when the last digit of the second is 5
    if int(time.time()) % 8 == 4:
        if node.is_validator():
            print(f"[INFO {datetime.now().isoformat()}] Chosen as the validator - creating block")
            block = node.create_block()
            await node.broadcast_block(block, os.environ["ADDRESS"])


api_router = APIRouter()
api_router.include_router(p2p_route.router)
api_router.include_router(data_route.router)
api_router.include_router(transaction_route.router)
api_router.include_router(account_route.router)

app.include_router(api_router)
