#!/usr/bin/env python3
"""COSMOX MCP Server — fetch test suite metrics from cosmosx.cisco.com (no-token only).

This MCP server provides access to 6 no-token COSMOX metrics that work 24/7
without any authentication or token refresh needed:
  - config: Suite configuration, owners, components, run types
  - pass_rate: Pass/fail rates and trends
  - timing: Prep, bringup, execution timing
  - violations: Active policy violations
  - violation_count: Violation count trends
  - violations_trend: Historical violation data

For full documentation: https://cosmosx.cisco.com:81/docs#/
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from cosmox_client import (
    DOCS_URL,
    DOCUMENTED_METRICS,
    VALID_TIME_RANGES,
    CosmoxClient,
)

# No-token COSMOX metrics (6 always-available metrics)
NO_TOKEN_METRICS = set(DOCUMENTED_METRICS.keys())

mcp = FastMCP("COSMOX MCP Server (No-Token)")

_client: CosmoxClient | None = None


def get_client() -> CosmoxClient:
    """Get or create the COSMOX client (no token required)."""
    global _client
    if not _client:
        _client = CosmoxClient(
            docs_base_url=os.environ.get("COSMOX_DOCS_BASE_URL") or "https://cosmosx.cisco.com:81",
            auth_base_url=os.environ.get("COSMOX_AUTH_BASE_URL") or "https://cosmosx.cisco.com:8100",
            access_token="",  # No token required
        )
    return _client


def _json(data: Any) -> str:
    return json.dumps(data, indent=2, default=str)


@mcp.tool()
def cosmox_help_for_llm() -> str:
    """COSMOX MCP guidance — overview of no-token metrics and API docs."""
    return _json(
        {
            "overview": (
                "COSMOX REST APIs for test suites. This MCP uses documented :81 endpoints "
                "which work WITHOUT any token or authentication. Works 24/7 forever."
            ),
            "docs_url": DOCS_URL,
            "openapi_url": "https://cosmosx.cisco.com:81/openapi.json",
            "authentication": "NONE REQUIRED - all metrics work without a token!",
            "available_metrics": {
                k: {
                    "description": v["description"],
                    "endpoint": v["path"],
                    "auth_required": v.get("auth_required", False)
                }
                for k, v in DOCUMENTED_METRICS.items()
            },
            "tools": {
                "list_available_metrics": "Show all 6 no-token metrics",
                "get_testsuite_metric": "Fetch one metric for a suite",
                "get_testsuite_metrics": "Fetch multiple metrics for a suite",
                "search_testsuites": "Search suites by name, owner, component",
            },
            "example": (
                "get_testsuite_metrics(testsuite_name='ulh_suite', "
                "metrics=['pass_rate','violations','timing'])"
            ),
            "time_ranges": list(VALID_TIME_RANGES),
            "defaults": {"time_range": "3m", "os_branch": "XR:xr-dev", "run_type": "nightly"},
        }
    )


@mcp.tool()
def list_available_metrics() -> str:
    """List the 6 no-token COSMOX metrics available in this MCP."""
    return _json(
        {
            "docs_url": DOCS_URL,
            "message": "All metrics work WITHOUT any token or authentication!",
            "available_metrics": {
                k: {
                    "description": v["description"],
                    "endpoint": v["path"],
                    "method": v["method"],
                }
                for k, v in DOCUMENTED_METRICS.items()
            },
            "time_ranges": list(VALID_TIME_RANGES),
            "defaults": {"time_range": "3m", "os_branch": "XR:xr-dev", "run_type": "nightly"},
        }
    )


@mcp.tool()
def get_testsuite_metric(
    testsuite_name: str,
    metric: str,
    os_branch: str = "XR:xr-dev",
    time_range: str = "3m",
    run_type: str = "nightly",
) -> str:
    """Fetch one no-token COSMOX metric. See list_available_metrics and https://cosmosx.cisco.com:81/docs#/"""
    metric_clean = metric.replace("-", "_")
    if metric_clean not in NO_TOKEN_METRICS:
        return _json(
            {
                "error": f"Metric '{metric}' is not available (requires token)",
                "available_no_token_metrics": sorted(NO_TOKEN_METRICS),
            }
        )
    return _json(
        get_client().get_metric(
            metric=metric,
            testsuite_name=testsuite_name,
            os_branch=os_branch,
            time_range=time_range,
            run_type=run_type,
        )
    )


@mcp.tool()
def get_testsuite_metrics(
    testsuite_name: str,
    metrics: list[str],
    os_branch: str = "XR:xr-dev",
    time_range: str = "3m",
    run_type: str = "nightly",
) -> str:
    """Fetch multiple no-token COSMOX metrics for one suite."""
    # Validate all metrics are no-token
    invalid = []
    for m in metrics:
        m_clean = m.replace("-", "_")
        if m_clean not in NO_TOKEN_METRICS:
            invalid.append(m)

    if invalid:
        return _json(
            {
                "error": f"These metrics require a token: {invalid}",
                "available_no_token_metrics": sorted(NO_TOKEN_METRICS),
            }
        )

    return _json(
        get_client().get_suite_metrics(
            testsuite_name=testsuite_name,
            metrics=metrics,
            os_branch=os_branch,
            time_range=time_range,
            run_type=run_type,
        )
    )


@mcp.tool()
def search_testsuites(
    testsuite_names: str = "",
    os_branch: str = "XR:xr-dev",
    user_id: str = "",
    comp_name: str = "",
    page: int = 0,
    size: int = 50,
) -> str:
    """Search suites via documented v2 configs API (no token required)."""
    return _json(
        get_client().search_testsuites(
            testsuite_names=testsuite_names,
            os_branch=os_branch,
            user_id=user_id,
            comp_name=comp_name,
            page=page,
            size=size,
        )
    )


if __name__ == "__main__":
    mcp.run()
