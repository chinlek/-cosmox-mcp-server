cd ~/cosmox-mcp-server
python3 -m pip install -r requirements.txt
# Quick API test (no token needed)
python3 - <<'PY'
from cosmox_client import CosmoxClient
c = CosmoxClient()
print(c.get_metric("violations", "kepler_cheetah_c2"))
PY
