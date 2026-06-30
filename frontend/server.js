import http from "node:http";
import { readFile } from "node:fs/promises";
import { readFileSync } from "node:fs";
import { extname, join, normalize } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = fileURLToPath(new URL(".", import.meta.url));
const PROJECT_ROOT = fileURLToPath(new URL("..", import.meta.url));
const runtimeConfig = JSON.parse(readFileSync(join(PROJECT_ROOT, "config/runtime.json"), "utf8"));
const PORT = Number(process.env.PORT || runtimeConfig.frontend.port);
const HOST = process.env.HOST || runtimeConfig.host;

const contentTypes = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8"
};

const server = http.createServer(async (req, res) => {
  try {
    const url = new URL(req.url, `http://${req.headers.host}`);
    if (url.pathname === "/config.js") {
      const bindOnlyHosts = new Set(["0.0.0.0", "::", ""]);
      const browserHost = url.hostname || "127.0.0.1";
      const apiHost = bindOnlyHosts.has(runtimeConfig.host) ? browserHost : runtimeConfig.host;
      const apiBaseUrl = `http://${apiHost}:${runtimeConfig.backend.port}${runtimeConfig.backend.apiPath}`;
      res.writeHead(200, { "Content-Type": "text/javascript; charset=utf-8" });
      res.end(`window.APP_CONFIG = ${JSON.stringify({ apiBaseUrl })};`);
      return;
    }

    const routeFallbacks = new Set(["/", "/products", "/inventory", "/inbound-documents", "/outbound-documents"]);
    const requestPath = routeFallbacks.has(url.pathname) ? "/index.html" : url.pathname;
    const safePath = normalize(requestPath).replace(/^(\.\.[/\\])+/, "");
    const filePath = join(ROOT, safePath);
    const data = await readFile(filePath);

    res.writeHead(200, {
      "Content-Type": contentTypes[extname(filePath)] || "application/octet-stream"
    });
    res.end(data);
  } catch {
    res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
    res.end("Not found");
  }
});

server.listen(PORT, HOST, () => {
  console.log(`Frontend running at http://${HOST}:${PORT}`);
});
