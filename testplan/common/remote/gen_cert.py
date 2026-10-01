"""
Make a self-signed EC key and cert. Runs on local or remote host.
"""

import argparse
import datetime
import os
from typing import Optional, Sequence

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

KEY_NAME = "key.pem"
CERT_NAME = "cert.pem"


def generate(out_dir: str, name: str, hours: int = 24) -> None:
    """
    Write ``key.pem`` (mode 0600) and ``cert.pem`` into ``out_dir``.
    """
    key = ec.generate_private_key(ec.SECP256R1())
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, name)])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        # allow for clock skew between hosts
        .not_valid_before(now - datetime.timedelta(minutes=5))
        .not_valid_after(now + datetime.timedelta(hours=hours))
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), True)
        .sign(key, hashes.SHA256())
    )

    os.makedirs(out_dir, mode=0o700, exist_ok=True)
    key_path = os.path.join(out_dir, KEY_NAME)
    fd = os.open(key_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(
            key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            )
        )
    with open(os.path.join(out_dir, CERT_NAME), "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))


def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--hours", type=int, default=24)
    args = parser.parse_args(argv)
    generate(args.out_dir, args.name, args.hours)


if __name__ == "__main__":
    main()
