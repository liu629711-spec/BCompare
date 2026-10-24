// Probe whether a persistent MCP session reuses one Ghidra analysis across queries.
// Strategy: spawn `rea --mcp`, open the target once, then issue several queries and
// compare wall-clock times. A reused session answers later queries in seconds; a
// re-analyzing session costs ~14 minutes each time.
import { Client } from "file:///C:/Users/liuxinlong/AppData/Roaming/npm/node_modules/rea-agents/node_modules/@modelcontextprotocol/client/dist/index.mjs";
import { StdioClientTransport } from "file:///C:/Users/liuxinlong/AppData/Roaming/npm/node_modules/rea-agents/node_modules/@modelcontextprotocol/client/dist/stdio.mjs";

const TARGET = "D:/bc-official/app/BCompare.exe";
const SNAPSHOT = "D:/Rea/extracted/bcompare.snapshot.json";

const log = (...args) => console.error("[probe]", ...args);
const t = () => new Date().toISOString().slice(11, 19);

const transport = new StdioClientTransport({
  command: process.execPath,
  args: [
    "C:/Users/liuxinlong/AppData/Roaming/npm/node_modules/rea-agents/scripts/rea.mjs",
    "--mcp",
  ],
  env: {
    ...process.env,
    GHIDRA_INSTALL_DIR: "D:\\Ghidra\\ghidra_12.1.4_PUBLIC",
    REA_GHIDRA_STARTUP_TIMEOUT_MS: "3600000",
  },
  stderr: "pipe",
});

const client = new Client({ name: "rea-session-probe", version: "1.0.0" });

// The first search pays for the whole Ghidra import + auto-analysis (~14 min),
// so every request needs a deadline well past the SDK's 60 s default.
const LONG = { timeout: 2_400_000, maxTotalTimeout: 2_400_000 };

try {
  log(t(), "connecting...");
  await client.connect(transport, { timeout: 2_400_000 });
  log(t(), "connected");

  const { tools } = await client.listTools();
  const names = tools.map((tool) => tool.name);
  log(t(), `tools: ${names.length}`);
  const relevant = names.filter((name) => /binary|decompile|function|search|xrefs|trace|instruction/i.test(name));
  log(t(), `relevant: ${relevant.join(", ")}`);

  const openTool = names.includes("open_binary") ? "open_binary" : relevant[0];
  log(t(), `opening with ${openTool}`);
  const start = Date.now();
  const opened = await client.callTool(
    { name: openTool, arguments: { path: TARGET, provider_id: "ghidra" } },
    undefined,
    LONG,
  );
  log(t(), `open took ${((Date.now() - start) / 1000).toFixed(1)}s, isError=${opened.isError}`);
  log(t(), JSON.stringify(opened.content).slice(0, 400));

  // Query 1: string search. This triggers the full analysis on first use.
  const q1 = Date.now();
  const r1 = await client.callTool(
    { name: "search_strings", arguments: { pattern: "Diff", mode: "literal" } },
    undefined,
    LONG,
  );
  log(t(), `search_strings took ${((Date.now() - q1) / 1000).toFixed(1)}s, isError=${r1.isError}`);
  log(t(), JSON.stringify(r1.content).slice(0, 300));

  // Query 2: a second search. Fast here means the analysis was reused.
  const q2 = Date.now();
  const r2 = await client.callTool(
    { name: "search_strings", arguments: { pattern: "Align", mode: "literal" } },
    undefined,
    LONG,
  );
  log(t(), `search_strings#2 took ${((Date.now() - q2) / 1000).toFixed(1)}s, isError=${r2.isError}`);
  log(t(), JSON.stringify(r2.content).slice(0, 200));

  // Query 3: procedure-name search to confirm the stripped-symbol hypothesis.
  const q3 = Date.now();
  const r3 = await client.callTool(
    { name: "search_procedures", arguments: { pattern: "Diff", mode: "literal" } },
    undefined,
    LONG,
  );
  log(t(), `search_procedures took ${((Date.now() - q3) / 1000).toFixed(1)}s, isError=${r3.isError}`);
  log(t(), JSON.stringify(r3.content).slice(0, 400));

  await client.close();
  log(t(), "done");
} catch (error) {
  log(t(), "FAILED:", error?.message ?? error);
  try {
    await client.close();
  } catch {}
  process.exitCode = 1;
}
