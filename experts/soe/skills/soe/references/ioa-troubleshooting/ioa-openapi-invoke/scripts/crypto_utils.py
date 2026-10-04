"""
iOA 凭证加密工具（与 ioa-resource-grant 同源）。

用途：
1. 客户希望加密存储 SecretId/SecretKey 时，在目标机器上生成密文：
       python crypto_utils.py <SecretId> <SecretKey>
   将输出粘贴到客户配置文件的 encrypted_secret_id / encrypted_secret_key。
   注意：密钥与机器特征绑定，仅能在同一台机器上解密。
2. rsa_encrypt_pkcs1_v15：对接口的敏感字段（如创建本地账号的 Password）做
   PKCS#1 v1.5 加密（先调用 common/DescribePublicEncryptKey 取 PEM 公钥）。
"""

import base64
import hashlib
import sys

try:
    from cryptography.fernet import Fernet
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False


def get_machine_key() -> bytes:
    machine_info = ""
    try:
        import platform
        machine_info += platform.node() + platform.machine() + platform.system()
    except Exception:
        pass
    try:
        import uuid
        machine_info += str(uuid.getnode())
    except Exception:
        pass
    key = hashlib.sha256(f"ioa-openapi-invoke-{machine_info}".encode()).digest()
    return base64.urlsafe_b64encode(key)


def encrypt_credential(plain_text: str) -> str:
    if not HAS_CRYPTO:
        return base64.b64encode(plain_text.encode()).decode()
    return Fernet(get_machine_key()).encrypt(plain_text.encode()).decode()


def decrypt_credential(encrypted_text: str) -> str:
    if not encrypted_text:
        return ""
    if not HAS_CRYPTO:
        try:
            return base64.b64decode(encrypted_text.encode()).decode()
        except Exception:
            return encrypted_text
    try:
        return Fernet(get_machine_key()).decrypt(encrypted_text.encode()).decode()
    except Exception:
        return encrypted_text


def rsa_encrypt_pkcs1_v15(plain_text: str, pem_public_key: str) -> str:
    """对明文做 PKCS#1 v1.5 加密（与服务端多块拼接逻辑一致），返回 base64 密文。"""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.backends import default_backend

    pub = serialization.load_pem_public_key(
        pem_public_key.encode("utf-8"), backend=default_backend())
    n_bytes = (pub.key_size + 7) // 8
    part_len = n_bytes - 11  # PKCS1 v1.5 padding overhead
    raw = plain_text.encode("utf-8")
    chunks = [pub.encrypt(raw[i:i + part_len], padding.PKCS1v15())
              for i in range(0, len(raw), part_len)]
    return base64.b64encode(b"".join(chunks)).decode("ascii")


if __name__ == "__main__":
    if not HAS_CRYPTO:
        print("Warning: 未安装 cryptography，回退 base64（不安全）。请执行: pip install cryptography")
    if len(sys.argv) >= 3:
        sid, skey = sys.argv[1], sys.argv[2]
    else:
        sid = input("SecretId: ").strip()
        skey = input("SecretKey: ").strip()
    print("encrypted_secret_id:", encrypt_credential(sid))
    print("encrypted_secret_key:", encrypt_credential(skey))
