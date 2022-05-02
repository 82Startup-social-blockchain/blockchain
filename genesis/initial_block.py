
# setup 10 accounts for ICO

import time
import json

from account.account_full import FullAccount
from block.block import Block
from transaction.transaction_type import TransactionType
from transaction.transaction_utils import generate_transaction
from utils.constants import ICO_PUBLIC_KEY_FILE, ICO_TOKENS
from utils.crypto import get_public_key_hex

ICO_ACCOUNTS = [FullAccount() for _ in range(10)]


def create_initial_block() -> Block:

    public_keys = []
    for account in ICO_ACCOUNTS:
        public_keys.append(get_public_key_hex(account.private_key.public_key()))
    with open(ICO_PUBLIC_KEY_FILE, 'w') as fp:
        json.dump(list(map(lambda x: x.decode('utf-8'), public_keys)), fp)

    transactions = list()

    for account in ICO_ACCOUNTS:
        transaction = generate_transaction(
            account.private_key.public_key(),
            TransactionType.ICO,
            tx_token=ICO_TOKENS
        )
        transaction.sign_transaction(account.private_key)
        transactions.append(transaction)

    block = Block(
        None,
        transactions,
        get_public_key_hex(ICO_ACCOUNTS[0].private_key.public_key()),
        time.time()
    )
    block.sign_block(ICO_ACCOUNTS[0].private_key)

    return block
