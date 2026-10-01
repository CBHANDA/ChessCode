"""AES-256-GCM file vault. Key = PBKDF2-HMAC-SHA256(password, salt).
File format: MAGIC | salt(16) | nonce(12) | ciphertext+tag"""
import os, sys
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.exceptions import InvalidTag

MAGIC = b"CHESSVLT1"


def _key(password: str, salt: bytes) -> bytes:
    return PBKDF2HMAC(hashes.SHA256(), 32, salt, 300_000).derive(password.encode())


def encrypt_file(src, password, dst=None):
    salt, nonce = os.urandom(16), os.urandom(12)
    data = open(src, "rb").read()
    name = os.path.basename(src).encode()
    blob = len(name).to_bytes(2, "big") + name + data  # keep original filename inside
    out = MAGIC + salt + nonce + AESGCM(_key(password, salt)).encrypt(nonce, blob, MAGIC)
    dst = dst or src + ".vault"
    open(dst, "wb").write(out)
    return dst


def decrypt_file(src, password, outdir):
    raw = open(src, "rb").read()
    if not raw.startswith(MAGIC):
        raise ValueError("Not a vault file.")
    salt, nonce, body = raw[9:25], raw[25:37], raw[37:]
    try:
        blob = AESGCM(_key(password, salt)).decrypt(nonce, body, MAGIC)
    except InvalidTag:
        raise ValueError("Wrong password or corrupted file.")
    n = int.from_bytes(blob[:2], "big")
    name = os.path.basename(blob[2:2 + n].decode())
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, name)
    open(path, "wb").write(blob[2 + n:])
    return path


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "lock":
        print("Created", encrypt_file(sys.argv[2], sys.argv[3]))
    else:
        print("Usage: python vault.py lock <file> <password>")
