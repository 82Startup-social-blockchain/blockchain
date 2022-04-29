from typing import Optional

from cryptography.hazmat.primitives.asymmetric import ec

from block.blockchain import Blockchain


class Account:
    def __init__(
        self,
        blockchain: Blockchain,
        private_key: Optional[ec.EllipticCurvePrivateKey] = None
    ):
        self.blockchain = blockchain

        if private_key is None:
            self.private_key = ec.generate_private_key(
                ec.SECP384R1()
            )
        else:
            self.private_key = private_key
