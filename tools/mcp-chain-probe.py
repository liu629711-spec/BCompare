"""Complete the chain: string -> xref -> function -> readable pseudocode.

`analyze_function` on a BC routine produces a result larger than the MCP stdio
response budget, so its payload never crosses the wire. REA keeps the complete
record in its session ledger and reports the retained Evidence id, which
`inspect_analysis_view` can project one facet at a time. That projection is what
makes the pseudocode readable, and it is the step this probe verifies.
"""
import json
import os
import pathlib
import subprocess
import sys
import time

REA = r"C:\Users\liuxinlong\AppData\Roaming\npm\node_modules\rea-agents\scripts\rea.mjs"
TARGET = "D:/bc-official/app/BCompare.exe"
# Code that references the "TogDiff" action name, established by the xrefs probe.
XREF_ADDRESS = "0x140da4b8f"

env = dict(os.environ)
env["GHIDRA_INSTALL_DIR"] = r"D:\Ghidra\ghidra_12.1.4_PUBLIC"
env["REA_GHIDRA_STARTUP_TIMEOUT_MS"] = "3600000"

proc = subprocess.Popen(
    ["node", REA, "--mcp"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
    stderr=subprocess.DEVNULL, env=env, text=True, encoding="utf-8", bufsize=1,
)

stamp = lambda: time.strftime("%H:%M:%S")


def send(payload):
    proc.stdin.write(json.dumps(payload) + "\n")
    proc.stdin.flush()


def read_response(request_id, budget):
    end = time.time() + budget
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
    raise TimeoutError(f"no response for id={request_id} in {budget}s")


def call(name, arguments, request_id, budget):
    started = time.time()
    print(f"[{stamp()}] -> {name} {json.dumps(arguments)[:150]}", file=sys.stderr, flush=True)
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
    return json.dumps(response)[:2000]


def retained_id(text):
    """Pull the retained Evidence id out of an oversized-response error blob."""
    try:
        doc = json.loads(text)
    except json.JSONDecodeError:
        return None
    details = (doc.get("error") or {}).get("details") or {}
    reference = details.get("evidence_reference") or {}
    return reference.get("evidence_id") or details.get("evidence_id")


out_dir = pathlib.Path(r"D:\Rea\extracted\pseudocode")
out_dir.mkdir(exist_ok=True)
record = {"steps": {}}

try:
    send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
          "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                     "clientInfo": {"name": "chain-probe", "version": "1.0.0"}}})
    read_response(1, 120)
    send({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})

    call("open_binary", {"path": TARGET, "provider_id": "ghidra"}, 2, 300)

    # Step 1: read the referencing function. This is the expensive call.
    fn_response, fn_seconds = call("analyze_function", {"procedure": XREF_ADDRESS}, 3, 3600)
    fn_text = text_of(fn_response)
    record["steps"]["analyze_function"] = {"seconds": fn_seconds, "chars": len(fn_text)}
    evidence = retained_id(fn_text)
    record["retained_evidence"] = evidence
    print(f"retained evidence: {evidence}")

    if evidence:
        # Step 2: project the pseudocode facet off the retained record.
        view_args = {
            "source": {"kind": "retained-evidence", "evidence_id": evidence},
            "view": {"kind": "native", "facet": "pseudocode", "offset": 0, "limit": 24},
        }
        view_response, view_seconds = call("inspect_analysis_view", view_args, 4, 600)
        view_text = text_of(view_response)
        record["steps"]["inspect_analysis_view"] = {"seconds": view_seconds, "chars": len(view_text)}
        (out_dir / "analyze_function-pseudocode.json").write_text(view_text, encoding="utf-8")
        print(f"--- pseudocode ({len(view_text)} chars) ---")
        print(view_text[:3000])

        # Step 3: read callees so the caller/callee structure is available too.
        callee_args = dict(view_args)
        callee_args["view"] = {"kind": "native", "facet": "callees", "offset": 0, "limit": 32}
        callee_response, callee_seconds = call("inspect_analysis_view", callee_args, 5, 600)
        callee_text = text_of(callee_response)
        record["steps"]["callees"] = {"seconds": callee_seconds, "chars": len(callee_text)}
        (out_dir / "analyze_function-callees.json").write_text(callee_text, encoding="utf-8")
        print(f"--- callees ---")
        print(callee_text[:1200])
finally:
    try:
        proc.stdin.close()
    except Exception:
        pass
    try:
        proc.wait(timeout=20)
    except Exception:
        proc.kill()
    pathlib.Path(r"D:\Rea\extracted\chain-result.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[{stamp()}] wrote chain-result.json", file=sys.stderr)
