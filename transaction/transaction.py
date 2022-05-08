import binascii
import time
from typing import Optional, Any
import json

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.exceptions import InvalidSignature
from account.account import Account
from validation.transaction.task import TransactionValidationTask
from .transaction_type import TransactionType, TransactionContentType


class TransactionSource:
    def __init__(
        self,
        # public key of the content creator - serialized to DER converted to hex
        source_public_key_hex: bytes,
        transaction_type: TransactionType,
        content_type: Optional[TransactionContentType] = None,
        content_hash: Optional[bytes] = None,
        tx_fee: Optional[float] = None
    ):
        self.source_public_key_hex = source_public_key_hex
        self.transaction_type = transaction_type
        self.content_type = content_type

        # S3 path => in actual blockchain, it will be IPFS address
        self.content_hash = content_hash

        self.tx_fee = tx_fee  # transaction fee if any

    def __str__(self):
        return json.dumps(self.to_dict())

    def __eq__(self, other: 'TransactionSource'):
        return self.source_public_key_hex == other.source_public_key_hex and \
            self.transaction_type == other.transaction_type and \
            self.content_type == other.content_type and \
            self.content_hash == other.content_hash and \
            self.tx_fee == other.tx_fee

    def to_dict(self) -> dict:
        # convert to json serializable dictionary
        if self.content_hash is not None:
            content_hash_hex = binascii.hexlify(self.content_hash).decode('utf-8')
        else:
            content_hash_hex = None

        return {
            "source_public_key_hex": self.source_public_key_hex.decode('utf-8'),
            "transaction_type": self.transaction_type,
            "content_type": self.content_type,
            "content_hash_hex": content_hash_hex,
            "tx_fee": self.tx_fee
        }


class TransactionTarget:
    def __init__(
        self,
        # hex value (binascii.hexlify) of parent transaction hash
        target_transaction_hash_hex: Optional[bytes] = None,
        # public key of the recipient - seralized to DER and converted to hex
        target_public_key_hex: Optional[bytes] = None,
        tx_token: Optional[float] = None,  # amount of token transfered
        tx_object: Optional[Any] = None,  # TODO: define type of this object
    ):
        self.target_transaction_hash_hex = target_transaction_hash_hex
        self.target_public_key_hex = target_public_key_hex
        self.tx_token = tx_token
        self.tx_object = tx_object

    def __str__(self):
        return json.dumps(self.to_dict())

    def __eq__(self, other: 'TransactionTarget'):
        return self.target_transaction_hash_hex == other.target_transaction_hash_hex and \
            self.target_public_key_hex == other.target_public_key_hex and \
            self.tx_token == other.tx_token and \
            self.tx_object == other.tx_object

    def to_dict(self) -> dict:
        # convert to json serializable dictionary
        return {
            "target_transaction_hash_hex": self.target_transaction_hash_hex.decode('utf-8')
            if self.target_transaction_hash_hex is not None else None,
            "target_public_key_hex": self.target_public_key_hex.decode('utf-8')
            if self.target_public_key_hex is not None else None,
            "tx_token": self.tx_token,
            "tx_object": self.tx_object,
        }


class Transaction:
    # Transaction object is the object being stored in blocks
    def __init__(
        self,
        transaction_source: TransactionSource,
        transaction_target: TransactionTarget,
        timestamp: Optional[float] = time.time()
    ):
        self.transaction_source = transaction_source
        self.transaction_target = transaction_target

        if timestamp is None:
            self.timestamp = time.time()
        else:
            self.timestamp = timestamp

        # transaction hash is used as an id of the transaction (e.g. finding the post for a comment)
        self.transaction_hash = self._get_hash()

        self.signature = None

    def __str__(self):
        return json.dumps(self.to_dict())

    def __eq__(self, other: 'Transaction'):
        return self.transaction_hash == other.transaction_hash and \
            self.signature == other.signature

    def _to_presigned_dict(self) -> dict:
        # convert to json serializable dictionary that will be hashed and signed
        return {
            **self.transaction_source.to_dict(),
            **self.transaction_target.to_dict(),
            "timestamp": self.timestamp
        }

    def to_dict(self) -> dict:
        tx_dict = self._to_presigned_dict()

        # Add signature hex
        if self.signature is not None:
            signature_hex = binascii.hexlify(self.signature).decode('utf-8')
        else:
            signature_hex = None
        tx_dict["signature_hex"] = signature_hex if signature_hex is not None else None

        # Add transaction hash
        tx_dict["transaction_hash_hex"] = binascii.hexlify(self.transaction_hash).decode('utf-8')

        return tx_dict

    def _get_hash(self) -> bytes:
        digest = hashes.Hash(hashes.SHA256())
        digest.update(json.dumps(self._to_presigned_dict()).encode('utf-8'))
        return digest.finalize()

    def sign_transaction(self, private_key: ec.EllipticCurvePrivateKey):
        self.signature = private_key.sign(
            json.dumps(self._to_presigned_dict()).encode('utf-8'),
            ec.ECDSA(hashes.SHA256())
        )

    def _verify_transaction(self) -> None:
        # If the signature is not verified, throw InvalidSignature excxeption
        if self.signature is None:
            raise InvalidSignature
        public_key_serialized = binascii.unhexlify(self.transaction_source.source_public_key_hex)
        public_key = serialization.load_der_public_key(public_key_serialized)
        public_key.verify(
            self.signature,
            json.dumps(self._to_presigned_dict()).encode('utf-8'),
            ec.ECDSA(hashes.SHA256())
        )

    def validate(self, account: Account, is_initial_block: bool = False) -> None:
        # verify transaction signature
        self._verify_transaction()

        # validate the transaction itself
        transaction_validation = TransactionValidationTask(self, account, is_initial_block=is_initial_block)
        transaction_validation.run()

# Notes
# We use hex so that it can be easily decoded to string and jsonified and so that
# the json object can be used for hashing
