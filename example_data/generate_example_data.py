# generate example data for testing purposes
from datetime import datetime
import json
import os

from block.block import Block
from block.blockchain import Blockchain
from example_data.example_account import ExampleAccount
from transaction.transaction import generate_transaction
from transaction.transaction_type import TransactionContentType, TransactionType
from utils.constants import EXAMPLE_DATA_DIR
from utils.crypto import get_public_key_hex

account1 = ExampleAccount()
account2 = ExampleAccount()
account3 = ExampleAccount()

#### Block1 ####

# account1 post1
transaction1 = generate_transaction(
    account1.private_key.public_key(),
    TransactionType.POST,
    content_type=TransactionContentType.STRING,
    content="Transaction1 - Account1 Post1"
)
transaction1.sign_transaction(account1.private_key)

# account1 follow account2
transaction2 = generate_transaction(
    account1.private_key.public_key(),
    TransactionType.FOLLOW,
    target_public_key=account2.private_key.public_key()
)
transaction2.sign_transaction(account1.private_key)

# account2 follow account1
transaction3 = generate_transaction(
    account2.private_key.public_key(),
    TransactionType.FOLLOW,
    target_public_key=account1.private_key.public_key()
)
transaction3.sign_transaction(account2.private_key)

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
transaction4.sign_transaction(account3.private_key)

# account2 post2
transaction5 = generate_transaction(
    account2.private_key.public_key(),
    TransactionType.POST,
    content_type=TransactionContentType.STRING,
    content="Transaction5 - Account2 Post2"
)
transaction5.sign_transaction(account2.private_key)

# account3 comment to post1
transaction6 = generate_transaction(
    account1.private_key.public_key(),
    TransactionType.COMMENT,
    content_type=TransactionContentType.STRING,
    content="Transaction4 - Account1 Post1 Comment1",
    target_transaction_hash=transaction1.transaction_hash
)
transaction6.sign_transaction(account1.private_key)

# Block2 signed by account1
block2 = Block(
    block1,
    [transaction4, transaction5, transaction6],
    get_public_key_hex(account1.private_key.public_key()),
    datetime.utcnow()
)
block2.sign_block(account1.private_key)

#### Block3 ####

# account3 tips 0.4 token to account2
transaction7 = generate_transaction(
    account3.private_key.public_key(),
    TransactionType.TIP,
    target_public_key=account2.private_key.public_key(),
    tx_token=0.4,
    tx_fee=0.01
)
transaction7.sign_transaction(account3.private_key)

# account1 replies to comment1
transaction8 = generate_transaction(
    account1.private_key.public_key(),
    TransactionType.REPLY,
    content_type=TransactionContentType.STRING,
    content="Transaction8 - Account1 Comment1 Reply1",
    target_transaction_hash=transaction6.transaction_hash
)
transaction8.sign_transaction(account1.private_key)

# account2 edits post2
transaction9 = generate_transaction(
    account2.private_key.public_key(),
    TransactionType.EDIT_POST,
    content_type=TransactionContentType.STRING,
    content="Transaction9 - Account2 Edit Post2",
    target_transaction_hash=transaction5.transaction_hash
)
transaction9.sign_transaction(account2.private_key)

# Block3 signed by account2
block3 = Block(
    block2,
    [transaction7, transaction8, transaction9],
    get_public_key_hex(account2.private_key.public_key()),
    datetime.utcnow()
)
block3.sign_block(account2.private_key)

# blockchain with block1, block2
blockchain_length2 = Blockchain(block2)

# blockchain with block1, block2, block3
blockchain_length3 = Blockchain(block3)

### Sample Transactions ###

# account3 posts post3
transaction10 = generate_transaction(
    account3.private_key.public_key(),
    TransactionType.POST,
    content_type=TransactionContentType.STRING,
    content="Transaction10 - Account3 Post3",
)
transaction10.sign_transaction(account3.private_key)

# account2 comments to post3
transaction11 = generate_transaction(
    account2.private_key.public_key(),
    TransactionType.COMMENT,
    content_type=TransactionContentType.STRING,
    content="Transcation11 - Account2 Post3 Comment1"
)
transaction11.sign_transaction(account2.private_key)

# account2 sends token to account1
transaction12 = generate_transaction(
    account2.private_key.public_key(),
    TransactionType.TRANSFER,
    tx_fee=0.01,
    target_public_key=account1.private_key.public_key(),
    tx_token=1.2
)
transaction12.sign_transaction(account2.private_key)

# Block4 signed by account1
block4 = Block(
    block3,
    [transaction10, transaction11, transaction12],
    get_public_key_hex(account1.private_key.public_key()),
    datetime.utcnow()
)
block4.sign_block(account1.private_key)

if __name__ == '__main__':
    with open(os.path.join(EXAMPLE_DATA_DIR, "blockchain_length2.json"), 'w') as fp:
        json.dump(blockchain_length2.to_dict_list(), fp)

    with open(os.path.join(EXAMPLE_DATA_DIR, "blockchain_length3.json"), 'w') as fp:
        json.dump(blockchain_length3.to_dict_list(), fp)

    with open(os.path.join(EXAMPLE_DATA_DIR, "block4.json"), 'w') as fp:
        json.dump(block4.to_dict(), fp)

    with open(os.path.join(EXAMPLE_DATA_DIR, "transaction10.json"), 'w') as fp:
        json.dump(transaction10.to_dict(), fp)

    with open(os.path.join(EXAMPLE_DATA_DIR, "transaction11.json"), 'w') as fp:
        json.dump(transaction11.to_dict(), fp)
