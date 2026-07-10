import { spawn, spawnSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const config = JSON.parse(readFileSync(join(root, "config/runtime.json"), "utf8"));

function hasUvicorn(candidate) {
  const result = spawnSync(
    candidate.command,
    [...candidate.args, "-c", "import uvicorn"],
    {
      cwd: root,
      stdio: "ignore"
    }
  );
  return result.status === 0;
}

function is32BitPython(candidate) {
  const result = spawnSync(
    candidate.command,
    [
      ...candidate.args,
      "-c",
      "import platform, sys; sys.exit(0 if platform.architecture()[0] == '32bit' else 1)"
    ],
    {
      cwd: root,
      stdio: "ignore"
    }
  );
  return result.status === 0;
}

function isPrintingEnabled() {
  return process.env.PRINT_SDK_ENABLED !== "0";
}

function hasBundledPrinterSdk() {
  return existsSync(join(root, "printer-sdk", "printSDK", "DDPrintSDK.dll"));
}

function resolvePython() {
  const unixVenvPython = join(root, ".venv", "bin", "python");
  const windowsVenvPython = join(root, ".venv", "Scripts", "python.exe");
  const prefer32BitPython = process.platform === "win32" && isPrintingEnabled() && hasBundledPrinterSdk();
  const candidates = [
    process.env.PYTHON ? { command: process.env.PYTHON, args: [] } : null,
    existsSync(windowsVenvPython) ? { command: windowsVenvPython, args: [] } : null,
    existsSync(unixVenvPython) ? { command: unixVenvPython, args: [] } : null,
    { command: "py", args: ["-3.14-32"] },
    { command: "py", args: ["-3.13-32"] },
    { command: "py", args: ["-3.12-32"] },
    { command: "py", args: ["-3.11-32"] },
    { command: "py", args: ["-3.14"] },
    { command: "py", args: ["-3.13"] },
    { command: "py", args: ["-3.12"] },
    { command: "py", args: ["-3.11"] },
    { command: "python", args: [] },
    { command: "python3.14", args: [] },
    { command: "python3.13", args: [] },
    { command: "python3.12", args: [] },
    { command: "python3.11", args: [] },
    { command: "python3", args: [] }
  ].filter(Boolean);

  let fallbackCandidate = null;
  for (const candidate of candidates) {
    if (!hasUvicorn(candidate)) {
      continue;
    }
    if (prefer32BitPython && is32BitPython(candidate)) {
      return candidate;
    }
    if (!fallbackCandidate) {
      fallbackCandidate = candidate;
    }
  }

  if (fallbackCandidate) {
    if (prefer32BitPython) {
      console.warn("Printing SDK is enabled but no 32-bit Python with uvicorn was found.");
      console.warn("The backend will start with a non-x86 interpreter and printing will remain unavailable.");
      console.warn("Recommended fix: recreate .venv with `py -3.12-32 -m venv .venv` or set `PRINT_SDK_ENABLED=0`.");
    }
    return fallbackCandidate;
  }

  console.error("No Python interpreter with uvicorn is available.");
  console.error("Windows with printer SDK: py -3.12-32 -m venv .venv");
  console.error("Windows: .\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt");
  console.error("macOS/Linux: python3 -m venv .venv");
  console.error("macOS/Linux: ./.venv/bin/python -m pip install -r requirements.txt");
  process.exit(1);
}

const python = resolvePython();
const reloadEnabled = process.env.BACKEND_RELOAD !== "0";
const uvicornArgs = [
  "-m",
  "uvicorn",
  "backend.main:app",
  "--host",
  config.host,
  "--port",
  String(config.backend.port)
];

if (reloadEnabled) {
  uvicornArgs.push("--reload", "--reload-dir", "backend");
}

const child = spawn(
  python.command,
  [...python.args, ...uvicornArgs],
  {
    cwd: root,
    stdio: "inherit"
  }
);

child.on("exit", (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }
  process.exit(code ?? 0);
});
