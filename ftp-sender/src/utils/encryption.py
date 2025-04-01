from cryptography.fernet import Fernet
import base64
import os

class PasswordEncryption:
    def __init__(self):
        self.key_file = "config/key.bin"
        self.key = self._load_or_generate_key()
        self.fernet = Fernet(self.key)

    def _load_or_generate_key(self):
        """加载或生成加密密钥"""
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            os.makedirs(os.path.dirname(self.key_file), exist_ok=True)
            with open(self.key_file, 'wb') as f:
                f.write(key)
            return key

    def encrypt(self, password):
        """加密密码"""
        return self.fernet.encrypt(password.encode()).decode()

    def decrypt(self, encrypted_password):
        """解密密码"""
        return self.fernet.decrypt(encrypted_password.encode()).decode()

# 创建全局加密工具实例
_encryption = PasswordEncryption()

def encrypt_password(password):
    """加密密码"""
    return _encryption.encrypt(password)

def decrypt_password(encrypted_password):
    """解密密码"""
    return _encryption.decrypt(encrypted_password)