import binascii

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization


def get_public_key_hex(public_key: ec.EllipticCurvePublicKey) -> bytes:
    public_key_serialized = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return binascii.hexlify(public_key_serialized)
