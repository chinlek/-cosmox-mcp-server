#!/bin/bash
# Test COSMOX MCP Server Metrics

cd /nobackup/lcv/cosmox-mcp-server

echo "================================"
echo "COSMOX Metrics Test Suite"
echo "================================"
echo ""

# Test 1: Health Check
echo "1️⃣  Health Check"
/auto/smartdev/bin/python3.10 << 'EOF'
import sys
sys.path.insert(0, '/nobackup/lcv/cosmox-mcp-server')
from cosmox_client import CosmoxClient

env_vars = {}
with open('.env', 'r') as f:
    for line in f:
        if '=' in line:
            key, val = line.strip().split('=', 1)
            env_vars[key] = val

print(f"✅ Token loaded: {len(env_vars['COSMOX_ACCESS_TOKEN'])} chars")
print(f"✅ Docs URL: {env_vars['COSMOX_DOCS_BASE_URL']}")
print(f"✅ Auth URL: {env_vars['COSMOX_AUTH_BASE_URL']}")
EOF
echo ""

# Test 2: All Metrics
echo "2️⃣  Test All 14 Metrics on ulh_suite"
/auto/smartdev/bin/python3.10 << 'EOF'
import sys
sys.path.insert(0, '/nobackup/lcv/cosmox-mcp-server')
from cosmox_client import CosmoxClient

env_vars = {}
with open('.env', 'r') as f:
    for line in f:
        if '=' in line:
            key, val = line.strip().split('=', 1)
            env_vars[key] = val

client = CosmoxClient(env_vars['COSMOX_DOCS_BASE_URL'], env_vars['COSMOX_AUTH_BASE_URL'], env_vars['COSMOX_ACCESS_TOKEN'])

metrics = ['runtime', 'stability', 'failure_rate', 'run_count', 'healthiness', 'known_breakage', 'details', 'timing_breakdown', 'pass_rate', 'violations', 'timing', 'violation_count', 'config', 'violations_trend']
suite = 'ulh_suite'

success = 0
for metric in metrics:
    result = client.get_metric(metric, testsuite_name=suite)
    if isinstance(result, dict) and 'error' not in result.get('result', {}):
        print(f"✅ {metric}")
        success += 1
    else:
        print(f"❌ {metric}")

print(f"\n{success}/{len(metrics)} metrics working!")
EOF
echo ""

# Test 3: Multiple Suites
echo "3️⃣  Test on Multiple Suites"
/auto/smartdev/bin/python3.10 << 'EOF'
import sys
sys.path.insert(0, '/nobackup/lcv/cosmox-mcp-server')
from cosmox_client import CosmoxClient

env_vars = {}
with open('.env', 'r') as f:
    for line in f:
        if '=' in line:
            key, val = line.strip().split('=', 1)
            env_vars[key] = val

client = CosmoxClient(env_vars['COSMOX_DOCS_BASE_URL'], env_vars['COSMOX_AUTH_BASE_URL'], env_vars['COSMOX_ACCESS_TOKEN'])

suites = ['ulh_suite', 'kepler_cheetah_c2', 'bgp_test']
for suite in suites:
    result = client.get_metric('runtime', testsuite_name=suite)
    if isinstance(result, dict) and 'error' not in result.get('result', {}):
        print(f"✅ {suite}")
    else:
        print(f"❌ {suite}")
EOF
echo ""

echo "✅ Test complete!"
