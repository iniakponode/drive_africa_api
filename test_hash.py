#!/usr/bin/env python3
import hashlib

# Test API key
test_key = "FeZGph0Os2oPHofcpgp0NlYODfdzwDSIErBC_105uVs"
hash_value = hashlib.sha256(test_key.encode("utf-8")).hexdigest()
print(f"API Key: {test_key}")
print(f"Hash: {hash_value}")
