import binascii
import datetime
from typing import Optional, Any
import json

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.exceptions import InvalidSignature
from account.account import Account

from transaction.transaction_validation import TransactionValidation

from .transaction_type import TransactionType, TransactionContentType
from utils.crypto import get_public_key_hex


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
            content_hash_hex = binascii.hexlify(
                self.content_hash).decode('utf-8')
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
        timestamp: Optional[datetime.datetime] = datetime.datetime.now(
            datetime.timezone.utc)
    ):
        self.transaction_source = transaction_source
        self.transaction_target = transaction_target

        if timestamp is None:
            self.timestamp = datetime.datetime.now(datetime.timezone.utc)
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
            "timestamp": self.timestamp.isoformat()
        }

    def to_dict(self) -> dict:
        tx_dict = self._to_presigned_dict()

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
        public_key_hex = binascii.unhexlify(
            self.transaction_source.source_public_key_hex)
        public_key = serialization.load_der_public_key(public_key_hex)
        public_key.verify(self.signature, json.dumps(self._to_presigned_dict()).encode('utf-8'),
                          ec.ECDSA(hashes.SHA256()))

    def validate(self, account: Account) -> None:
        # verify transactino signature
        self._verify_transaction()

        # validate the transaction itself
        transaction_validation = TransactionValidation(self, account)
        transaction_validation.run()


def create_transaction_from_dict(tx_dict: dict) -> Transaction:
    """ Coverts transaction_dict (generated from to_dict()) to Transaction object.
    Parameter timestamp is to allow user input for timestamp
    transaction_dict has the following items
    - source_public_key_hex       : bytes
    - transaction_type            : TransactionType
    - content_type                : Optional[TransactionContentType]
    - content_hash_hex            : Optional[bytes]
    - tx_fee                      : Optional[float]
    - target_transaction_hash_hex : Optional[bytes]
    - target_public_key_hex       : Optional[bytes]
    - tx_token                    : Optional[float]
    - tx_object                   : Optional[bytes]
    - signature_hex               : Optional[bytes]
    - transaction_hash_hex        : byte
    - timestamp                   : str
    """
    # create TransactionSource object
    content_type = TransactionContentType(
        tx_dict["content_type"]
    ) if tx_dict["content_type"] is not None else None

    if tx_dict["content_hash_hex"] is not None:
        content_hash = binascii.unhexlify(
            tx_dict["content_hash_hex"].encode('utf-8'))
    else:
        content_hash = None

    transaction_source = TransactionSource(
        tx_dict["source_public_key_hex"].encode('utf-8'),
        TransactionType(tx_dict["transaction_type"]),
        content_type=content_type,
        content_hash=content_hash,
        tx_fee=tx_dict["tx_fee"]
    )

    # create TransactionTarget object
    if tx_dict["target_transaction_hash_hex"] is not None:
        target_transaction_hash_hex = tx_dict["target_transaction_hash_hex"].encode(
            'utf-8')
    else:
        target_transaction_hash_hex = None

    if tx_dict["target_public_key_hex"] is not None:
        target_public_key_hex = tx_dict["target_public_key_hex"].encode(
            'utf-8')
    else:
        target_public_key_hex = None

    transaction_target = TransactionTarget(
        target_transaction_hash_hex=target_transaction_hash_hex,
        target_public_key_hex=target_public_key_hex,
        tx_token=tx_dict["tx_token"],
        tx_object=tx_dict["tx_object"]
    )

    # create Transaction object
    if tx_dict["signature_hex"] is not None:
        signature_hex = tx_dict["signature_hex"].encode('utf-8')
        signature = binascii.unhexlify(signature_hex)
    else:
        signature = None

    transaction = Transaction(
        transaction_source,
        transaction_target,
        timestamp=datetime.datetime.fromisoformat(tx_dict["timestamp"])
    )
    transaction.signature = signature
    return transaction


def generate_transaction(
    public_key: ec.EllipticCurvePublicKey,
    transaction_type: TransactionType,
    content: Optional[str] = None,
    content_type: Optional[TransactionContentType] = None,
    tx_fee: Optional[float] = None,
    target_transaction_hash: Optional[bytes] = None,
    target_public_key: Optional[ec.EllipticCurvePublicKey] = None,
    tx_token: Optional[float] = None,
    tx_object: Optional[Any] = None
) -> Transaction:
    # create TransactionSource instance
    if content is not None:
        content_digest = hashes.Hash(hashes.SHA256())
        content_digest.update(content.encode('utf-8'))
        content_hash = content_digest.finalize()
    else:
        content_hash = None

    transaction_source = TransactionSource(
        get_public_key_hex(public_key),
        transaction_type,
        content_type=content_type,
        content_hash=content_hash,
        tx_fee=tx_fee
    )

    # create TransactionTarget instance
    if target_transaction_hash is not None:
        target_transaction_hash_hex = binascii.hexlify(target_transaction_hash)
    else:
        target_transaction_hash_hex = None

    if target_public_key is not None:
        target_public_key_hex = get_public_key_hex(target_public_key)
    else:
        target_public_key_hex = None

    transaction_target = TransactionTarget(
        target_transaction_hash_hex=target_transaction_hash_hex,
        target_public_key_hex=target_public_key_hex,
        tx_token=tx_token,
        tx_object=tx_object
    )

    return Transaction(transaction_source, transaction_target)

# Notes
# We use hex so that it can be easily decoded to string and jsonified and so that
# the json object can be used for hashing
