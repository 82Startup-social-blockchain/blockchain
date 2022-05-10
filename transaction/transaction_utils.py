
import binascii
import json
import os
import time
from typing import Any, Optional

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from runner.models.transaction import TransactionCreateRequest

from transaction.transaction import Transaction, TransactionSource, TransactionTarget
from transaction.transaction_type import TransactionContentType, TransactionType
from utils.constants import STORAGE_PATH
from utils.crypto import get_fernet, get_public_key_hex


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
    - timestamp                   : float
    """
    # create TransactionSource object
    content_type = TransactionContentType(
        tx_dict["content_type"]
    ) if tx_dict["content_type"] is not None else None

    if tx_dict["content_hash_hex"] is not None:
        content_hash = binascii.unhexlify(tx_dict["content_hash_hex"].encode('utf-8'))
    else:
        content_hash = None

    transaction_source = TransactionSource(
        tx_dict["source_public_key_hex"].encode('utf-8'),
        TransactionType(tx_dict["transaction_type"]),
        content_type=content_type,
        content_hash=content_hash,
        tx_fee=tx_dict.get("tx_fee", None)
    )

    # create TransactionTarget object
    if tx_dict.get("target_transaction_hash_hex", None) is not None:
        target_transaction_hash_hex = tx_dict["target_transaction_hash_hex"].encode('utf-8')
    else:
        target_transaction_hash_hex = None

    if tx_dict.get("target_public_key_hex", None) is not None:
        target_public_key_hex = tx_dict["target_public_key_hex"].encode('utf-8')
    else:
        target_public_key_hex = None

    transaction_target = TransactionTarget(
        target_transaction_hash_hex=target_transaction_hash_hex,
        target_public_key_hex=target_public_key_hex,
        tx_token=tx_dict.get("tx_token", None),
        tx_object=tx_dict.get("tx_object", None)
    )

    # create Transaction object
    if tx_dict.get("signature_hex", None) is not None:
        signature_hex = tx_dict["signature_hex"].encode('utf-8')
        signature = binascii.unhexlify(signature_hex)
    else:
        signature = None

    transaction = Transaction(
        transaction_source,
        transaction_target,
        timestamp=tx_dict["timestamp"]
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


def create_transaction_from_request(tx_request: TransactionCreateRequest) -> Transaction:
    timestamp = time.time()

    # create TransactionSource object
    private_key_serialized = binascii.unhexlify(tx_request.private_key_hex.encode('utf-8'))
    private_key = serialization.load_der_private_key(private_key_serialized, None)
    public_key_hex = get_public_key_hex(private_key.public_key())

    content_type = TransactionContentType(tx_request.content_type) if tx_request.content_type is not None else None
    content_hash = upload_content_to_storage(tx_request, timestamp)

    transaction_source = TransactionSource(
        public_key_hex,
        tx_request.transaction_type,
        content_type=content_type,
        content_hash=content_hash,
        tx_fee=tx_request.tx_fee
    )

    # create TransactionTarget object
    if tx_request.target_transaction_hash_hex is not None:
        target_transaction_hash_hex = tx_request.target_transaction_hash_hex.encode('utf-8')
    else:
        target_transaction_hash_hex = None

    if tx_request.target_public_key_hex is not None:
        target_public_key_hex = tx_request.target_public_key_hex.encode('utf-8')
    else:
        target_public_key_hex = None

    transaction_target = TransactionTarget(
        target_transaction_hash_hex=target_transaction_hash_hex,
        target_public_key_hex=target_public_key_hex,
        tx_token=tx_request.tx_token,
        tx_object=tx_request.tx_object
    )

    # create Transaction object
    transaction = Transaction(
        transaction_source,
        transaction_target,
        timestamp
    )
    transaction.sign_transaction(private_key)
    return transaction


# upload content to storage and return the content hash
def upload_content_to_storage(
    tx_request: TransactionCreateRequest,
    timestamp: float
) -> Optional[bytes]:
    if tx_request.content is None:
        return None

    content_hash = get_content_hash_from_request(tx_request, timestamp)
    content_hash_hex_str = binascii.hexlify(content_hash).decode('utf-8')

    if tx_request.encryption_key is not None:
        fernet = get_fernet(tx_request.encryption_key)
        content_encrypted = fernet.encrypt(tx_request.content.encode('utf-8'))
    else:
        content_encrypted = tx_request.content.encode('utf-8')

    with open(os.path.join(STORAGE_PATH, content_hash_hex_str + '.json'), 'w') as fp:
        json.dump(content_encrypted.decode('utf-8'), fp)

    return content_hash


def get_content_hash_from_request(tx_request: TransactionCreateRequest, timestamp: float) -> bytes:
    # get content hash from content, source public key hex, target transaction hash, timestamp
    digest = hashes.Hash(hashes.SHA256())
    # include content to hash
    if tx_request.content is not None:
        digest.update(tx_request.content.encode('utf-8'))

    # include source public key to hash
    private_key_serialized = binascii.unhexlify(tx_request.private_key_hex.encode('utf-8'))
    private_key = serialization.load_der_private_key(private_key_serialized, None)
    public_key_hex = get_public_key_hex(private_key.public_key())
    digest.update(public_key_hex)

    # include target transaction hash
    if tx_request.target_transaction_hash_hex is not None:
        digest.update(tx_request.target_transaction_hash_hex.encode('utf-8'))

    # include timestamp
    digest.update(str(timestamp).encode('utf-8'))

    return digest.finalize()


def get_content_from_transaction(transaction: Transaction, encryption_key: str) -> Optional[str]:
    content_hash = transaction.transaction_source.content_hash
    if content_hash is None:
        return None
    content_hash_hex = binascii.hexlify(content_hash)

    content_file_path = os.path.join(STORAGE_PATH, content_hash_hex.decode('utf-8') + '.json')
    if not os.path.exists(content_file_path):
        return None

    with open(content_file_path, 'r') as fp:
        content = json.load(fp)

    if encryption_key is not None:
        fernet = get_fernet(encryption_key)
        content = fernet.decrypt(content.encode('utf-8')).decode('utf-8')

    return content
