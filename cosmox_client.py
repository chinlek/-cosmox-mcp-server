"""HTTP client for the COSMOX REST API.

Official API docs (Swagger): https://cosmosx.cisco.com:81/docs#/
OpenAPI spec: https://cosmosx.cisco.com:81/openapi.json

Most documented endpoints on port 81 work without a token from the Cisco network.
Undocumented UI endpoints (suite details, ci-tests, insight tiles) require a Bearer
token from https://cosmosx.cisco.com SSO login (localStorage `access_token`) against
port 8100.
"""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import urlencode

import httpx

DOCS_BASE_URL = "https://cosmosx.cisco.com:81"
AUTH_BASE_URL = "https://cosmosx.cisco.com:8100"
DOCS_URL = "https://cosmosx.cisco.com:81/docs#/"

DOCUMENTED_METRICS: dict[str, dict[str, Any]] = {
    "config": {
        "path": "/api/v2/testsuites/configs",
        "method": "GET",
        "base": "docs",
        "auth_required": False,
        "description": "Suite configuration (owners, run types, components)",
    },
    "pass_rate": {
        "path": "/api/v1/testsuites/tests/{run_type}/trend",
        "method": "GET",
        "base": "docs",
        "auth_required": False,
        "description": "Nightly/precommit pass rate trend",
        "path_params": {"run_type": "nightly"},
    },
    "timing": {
        "path": "/api/v1/testsuites/timing",
        "method": "GET",
        "base": "docs",
        "auth_required": False,
        "description": "Average prep/bringup/execution/total timing",
    },
    "violations": {
        "path": "/api/v1/testsuites/violations",
        "method": "GET",
        "base": "docs",
        "auth_required": False,
        "description": "Active policy violations (V.A1, V.A15, etc.)",
    },
    "violation_count": {
        "path": "/api/v1/testsuites/violation-count/trend",
        "method": "GET",
        "base": "docs",
        "auth_required": False,
        "description": "Violation and pipeline-access trend",
    },
    "violations_trend": {
        "path": "/api/v1/testsuites/violations/trend",
        "method": "GET",
        "base": "docs",
        "auth_required": False,
        "description": "Violation count trend across suites",
    },
}

AUTHENTICATED_METRICS: dict[str, dict[str, Any]] = {
    "details": {
        "path": "/api/v1/testsuites/details",
        "method": "GET",
        "base": "auth",
        "auth_required": True,
        "description": "Full suite metadata from the UI details tab",
    },
    "runtime": {
        "path": "/api/v1/ci-tests/runtime",
        "method": "POST",
        "base": "auth",
        "auth_required": True,
        "description": "Suite runtime formula metrics",
    },
    "stability": {
        "path": "/api/v1/ci-tests/stability",
        "method": "POST",
        "base": "auth",
        "auth_required": True,
        "description": "Suite stability score",
    },
    "timing_breakdown": {
        "path": "/api/v1/ci-tests/timing-breakdown",
        "method": "POST",
        "base": "auth",
        "auth_required": True,
        "description": "Detailed timing breakdown from ci-tests API",
    },
    "failure_rate": {
        "path": "/api/v1/testsuites/failure-rate",
        "method": "POST",
        "base": "auth",
        "auth_required": True,
        "description": "Failure rate insight tile",
    },
    "healthiness": {
        "path": "/api/v1/testsuites/healthiness",
        "method": "POST",
        "base": "auth",
        "auth_required": True,
        "description": "Healthiness insight tile",
    },
    "run_count": {
        "path": "/api/v1/testsuites/run-count",
        "method": "POST",
        "base": "auth",
        "auth_required": True,
        "description": "Run count insight tile",
    },
    "known_breakage": {
        "path": "/api/v1/testsuites/known-breakage",
        "method": "POST",
        "base": "auth",
        "auth_required": True,
        "description": "Known breakage ratio insight tile",
    },
}

ALL_METRICS = {**DOCUMENTED_METRICS, **AUTHENTICATED_METRICS}
VALID_TIME_RANGES = ("1m", "3m", "6m", "1y", "2y", "all", "14d", "28d", "7d", "90d")


