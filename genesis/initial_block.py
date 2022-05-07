
# setup 10 accounts for ICO

import binascii
import os
import time
import json

from cryptography.hazmat.primitives import serialization

from account.account_full import FullAccount
from block.block import Block
from transaction.transaction_type import TransactionType
from transaction.transaction_utils import generate_transaction
from utils.constants import ICO_PUBLIC_KEY_FILE, ICO_TOKENS
from utils.crypto import get_public_key_hex


def create_initial_block(save_accounts=True, load_accounts=False) -> Block:
    public_keys = []

    if save_accounts:
        ico_accounts = [FullAccount() for _ in range(4)]
        for account in ico_accounts:
            public_keys.append(get_public_key_hex(account.private_key.public_key()))

        with open(ICO_PUBLIC_KEY_FILE, 'w') as fp:
            json.dump(list(map(lambda x: x.decode('utf-8'), public_keys)), fp)
        print(f'[INFO] Saved public keys to {ICO_PUBLIC_KEY_FILE}')
        # save private keys to json file - only for running on local host
        # TODO: think about how to accomlish the effect in deployment
        for idx, account in enumerate(ico_accounts):
            private_key_serialized = account.private_key.private_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            private_key_hex = binascii.hexlify(private_key_serialized).decode('utf-8')
            with open(os.path.join(os.getcwd(), "genesis", f"account_{idx}.json"), 'w') as fp:
                json.dump(private_key_hex, fp)
        print(f'[INFO] Saved private keys')

    elif load_accounts:
        ico_accounts = []
        with open(ICO_PUBLIC_KEY_FILE, 'r') as fp:
            public_keys = json.load(fp)
        for idx in range(len(public_keys)):
            with open(os.path.join(os.getcwd(), "genesis", f"account_{idx}.json"), 'r') as fp:
                private_key_serialized = binascii.unhexlify(json.load(fp).encode('utf-8'))
                private_key = serialization.load_der_private_key(private_key_serialized, None)
                ico_accounts.append(FullAccount(private_key=private_key))
        # print(f'[INFO] Loaded private keys')

    else:
        ico_accounts = [FullAccount() for _ in range(4)]

    transactions = list()
    for account in ico_accounts:
        transaction = generate_transaction(
            account.private_key.public_key(),
            TransactionType.ICO,
            tx_token=ICO_TOKENS
        )
        transaction.sign_transaction(account.private_key)
        transactions.append(transaction)

    block = Block(
        None,
        None,
        transactions,
        get_public_key_hex(ico_accounts[0].private_key.public_key()),
        time.time()
    )
    block.sign_block(ico_accounts[0].private_key)

    return block


if __name__ == '__main__':
    create_initial_block()
