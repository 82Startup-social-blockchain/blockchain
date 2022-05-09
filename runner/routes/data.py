

from fastapi import APIRouter, Depends
from node.node import Node
from runner.deps import get_node


router = APIRouter(prefix="/data", tags=["data"])


##### Endpoints that show data of nodes and blockchain for utility #####

@router.get("/blockchain")
async def get_blockchain(node: Node = Depends(get_node)):
    # return the current state of blockchain that the node has
    if node.blockchain is None:
        return []

    return node.blockchain.to_dict_list()


@router.get("/blockchain/length")
async def get_blockchain_length(node: Node = Depends(get_node)):
    if node.blockchain is None:
        return 0

    return len(node.blockchain)


# get all accounts stored in the node
@router.get("/accounts")
async def get_accounts(node: Node = Depends(get_node)):
    return {
        public_key_hex: account.to_dict()
        for public_key_hex, account in node.account_dict.items()
    }


@router.get("/transaction-pool")
async def get_transaction_pool(node: Node = Depends(get_node)):
    return {
        tx_hash_hex.decode('utf-8'): tx.to_dict()
        for tx_hash_hex, tx in node.transaction_pool.items()
    }
