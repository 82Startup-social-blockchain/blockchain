from typing import Optional

from fastapi import FastAPI

from models import TransactionRequest

app = FastAPI()


@app.post("/validation/block")
async def validate_block():
    # hit this endpoint to broadcast block to this node

    # 1. create block instance
    # 2. validate block
    # 3. add block to blockchain
    # 4. remove activities from activity pool
    pass


@app.post("/validation/transaction")
async def validate_activity():
    # hit this endpoint to broadcast transaction to this node

    # 1. create Activity instance
    # 2. add activity to activity pool
    pass


@app.post("/activity")
async def create_activity(activityRequest: TransactionRequest):
    # User-side API to create activity based on type and content

    # 1. create transaction instance and activity instance from activity request
    # 2. add to activity pool and broadcast to other nodes
    pass


@app.get("/activity/{public_key}")
async def get_activities_by_public_key(
    public_key: str,
    tx_type: Optional[str] = None
):
    # get activities of a user with input public key - filter by multiple query paraemters
    pass
