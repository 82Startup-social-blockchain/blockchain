import binascii
import json
import os
from typing import Optional

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization


# example account class where account has private key as a property
# it is more like utility class for testing.
class FullAccount:
    def __init__(
        self,
        private_key: Optional[ec.EllipticCurvePrivateKey] = None,
        private_key_file_path: Optional[str] = None
    ):
        if private_key is not None:
            self.private_key = private_key
        elif private_key_file_path is not None:
            with open(private_key_file_path, 'r') as fp:
                private_key_serialized = binascii.unhexlify(json.load(fp).encode('utf-8'))
                self.private_key = serialization.load_der_private_key(private_key_serialized, None)
        else:
            self.private_key = ec.generate_private_key(ec.SECP384R1())
