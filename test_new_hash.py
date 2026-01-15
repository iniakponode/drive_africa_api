#!/usr/bin/env python3
import hashlib

key = "02QDlql_JlwQXjdcj-Awsw8gBPs06-6JEP-aasDKf38"
hash_value = hashlib.sha256(key.encode("utf-8")).hexdigest()
print(f"Key: {key}")
print(f"Hash: {hash_value}")
print(f"Prefix: {hash_value[:20]}")
