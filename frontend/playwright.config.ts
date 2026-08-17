import { defineConfig } from "@playwright/test";

const chromePath = "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  timeout: 60_000,
  reporter: "list",
  outputDir: "test-results",
  use: {
    baseURL: "http://127.0.0.1:4175",
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  projects: [{
    name: "chromium",
    use: { browserName: "chromium", launchOptions: { executablePath: chromePath } },
  }],
  webServer: [
    {
      command: ".\\.venv\\Scripts\\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 4183",
      cwd: "../backend",
      url: "http://127.0.0.1:4183/healthz",
      env: {
        DATABASE_URL: "sqlite:///./promptforge_e2e.db",
        FRONTEND_ORIGINS: "http://127.0.0.1:4175",
        FRONTEND_URL: "http://127.0.0.1:4175",
        JWT_SECRET_KEY: "e2e-tests-only-change-in-production",
      },
    },
    {
      command: "\"C:\\Users\\lukas\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\node\\bin\\node.exe\" .\\node_modules\\vite\\bin\\vite.js --host 127.0.0.1 --port 4175",
      cwd: ".",
      url: "http://127.0.0.1:4175",
      env: { VITE_API_PROXY_URL: "http://127.0.0.1:4183" },
    },
  ],
});
