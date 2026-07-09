import { spawn, spawnSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

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

function resolvePython() {
  const unixVenvPython = join(root, ".venv", "bin", "python");
  const windowsVenvPython = join(root, ".venv", "Scripts", "python.exe");
  const candidates = [
    process.env.PYTHON ? { command: process.env.PYTHON, args: [] } : null,
    existsSync(windowsVenvPython) ? { command: windowsVenvPython, args: [] } : null,
    existsSync(unixVenvPython) ? { command: unixVenvPython, args: [] } : null,
    { command: "py", args: ["-3.12-32"] },
    { command: "py", args: ["-3.11-32"] },
    { command: "python", args: [] },
    { command: "python3.13", args: [] },
    { command: "python3.12", args: [] },
    { command: "python3.11", args: [] },
    { command: "python3", args: [] }
  ].filter(Boolean);

  for (const candidate of candidates) {
    if (hasUvicorn(candidate)) {
      return candidate;
    }
  }

  console.error("未找到已安装 uvicorn 的 Python。请先执行：");
  console.error("  Windows: py -3.12-32 -m venv .venv");
  console.error("  Windows: .\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt");
  console.error("  macOS/Linux: python3 -m venv .venv");
  console.error("  macOS/Linux: ./.venv/bin/python -m pip install -r requirements.txt");
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
