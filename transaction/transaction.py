import binascii
import datetime
from typing import Optional
import json

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.exceptions import InvalidSignature

from .transaction_type import TransactionType, TransactionContentType


class TransactionSource:
    def __init__(
        self,
        # public key of the content creator - serialized to DER converted to hex
        source_public_key_hex: bytes,
        transaction_type: TransactionType,
        content_type: Optional[TransactionContentType] = None,
        content_hash: Optional[bytes] = None,
    ):
        self.source_public_key_hex = source_public_key_hex
        self.transaction_type = transaction_type
        self.content_type = content_type

        # S3 path => in actual blockchain, it will be IPFS address
        self.content_hash = content_hash

    def __str__(self):
        return json.dumps(self.to_dict())

    def to_dict(self) -> dict:
        # convert to json serializable dictionary
        if self.content_hash is not None:
            content_hash_hex = binascii.hexlify(self.content_hash)
        else:
            content_hash_hex = None

        return {
            "source_public_key_hex": self.source_public_key_hex.decode('utf-8'),
            "transaction_type": self.transaction_type,
            "content_type": self.content_type,
            "content_hash": content_hash_hex.decode('utf-8')
        }


class TransactionTarget:
    def __init__(
        self,
        # hex value (binascii.hexlify) of parent transaction hash
        target_transaction_hash_hex: Optional[bytes] = None,
        # public key of the recipient - seralized to DER and converted to hex
        target_public_key_hex: Optional[bytes] = None,
        amount: Optional[float] = None
    ):
        self.target_transaction_hash_hex = target_transaction_hash_hex
        self.target_public_key_hex = target_public_key_hex
        self.amount = amount

    def __str__(self):
        return json.dumps(self.to_dict())

    def to_dict(self) -> dict:
        # convert to json serializable dictionary
        return {
            "target_transaction_hash_hex": self.target_transaction_hash_hex.decode('utf-8')
            if self.target_transaction_hash_hex is not None else None,
            "target_public_key_hex": self.target_public_key_hex.decode('utf-8')
            if self.target_public_key_hex is not None else None,
            "amount": self.amount
        }


class Transaction:
    # Transaction object is the object being stored in blocks
    def __init__(
        self,
        transaction_source: TransactionSource,
        transaction_target: TransactionTarget
    ):
        self.transaction_source = transaction_source
        self.transaction_target = transaction_target

        self.timestamp = datetime.datetime.now(datetime.timezone.utc)

        # transaction hash is used as an id of the transaction (e.g. finding the post for a comment)
        self.transaction_hash = self.get_hash()

        self.signature = None

    def __str__(self):
        tx_dict = self.to_dict()

        # Add signature hex
        if self.signature is not None:
            signature_hex = binascii.hexlify(self.signature)
        else:
            signature_hex = None
        tx_dict["signature_hex"] = signature_hex.decode(
            'utf-8') if signature_hex is not None else None

        # Add transaction hash
        tx_dict["transaction_hash_hex"] = binascii.hexlify(
            self.transaction_hash).decode('utf-8')

        return json.dumps(tx_dict)

    def to_dict(self) -> dict:
        # convert to json serializable dictionary that will be hashed and signed
        return {
            **self.transaction_source.to_dict(),
            **self.transaction_target.to_dict(),
            "timestamp": self.timestamp.isoformat()
        }

    def get_hash(self) -> bytes:
        digest = hashes.Hash(hashes.SHA256())
        digest.update(json.dumps(self.to_dict()).encode('utf-8'))
        return digest.finalize()

    def sign_transaction(self, private_key: ec.EllipticCurvePrivateKey):
        self.signature = private_key.sign(
            json.dumps(self.to_dict()).encode('utf-8'),
            ec.ECDSA(hashes.SHA256())
        )

    def _verify_transaction(self) -> None:
        # If the signature is not verified, throw InvalidSignature excxeption
        if self.signature is None:
            raise InvalidSignature
        public_key_hex = binascii.unhexlify(
            self.transaction_source.source_public_key_hex)
        public_key = serialization.load_der_public_key(public_key_hex)
        public_key.verify(self.signature, json.dumps(self.to_dict()).encode('utf-8'),
                          ec.ECDSA(hashes.SHA256()))

    def validate_transaction(self) -> None:
        self._verify_transaction()
        # TODO: validate for each transaction type (e.g. TIP more than what an account has)


# Notes
# We use hex so that it can be easily decoded to string and jsonified and so that
# the json object can be used for hashing
