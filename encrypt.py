import hashlib
import os

from Crypto.Cipher import AES

SALT_SIZE = 16
KEY_SIZE = 32
NONCE_SIZE = 16
TAG_SIZE = 16


class CryptoError(Exception):
    """Key derivation or encryption failed."""


class DecryptionError(CryptoError):
    """Decryption failed: wrong master password, or the data is damaged."""


def new_salt():
    """Random salt, generated once when the vault is created."""
    return os.urandom(SALT_SIZE)


def derive_key(master_password, salt):
    """Turn the master password into a 32-byte AES key using scrypt.

    scrypt is deliberately slow and memory-hungry, which makes guessing
    passwords offline far more expensive than a single SHA-256 would.
    """
    if not isinstance(master_password, str) or not master_password:
        raise CryptoError("Master password must be a non-empty string.")
    if not isinstance(salt, bytes) or len(salt) != SALT_SIZE:
        raise CryptoError("Salt is invalid - the vault file may be damaged.")

    try:
        return hashlib.scrypt(
            master_password.encode("utf-8"),
            salt=salt,
            n=2**15,
            r=8,
            p=1,
            maxmem=64 * 1024 * 1024,
            dklen=KEY_SIZE,
        )
    except AttributeError:
        # Some Python builds are compiled without scrypt support.
        raise CryptoError(
            "This Python build doesn't support scrypt. Install Python 3.8+ "
            "from python.org (or your package manager) and try again."
        ) from None
    except (ValueError, MemoryError) as e:
        raise CryptoError(f"Key derivation failed (not enough memory?): {e}") from e


def _check_key(key):
    if not isinstance(key, bytes) or len(key) != KEY_SIZE:
        raise CryptoError("Invalid encryption key.")


def encrypt(key, plaintext):
    """Encrypt bytes with AES-GCM. Returns nonce + tag + ciphertext."""
    _check_key(key)
    if not isinstance(plaintext, bytes):
        raise CryptoError("Only bytes can be encrypted.")

    try:
        cipher = AES.new(key, AES.MODE_GCM)  # fresh random nonce every time
        ciphertext, tag = cipher.encrypt_and_digest(plaintext)
    except (ValueError, TypeError) as e:
        raise CryptoError(f"Encryption failed: {e}") from e
    return cipher.nonce + tag + ciphertext


def decrypt(key, blob):
    """Decrypt data produced by encrypt().

    Raises DecryptionError if the key is wrong or the data was modified.
    """
    _check_key(key)
    if not isinstance(blob, bytes) or len(blob) < NONCE_SIZE + TAG_SIZE:
        raise DecryptionError("Encrypted data is too short - the vault file is damaged.")

    nonce = blob[:NONCE_SIZE]
    tag = blob[NONCE_SIZE:NONCE_SIZE + TAG_SIZE]
    ciphertext = blob[NONCE_SIZE + TAG_SIZE:]

    try:
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        return cipher.decrypt_and_verify(ciphertext, tag)
    except ValueError as e:
        raise DecryptionError("Wrong master password, or the vault file is damaged.") from e
