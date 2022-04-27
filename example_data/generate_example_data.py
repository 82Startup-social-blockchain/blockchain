# generate example data for testing purposes
from datetime import datetime
import json
import os

from account.account import Account
from block.block import Block
from block.blockchain import Blockchain
from transaction.transaction import generate_transaction
from transaction.transaction_type import TransactionContentType, TransactionType
from utils.constants import EXAMPLE_DATA_DIR
from utils.crypto import get_public_key_hex

account1 = Account()
account2 = Account()
account3 = Account()

#### Block1 ####

# account1 post1
transaction1 = generate_transaction(
    account1.private_key.public_key(),
    TransactionType.POST,
    content_type=TransactionContentType.STRING,
    content="Transaction1 - Account1 Post1"
)

# account1 follow account2
transaction2 = generate_transaction(
    account1.private_key.public_key(),
    TransactionType.FOLLOW,
    target_public_key=account2.private_key.public_key()
)

# account2 follow account1
transaction3 = generate_transaction(
    account2.private_key.public_key(),
    TransactionType.FOLLOW,
    target_public_key=account1.private_key.public_key()
)

# Block1 signed by account1
block1 = Block(
    None,
    [transaction1, transaction2, transaction3],
    get_public_key_hex(account1.private_key.public_key()),
    datetime.utcnow()
)
block1.sign_block(account1.private_key)

#### Block2 ####
# account3 follow account1
transaction4 = generate_transaction(
    account3.private_key.public_key(),
    TransactionType.FOLLOW,
    target_public_key=account1.private_key.public_key()
)

# account2 post2
transaction5 = generate_transaction(
    account2.private_key.public_key(),
    TransactionType.POST,
    content_type=TransactionContentType.STRING,
    content="Transaction5 - Account2 Post2"
)

# account3 comment to post1
transaction6 = generate_transaction(
    account1.private_key.public_key(),
    TransactionType.COMMENT,
    content_type=TransactionContentType.STRING,
    content="Transaction4 - Account1 Post1 Comment1",
    target_transaction_hash=transaction1.transaction_hash
)

# Block2 signed by account1
block2 = Block(
    block1,
    [transaction4, transaction5, transaction6],
    get_public_key_hex(account1.private_key.public_key()),
    datetime.utcnow()
)
block2.sign_block(account1.private_key)

#### Block3 ####

# account2 pays 0.4 token to account3
transaction7 = generate_transaction(
    account2.private_key.public_key(),
    TransactionType.PAY,
    target_public_key=account3.private_key.public_key(),
    tx_token=0.4,
    tx_fee=0.01
)

# account1 replies to comment1
transaction8 = generate_transaction(
    account1.private_key.public_key(),
    TransactionType.REPLY,
    content_type=TransactionContentType.STRING,
    content="Transaction8 - Account1 Comment1 Reply1",
    target_transaction_hash=transaction6.transaction_hash
)

# account2 edits post2
transaction9 = generate_transaction(
    account2.private_key.public_key(),
    TransactionType.EDIT_POST,
    content_type=TransactionContentType.STRING,
    content="Transaction9 - Account2 Edit Post2",
    target_transaction_hash=transaction5.transaction_hash
)

# Block3 signed by account2
block3 = Block(
    block2,
    [transaction7, transaction8, transaction9],
    get_public_key_hex(account2.private_key.public_key()),
    datetime.utcnow()
)
block3.sign_block(account1.private_key)

# blockchain with block1, block2
blockchain_length2 = Blockchain(block2)

# blockchain with block1, block2, block3
blockchain_length3 = Blockchain(block3)

if __name__ == '__main__':
    with open(os.path.join(EXAMPLE_DATA_DIR, "blockchain_length2.json"), 'w') as fp:
        json.dump(blockchain_length2.to_dict_list(), fp)

    with open(os.path.join(EXAMPLE_DATA_DIR, "blockchain_length3.json"), 'w') as fp:
        json.dump(blockchain_length3.to_dict_list(), fp)
