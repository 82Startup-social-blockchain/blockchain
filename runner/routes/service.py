import binascii
import os
from typing import List, Optional
from fastapi import APIRouter, Depends

from node.node import Node
from runner.deps import get_node
from runner.models.account import Account
from runner.models.transaction import Transaction, TransactionCreateRequest
from transaction.transaction_utils import create_transaction_from_request


router = APIRouter(prefix="/service", tags=["service"])


##### Endpoints that services call to get data needed for service #####

# get all activities by account with requested public key hex
@router.get("/transactions/{transaction_hash_hex}", response_model=Optional[Transaction])
async def get_transaction(
    transaction_hash_hex: str,
    node: Node = Depends(get_node)
):
    transaction_hash_hex = transaction_hash_hex.encode('utf-8')
    curr_block = node.blockchain.head
    while curr_block is not None:
        for tx in curr_block.transaction_list:
            print(f'***** {binascii.hexlify(tx.transaction_hash)} ? {transaction_hash_hex}')
            if binascii.hexlify(tx.transaction_hash) == transaction_hash_hex:
                return tx.to_dict()
        curr_block = curr_block.previous_block

    return None


# post transactions to blockchain
@router.post("/transactions", response_model=Transaction)
async def create_transaction(
    tx_create_request: TransactionCreateRequest,
    node: Node = Depends(get_node)
):
    transaction = create_transaction_from_request(tx_create_request)
    await node.accept_transaction(transaction, os.environ["ADDRESS"])

    return transaction.to_dict()


# get balance and stake for all accounts
@router.get("/accounts", response_model=List[Account])
async def get_accounts(node: Node = Depends(get_node)):
    return node.account_dict.values()


# get account information of the input account
@router.get("/accounts/{public_key_hex}", response_model=Optional[Account])
async def get_account(
    public_key_hex: str,
    node: Node = Depends(get_node)
):
    public_key_hex = public_key_hex.encode('utf-8')
    for acct_public_key_hex in node.account_dict:
        if acct_public_key_hex == public_key_hex:
            return node.account_dict[acct_public_key_hex].to_dict()
    return None


@router.get("/accounts/{public_key_hex}/transactions", response_model=List[Transaction])
async def get_account_transactions(
    public_key_hex: str,
    node: Node = Depends(get_node)
):
    transactions = []
    public_key_hex = public_key_hex.encode('utf-8')
    curr_block = node.blockchain.head
    while curr_block is not None:
        for tx in curr_block.transaction_list:
            if public_key_hex == tx.transaction_source.source_public_key_hex:
                transactions.append(tx.to_dict())
        curr_block = curr_block.previous_block

    return transactions
