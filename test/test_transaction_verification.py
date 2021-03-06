import unittest
import binascii

from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

from account.account_full import FullAccount
from transaction.transaction_type import TransactionType, TransactionContentType
from transaction.transaction_utils import generate_transaction


class TransactionVerificationTestCase(unittest.TestCase):
    def setUp(self):
        self.account1 = FullAccount()

    def test_valid_signature(self):
        transaction = generate_transaction(
            self.account1.private_key.public_key(),
            TransactionType.POST,
            content="Random content",
            content_type=TransactionContentType.STRING
        )
        transaction.sign_transaction(self.account1.private_key)

        transaction.validate(None)

    def test_transaction_manipulation(self):
        transaction = generate_transaction(
            self.account1.private_key.public_key(),
            TransactionType.POST,
            content="Random content",
            content_type=TransactionContentType.STRING
        )
        transaction.sign_transaction(self.account1.private_key)

        # manipulate transaction data - transaction target data
        transaction.transaction_target.tx_token = 1
        self.assertRaises(InvalidSignature, lambda: transaction.validate(None))
        transaction.transaction_target.tx_token = None

        # manipulate transaction data - transaction source data
        account2 = FullAccount()
        new_public_key = account2.private_key.public_key()
        new_public_key_hex = binascii.hexlify(
            new_public_key.public_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
        )
        transaction.transaction_source.source_public_key_hex = new_public_key_hex
        self.assertRaises(InvalidSignature, lambda: transaction.validate(None))

    # TODO: test every type of transaction


if __name__ == '__main__':
    unittest.main()
