import base64
import os

class Encryption:
    @staticmethod
    def encrypt_password(password: str) -> str:
        """Encrypt the password using base64 encoding."""
        encoded_bytes = base64.b64encode(password.encode('utf-8'))
        return encoded_bytes.decode('utf-8')

    @staticmethod
    def decrypt_password(encrypted_password: str) -> str:
        """Decrypt the password using base64 decoding."""
        decoded_bytes = base64.b64decode(encrypted_password.encode('utf-8'))
        return decoded_bytes.decode('utf-8')

# Example usage:
if __name__ == "__main__":
    original_password = "my_secret_password"
    encrypted = Encryption.encrypt_password(original_password)
    print(f"Encrypted: {encrypted}")
    decrypted = Encryption.decrypt_password(encrypted)
    print(f"Decrypted: {decrypted}")