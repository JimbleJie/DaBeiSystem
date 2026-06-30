import { spawn, spawnSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const config = JSON.parse(readFileSync(join(root, "config/runtime.json"), "utf8"));

function hasUvicorn(pythonCommand) {
  const result = spawnSync(
    pythonCommand,
    ["-c", "import uvicorn"],
    {
      cwd: root,
      stdio: "ignore"
    }
  );
  return result.status === 0;
}

function resolvePython() {
  const venvPython = join(root, ".venv/bin/python");
  const candidates = [
    process.env.PYTHON,
    existsSync(venvPython) ? venvPython : null,
    "python3.13",
    "python3.12",
    "python3.11",
    "python3"
  ].filter(Boolean);

  for (const candidate of candidates) {
    if (hasUvicorn(candidate)) {
      return candidate;
    }
  }

  console.error("未找到已安装 uvicorn 的 Python。请先执行：");
  console.error("  python3 -m venv .venv");
  console.error("  ./.venv/bin/pip install -r requirements.txt");
  process.exit(1);
}

const python = resolvePython();

const child = spawn(
  python,
  [
    "-m",
    "uvicorn",
    "backend.main:app",
    "--host",
    config.host,
    "--port",
    String(config.backend.port)
  ],
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
