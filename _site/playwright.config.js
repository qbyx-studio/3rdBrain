const { defineConfig } = require("@playwright/test");

module.exports = defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  use: {
    baseURL: "http://127.0.0.1:8766",
    trace: "retain-on-failure",
  },
  webServer: {
    command: "node tests/serve-site.mjs",
    url: "http://127.0.0.1:8766",
    reuseExistingServer: false,
    timeout: 30_000,
  },
});


