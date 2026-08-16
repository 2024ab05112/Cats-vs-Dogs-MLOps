"""
Helper script to decode KUBECONFIG_BASE64 secret into ~/.kube/config.
Handles:
1. Raw YAML text
2. Single/Double/Multi-pass Base64 encoded strings
3. Strips whitespace, missing base64 padding, and multi-line breaks
"""
import base64
import os

raw = os.environ.get("KUBECONFIG_BASE64", "")
curr = raw
content = None

for _ in range(5):
    if "apiVersion:" in curr or "kind: Config" in curr:
        content = curr.encode("utf-8")
        break
    try:
        s = "".join(curr.split())
        s += "=" * (-len(s) % 4)
        curr = base64.b64decode(s).decode("utf-8", errors="ignore")
    except Exception:
        break

if not content:
    content = curr.encode("utf-8")

target_path = os.path.expanduser("~/.kube/config")
os.makedirs(os.path.dirname(target_path), exist_ok=True)
with open(target_path, "wb") as f:
    f.write(content)

print(f"Kubeconfig successfully written to {target_path} ({len(content)} bytes)")
