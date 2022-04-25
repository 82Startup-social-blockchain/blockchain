import binascii
import json
from datetime import datetime
from typing import Optional, List

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.exceptions import InvalidSignature

from transaction.transaction import Transaction


class Block:
    def __init__(
        self,
        previous_block: Optional['Block'],
        transaction_list: List[Transaction],
        validator_public_key_hex: bytes,
        timestamp: datetime
    ):
        self.previous_block = previous_block
        self.transaction_list = transaction_list
        self.timestamp = timestamp
        self.validator_public_key_hex = validator_public_key_hex

        # block hash is used as an id of the block
        self.block_hash = self.get_hash()

        self.signature = None

    def __len__(self):
        if self.previous_block is None:
            return 1
        cnt = 1
        current_block = self
        while current_block.previous_block:
            cnt += 1
            current_block = current_block.previous_block
        return cnt

    def __str__(self):
        return json.dumps(self.to_dict())

    def _to_presigned_dict(self) -> dict:
        # conver to json serializable dictionary that will be hashed and signed
        if self.previous_block is not None:
            previous_block_hash = binascii.hexlify(
                self.previous_block.block_hash).decode('utf-8')
        else:
            previous_block_hash = None

        # for transactions, use list of transaction hashes
        transaction_hash_hex_list = list(map(
            lambda tx: binascii.hexlify(tx.transaction_hash).decode('utf-8'), self.transaction_list))

        return {
            "previous_block_hash": previous_block_hash,
            "transaction_hash_hex_list": transaction_hash_hex_list,
            "validator_public_key_hex": self.validator_public_key_hex.decode('utf-8'),
            "timestamp": self.timestamp.isoformat(),
        }

    def to_dict(self) -> dict:
        # convert to json serializable dictionary with all block data
        block_dict = self._to_presigned_dict()

        # add signature hex
        if self.signature is not None:
            signature_hex = binascii.hexlify(self.signature)
        else:
            signature_hex = None
        block_dict["signature_hex"] = signature_hex.decode(
            'utf-8') if signature_hex is not None else None

        # add block hash
        block_dict["block_hash_hex"] = binascii.hexlify(
            self.block_hash).decode('utf-8')

        return block_dict

    def get_hash(self):
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
        public_key.verify(self.signature, json.dumps(self._to_presigned_dict()).encode('utf-8'),
                          ec.ECDSA(hashes.SHA256()))

    def validate(self):
        # If the block is invalid, throw InvalidSignature exception

        # 1. verify the block signature
        self._verify_block()

        # 2. validate all the transactions
        for transaction in self.transaction_list:
            transaction.validate()

        # TODO: 3. vadliate that the validator got the right amount of reward

# Notes

# How do you prevent the validator from setting previous block as some block in the past?
# What if the most recent block that you have is not the most recent block => there is sth missing

# References

# https://github.com/deso-protocol/core/blob/85437b36ff233204195f99a9833ded435aa32248/lib/blockchain.go#L126
# https://github.com/deso-protocol/core/blob/85437b36ff233204195f99a9833ded435aa32248/lib/network.go#L2099
# https://github.com/deso-protocol/core/blob/85437b36ff233204195f99a9833ded435aa32248/lib/network.go#L1679
# https://github.com/deso-protocol/core/blob/85437b36ff233204195f99a9833ded435aa32248/lib/network.go#L2327
# https://github.com/deso-protocol/core/blob/85437b36ff233204195f99a9833ded435aa32248/lib/blockchain.go#L403
