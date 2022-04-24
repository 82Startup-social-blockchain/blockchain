from typing import Optional

from cryptography.hazmat.primitives.asymmetric import ec


class Account:
    def __init__(
        self,
        private_key: Optional[ec.EllipticCurvePrivateKey] = None
    ):
        if private_key is None:
            self.private_key = ec.generate_private_key(
                ec.SECP384R1()
            )
        else:
            self.private_key = private_key
