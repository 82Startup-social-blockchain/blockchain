
import binascii
import os
from typing import List, Optional
from fastapi import APIRouter, Depends

from node.node import Node
from runner.deps import get_node
from runner.models.transaction import Transaction, TransactionCreateRequest
from transaction.transaction_utils import create_transaction_from_request, get_content_from_transaction

router = APIRouter(prefix="/service/transactions", tags=["service_transactions"])


##### Endpoints that services call to get/post transaction data needed for service #####


# post transactions to blockchain
@router.post("/", response_model=Transaction)
async def create_transaction(
    tx_create_request: TransactionCreateRequest,
    node: Node = Depends(get_node)
):
    transaction = create_transaction_from_request(tx_create_request)
    await node.accept_transaction(transaction, os.environ["ADDRESS"])

    return transaction.to_dict()


# get transaction information for the given transaction_hash_hex
@router.get("/{transaction_hash_hex}", response_model=Optional[Transaction])
async def get_transaction(
    transaction_hash_hex: str,
    node: Node = Depends(get_node)
):
    transaction_hash_hex = transaction_hash_hex.encode('utf-8')
    curr_block = node.blockchain.head
    while curr_block is not None:
        for tx in curr_block.transaction_list:
            if binascii.hexlify(tx.transaction_hash) == transaction_hash_hex:
                return tx.to_dict()
        curr_block = curr_block.previous_block

    return None


# get all children transactions of the given transaction_hash_hex - desc order
@router.get("/{transaction_hash_hex}/children", response_model=List[Transaction])
async def get_transaction_children(
    transaction_hash_hex: str,
    node: Node = Depends(get_node)
):
    transactions = []
    transaction_hash_hex = transaction_hash_hex.encode('utf-8')

    curr_block = node.blockchain.head
    while curr_block is not None:
        for tx in curr_block.transaction_list:
            if tx.transaction_target.target_transaction_hash_hex == transaction_hash_hex:
                transactions.append(tx.to_dict())
        curr_block = curr_block.previous_block

    return transactions


# get the content
@router.get("/{transaction_hash_hex}/content")
async def get_transaction_content(
    transaction_hash_hex: str,
    encryption_key: Optional[str] = None,
    node: Node = Depends(get_node)
):
    transaction_hash_hex = transaction_hash_hex.encode('utf-8')

    curr_block = node.blockchain.head
    while curr_block is not None:
        for tx in curr_block.transaction_list:
            if binascii.hexlify(tx.transaction_hash) == transaction_hash_hex:
                content = get_content_from_transaction(tx, encryption_key)
                return content
        curr_block = curr_block.previous_block

    return None
