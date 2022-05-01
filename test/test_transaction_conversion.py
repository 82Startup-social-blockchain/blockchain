import unittest
import binascii

from cryptography.hazmat.primitives import hashes

from account.account_full import FullAccount
from transaction.transaction_utils import create_transaction_from_dict, \
    generate_transaction
from transaction.transaction_type import TransactionType, TransactionContentType
from utils.crypto import get_public_key_hex


class TransactionConversionTestCase(unittest.TestCase):
    def setUp(self):
        self.account1 = FullAccount()
        content = "Random content"
        content_digest = hashes.Hash(hashes.SHA256())
        content_digest.update(content.encode('utf-8'))
        self.content_hash = content_digest.finalize()

        self.transaction = generate_transaction(
            self.account1.private_key.public_key(),
            TransactionType.POST,
            content=content,
            content_type=TransactionContentType.STRING
        )
        self.transaction.sign_transaction(self.account1.private_key)

        self.tx_dict = {
            "source_public_key_hex": get_public_key_hex(self.account1.private_key.public_key()).decode('utf-8'),
            "transaction_type": TransactionType.POST.value,
            "content_type": TransactionContentType.STRING.value,
            "content_hash_hex": binascii.hexlify(self.content_hash).decode('utf-8'),
            "tx_fee": None,
            "target_transaction_hash_hex": None,
            "target_public_key_hex": None,
            "tx_token": None,
            "tx_object": None,
            "signature_hex": binascii.hexlify(self.transaction.signature).decode('utf-8'),
            "transaction_hash_hex": binascii.hexlify(self.transaction.transaction_hash).decode('utf-8'),
            "timestamp": self.transaction.timestamp.isoformat()
        }

    def test_transaction_to_dict(self):
        tx_dict = self.transaction.to_dict()
        self.assertEqual(tx_dict["source_public_key_hex"].encode('utf-8'),
                         get_public_key_hex(self.account1.private_key.public_key()))
        self.assertEqual(tx_dict["content_type"],
                         TransactionContentType.STRING.value)
        self.assertEqual(tx_dict["content_hash_hex"].encode('utf-8'),
                         binascii.hexlify(self.content_hash))
        self.assertIs(tx_dict["tx_fee"], None)
        self.assertEqual(binascii.unhexlify(tx_dict['signature_hex'].encode('utf-8')),
                         self.transaction.signature)

    def test_dict_to_transaction(self):
        transaction = create_transaction_from_dict(self.tx_dict)
        self.assertEqual(transaction.signature,
                         binascii.unhexlify(self.tx_dict["signature_hex"].encode('utf-8'))),
        self.assertEqual(transaction.transaction_source.tx_fee,
                         self.tx_dict["tx_fee"])
        self.assertEqual(transaction.transaction_target.tx_token,
                         self.tx_dict["tx_token"])
        self.assertEqual(transaction.transaction_source.content_hash,
                         binascii.unhexlify(self.tx_dict["content_hash_hex"].encode('utf-8')))

    def test_bidirection_conversion(self):
        self.maxDiff = None
        # transaction -> tx_dict -> transaction
        tx_dict = self.transaction.to_dict()
        transaction_same = create_transaction_from_dict(tx_dict)
        self.assertTrue(self.transaction == transaction_same)

        # tx_dict -> transaction -> tx_dict
        transaction = create_transaction_from_dict(self.tx_dict)
        tx_dict_same = transaction.to_dict()
        self.assertDictEqual(self.tx_dict, tx_dict_same)
