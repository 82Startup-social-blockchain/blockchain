import time
import unittest

from account.account_full import FullAccount
from block.block import Block
from block.blockchain import Blockchain
from genesis.initial_block import create_initial_block
from transaction.transaction_exception import TransactionAccountError, TransactionStakeError, TransactionTipError, TransactionTransferError
from transaction.transaction_type import TransactionType
from transaction.transaction_utils import generate_transaction
from utils.constants import VALIDATION_REWARD
from utils.crypto import get_public_key_hex


class TransactionValidationTestCase(unittest.TestCase):
    def setUp(self):
        self.account1 = FullAccount()
        self.account2 = FullAccount()
        self.account3 = FullAccount()
        self.account4 = FullAccount()

        self.public_key_hex1 = get_public_key_hex(self.account1.private_key.public_key())
        self.public_key_hex2 = get_public_key_hex(self.account2.private_key.public_key())
        self.public_key_hex3 = get_public_key_hex(self.account3.private_key.public_key())
        self.public_key_hex4 = get_public_key_hex(self.account4.private_key.public_key())

        #### Block 0 - ICO ####
        self.block0 = create_initial_block(save_accounts=False)

        # account1 signs empty block to get balance ####
        self.block1 = Block(
            self.block0,
            None,
            [],
            self.public_key_hex1,
            time.time()
        )
        self.block1.sign_block(self.account1.private_key)

        # account1 tips 10 token to account2
        self.transaction1 = generate_transaction(
            self.account1.private_key.public_key(),
            TransactionType.TIP,
            target_public_key=self.account2.private_key.public_key(),
            tx_token=10
        )
        self.transaction1.sign_transaction(self.account1.private_key)

        # account1 transfers 9.5 (+0.5 fee) token to account3
        self.transaction2 = generate_transaction(
            self.account1.private_key.public_key(),
            TransactionType.TRANSFER,
            target_public_key=self.account3.private_key.public_key(),
            tx_token=9.5,
            tx_fee=0.5
        )
        self.transaction2.sign_transaction(self.account1.private_key)

        # account1 stakes 20 tokens
        self.transaction3 = generate_transaction(
            self.account1.private_key.public_key(),
            TransactionType.STAKE,
            tx_token=20
        )
        self.transaction3.sign_transaction(self.account1.private_key)

        #### Block 2 - signed by account2 ####
        self.block2 = Block(
            self.block1,
            None,
            [self.transaction1, self.transaction2, self.transaction3],
            self.public_key_hex2,
            time.time()
        )
        self.block2.sign_block(self.account2.private_key)

        # account1 takes 5 tokens from staking
        self.transaction4 = generate_transaction(
            self.account1.private_key.public_key(),
            TransactionType.STAKE,
            tx_token=-5
        )
        self.transaction4.sign_transaction(self.account1.private_key)

        #### Block 3 - signed by account3 ###
        self.block3 = Block(
            self.block2,
            None,
            [self.transaction4],
            self.public_key_hex3,
            time.time()
        )
        self.block3.sign_block(self.account3.private_key)

        #### Update account ####
        self.blockchain = Blockchain(head=self.block3)
        self.blockchain.validate()

        self.account_dict = dict()
        self.block0.update_account_dict(self.account_dict)
        self.block1.update_account_dict(self.account_dict)
        self.block2.update_account_dict(self.account_dict)
        self.block3.update_account_dict(self.account_dict)

    def test_valid_transactions(self):
        # account1
        self.assertEqual(self.account_dict[self.public_key_hex1].stake, 20 - 5)
        self.assertEqual(self.account_dict[self.public_key_hex1].balance, VALIDATION_REWARD - 10 - 10 - 20 + 5)

        # account2
        self.assertEqual(self.account_dict[self.public_key_hex2].stake, 0)
        self.assertEqual(self.account_dict[self.public_key_hex2].balance, VALIDATION_REWARD + 10)

        # account3
        self.assertEqual(self.account_dict[self.public_key_hex3].stake, 0)
        self.assertEqual(self.account_dict[self.public_key_hex3].balance, VALIDATION_REWARD + 9.5)

        # account4
        self.assertIsNone(self.account_dict.get(self.public_key_hex4, None))

    def test_invalid_stake_transactions(self):
        # Balance insufficient for staking
        transaction_error = generate_transaction(
            self.account1.private_key.public_key(),
            TransactionType.STAKE,
            tx_token=100,
        )
        transaction_error.sign_transaction(self.account1.private_key)
        self.assertRaises(
            TransactionStakeError,
            lambda: transaction_error.validate(self.account_dict.get(self.public_key_hex1, None))
        )

        # Staking account null
        transaction_error = generate_transaction(
            self.account4.private_key.public_key(),
            TransactionType.STAKE,
            tx_token=20,
        )
        transaction_error.sign_transaction(self.account4.private_key)
        self.assertRaises(
            TransactionAccountError,
            lambda: transaction_error.validate(self.account_dict.get(self.public_key_hex4, None))
        )

        # Staking token None
        transaction_error = generate_transaction(
            self.account3.private_key.public_key(),
            TransactionType.STAKE
        )
        transaction_error.sign_transaction(self.account3.private_key)
        self.assertRaises(
            TransactionStakeError,
            lambda: transaction_error.validate(self.account_dict.get(self.public_key_hex3, None))
        )

    def test_invalid_transfer_transaction(self):
        # Transfer negative token
        transaction_error = generate_transaction(
            self.account1.private_key.public_key(),
            TransactionType.TRANSFER,
            tx_token=-10,
            target_public_key=self.account2.private_key.public_key()
        )
        transaction_error.sign_transaction(self.account1.private_key)
        self.assertRaises(
            TransactionTransferError,
            lambda: transaction_error.validate(self.account_dict.get(self.public_key_hex1, None))
        )

        # Transfer token amount null
        transaction_error = generate_transaction(
            self.account1.private_key.public_key(),
            TransactionType.TRANSFER,
            target_public_key=self.account2.private_key.public_key()
        )
        transaction_error.sign_transaction(self.account1.private_key)

        # Transfer account null
        transaction_error = generate_transaction(
            self.account4.private_key.public_key(),
            TransactionType.TRANSFER,
            tx_token=10,
            target_public_key=self.account2.private_key.public_key()
        )
        transaction_error.sign_transaction(self.account4.private_key)
        self.assertRaises(
            TransactionAccountError,
            lambda: transaction_error.validate(self.account_dict.get(self.public_key_hex4, None))
        )

        # Transfer amount greater than balance
        transaction_error = generate_transaction(
            self.account1.private_key.public_key(),
            TransactionType.TRANSFER,
            tx_token=VALIDATION_REWARD,
            target_public_key=self.account2.private_key.public_key()
        )
        transaction_error.sign_transaction(self.account1.private_key)
        self.assertRaises(
            TransactionTransferError,
            lambda: transaction_error.validate(self.account_dict.get(self.public_key_hex1, None))
        )

        # Transfer target null
        transaction_error = generate_transaction(
            self.account1.private_key.public_key(),
            TransactionType.TRANSFER,
            tx_token=10
        )
        transaction_error.sign_transaction(self.account1.private_key)
        self.assertRaises(
            TransactionTransferError,
            lambda: transaction_error.validate(self.account_dict.get(self.public_key_hex1, None))
        )

    def test_invalid_tip_transaction(self):
        # Tip negative token
        transaction_error = generate_transaction(
            self.account1.private_key.public_key(),
            TransactionType.TIP,
            tx_token=-10,
            target_public_key=self.account2.private_key.public_key()
        )
        transaction_error.sign_transaction(self.account1.private_key)
        self.assertRaises(
            TransactionTipError,
            lambda: transaction_error.validate(self.account_dict.get(self.public_key_hex1, None))
        )

        # Tip amount null
        transaction_error = generate_transaction(
            self.account1.private_key.public_key(),
            TransactionType.TIP,
            target_public_key=self.account2.private_key.public_key()
        )
        transaction_error.sign_transaction(self.account1.private_key)
        self.assertRaises(
            TransactionTipError,
            lambda: transaction_error.validate(self.account_dict.get(self.public_key_hex1, None))
        )

        # Tip account null
        transaction_error = generate_transaction(
            self.account4.private_key.public_key(),
            TransactionType.TIP,
            tx_token=10,
            target_public_key=self.account2.private_key.public_key()
        )
        transaction_error.sign_transaction(self.account4.private_key)
        self.assertRaises(
            TransactionAccountError,
            lambda: transaction_error.validate(self.account_dict.get(self.public_key_hex4, None))
        )

        # Tip amount greater than balance
        transaction_error = generate_transaction(
            self.account1.private_key.public_key(),
            TransactionType.TIP,
            tx_token=VALIDATION_REWARD,
            target_public_key=self.account2.private_key.public_key()
        )
        transaction_error.sign_transaction(self.account1.private_key)
        self.assertRaises(
            TransactionTipError,
            lambda: transaction_error.validate(self.account_dict.get(self.public_key_hex1, None))
        )

        # Tip target null
        transaction_error = generate_transaction(
            self.account1.private_key.public_key(),
            TransactionType.TIP,
            tx_token=10,
        )
        transaction_error.sign_transaction(self.account1.private_key)
        self.assertRaises(
            TransactionTipError,
            lambda: transaction_error.validate(self.account_dict.get(self.public_key_hex1, None))
        )
