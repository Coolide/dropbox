import datetime
import ipaddress
import socket
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


def _local_ip_addresses() -> list[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    """Return all non-loopback IPs assigned to this machine.

    We connect a UDP socket to a public address (no data is sent) purely to
    discover which local interface the OS would use — a reliable cross-platform
    trick to find the LAN IP without parsing ifconfig output.
    """
    ips: list[ipaddress.IPv4Address | ipaddress.IPv6Address] = [ipaddress.ip_address("127.0.0.1")]
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            lan_ip = s.getsockname()[0]
            ips.append(ipaddress.ip_address(lan_ip))
    except OSError:
        pass
    return ips


def ensure_certs(
    cert_dir: str | Path,
    extra_ips: list[str] | None = None,
    extra_hostnames: list[str] | None = None,
) -> tuple[Path, Path]:
    d = Path(cert_dir)
    d.mkdir(parents=True, exist_ok=True)
    cert_path = d / "cert.pem"
    key_path = d / "key.pem"

    if cert_path.exists() and key_path.exists():
        return cert_path, key_path

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "dropbox-sync")])

    # Build SAN entries — always include localhost + all local IPs
    san_dns = [x509.DNSName("localhost")]
    san_ips = [x509.IPAddress(ip) for ip in _local_ip_addresses()]

    for hostname in extra_hostnames or []:
        san_dns.append(x509.DNSName(hostname))
    for ip_str in extra_ips or []:
        san_ips.append(x509.IPAddress(ipaddress.ip_address(ip_str)))

    detected_ips = [str(ip) for ip in _local_ip_addresses()]
    print(f"[tls] Generating cert valid for: {detected_ips}")

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.UTC))
        .not_valid_after(datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=365))
        .add_extension(
            x509.SubjectAlternativeName(san_dns + san_ips),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )

    key_path.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        )
    )
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    print(f"[tls] Generated self-signed cert → {cert_path}")
    return cert_path, key_path
