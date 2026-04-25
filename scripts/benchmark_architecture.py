#!/usr/bin/env python3
"""Benchmark selected StayFit API endpoints for architecture analysis.

Run once against the monolith (`python backend/run.py`) and once against the
microservices gateway (`python backend/start_microservices.py`). Use the same
base URL in both cases so the frontend API contract is unchanged.
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
import urllib.error
import urllib.request


DEFAULT_ENDPOINTS = [
    "/api/analytics/daily",
    "/api/analytics/weekly",
    "/api/meals/today",
    "/api/auth/profile",
]


def percentile(values: list[float], percentile_value: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = (len(ordered) - 1) * percentile_value
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    if lower == upper:
        return ordered[lower]
    weight = index - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def request_once(base_url: str, endpoint: str, token: str, timeout: float) -> tuple[int, float]:
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}{endpoint}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        },
        method="GET",
    )

    start = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response.read()
            status = response.status
    except urllib.error.HTTPError as exc:
        exc.read()
        status = exc.code
    except urllib.error.URLError:
        status = 0
    elapsed_ms = (time.perf_counter() - start) * 1000
    return status, elapsed_ms


def benchmark_endpoint(
    base_url: str,
    endpoint: str,
    token: str,
    warmups: int,
    requests_count: int,
    timeout: float,
) -> dict[str, float | int | str]:
    for _ in range(warmups):
        request_once(base_url, endpoint, token, timeout)

    timings: list[float] = []
    statuses: dict[int, int] = {}
    measured_start = time.perf_counter()
    for _ in range(requests_count):
        status, elapsed_ms = request_once(base_url, endpoint, token, timeout)
        timings.append(elapsed_ms)
        statuses[status] = statuses.get(status, 0) + 1
    measured_seconds = time.perf_counter() - measured_start
    throughput_rps = requests_count / measured_seconds if measured_seconds > 0 else 0

    return {
        "endpoint": endpoint,
        "requests": requests_count,
        "status_counts": json.dumps(statuses, sort_keys=True),
        "throughput_rps": round(throughput_rps, 2),
        "avg_ms": round(statistics.mean(timings), 2),
        "p50_ms": round(percentile(timings, 0.50), 2),
        "p95_ms": round(percentile(timings, 0.95), 2),
        "min_ms": round(min(timings), 2),
        "max_ms": round(max(timings), 2),
    }


def print_markdown_table(results: list[dict[str, float | int | str]], label: str) -> None:
    print(f"\n## {label} Results\n")
    print("| Endpoint | Requests | Status counts | Throughput req/s | Avg ms | p50 ms | p95 ms | Min ms | Max ms |")
    print("| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    total_throughput = 0.0
    total_latency = 0.0
    count = 0
    for result in results:
        print(
            "| {endpoint} | {requests} | `{status_counts}` | {throughput_rps} | {avg_ms} | {p50_ms} | "
            "{p95_ms} | {min_ms} | {max_ms} |".format(**result)
        )
        try:
            total_throughput += float(result["throughput_rps"])
            total_latency += float(result["avg_ms"])
            count += 1
        except Exception:
            pass
    avg_latency = total_latency / count if count > 0 else 0.0
    print(f"\n**Total throughput:** {round(total_throughput, 2)} req/s")
    print(f"**Average latency:** {round(avg_latency, 2)} ms")


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark StayFit API endpoints.")
    parser.add_argument("--base-url", default="http://localhost:5000")
    parser.add_argument("--token", required=True, help="JWT copied from frontend localStorage.")
    parser.add_argument("--label", default="Architecture Benchmark")
    parser.add_argument("--warmups", type=int, default=30)
    parser.add_argument("--requests", type=int, default=100)
    parser.add_argument("--timeout", type=float, default=10)
    parser.add_argument("--endpoint", action="append", dest="endpoints")
    args = parser.parse_args()

    endpoints = args.endpoints or DEFAULT_ENDPOINTS
    results = [
        benchmark_endpoint(
            args.base_url,
            endpoint,
            args.token,
            args.warmups,
            args.requests,
            args.timeout,
        )
        for endpoint in endpoints
    ]
    print_markdown_table(results, args.label)


if __name__ == "__main__":
    main()
