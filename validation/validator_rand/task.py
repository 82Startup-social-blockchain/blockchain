from __future__ import annotations
import binascii
import json
from typing import TYPE_CHECKING

from block.validator_rand import ValidatorRand
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from validation.validator_rand.exception import ValidatorRandSignatureError, ValidatorRandValueError

if TYPE_CHECKING:
    from block.validator_rand import ValidatorRand


class ValidatorRandValidationTask:
    def __init__(self, validator_rand: ValidatorRand):
        self.validator_rand = validator_rand

    def _validate_signature(self):
        if self.validator_rand.signature is None:
            raise ValidatorRandSignatureError("Signature null")

        public_key_serialized = binascii.unhexlify(self.validator_rand.validator_public_key_hex)
        public_key = serialization.load_der_public_key(public_key_serialized)
        public_key.verify(
            self.validator_rand.signature,
            json.dumps(self.validator_rand._to_presigned_dict()).encode('utf-8'),
            ec.ECDSA(hashes.SHA256())
        )

    def _validate_rand_value(self):
        if not isinstance(self.validator_rand.rand, int):
            raise ValidatorRandValueError("Rand not int")

        if self.validator_rand.rand < 0:
            raise ValidatorRandValueError("Rand negative")

    def run(self):
        self._validate_signature()
        self._validate_rand_value()
