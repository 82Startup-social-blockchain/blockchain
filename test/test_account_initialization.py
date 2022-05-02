import time
import unittest

from account.account_full import FullAccount
from block.block import Block
from block.blockchain import Blockchain
from test.test_node import TestNode
from transaction.transaction_type import TransactionContentType, TransactionType
from transaction.transaction_utils import generate_transaction
from utils.crypto import get_public_key_hex


class AccountInitialization(unittest.TestCase):
    def setUp(self):
        self.account1 = FullAccount()
        self.account2 = FullAccount()
        self.account3 = FullAccount()
        self.account4 = FullAccount()
        self.accounts = [
            self.account1, self.account2, self.account3, self.account4
        ]

        self.account1_stakes = [3.15]
        self.account2_stakes = [5.1, 4.9]
        self.account3_stakes = [10.05]
        self.account4_stakes = [1.5]
        self.account_stakes = [
            self.account1_stakes, self.account2_stakes,
            self.account3_stakes, self.account4_stakes
        ]

        # account1 posts
        self.transaction1 = generate_transaction(
            self.account1.private_key.public_key(),
            TransactionType.POST,
            content="Random content",
            content_type=TransactionContentType.STRING
        )
        self.transaction1.sign_transaction(self.account1.private_key)

        # account2 stakes 5.1 tokens
        self.transaction2 = generate_transaction(
            self.account2.private_key.public_key(),
            TransactionType.STAKE,
            tx_token=self.account2_stakes[0]
        )
        self.transaction2.sign_transaction(self.account2.private_key)

        # account3 stakes 10.05 tokens
        self.transaction3 = generate_transaction(
            self.account3.private_key.public_key(),
            TransactionType.STAKE,
            tx_token=self.account3_stakes[0]
        )
        self.transaction3.sign_transaction(self.account3.private_key)

        # Block1 signed by account1
        self.block1 = Block(
            None,
            [self.transaction1, self.transaction2, self.transaction3],
            get_public_key_hex(self.account1.private_key.public_key()),
            time.time()
        )
        self.block1.sign_block(self.account1.private_key)

        # account1 stakes 3.15 tokens
        self.transaction4 = generate_transaction(
            self.account1.private_key.public_key(),
            TransactionType.STAKE,
            tx_token=self.account1_stakes[0]
        )
        self.transaction4.sign_transaction(self.account1.private_key)

        # account2 stakes 4.9 coins
        self.transaction5 = generate_transaction(
            self.account2.private_key.public_key(),
            TransactionType.STAKE,
            tx_token=self.account2_stakes[1]
        )
        self.transaction5.sign_transaction(self.account2.private_key)

        # account3 sends 2.4 coins to account1
        self.transaction6 = generate_transaction(
            self.account3.private_key.public_key(),
            TransactionType.TRANSFER,
            tx_token=2.4,
            tx_fee=0.1,
            target_public_key=self.account1.private_key.public_key()
        )
        self.transaction6.sign_transaction(self.account3.private_key)

        # Block2 signed by account2
        self.block2 = Block(
            self.block1,
            [self.transaction4, self.transaction5, self.transaction6],
            get_public_key_hex(self.account2.private_key.public_key()),
            time.time()
        )
        self.block2.sign_block(self.account2.private_key)

        # account4 stakes 1.5 tokens
        self.transaction7 = generate_transaction(
            self.account4.private_key.public_key(),
            TransactionType.STAKE,
            tx_token=self.account4_stakes[0]
        )
        self.transaction7.sign_transaction(self.account4.private_key)

        # account1 sends 3.2 coins to account4
        self.transaction8 = generate_transaction(
            self.account1.private_key.public_key(),
            TransactionType.TRANSFER,
            tx_token=3.2,
            tx_fee=0.11,
            target_public_key=self.account4.private_key.public_key()
        )
        self.transaction8.sign_transaction(self.account1.private_key)

        # account3 sends 7.1 coins to account1
        self.transaction9 = generate_transaction(
            self.account3.private_key.public_key(),
            TransactionType.TRANSFER,
            tx_token=7.1,
            tx_fee=0.12,
            target_public_key=self.account1.private_key.public_key()
        )
        self.transaction9.sign_transaction(self.account3.private_key)

        # block3 signed by account1
        self.block3 = Block(
            self.block2,
            [self.transaction7, self.transaction8, self.transaction9],
            get_public_key_hex(self.account1.private_key.public_key()),
            time.time()
        )
        self.block3.sign_block(self.account1.private_key)

        self.blockchain_length1 = Blockchain(self.block1)
        self.blockchain_length2 = Blockchain(self.block2)
        self.blockchain_length3 = Blockchain(self.block3)

    def test_accounts_on_init_length1(self):
        node = TestNode(self.blockchain_length1)

        self.assertEqual(
            node.account_dict[get_public_key_hex(
                self.account1.private_key.public_key())].stake, 0
        )
        self.assertEqual(
            node.account_dict[get_public_key_hex(
                self.account2.private_key.public_key())].stake,
            self.account2_stakes[0])
        self.assertEqual(
            node.account_dict[get_public_key_hex(
                self.account3.private_key.public_key())].stake,
            self.account3_stakes[0]
        )

    def test_accounts_on_init_length2(self):
        node = TestNode(self.blockchain_length3)

        for idx, account in enumerate(self.accounts):
            self.assertEqual(
                node.account_dict[get_public_key_hex(
                    account.private_key.public_key())].stake,
                sum(self.account_stakes[idx])
            )
