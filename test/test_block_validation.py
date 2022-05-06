import time
import unittest

from cryptography.exceptions import InvalidSignature

from block.block import Block
from account.account_full import FullAccount
from transaction.transaction_type import TransactionContentType, TransactionType
from transaction.transaction_utils import generate_transaction
from utils.crypto import get_public_key_hex


class BlockValidationTestCase(unittest.TestCase):
    def setUp(self):
        self.account1 = FullAccount()
        self.account2 = FullAccount()

        self.transaction1 = generate_transaction(
            self.account1.private_key.public_key(),
            TransactionType.POST,
            content="Random content",
            content_type=TransactionContentType.STRING
        )
        self.transaction1.sign_transaction(self.account1.private_key)

        self.transaction2 = generate_transaction(
            self.account2.private_key.public_key(),
            TransactionType.COMMENT,
            content="Random comment",
            content_type=TransactionContentType.STRING,
            target_transaction_hash=self.transaction1.transaction_hash
        )
        self.transaction2.sign_transaction(self.account2.private_key)

        self.transaction3 = generate_transaction(
            self.account1.private_key.public_key(),
            TransactionType.FOLLOW,
            target_public_key=self.account2.private_key.public_key()
        )
        self.transaction3.sign_transaction(self.account1.private_key)

        self.block1 = Block(
            None,
            None,
            [self.transaction1, self.transaction2],
            get_public_key_hex(self.account1.private_key.public_key()),
            time.time()
        )
        self.block1.sign_block(self.account1.private_key)

        self.block2 = Block(
            self.block1,
            None,
            [self.transaction3],
            get_public_key_hex(self.account2.private_key.public_key()),
            time.time()
        )
        self.block2.sign_block(self.account2.private_key)

    def test_valid_signature(self):
        self.block1.validate({})
        self.block2.validate({})

    def test_transaction_manipulation(self):
        self.transaction3.transaction_source.transaction_type = TransactionType.UNFOLLOW

        self.block1.validate({})
        self.assertRaises(InvalidSignature, lambda: self.block2.validate({}))

        self.transaction3.transaction_source.transaction_type = TransactionType.FOLLOW

    def test_block_manipulation(self):
        # try unsigning
        self.block1.signature = None

        self.assertRaises(InvalidSignature, lambda: self.block1.validate({}))
        self.block2.validate({})

        self.block1.sign_block(self.account1.private_key)

        # try setting block2 previous hash to None
        self.block2.previous_block = None

        self.block1.validate({})
        self.assertRaises(InvalidSignature, lambda: self.block2.validate({}))

        self.block2.previous_block = self.block1


if __name__ == '__main__':
    unittest.main()
