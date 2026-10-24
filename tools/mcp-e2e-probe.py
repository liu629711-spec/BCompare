"""End-to-end proof: in one persistent MCP session, go from a BC string to decompiled code.

Sequence that the "reverse engineer, then rebuild" workflow needs:
  1. search_strings  -- pay the one-time Ghidra import + auto-analysis
  2. find_xrefs_to_name / xrefs -- locate code referencing that string
  3. analyze_function / batch_decompile -- read the referencing function as pseudocode

Every request after the first is served from the same analysis, so the expensive
step is paid once. Raw stdio JSON-RPC is used because the bundled SDK client caps
requests at 60 s, which a first-time import always exceeds.
"""
import json
import os
import subprocess
import sys
import time

REA = r"C:\Users\liuxinlong\AppData\Roaming\npm\node_modules\rea-agents\scripts\rea.mjs"
TARGET = "D:/bc-official/app/BCompare.exe"
# "TogDiff" is a BC action name; its referencing code sits in the diff/alignment layer.
SEED_STRING = "TogDiff"

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
    print(f"[{stamp()}] -> {name} {json.dumps(arguments)[:120]}", file=sys.stderr, flush=True)
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
    return json.dumps(response)[:500]


results = {}
try:
    send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
          "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                     "clientInfo": {"name": "e2e-probe", "version": "1.0.0"}}})
    read_response(1, 120)
    send({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})

    call("open_binary", {"path": TARGET, "provider_id": "ghidra"}, 2, 300)

    # 1. Seed: find the string and its address.
    seed_response, seed_seconds = call("search_strings", {"pattern": SEED_STRING, "mode": "literal"}, 3, 3000)
    seed_text = text_of(seed_response)
    results["seed_search_seconds"] = seed_seconds
    seed_doc = json.loads(seed_text)
    hits = seed_doc.get("raw_result") or []
    results["seed_hits"] = hits
    print(f"seed hits: {json.dumps(hits, ensure_ascii=False)[:600]}")

    address = None
    for hit in hits:
        if hit.get("value") == SEED_STRING:
            address = hit.get("address")
            break
    results["seed_address"] = address
    print(f"seed address: {address}")

    # 2. Who references that string?
    if address:
        xref_response, xref_seconds = call("xrefs", {"address": address}, 4, 600)
        xref_text = text_of(xref_response)
        results["xref_seconds"] = xref_seconds
        results["xref_raw"] = xref_text[:4000]
        print(f"xrefs: {xref_text[:800]}")

        # 3. Read the referencing function as pseudocode.
        try:
            xref_doc = json.loads(xref_text)
            refs = xref_doc.get("raw_result") or []
        except json.JSONDecodeError:
            refs = []
        target_fn = None
        for ref in refs:
            if isinstance(ref, dict):
                target_fn = ref.get("function") or ref.get("from_function") or ref.get("from")
                if target_fn:
                    break
        results["target_function"] = target_fn
        print(f"target function: {target_fn}")

        if target_fn:
            fn_response, fn_seconds = call("analyze_function", {"address": target_fn}, 5, 900)
            fn_text = text_of(fn_response)
            results["decompile_seconds"] = fn_seconds
            results["decompile_raw"] = fn_text[:8000]
            print(f"decompiled chars: {len(fn_text)}")
            print(fn_text[:1200])

    print("RESULTS " + json.dumps(results, ensure_ascii=False)[:200])
finally:
    try:
        proc.stdin.close()
    except Exception:
        pass
    try:
        proc.wait(timeout=30)
    except Exception:
        proc.kill()

    import pathlib
    pathlib.Path(r"D:\Rea\extracted\e2e-result.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[{stamp()}] wrote D:\\Rea\\extracted\\e2e-result.json", file=sys.stderr)
