import binascii
import unittest
from datetime import datetime

from account.account import Account
from block.block import Block, create_block_from_dict
from transaction.transaction import generate_transaction
from transaction.transaction_type import TransactionContentType, TransactionType
from utils.crypto import get_public_key_hex


class BlockConversionTestCase(unittest.TestCase):
    def setUp(self):
        self.account1 = Account()
        self.account2 = Account()

        self.transaction1 = generate_transaction(
            self.account1.private_key.public_key(),
            TransactionType.POST,
            content="Random content",
            content_type=TransactionContentType.STRING
        )
        self.transaction1.sign_transaction(self.account1.private_key)
        self.tx1_dict = self.transaction1.to_dict()

        self.transaction2 = generate_transaction(
            self.account2.private_key.public_key(),
            TransactionType.COMMENT,
            content="Random comment",
            content_type=TransactionContentType.STRING,
            target_transaction_hash=self.transaction1.transaction_hash,
            tx_fee=1,
            tx_token=0.5
        )
        self.transaction2.sign_transaction(self.account2.private_key)
        self.tx2_dict = self.transaction2.to_dict()

        self.transaction3 = generate_transaction(
            self.account1.private_key.public_key(),
            TransactionType.FOLLOW,
            target_public_key=self.account2.private_key.public_key()
        )
        self.transaction3.sign_transaction(self.account1.private_key)
        self.tx3_dict = self.transaction3.to_dict()

        self.block1 = Block(
            None,
            [self.transaction1, self.transaction2],
            get_public_key_hex(self.account1.private_key.public_key()),
            datetime.utcnow()
        )
        self.block1.sign_block(self.account1.private_key)

        self.block2 = Block(
            self.block1,
            [self.transaction3],
            get_public_key_hex(self.account2.private_key.public_key()),
            datetime.utcnow()
        )
        self.block2.sign_block(self.account2.private_key)

    def test_bidirection_conversion(self):
        self.maxDiff = None
        # block -> block_dict -> block
        block1_dict = self.block1.to_dict()
        block1_same = create_block_from_dict(block1_dict)
        self.assertTrue(self.block1 == block1_same)

        # block_dict -> block -> block_dict
