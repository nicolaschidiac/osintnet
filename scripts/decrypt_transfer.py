#!/usr/bin/env python3
"""Decrypt an envelope on its destination; never print the plaintext."""
import argparse
import base64
import json
import os
from pathlib import Path
from cryptography.hazmat.primitives import serialization,hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def main():
    p=argparse.ArgumentParser();p.add_argument('directory');p.add_argument('envelope');p.add_argument('output');a=p.parse_args()
    root=Path(a.directory);envelope=json.loads((root/a.envelope).read_text());private=serialization.load_pem_private_key((root/'tunnel-transfer.key').read_bytes(),password=None)
    key=private.decrypt(base64.b64decode(envelope['wrapped_key']),padding.OAEP(mgf=padding.MGF1(hashes.SHA256()),algorithm=hashes.SHA256(),label=None))
    raw=AESGCM(key).decrypt(base64.b64decode(envelope['iv']),base64.b64decode(envelope['ciphertext']),None)
    target=root/a.output
    with target.open('xb')as f:f.write(raw)
    os.chmod(target,0o600)
    if os.geteuid()==0:os.chown(target,root.stat().st_uid,root.stat().st_gid)
    print('Envelope decrypted into protected destination file.')

if __name__=='__main__':main()
