import binascii
import json
import secrets
import time
from typing import Dict, Optional

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes


class ValidatorRand:
    def __init__(
        self,
        validator_public_key_hex: bytes,
        previous_block_hash_hex: bytes,
        timestamp: Optional[float] = None,
        rand: Optional[int] = None
    ):
        if timestamp is not None:
            self.timestamp = timestamp
        else:
            self.timestamp = time.time()

        if rand is not None:
            self.rand = rand
        else:
            self.rand = int(secrets.token_hex(8), 16)

        self.validator_public_key_hex = validator_public_key_hex
        self.previous_block_hash_hex = previous_block_hash_hex

        self.signature = None

    def _to_presigned_dict(self) -> Dict:
        return {
            "previous_block_hash_hex": self.previous_block_hash_hex,
            "validator_public_key_hex": self.validator_public_key_hex,
            "rand": self.rand,
            "timestamp": self.timestamp
        }

    def to_dict(self) -> Dict:
        validator_rand_dict = self._to_presigned_dict()
        # add signature hex
        if self.signature is not None:
            signature_hex = binascii.hexlify(self.signature)
        else:
            signature_hex = None
        validator_rand_dict["signature_hex"] = signature_hex.decode('utf-8') \
            if signature_hex is not None else None

        return validator_rand_dict

    def sign(self, private_key: ec.EllipticCurvePrivateKey) -> None:
        self.signature = private_key.sign(
            json.dumps(self._to_presigned_dict()).encode('utf-8'),
            ec.ECDSA(hashes.SHA256())
        )
