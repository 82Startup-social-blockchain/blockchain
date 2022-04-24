import unittest
import binascii
from typing import Optional

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.exceptions import InvalidSignature

from account.account import Account
from transaction.transaction import TransactionSource, TransactionTarget, Transaction
from transaction.transaction_type import TransactionType, TransactionContentType


def get_sample_transaction(
    public_key: ec.EllipticCurvePublicKey,
    transaction_type: TransactionType,
    content: Optional[str] = None,
    content_type: Optional[TransactionContentType] = None,
    target_transaction_hash: Optional[bytes] = None,
    target_public_key: Optional[ec.EllipticCurvePublicKey] = None,
    amount: Optional[float] = None
):
    # create TransactionSource instance
    content_hash = hashes.Hash(hashes.SHA256())
    content_hash.update(content.encode('utf-8'))

    public_key_serialized = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    public_key_hex = binascii.hexlify(public_key_serialized)

    transaction_source = TransactionSource(
        public_key_hex,
        transaction_type,
        content_type=content_type,
        content_hash=content_hash.finalize()
    )

    # create TransactionTarget instance
    if target_transaction_hash is not None:
        target_transaction_hash_hex = binascii.hexlify(target_transaction_hash)
    else:
        target_transaction_hash_hex = None

    if target_public_key is not None:
        target_public_key_serialized = target_public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        target_public_key_hex = binascii.hexlify(target_public_key_serialized)
    else:
        target_public_key_hex = None

    transaction_target = TransactionTarget(
        target_transaction_hash_hex=target_transaction_hash_hex,
        target_public_key_hex=target_public_key_hex,
        amount=amount
    )

    return Transaction(transaction_source, transaction_target)


class SignatureTestCase(unittest.TestCase):
    def setUp(self):
        self.account1 = Account()

    def test_valid_signature(self):
        transaction = get_sample_transaction(
            self.account1.private_key.public_key(),
            TransactionType.POST,
            content="Random content",
            content_type=TransactionContentType.STRING
        )
        transaction.sign_transaction(self.account1.private_key)

        transaction.validate_transaction()

    def test_invalid_signature(self):
        transaction = get_sample_transaction(
            self.account1.private_key.public_key(),
            TransactionType.POST,
            content="Random content",
            content_type=TransactionContentType.STRING
        )
        transaction.sign_transaction(self.account1.private_key)

        # manipulate transaction data
        transaction.transaction_target.amount = 1
        self.assertRaises(InvalidSignature, transaction.validate_transaction)


if __name__ == '__main__':

    # try
    unittest.main()
