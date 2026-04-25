"""
Microservices cluster launcher — cross-platform (Windows + macOS/Linux).

Redis startup strategy:
  • Windows  → Redis runs inside WSL2 (bound to 0.0.0.0).
               A 'netsh portproxy' rule forwards Windows localhost:6379
               to the WSL2 VM's IP so native Windows processes can reach it.
               Requires Administrator privileges for the portproxy step.
  • macOS / Linux → Redis is started directly via 'redis-server'.
               No port-forwarding needed; localhost:6379 works natively.
"""

import platform
import subprocess
import time
import sys
import shutil

# ── Microservice definitions ────────────────────────────────────────────────
SERVICES = [
    ("Auth Microservice",          "run_auth.py"),
    ("Meals Microservice",         "run_meals.py"),
    ("Analytics Microservice",     "run_analytics.py"),
    ("Notifications Microservice", "run_notifications.py"),
    ("API Gateway",                "api_gateway.py"),
]

IS_WINDOWS = platform.system() == "Windows"

active_processes = []
redis_process    = None
_wsl_ip          = None  # populated on Windows only


# ── Helpers: Windows / WSL2 ─────────────────────────────────────────────────

def _get_wsl_ip():
    """Return the primary WSL2 VM IP visible from the Windows host."""
    result = subprocess.run(
        ["wsl", "--", "hostname", "-I"],
        capture_output=True, text=True
    )
    return result.stdout.strip().split()[0]


def _add_port_forward(wsl_ip):
    """Forward Windows 127.0.0.1:6379 → WSL2 IP:6379 via netsh portproxy."""
    print(f"  Adding port-forward: 127.0.0.1:6379 → {wsl_ip}:6379 ...")
    subprocess.run(
        [
            "netsh", "interface", "portproxy", "add", "v4tov4",
            "listenaddress=127.0.0.1", "listenport=6379",
            f"connectaddress={wsl_ip}",  "connectport=6379",
        ],
        check=False, capture_output=True
    )


def _remove_port_forward():
    """Remove the netsh portproxy rule created on startup (Windows only)."""
    subprocess.run(
        [
            "netsh", "interface", "portproxy", "delete", "v4tov4",
            "listenaddress=127.0.0.1", "listenport=6379",
        ],
        check=False, capture_output=True
    )


# ── Helpers: macOS / Linux ───────────────────────────────────────────────────

def _check_native_redis():
    """Return True if redis-server is available natively on PATH."""
    return shutil.which("redis-server") is not None


# ── Main Redis start function (dispatches by OS) ─────────────────────────────

def start_redis():
    """
    Start Redis and return its process handle (or None if it couldn't start).

    Windows  → WSL2 + netsh portproxy (requires Admin).
    macOS/Linux → native redis-server.
    """
    global _wsl_ip

    if IS_WINDOWS:
        print("Starting Redis via WSL2 (Windows)...")
        _wsl_ip = _get_wsl_ip()
        proc = subprocess.Popen(
            ["wsl", "--", "redis-server", "--bind", "0.0.0.0", "--daemonize", "no"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(1)           # let Redis bind

        _add_port_forward(_wsl_ip)
        time.sleep(0.5)

        # Verify connectivity from the Windows side
        check = subprocess.run(
            ["wsl", "--", "redis-cli", "-h", _wsl_ip, "ping"],
            capture_output=True, text=True
        )
        if check.stdout.strip() == "PONG":
            print("Redis is up and reachable on localhost:6379 ✓")
        else:
            print("⚠ Redis did not respond — caching/Celery may be unavailable.")
            print("  Tip: re-run this script as Administrator so the port-forward can be added.")
        return proc

    else:
        # macOS / Linux
        print("Starting Redis natively (macOS/Linux)...")
        if not _check_native_redis():
            print("⚠ redis-server not found on PATH.")
            print("  macOS  → install with: brew install redis")
            print("  Ubuntu → install with: sudo apt install redis-server")
            return None

        proc = subprocess.Popen(
            ["redis-server"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(1)

        check = subprocess.run(
            ["redis-cli", "ping"],
            capture_output=True, text=True
        )
        if check.stdout.strip() == "PONG":
            print("Redis is up and reachable on localhost:6379 ✓")
        else:
            print("⚠ Redis did not respond — caching/Celery may be unavailable.")
        return proc


def shutdown():
    """Gracefully stop all processes and clean up."""
    print("\nShutting down microservices cluster...")
    for name, p in active_processes:
        print(f"  Terminating {name}...")
        p.terminate()
        p.wait()

    if redis_process:
        print("  Stopping Redis...")
        redis_process.terminate()
        redis_process.wait()

    if IS_WINDOWS and _wsl_ip:
        print("  Removing port-forward rule...")
        _remove_port_forward()

    print("Shutdown complete.")


# ── Entry point ──────────────────────────────────────────────────────────────

try:
    print("====================================")
    print("STARTING MICROSERVICES CLUSTER")
    print(f"Platform: {platform.system()}")
    print("====================================")

    redis_process = start_redis()

    for name, script in SERVICES:
        print(f"Starting {name}...")
        p = subprocess.Popen([sys.executable, script])
        active_processes.append((name, p))
        time.sleep(1)   # small delay to avoid interleaved startup logs

    print("====================================")
    print("All Microservices Running. (Press CTRL+C to stop all)")
    print("====================================")

    while True:
        time.sleep(1)

except KeyboardInterrupt:
    shutdown()
