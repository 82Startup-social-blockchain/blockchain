
import binascii
from datetime import datetime
from typing import Any, Optional

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes

from transaction.transaction import Transaction, TransactionSource, TransactionTarget
from transaction.transaction_type import TransactionContentType, TransactionType
from utils.crypto import get_public_key_hex


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
        timestamp=datetime.fromisoformat(tx_dict["timestamp"])
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
