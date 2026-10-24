"""Dump the input schemas of the tools the reverse-engineering workflow needs.

`tools/list` needs no analysis, so this is a cheap call that avoids wasting a
25-minute cycle on a parameter-name mistake.
"""
import json
import os
import pathlib
import subprocess
import sys
import time

REA = r"C:\Users\liuxinlong\AppData\Roaming\npm\node_modules\rea-agents\scripts\rea.mjs"
WANTED = {
    "open_binary", "close_binary", "binary_session",
    "search_strings", "search_procedures", "xrefs",
    "analyze_function", "batch_decompile", "read_function_instructions",
    "inspect_analysis_view", "get_evidence_bundle", "export_evidence_bundle",
    "find_xrefs_to_name", "trace_feature", "trace_native_values", "compare_functions",
}

env = dict(os.environ)
env["GHIDRA_INSTALL_DIR"] = r"D:\Ghidra\ghidra_12.1.4_PUBLIC"

proc = subprocess.Popen(
    ["node", REA, "--mcp"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
    stderr=subprocess.DEVNULL, env=env, text=True, encoding="utf-8", bufsize=1,
)


def send(payload):
    proc.stdin.write(json.dumps(payload) + "\n")
    proc.stdin.flush()


def read_response(request_id, budget=120):
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
    raise TimeoutError(f"no response for id={request_id}")


try:
    send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
          "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                     "clientInfo": {"name": "schema-dump", "version": "1.0.0"}}})
    read_response(1)
    send({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
    send({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    listing = read_response(2, 300)

    tools = (listing.get("result") or {}).get("tools") or []
    chosen = {t["name"]: t for t in tools if t["name"] in WANTED}
    out = pathlib.Path(r"D:\Rea\extracted\tool-schemas.json")
    out.write_text(json.dumps(chosen, ensure_ascii=False, indent=1), encoding="utf-8")

    for name in sorted(chosen):
        schema = chosen[name].get("inputSchema") or {}
        props = schema.get("properties") or {}
        required = schema.get("required") or []
        print(f'{name}: required={required}')
        for prop, spec in props.items():
            kind = spec.get("type") or spec.get("anyOf") or spec
            desc = (spec.get("description") or "")[:90].replace("\n", " ")
            print(f'    {prop}: {json.dumps(kind)[:80]}  {desc}')
    print(f"\nwrote {out}")
finally:
    try:
        proc.stdin.close()
    except Exception:
        pass
    try:
        proc.wait(timeout=20)
    except Exception:
        proc.kill()
