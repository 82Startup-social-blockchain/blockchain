import binascii
from typing import List, Optional

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import APIRouter, Depends

from runner.models.account import Account
from node.node import Node
from runner.deps import get_node
from runner.models.transaction import Transaction


router = APIRouter(prefix="/service/accounts", tags=["service_accounts"])


# get balance and stake for all accounts
@router.get("/", response_model=List[Account])
async def get_accounts(node: Node = Depends(get_node)):
    return list(map(lambda acct: acct.to_dict(), node.account_dict.values()))


# get account information of the input account
@router.get("/{public_key_hex}", response_model=Optional[Account])
async def get_account(
    public_key_hex: str,
    node: Node = Depends(get_node)
):
    public_key_hex = public_key_hex.encode('utf-8')
    for acct_public_key_hex in node.account_dict:
        if acct_public_key_hex == public_key_hex:
            return node.account_dict[acct_public_key_hex].to_dict()
    return None


# get transactions by the input public_key_hex - desc order
@router.get("/{public_key_hex}/transactions", response_model=List[Transaction])
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


# create account - return private key encoded hex
@router.post("/")
async def create_account():
    private_key = ec.generate_private_key(ec.SECP384R1())
    private_key_serialized = private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    private_key_hex = binascii.hexlify(private_key_serialized).decode('utf-8')

    return private_key_hex