class CosmoxClient:
    def __init__(
        self,
        docs_base_url: str | None = None,
        auth_base_url: str | None = None,
        access_token: str | None = None,
        timeout: float = 60.0,
    ) -> None:
        self.docs_base_url = (
            docs_base_url or os.environ.get("COSMOX_DOCS_BASE_URL") or DOCS_BASE_URL
        ).rstrip("/")
        self.auth_base_url = (
            auth_base_url or os.environ.get("COSMOX_AUTH_BASE_URL") or AUTH_BASE_URL
        ).rstrip("/")
        self.access_token = access_token or os.environ.get("COSMOX_ACCESS_TOKEN", "")
        self.timeout = timeout

    def _headers(self, json_body: bool = False) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if json_body:
            headers["Content-Type"] = "application/json"
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        *,
        base: str = "docs",
    ) -> dict[str, Any]:
        base_url = self.auth_base_url if base == "auth" else self.docs_base_url
        url = f"{base_url}{path}"
        clean_params = {k: v for k, v in (params or {}).items() if v is not None and v != ""}

        try:
            with httpx.Client(timeout=self.timeout, verify=True) as client:
                if method.upper() == "GET":
                    response = client.get(url, params=clean_params, headers=self._headers())
                else:
                    response = client.post(
                        url,
                        params=clean_params,
                        json={},
                        headers=self._headers(json_body=True),
                    )

                if response.status_code == 401:
                    return {
                        "error": (
                            "Unauthorized. For authenticated endpoints, set COSMOX_ACCESS_TOKEN "
                            "(from https://cosmosx.cisco.com → DevTools → localStorage → access_token). "
                            "Documented endpoints on :81 often work without a token — see "
                            f"{DOCS_URL}"
                        )
                    }

                response.raise_for_status()
                if not response.content:
                    return {"data": None}
                return response.json()
        except httpx.HTTPStatusError as exc:
            body = exc.response.text[:500]
            return {"error": f"HTTP {exc.response.status_code} for {path}: {body}"}
        except httpx.RequestError as exc:
            return {"error": f"Request failed for {path}: {exc}"}

    @staticmethod
    def split_os_branch(os_branch: str) -> tuple[str, str]:
        if ":" in os_branch:
            os_name, branch = os_branch.split(":", 1)
            return os_name, branch
        return "XR", os_branch

    def build_suite_params(
        self,
        testsuite_name: str,
        os_branch: str = "XR:xr-dev",
        time_range: str = "3m",
        run_type: str = "nightly",
        agg_type: str = "avg",
        time_interval: str = "1d",
        user_id: str = "",
        comp_name: str = "",
        testsuite_range: str = "14d",
    ) -> dict[str, Any]:
        os_name, branch = self.split_os_branch(os_branch)
        return {
            "testsuiteName": testsuite_name,
            "testsuite": testsuite_name,
            "testsuiteNames": testsuite_name,
            "osBranch": os_branch,
            "os": os_name,
            "branch": branch,
            "timeRange": time_range,
            "runType": run_type,
            "aggType": agg_type,
            "timeInterval": time_interval,
            "timeZone": "America/Los_Angeles",
            "userId": user_id,
            "compName": comp_name,
            "testsuiteRange": testsuite_range,
        }

    def get_metric(
        self,
        metric: str,
        testsuite_name: str,
        os_branch: str = "XR:xr-dev",
        time_range: str = "3m",
        run_type: str = "nightly",
        **extra: Any,
    ) -> dict[str, Any]:
        metric_key = metric.replace("-", "_")
        spec = ALL_METRICS.get(metric_key)
        if not spec:
            return {
                "error": f"Unknown metric '{metric}'. Use list_available_metrics.",
                "available": sorted(ALL_METRICS.keys()),
            }

        if spec["auth_required"] and not self.access_token:
            return {
                "error": (
                    f"Metric '{metric_key}' requires COSMOX_ACCESS_TOKEN. "
                    f"See {DOCS_URL} for documented no-token alternatives, or log in at "
                    "https://cosmosx.cisco.com and copy localStorage access_token."
                ),
                "docs_url": DOCS_URL,
                "no_token_alternatives": sorted(DOCUMENTED_METRICS.keys()),
            }

        path = spec["path"]
        path_params = dict(spec.get("path_params") or {})
        if "{run_type}" in path:
            path_params["run_type"] = extra.get("run_type", run_type)
        for key, value in path_params.items():
            path = path.replace(f"{{{key}}}", str(value))

        params = self.build_suite_params(
            testsuite_name=testsuite_name,
            os_branch=os_branch,
            time_range=time_range,
            run_type=run_type,
            agg_type=extra.get("agg_type", "avg"),
            user_id=extra.get("user_id", ""),
            comp_name=extra.get("comp_name", ""),
        )

        data = self._request(
            spec["method"],
            path,
            params,
            base=spec["base"],
        )
        return {
            "metric": metric_key,
            "testsuite": testsuite_name,
            "os_branch": os_branch,
            "time_range": time_range,
            "endpoint": path,
            "api_base": self.docs_base_url if spec["base"] == "docs" else self.auth_base_url,
            "auth_required": spec["auth_required"],
            "description": spec["description"],
            "docs_url": DOCS_URL,
            "cosmosx_url": self.suite_insights_url(testsuite_name, os_branch, time_range),
            "result": data,
        }

    def get_suite_metrics(
        self,
        testsuite_name: str,
        metrics: list[str],
        os_branch: str = "XR:xr-dev",
        time_range: str = "3m",
        run_type: str = "nightly",
    ) -> dict[str, Any]:
        return {
            "testsuite": testsuite_name,
            "os_branch": os_branch,
            "time_range": time_range,
            "docs_url": DOCS_URL,
            "cosmosx_url": self.suite_insights_url(testsuite_name, os_branch, time_range),
            "metrics": {
                metric: self.get_metric(
                    metric=metric,
                    testsuite_name=testsuite_name,
                    os_branch=os_branch,
                    time_range=time_range,
                    run_type=run_type,
                )
                for metric in metrics
            },
        }

    def search_testsuites(
        self,
        testsuite_names: str = "",
        os_branch: str = "XR:xr-dev",
        user_id: str = "",
        comp_name: str = "",
        page: int = 0,
        size: int = 50,
    ) -> dict[str, Any]:
        os_name, branch = self.split_os_branch(os_branch)
        params = {
            "testsuiteNames": testsuite_names,
            "osBranch": os_branch,
            "os": os_name,
            "branch": branch,
            "userId": user_id,
            "compName": comp_name,
            "page": page,
            "size": size,
        }
        return self._request("GET", "/api/v2/testsuites/configs", params, base="docs")

    @staticmethod
    def suite_insights_url(testsuite_name: str, os_branch: str, time_range: str) -> str:
        query = urlencode(
            {
                "tab": "insights",
                "os_branch": os_branch,
                "testsuite": testsuite_name,
                "time_range": time_range,
            }
        )
        return f"https://cosmosx.cisco.com/testsuites/testsuite?{query}"
