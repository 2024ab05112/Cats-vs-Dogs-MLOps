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

# ── Sanitize YAML control characters (\r, \x00, etc.) ─────────────────────────
import string
text_str = content.decode("utf-8", errors="ignore")
printable_set = set(string.printable)
cleaned_str = "".join(c for c in text_str if c in printable_set or c in ("\n", "\t")).replace("\r", "")
final_bytes = cleaned_str.encode("utf-8")

target_path = os.path.expanduser("~/.kube/config")
os.makedirs(os.path.dirname(target_path), exist_ok=True)
with open(target_path, "wb") as f:
    f.write(final_bytes)

print(f"Kubeconfig successfully written to {target_path} ({len(final_bytes)} bytes)")
