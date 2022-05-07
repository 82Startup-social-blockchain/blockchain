import binascii
import json
from typing import Dict, Optional, List

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization

from account.account import Account
from transaction.transaction import Transaction
from transaction.transaction_type import TransactionType
from transaction.transaction_utils import create_transaction_from_dict
from utils import constants


class Block:
    def __init__(
        self,
        previous_block: Optional['Block'],
        previous_block_hash_hex: Optional[bytes],
        transaction_list: List[Transaction],
        validator_public_key_hex: bytes,
        timestamp: float
    ):
        self.previous_block = previous_block
        self.previous_block_hash_hex = previous_block_hash_hex
        self.transaction_list = transaction_list
        self.timestamp = timestamp
        self.validator_public_key_hex = validator_public_key_hex

        # block hash is used as an id of the block
        self.block_hash = self._get_hash()

        self.signature = None

    def __len__(self):
        cnt = 1
        current_block = self
        while current_block.previous_block:
            cnt += 1
            current_block = current_block.previous_block
        return cnt

    def __str__(self):
        return json.dumps(self.to_dict())

    def __eq__(self, other: 'Block'):
        return self.block_hash == other.block_hash and \
            self.signature == other.signature

    def _to_presigned_dict(self) -> dict:
        # conver to json serializable dictionary that will be hashed and signed
        if self.previous_block_hash_hex is not None:
            previous_block_hash_hex = self.previous_block_hash_hex.decode('utf-8')
        elif self.previous_block is not None:
            previous_block_hash_hex = binascii.hexlify(
                self.previous_block.block_hash).decode('utf-8')
        else:
            previous_block_hash_hex = None

        # for transactions, use list of transaction hashes
        transaction_hash_hex_list = list(map(
            lambda tx: binascii.hexlify(tx.transaction_hash).decode('utf-8'), self.transaction_list))

        return {
            "previous_block_hash_hex": previous_block_hash_hex,
            "transaction_hash_hex_list": transaction_hash_hex_list,
            "validator_public_key_hex": self.validator_public_key_hex.decode('utf-8'),
            "timestamp": self.timestamp,
        }

    def to_dict(self) -> dict:
        # convert to json serializable dictionary with all block data
        block_dict = self._to_presigned_dict()

        # add signature hex
        if self.signature is not None:
            block_dict["signature_hex"] = binascii.hexlify(self.signature).decode('utf-8')

        # add block hash
        block_dict["block_hash_hex"] = binascii.hexlify(
            self.block_hash).decode('utf-8')

        # add transaction_list
        block_dict["transaction_dict_list"] = list(
            map(lambda tx: tx.to_dict(), self.transaction_list))

        return block_dict

    def _get_hash(self) -> bytes:
        digest = hashes.Hash(hashes.SHA256())
        digest.update(json.dumps(self._to_presigned_dict()).encode('utf-8'))
        return digest.finalize()

    def sign_block(self, private_key: ec.EllipticCurvePrivateKey):
        self.signature = private_key.sign(
            json.dumps(self._to_presigned_dict()).encode('utf-8'),
            ec.ECDSA(hashes.SHA256())
        )

    def _verify_block(self) -> None:
        if self.signature is None:
            raise InvalidSignature
        public_key_hex = binascii.unhexlify(self.validator_public_key_hex)
        public_key = serialization.load_der_public_key(public_key_hex)
        public_key.verify(
            self.signature,
            json.dumps(self._to_presigned_dict()).encode('utf-8'),
            ec.ECDSA(hashes.SHA256())
        )

    def validate(self, account_dict: Dict[bytes, Account]):
        # 1. verify the block signature - if invalid, throw InvalidSignature exception
        self._verify_block()

        # 2. validate all the transactions
        for transaction in self.transaction_list:
            tx_publick_key_hex = transaction.transaction_source.source_public_key_hex
            transaction.validate(account_dict.get(tx_publick_key_hex, None))

        # TODO: 3. validate that type is not ICO if it's not the first block

        # TODO: 4. validate the validator

    def update_account_dict(self, account_dict: Dict[bytes, Account]):
        # assume block is already validated
        # update account_dict in place
        for tx in self.transaction_list:
            public_key_hex = tx.transaction_source.source_public_key_hex
            target_public_key_hex = tx.transaction_target.target_public_key_hex
            tx_type = tx.transaction_source.transaction_type
            tx_token = tx.transaction_target.tx_token
            tx_fee = tx.transaction_source.tx_fee

            if public_key_hex not in account_dict:
                account_dict[public_key_hex] = Account(public_key_hex)
            if target_public_key_hex is not None and target_public_key_hex not in account_dict:
                account_dict[target_public_key_hex] = Account(target_public_key_hex)

            if tx_type == TransactionType.STAKE:
                account_dict[public_key_hex].stake += tx_token
                account_dict[public_key_hex].balance -= tx_token
            elif tx_type == TransactionType.TRANSFER:
                account_dict[target_public_key_hex].balance += tx_token
                account_dict[public_key_hex].balance -= tx_token
            elif tx_type == TransactionType.TIP:
                account_dict[target_public_key_hex].balance += tx_token
                account_dict[public_key_hex].balance -= tx_token
            elif tx_type == TransactionType.ICO:
                account_dict[public_key_hex].stake += tx_token

            if tx_fee is not None:
                account_dict[public_key_hex].balance -= tx_fee
                # TODO: add fee to balance

        if self.validator_public_key_hex not in account_dict:
            account_dict[self.validator_public_key_hex] = Account(self.validator_public_key_hex)
        account_dict[self.validator_public_key_hex].balance += constants.VALIDATION_REWARD


def create_block_from_dict(block_dict: Dict, previous_block: Optional[Block] = None) -> Block:
    """ Create a Block instance from input block dict
    block_dict has the following items
    - previous_block_hash_hex   : Optional[bytes]
    - transaction_hash_hex_list : List[bytes]
    - validator_public_key_hex  : byte
    - timestamp                 : float
    - signature_hex             : Optiona[byte]
    - block_hash_hex            : byte
    - transaction_dict_list     : List[dict]
    """
    transaction_list = list(
        map(lambda tx_dict: create_transaction_from_dict(tx_dict),
            block_dict["transaction_dict_list"])
    )

    if block_dict["signature_hex"] is not None:
        signature_hex = block_dict["signature_hex"].encode('utf-8')
        signature = binascii.unhexlify(signature_hex)
    else:
        signature = None

    block = Block(
        previous_block,
        binascii.hexlify(previous_block.block_hash) if previous_block is not None else None,
        transaction_list,
        block_dict["validator_public_key_hex"].encode('utf-8'),
        block_dict["timestamp"]
    )
    block.signature = signature

    return block


# Notes

# How do you prevent the validator from setting previous block as some block in the past?
# What if the most recent block that you have is not the most recent block => there is sth missing

# References

# https://github.com/deso-protocol/core/blob/85437b36ff233204195f99a9833ded435aa32248/lib/blockchain.go#L126
# https://github.com/deso-protocol/core/blob/85437b36ff233204195f99a9833ded435aa32248/lib/network.go#L2099
# https://github.com/deso-protocol/core/blob/85437b36ff233204195f99a9833ded435aa32248/lib/network.go#L1679
# https://github.com/deso-protocol/core/blob/85437b36ff233204195f99a9833ded435aa32248/lib/network.go#L2327
# https://github.com/deso-protocol/core/blob/85437b36ff233204195f99a9833ded435aa32248/lib/blockchain.go#L403
