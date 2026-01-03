"""
Encryption Module

AES-256-GCM encryption for data at rest.
"""

import base64
import os
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .config import security_settings


def _get_key() -> bytes:
    """Get encryption key as bytes."""
    key = security_settings.encryption_key
    # Ensure key is 32 bytes (256 bits)
    if len(key) < 32:
        key = key.ljust(32, '0')
    return key[:32].encode('utf-8')


def encrypt_data(plaintext: bytes) -> bytes:
    """
    Encrypt binary data using AES-256-GCM.

    Args:
        plaintext: Data to encrypt

    Returns:
        Encrypted data (nonce + ciphertext + tag)
    """
    key = _get_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # 96-bit nonce for GCM
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    return nonce + ciphertext


def decrypt_data(ciphertext: bytes) -> bytes:
    """
    Decrypt binary data encrypted with AES-256-GCM.

    Args:
        ciphertext: Encrypted data (nonce + ciphertext + tag)

    Returns:
        Decrypted data
    """
    key = _get_key()
    aesgcm = AESGCM(key)
    nonce = ciphertext[:12]
    encrypted = ciphertext[12:]
    return aesgcm.decrypt(nonce, encrypted, None)


def encrypt_field(value: str) -> str:
    """
    Encrypt a string field and return base64-encoded result.

    Args:
        value: String to encrypt

    Returns:
        Base64-encoded encrypted string
    """
    encrypted = encrypt_data(value.encode('utf-8'))
    return base64.b64encode(encrypted).decode('ascii')


def decrypt_field(encrypted_value: str) -> str:
    """
    Decrypt a base64-encoded encrypted field.

    Args:
        encrypted_value: Base64-encoded encrypted string

    Returns:
        Decrypted string
    """
    ciphertext = base64.b64decode(encrypted_value.encode('ascii'))
    decrypted = decrypt_data(ciphertext)
    return decrypted.decode('utf-8')


def encrypt_dict_fields(
    data: dict[str, Any],
    fields_to_encrypt: list[str],
) -> dict[str, Any]:
    """
    Encrypt specific fields in a dictionary.

    Args:
        data: Dictionary containing data
        fields_to_encrypt: List of field names to encrypt

    Returns:
        Dictionary with specified fields encrypted
    """
    result = data.copy()
    for field in fields_to_encrypt:
        if field in result and result[field] is not None:
            result[field] = encrypt_field(str(result[field]))
    return result


def decrypt_dict_fields(
    data: dict[str, Any],
    fields_to_decrypt: list[str],
) -> dict[str, Any]:
    """
    Decrypt specific fields in a dictionary.

    Args:
        data: Dictionary containing encrypted data
        fields_to_decrypt: List of field names to decrypt

    Returns:
        Dictionary with specified fields decrypted
    """
    result = data.copy()
    for field in fields_to_decrypt:
        if field in result and result[field] is not None:
            try:
                result[field] = decrypt_field(str(result[field]))
            except Exception:
                # If decryption fails, leave the value as-is
                pass
    return result
