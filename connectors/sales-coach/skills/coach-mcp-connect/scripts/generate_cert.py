#!/usr/bin/env python3
"""
TLS 证书生成脚本 - 跨平台

为 OAuth 回调服务器生成自签名证书。
支持 Windows/macOS/Linux，无需安装 openssl 命令行工具。

输出：
  ~/.config/coach-mcp-connect/localhost.pem     (证书)
  ~/.config/coach-mcp-connect/localhost-key.pem (私钥)
"""

import sys
import os
import datetime
import ipaddress
from pathlib import Path


def generate_certificate():
    """生成自签名证书"""
    try:
        # 尝试使用 cryptography 库（如果已安装）
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa

        # 生成私钥
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        # 构建证书主题
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ])

        # 构建证书
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
            .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365))
            .add_extension(
                x509.SubjectAlternativeName([
                    x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
                    x509.DNSName("localhost"),
                ]),
                critical=False,
            )
            .sign(key, hashes.SHA256())
        )

        # 保存证书和私钥
        config_dir = Path.home() / ".config" / "coach-mcp-connect"
        config_dir.mkdir(parents=True, exist_ok=True)

        cert_path = config_dir / "localhost.pem"
        key_path = config_dir / "localhost-key.pem"

        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

        with open(key_path, "wb") as f:
            f.write(key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            ))

        # 设置权限（仅 Unix）
        if os.name != "nt":
            os.chmod(cert_path, 0o644)
            os.chmod(key_path, 0o600)

        print(f"✓ 证书已生成：{cert_path}")
        print(f"✓ 私钥已生成：{key_path}")
        print(f"✓ 有效期：365 天")
        return True

    except ImportError:
        # cryptography 库未安装，尝试使用 openssl 命令
        return generate_with_openssl()


def generate_with_openssl():
    """使用 openssl 命令行工具生成证书（备用方案）"""
    import subprocess

    config_dir = Path.home() / ".config" / "coach-mcp-connect"
    config_dir.mkdir(parents=True, exist_ok=True)

    cert_path = config_dir / "localhost.pem"
    key_path = config_dir / "localhost-key.pem"

    try:
        # 调用 openssl 生成证书
        cmd = [
            "openssl", "req", "-x509", "-newkey", "rsa:2048",
            "-keyout", str(key_path),
            "-out", str(cert_path),
            "-days", "365", "-nodes",
            "-subj", "/CN=localhost",
            "-addext", "subjectAltName=IP:127.0.0.1,DNS:localhost",
        ]

        subprocess.run(cmd, check=True, capture_output=True, text=True)

        # 设置权限（仅 Unix）
        if os.name != "nt":
            os.chmod(cert_path, 0o644)
            os.chmod(key_path, 0o600)

        print(f"✓ 证书已生成：{cert_path}")
        print(f"✓ 私钥已生成：{key_path}")
        print(f"✓ 有效期：365 天")
        return True

    except FileNotFoundError:
        print("错误：无法生成证书", file=sys.stderr)
        print("", file=sys.stderr)
        print("未找到 openssl 工具。请安装以下之一：", file=sys.stderr)
        print("", file=sys.stderr)
        print("  方案 1（推荐）：安装 cryptography 库", file=sys.stderr)
        print("    pip install cryptography", file=sys.stderr)
        print("    然后重新运行此脚本", file=sys.stderr)
        print("", file=sys.stderr)
        print("  方案 2：安装 openssl", file=sys.stderr)
        if sys.platform == "win32":
            print("    Windows: 下载 https://slproweb.com/products/Win32-OpenSSL.html", file=sys.stderr)
        elif sys.platform == "darwin":
            print("    macOS: brew install openssl", file=sys.stderr)
        else:
            print("    Linux: sudo apt install openssl  # 或 sudo yum install openssl", file=sys.stderr)
        print("", file=sys.stderr)
        print("安装后重新运行此脚本。", file=sys.stderr)
        return False

    except subprocess.CalledProcessError as e:
        print(f"错误：openssl 命令失败：{e.stderr}", file=sys.stderr)
        return False


def main():
    config_dir = Path.home() / ".config" / "coach-mcp-connect"
    cert_path = config_dir / "localhost.pem"
    key_path = config_dir / "localhost-key.pem"

    # 检查证书是否已存在
    if cert_path.exists() and key_path.exists():
        print(f"证书已存在：{cert_path}")
        print(f"如需重新生成，请先删除上述文件。")
        return 0

    print("正在生成 TLS 证书...")
    print("")

    success = generate_certificate()

    if success:
        print("")
        print("提示：OAuth 授权时浏览器可能显示安全警告，这是正常的。")
        print("证书仅用于本地回调服务器（127.0.0.1），可安全忽略警告。")
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
