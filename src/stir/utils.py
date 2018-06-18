import os
import base64
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends.openssl.rsa import _RSAPrivateKey, _RSAPublicKey
from cryptography.hazmat.backends.openssl.dsa import _DSAPrivateKey, _DSAPublicKey


def load_private_key(path, password=None):

    with open(path, "rb") as fh:
        private_key = serialization.load_pem_private_key(
            fh.read(),
            password=password,
            backend=default_backend()
        )
        return private_key


def load_public_key(path):

    with open(path, "rb") as fh:
        public_key = serialization.load_ssh_public_key(
            fh.read(),
            backend=default_backend()
        )
        return public_key


def sign_message(message, private_key):

    if not isinstance(message, bytes):
        message = bytes(message.encode("utf-8"))

    if isinstance(private_key, _DSAPrivateKey):
        sig = private_key.sign(
            message,
            hashes.SHA256()
        )
    elif isinstance(private_key, _RSAPrivateKey):
        sig = private_key.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
    else:
        raise Exception("Unsupported private key, must be RSA or DSA")

    return sig


def verify_message(message, signature, public_key):

    if not isinstance(message, bytes):
        message = bytes(message.encode("utf-8"))

    if isinstance(public_key, _DSAPublicKey):
        public_key.verify(
            signature,
            message,
            hashes.SHA256()
        )
    elif isinstance(public_key, _RSAPublicKey):
        public_key.verify(
            signature,
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
    else:
        raise Exception("Unsupported public key, must be DSA or RSA")
