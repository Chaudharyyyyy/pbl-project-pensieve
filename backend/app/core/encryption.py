"""
Encryption Service

Provides AES-256-GCM encryption for journal entries with per-user key derivation.
Zero-knowledge architecture: server cannot decrypt without user's password.
"""

import os
import secrets
from dataclasses import dataclass

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


@dataclass
class EncryptedData:
    """Container for encrypted content with metadata."""
    ciphertext: bytes
    iv: bytes
    auth_tag: bytes


class EncryptionService:
    """
    AES-256-GCM encryption service with per-user key derivation.
    
    Security Properties:
    - Keys derived from user password using PBKDF2-HMAC-SHA256
    - Each encryption uses a unique random IV
    - GCM provides authenticated encryption
    - Salt is unique per user, stored in database
    """

    SALT_LENGTH = 32
    KEY_LENGTH = 32  # 256 bits for AES-256
    IV_LENGTH = 12   # 96 bits recommended for GCM
    TAG_LENGTH = 16  # 128-bit authentication tag

    def __init__(self, iterations: int = 100_000):
        """
        Initialize encryption service.
        
        Args:
            iterations: PBKDF2 iteration count. Higher = slower but more secure.
        """
        self.iterations = iterations
        self.backend = default_backend()

    def generate_salt(self) -> bytes:
        """Generate a cryptographically secure random salt."""
        return secrets.token_bytes(self.SALT_LENGTH)

    def derive_key(self, password: str, salt: bytes) -> bytes:
        """
        Derive encryption key from user password and salt.
        
        The derived key is used for AES encryption. It should NEVER be stored;
        it must be re-derived each time from the user's password.
        
        Args:
            password: User's plaintext password
            salt: User-specific salt from database
            
        Returns:
            32-byte encryption key
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.KEY_LENGTH,
            salt=salt,
            iterations=self.iterations,
            backend=self.backend,
        )
        return kdf.derive(password.encode("utf-8"))

    def encrypt(self, plaintext: str, key: bytes) -> EncryptedData:
        """
        Encrypt text using AES-256-GCM.
        
        Each encryption generates a new random IV for semantic security.
        The authentication tag ensures ciphertext integrity.
        
        Args:
            plaintext: Text to encrypt
            key: 32-byte encryption key from derive_key()
            
        Returns:
            EncryptedData containing ciphertext, IV, and auth tag
        """
        iv = os.urandom(self.IV_LENGTH)
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(iv),
            backend=self.backend,
        )
        encryptor = cipher.encryptor()
        
        ciphertext = encryptor.update(plaintext.encode("utf-8")) + encryptor.finalize()
        
        return EncryptedData(
            ciphertext=ciphertext,
            iv=iv,
            auth_tag=encryptor.tag,
        )

    def decrypt(self, encrypted: EncryptedData, key: bytes) -> str:
        """
        Decrypt text using AES-256-GCM.
        
        Args:
            encrypted: EncryptedData from encrypt()
            key: 32-byte encryption key from derive_key()
            
        Returns:
            Decrypted plaintext
            
        Raises:
            InvalidTag: If ciphertext was tampered with
        """
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(encrypted.iv, encrypted.auth_tag),
            backend=self.backend,
        )
        decryptor = cipher.decryptor()
        
        plaintext = decryptor.update(encrypted.ciphertext) + decryptor.finalize()
        
        return plaintext.decode("utf-8")

    def encrypt_for_storage(self, plaintext: str, key: bytes) -> tuple[bytes, bytes, bytes]:
        """
        Encrypt and return components ready for database storage.
        
        Args:
            plaintext: Text to encrypt
            key: Encryption key
            
        Returns:
            Tuple of (ciphertext, iv, auth_tag) as bytes
        """
        encrypted = self.encrypt(plaintext, key)
        return encrypted.ciphertext, encrypted.iv, encrypted.auth_tag

    def decrypt_from_storage(
        self, 
        ciphertext: bytes, 
        iv: bytes, 
        auth_tag: bytes, 
        key: bytes
    ) -> str:
        """
        Decrypt content retrieved from database.
        
        Args:
            ciphertext: Encrypted content from database
            iv: Initialization vector from database
            auth_tag: Authentication tag from database
            key: Encryption key derived from password
            
        Returns:
            Decrypted plaintext
        """
        encrypted = EncryptedData(
            ciphertext=ciphertext,
            iv=iv,
            auth_tag=auth_tag,
        )
        return self.decrypt(encrypted, key)


# Singleton instance
_encryption_service: EncryptionService | None = None


def get_encryption_service(iterations: int = 100_000) -> EncryptionService:
    """Get or create encryption service singleton."""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService(iterations=iterations)
    return _encryption_service
