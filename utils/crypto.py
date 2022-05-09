import binascii
import codecs

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization


def get_public_key_hex(public_key: ec.EllipticCurvePublicKey) -> bytes:
    public_key_serialized = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return binascii.hexlify(public_key_serialized)


def get_fernet(encryption_key: str) -> Fernet:
    digest = hashes.Hash(hashes.SHA256())
    digest.update(encryption_key.encode('utf-8'))
    encryption_key_hash = digest.finalize()

    encryption_key_hash_hex = binascii.hexlify(encryption_key_hash)
    encryption_key_64 = codecs.encode(codecs.decode(encryption_key_hash_hex, 'hex'), 'base64').decode()
    return Fernet(encryption_key_64)


def convert_ec_key_to_fernet_key(private_key: ec.EllipticCurvePrivateKey) -> Fernet:
    private_key_serialized = private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    digest = hashes.Hash(hashes.SHA256())
    digest.update(private_key_serialized)
    private_key_hash = digest.finalize()
    private_key_hash_hex = binascii.hexlify(private_key_hash)

    private_key_64 = codecs.encode(codecs.decode(private_key_hash_hex, 'hex'), 'base64').decode()
    return Fernet(private_key_64)
