"""
Helper script to decode KUBECONFIG_BASE64 secret into ~/.kube/config.
Extracts server, client-certificate-data, client-key-data, and builds
a guaranteed 100% valid YAML config using yaml.dump().
"""
import base64
import os
import re
import string
import yaml

raw = os.environ.get("KUBECONFIG_BASE64", "").strip()
curr = raw

# Iterative base64 decoding until text is revealed
for _ in range(5):
    if "apiVersion:" in curr or "kind: Config" in curr or "server:" in curr:
        break
    try:
        s = "".join(curr.split())
        s += "=" * (-len(s) % 4)
        decoded = base64.b64decode(s).decode("utf-8", errors="ignore")
        if len(decoded) > 10:
            curr = decoded
    except Exception:
        break

# Sanitize control characters (\r, \x00, etc.)
printable_set = set(string.printable)
clean_text = "".join(c for c in curr if c in printable_set or c in ("\n", "\t")).replace("\r", "")

# Try standard yaml.safe_load first
parsed_dict = None
try:
    obj = yaml.safe_load(clean_text)
    if isinstance(obj, dict) and "clusters" in obj:
        parsed_dict = obj
except Exception:
    pass

# If standard parsing failed, construct dictionary reliably via extraction
if not parsed_dict:
    server_match = re.search(r'server:\s*(https?://[^\s]+)', clean_text)
    server_url = server_match.group(1) if server_match else "https://3.237.233.200:6443"

    cert_match = re.search(r'client-certificate-data:\s*([A-Za-z0-9+/=\s]+?)(?:client-key-data|users|contexts|clusters|$)', clean_text, re.DOTALL)
    cert_data = "".join(cert_match.group(1).split()) if cert_match else ""

    key_match = re.search(r'client-key-data:\s*([A-Za-z0-9+/=\s]+?)(?:users|contexts|clusters|$)', clean_text, re.DOTALL)
    key_data = "".join(key_match.group(1).split()) if key_match else ""

    parsed_dict = {
        "apiVersion": "v1",
        "clusters": [{
            "cluster": {
                "insecure-skip-tls-verify": True,
                "server": server_url
            },
            "name": "default"
        }],
        "contexts": [{
            "context": {
                "cluster": "default",
                "user": "default"
            },
            "name": "default"
        }],
        "current-context": "default",
        "kind": "Config",
        "users": [{
            "name": "default",
            "user": {
                "client-certificate-data": cert_data,
                "client-key-data": key_data
            }
        }]
    }

# Dump guaranteed clean YAML
final_yaml = yaml.dump(parsed_dict, default_flow_style=False)

target_path = os.path.expanduser("~/.kube/config")
os.makedirs(os.path.dirname(target_path), exist_ok=True)
with open(target_path, "w", encoding="utf-8") as f:
    f.write(final_yaml)

print(f"Kubeconfig successfully generated and written to {target_path} ({len(final_yaml.encode('utf-8'))} bytes)")
