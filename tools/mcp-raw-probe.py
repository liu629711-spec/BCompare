"""Probe an REA MCP session with a raw stdio JSON-RPC client.

The bundled MCP SDK client caps every request at 60 s, which a first-time Ghidra
import (~14 min) always exceeds. Speaking the stdio protocol directly removes
that cap and answers the question the SDK probe could not: after one analysis,
do later queries in the same session answer quickly?
"""
import json
import os
import subprocess
import sys
import time

REA = r"C:\Users\liuxinlong\AppData\Roaming\npm\node_modules\rea-agents\scripts\rea.mjs"
TARGET = "D:/bc-official/app/BCompare.exe"

env = dict(os.environ)
env["GHIDRA_INSTALL_DIR"] = r"D:\Ghidra\ghidra_12.1.4_PUBLIC"
env["REA_GHIDRA_STARTUP_TIMEOUT_MS"] = "3600000"

proc = subprocess.Popen(
    ["node", REA, "--mcp"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    env=env,
    text=True,
    encoding="utf-8",
    bufsize=1,
)


def stamp() -> str:
    return time.strftime("%H:%M:%S")


def send(payload: dict) -> None:
    proc.stdin.write(json.dumps(payload) + "\n")
    proc.stdin.flush()


def read_response(request_id: int, deadline_seconds: int) -> dict:
    """Read stdout lines until the response for request_id arrives."""
    end = time.time() + deadline_seconds
    while time.time() < end:
        line = proc.stdout.readline()
        if not line:
            raise RuntimeError("server closed stdout")
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            print(f"[{stamp()}] non-JSON line: {line[:120]}", file=sys.stderr)
            continue
        if message.get("id") == request_id:
            return message
        # Server-initiated traffic (logging, progress) is expected; note it briefly.
        method = message.get("method")
        if method:
            print(f"[{stamp()}] server notice: {method}", file=sys.stderr)
    raise TimeoutError(f"no response for id={request_id} within {deadline_seconds}s")


def call(name: str, arguments: dict, request_id: int, budget: int) -> tuple[dict, float]:
    started = time.time()
    print(f"[{stamp()}] -> {name}", file=sys.stderr)
    send({"jsonrpc": "2.0", "id": request_id, "method": "tools/call",
          "params": {"name": name, "arguments": arguments}})
    response = read_response(request_id, budget)
    elapsed = time.time() - started
    print(f"[{stamp()}] <- {name} in {elapsed:.1f}s", file=sys.stderr)
    return response, elapsed


def text_of(response: dict) -> str:
    content = (response.get("result") or {}).get("content") or []
    for block in content:
        if block.get("type") == "text":
            return block.get("text", "")
    return ""


try:
    send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
          "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                     "clientInfo": {"name": "raw-probe", "version": "1.0.0"}}})
    handshake = read_response(1, 120)
    print(f"[{stamp()}] initialized: {json.dumps(handshake.get('result', {}).get('serverInfo', {}))}", file=sys.stderr)
    send({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})

    open_response, open_seconds = call("open_binary", {"path": TARGET, "provider_id": "ghidra"}, 2, 300)
    print(f"open_binary result: {text_of(open_response)[:300]}")

    # First search pays for the Ghidra import and auto-analysis.
    first, first_seconds = call("search_strings", {"pattern": "TogDiff", "mode": "literal"}, 3, 2400)
    body = text_of(first)
    print(f"search#1 chars={len(body)} :: {body[:400]}")

    # Second search: near-instant here means the session reused the analysis.
    second, second_seconds = call("search_strings", {"pattern": "AlignWith", "mode": "literal"}, 4, 600)
    body2 = text_of(second)
    print(f"search#2 chars={len(body2)} :: {body2[:300]}")

    # Locate the function that references a known BC dialog string.
    joined = text_of(call("search_strings", {"pattern": "NeverAlignDiffs", "mode": "literal"}, 5, 300)[0])
    print(f"search#3 :: {joined[:300]}")

    print(f"SUMMARY open={open_seconds:.1f}s first_search={first_seconds:.1f}s second_search={second_seconds:.1f}s")
finally:
    try:
        proc.stdin.close()
    except Exception:
        pass
    try:
        proc.wait(timeout=30)
    except Exception:
        proc.kill()
    stderr_tail = proc.stderr.read()[-2000:] if proc.stderr else ""
    if stderr_tail:
        print("--- server stderr tail ---", file=sys.stderr)
        print(stderr_tail, file=sys.stderr)
