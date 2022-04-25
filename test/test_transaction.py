import unittest
import binascii

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.exceptions import InvalidSignature

from account.account import Account
from transaction.transaction import generate_transaction
from transaction.transaction_type import TransactionType, TransactionContentType


class TransactionTestCase(unittest.TestCase):
    def setUp(self):
        self.account1 = Account()

    def test_valid_signature(self):
        transaction = generate_transaction(
            self.account1.private_key.public_key(),
            TransactionType.POST,
            content="Random content",
            content_type=TransactionContentType.STRING
        )
        transaction.sign_transaction(self.account1.private_key)

        transaction.validate()

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
        self.assertRaises(InvalidSignature, transaction.validate)
        transaction.transaction_target.tx_token = None

        # manipulate transaction data - transaction source data
        account2 = Account()
        new_public_key = account2.private_key.public_key()
        new_public_key_hex = binascii.hexlify(
            new_public_key.public_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
        )
        transaction.transaction_source.source_public_key_hex = new_public_key_hex
        self.assertRaises(InvalidSignature, transaction.validate)

    # TODO: test every type of transaction


if __name__ == '__main__':
    unittest.main()
