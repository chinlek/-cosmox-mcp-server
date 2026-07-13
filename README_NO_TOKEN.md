# COSMOX MCP Server - No-Token Edition

**Production-ready COSMOX metrics MCP that works 24/7 without any authentication or token refresh.**

## Features

✅ **6 Always-Available Metrics** (no token needed):
- `config` - Suite configuration, owners, components, run types
- `pass_rate` - Pass/fail rates and trends (nightly/precommit)
- `timing` - Prep, bringup, execution, and total timing
- `violations` - Active policy violations (V.A1, V.A15, etc.)
- `violation_count` - Violation count trends over time
- `violations_trend` - Historical violation trends

✅ **Zero Maintenance**
- No token refresh needed
- No cron jobs or automation
- Works forever without any action

✅ **Production Ready**
- HTTP error handling
- JSON output for all metrics
- Search suites by name, owner, component

---

## Quick Start

### 1. Start the MCP Server

```bash
cd /nobackup/lcv/cosmox-mcp-server
/auto/smartdev/bin/python3.10 -m pip install -r requirements.txt  # One-time
/auto/smartdev/bin/python3.10 server.py
```

Server will start on localhost and be ready for MCP calls.

### 2. Use in VS Code

In `.vscode/settings.json`, configure the MCP client:
```json
{
  "mcpServers": {
    "cosmox": {
      "command": "/auto/smartdev/bin/python3.10",
      "args": ["/nobackup/lcv/cosmox-mcp-server/server.py"]
    }
  }
}
```

### 3. Use via CLI

```bash
# Get all metrics for a suite
/auto/smartdev/bin/python3.10 << 'EOF'
import sys
sys.path.insert(0, '/nobackup/lcv/cosmox-mcp-server')
from cosmox_client import CosmoxClient

client = CosmoxClient(
    docs_base_url="https://cosmosx.cisco.com:81",
    auth_base_url="https://cosmosx.cisco.com:8100",
    access_token=""  # No token needed!
)

result = client.get_metric('pass_rate', testsuite_name='ulh_suite')
print(result)
EOF
```

---

## Available MCP Tools

### `cosmox_help_for_llm()`
Returns overview of all available metrics and endpoints.

### `list_available_metrics()`
Lists the 6 no-token metrics with descriptions and parameters.

### `get_testsuite_metric(testsuite_name, metric, ...)`
Fetch a single metric for a suite.

**Parameters:**
- `testsuite_name` (required): Suite name (e.g., "ulh_suite")
- `metric` (required): One of: config, pass_rate, timing, violations, violation_count, violations_trend
- `os_branch` (optional): Default "XR:xr-dev"
- `time_range` (optional): "3m", "1h", "1d", "7d" (default "3m")
- `run_type` (optional): "nightly", "precommit" (default "nightly")

### `get_testsuite_metrics(testsuite_name, metrics, ...)`
Fetch multiple metrics for a suite.

**Parameters:**
- `testsuite_name` (required): Suite name
- `metrics` (required): List of metric names (e.g., ["pass_rate", "violations", "timing"])
- `os_branch`, `time_range`, `run_type`: Same as single metric

### `search_testsuites(testsuite_names, os_branch, user_id, comp_name, ...)`
Search for test suites.

**Parameters:**
- `testsuite_names` (optional): Name pattern (e.g., "ulh")
- `user_id` (optional): Filter by owner
- `comp_name` (optional): Filter by component
- `os_branch` (optional): Default "XR:xr-dev"

---

## Limitations (Token-Only Metrics)

These metrics require COSMOX token refresh (not included in this MCP):
- `runtime` - Real-time performance metrics
- `stability` - Stability score
- `failure_rate` - Test failure analysis
- `run_count` - Number of test executions
- `healthiness` - Suite health
- `known_breakage` - Known issues

For these, see [TOKEN_REFRESH_GUIDE.md](TOKEN_REFRESH_GUIDE.md) if you need hourly token refresh.

---

## Configuration

### Environment Variables (Optional)

```bash
# Defaults to https://cosmosx.cisco.com:81
export COSMOX_DOCS_BASE_URL=https://cosmosx.cisco.com:81

# Defaults to https://cosmosx.cisco.com:8100
export COSMOX_AUTH_BASE_URL=https://cosmosx.cisco.com:8100
```

### .env File (Optional)

Create `.env` in workspace root (not needed for no-token operation):
```
COSMOX_DOCS_BASE_URL=https://cosmosx.cisco.com:81
COSMOX_AUTH_BASE_URL=https://cosmosx.cisco.com:8100
```

---

## Testing

### Quick Health Check

```bash
/auto/smartdev/bin/python3.10 test_metrics.sh
```

### Manual Test

```bash
/auto/smartdev/bin/python3.10 << 'EOF'
import sys
sys.path.insert(0, '/nobackup/lcv/cosmox-mcp-server')
from cosmox_client import CosmoxClient

client = CosmoxClient(
    "https://cosmosx.cisco.com:81",
    "https://cosmosx.cisco.com:8100",
    ""  # Empty token = no auth
)

# Test each metric
metrics = ['config', 'pass_rate', 'timing', 'violations', 'violation_count', 'violations_trend']
for m in metrics:
    result = client.get_metric(m, testsuite_name='ulh_suite')
    print(f"{m}: {'✅' if 'error' not in result.get('result', {}) else '❌'}")
EOF
```

---

## Troubleshooting

### Metric returns error
- Check metric name is one of: config, pass_rate, timing, violations, violation_count, violations_trend
- Verify suite name exists
- Try different `time_range` values

### Server won't start
```bash
# Install dependencies
/auto/smartdev/bin/python3.10 -m pip install -r requirements.txt

# Run with debug
/auto/smartdev/bin/python3.10 -u server.py
```

### Connection refused
- Ensure server is running: `ps aux | grep "python3.10.*server.py"`
- Check port availability: `netstat -tuln | grep 8000`

---

## Architecture

```
┌─────────────────────────────────────────────┐
│         VS Code / Claude Chat                │
└──────────────┬──────────────────────────────┘
               │ MCP Protocol
┌──────────────▼──────────────────────────────┐
│      server.py (FastMCP Server)             │
│  - cosmox_help_for_llm()                   │
│  - list_available_metrics()                │
│  - get_testsuite_metric()                  │
│  - get_testsuite_metrics()                 │
│  - search_testsuites()                     │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│    cosmox_client.py (HTTP Client)           │
│  - Constructs API requests                 │
│  - Handles timeouts & retries              │
│  - Returns JSON responses                  │
└──────────────┬──────────────────────────────┘
               │ HTTPS
┌──────────────▼──────────────────────────────┐
│   COSMOX REST API (port :81)               │
│   - No authentication required             │
│   - Public documented endpoints            │
│   - Always available                       │
└─────────────────────────────────────────────┘
```

---

## API Documentation

Full COSMOX API docs: https://cosmosx.cisco.com:81/docs#/

OpenAPI spec: https://cosmosx.cisco.com:81/openapi.json

---

## Support

For COSMOX API issues, see official docs at https://cosmosx.cisco.com:81/docs

For MCP server issues:
- Check error messages in terminal
- Verify API connectivity: `curl https://cosmosx.cisco.com:81/api/v2/testsuites/configs?testsuite=ulh_suite`
- Ensure Python 3.10+ is in use

---

## License

Internal tool for Cisco employees.
