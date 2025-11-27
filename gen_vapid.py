#!/usr/bin/env python3
import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

# Generar par de claves
private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
public_key = private_key.public_key()

# Exportar clave privada en formato raw
private_numbers = private_key.private_numbers()
private_bytes = private_numbers.private_value.to_bytes(32, 'big')
private_b64 = base64.urlsafe_b64encode(private_bytes).decode().rstrip('=')

# Exportar clave pública en formato uncompressed
public_bytes = public_key.public_bytes(
    encoding=serialization.Encoding.X962,
    format=serialization.PublicFormat.UncompressedPoint
)
public_b64 = base64.urlsafe_b64encode(public_bytes).decode().rstrip('=')

print(f'VAPID_PUBLIC_KEY={public_b64}')
print(f'VAPID_PRIVATE_KEY={private_b64}')
