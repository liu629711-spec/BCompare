"""Final proof step: decompile the code that references a known BC string.

Starts from xref addresses already established by the previous probe
(0x140da4b8f / 0x140da4b96 reference the "TogDiff" action name). The first
analyze_function call pays the one-time import + auto-analysis; the second
should return instantly from the same session.
"""
import json
import os
import pathlib
import subprocess
import sys
import time

REA = r"C:\Users\liuxinlong\AppData\Roaming\npm\node_modules\rea-agents\scripts\rea.mjs"
TARGET = "D:/bc-official/app/BCompare.exe"
XREFS = ["0x140da4b8f", "0x140da4b96"]

env = dict(os.environ)
env["GHIDRA_INSTALL_DIR"] = r"D:\Ghidra\ghidra_12.1.4_PUBLIC"
env["REA_GHIDRA_STARTUP_TIMEOUT_MS"] = "3600000"

proc = subprocess.Popen(
    ["node", REA, "--mcp"],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    env=env, text=True, encoding="utf-8", bufsize=1,
)

stamp = lambda: time.strftime("%H:%M:%S")


def send(payload):
    proc.stdin.write(json.dumps(payload) + "\n")
    proc.stdin.flush()


def read_response(request_id, deadline_seconds):
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
            continue
        if message.get("id") == request_id:
            return message
    raise TimeoutError(f"no response for id={request_id} in {deadline_seconds}s")


def call(name, arguments, request_id, budget):
    started = time.time()
    print(f"[{stamp()}] -> {name} {json.dumps(arguments)[:140]}", file=sys.stderr, flush=True)
    send({"jsonrpc": "2.0", "id": request_id, "method": "tools/call",
          "params": {"name": name, "arguments": arguments}})
    response = read_response(request_id, budget)
    elapsed = time.time() - started
    print(f"[{stamp()}] <- {name} in {elapsed:.1f}s", file=sys.stderr, flush=True)
    return response, elapsed


def text_of(response):
    for block in (response.get("result") or {}).get("content") or []:
        if block.get("type") == "text":
            return block.get("text", "")
    return json.dumps(response)[:800]


timings = {}
out = pathlib.Path(r"D:\Rea\extracted\decompile-result.json")
try:
    send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
          "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                     "clientInfo": {"name": "decompile-probe", "version": "1.0.0"}}})
    read_response(1, 120)
    send({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})

    call("open_binary", {"path": TARGET, "provider_id": "ghidra"}, 2, 300)

    payloads = {}
    for index, address in enumerate(XREFS, start=3):
        response, seconds = call("analyze_function", {"procedure": address}, index, 3600)
        timings[address] = seconds
        payloads[address] = text_of(response)
        print(f"--- {address} ({seconds:.1f}s, {len(payloads[address])} chars) ---")
        print(payloads[address][:2500])

    out.write_text(json.dumps({"timings": timings, "results": payloads}, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print(f"[{stamp()}] wrote {out}", file=sys.stderr)
finally:
    try:
        proc.stdin.close()
    except Exception:
        pass
    try:
        proc.wait(timeout=30)
    except Exception:
        proc.kill()
