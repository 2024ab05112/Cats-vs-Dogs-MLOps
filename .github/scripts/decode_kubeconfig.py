"""
Helper script to decode KUBECONFIG_BASE64 secret into ~/.kube/config.
Handles:
1. Decoding secret (tolerates being base64-encoded multiple times)
2. Structural validation
"""
import base64
import sys
import os
import yaml

raw = os.environ.get("KUBECONFIG_BASE64", "").strip()
curr = raw

if not curr:
    print("Error: KUBECONFIG_BASE64 secret is empty.", file=sys.stderr)
    sys.exit(1)

# Iterative base64 decoding in case the secret was encoded more than once
for _ in range(5):
    if "apiVersion:" in curr or "kind: Config" in curr:
        break
    try:
        s = "".join(curr.split())
        s += "=" * (-len(s) % 4)
        decoded = base64.b64decode(s).decode("utf-8", errors="ignore")
        if len(decoded) > 10:
            curr = decoded
    except Exception:
        break

# Validate certificate data presence
valid = False
try:
    data = yaml.safe_load(curr)
    if isinstance(data, dict) and "users" in data and len(data["users"]) > 0:
        user_entry = data["users"][0].get("user", {})
        cert = user_entry.get("client-certificate-data", "")
        if len(cert) > 50:
            valid = True
except Exception:
    pass

if not valid:
    print(
        "Error: KUBECONFIG_BASE64 secret decoded but did not produce a valid "
        "kubeconfig with certificate data. Update the GitHub secret with a "
        "current kubeconfig for the target cluster.",
        file=sys.stderr,
    )
    sys.exit(1)

target_path = os.path.expanduser("~/.kube/config")
os.makedirs(os.path.dirname(target_path), exist_ok=True)
with open(target_path, "w", encoding="utf-8") as f:
    f.write(curr)

print(f"Kubeconfig successfully written to {target_path} ({len(curr.encode('utf-8'))} bytes)")
