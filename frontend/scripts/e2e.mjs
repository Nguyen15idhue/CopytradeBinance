import { existsSync } from "node:fs";

import { chromium } from "playwright-core";

const candidates = [
  process.env.CHROME_PATH,
  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
].filter(Boolean);

const executablePath = candidates.find((path) => existsSync(path));
if (!executablePath) {
  throw new Error("Không tìm thấy Chrome/Edge. Đặt biến CHROME_PATH.");
}

const base = process.env.BASE_URL ?? "http://localhost:8090";
const browser = await chromium.launch({ executablePath, headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const consoleErrors = [];

page.on("console", (message) => {
  if (message.type() === "error") consoleErrors.push(message.text());
});
page.on("pageerror", (error) => consoleErrors.push(error.message));

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

try {
  await page.goto(`${base}/login`, { waitUntil: "domcontentloaded" });
  await page.getByRole("heading", { name: "Đăng nhập" }).waitFor();
  await page.getByLabel("Email").fill("admin@example.com");
  await page.getByLabel("Mật khẩu").fill("Admin123!ChangeMe");
  await page.getByRole("button", { name: "Đăng nhập" }).click();

  await page.waitForURL(`${base}/`);
  await page.getByRole("heading", { name: "Trader demo" }).waitFor();
  console.log("Đăng nhập: OK");

  await page.getByRole("button", { name: /Sáng/ }).click();
  await page.waitForFunction(() => document.documentElement.classList.contains("light"));
  await page.waitForFunction(
    () => getComputedStyle(document.body).backgroundColor === "rgb(248, 250, 252)",
  );
  await page.getByRole("button", { name: /Tối/ }).click();
  await page.waitForFunction(() => document.documentElement.classList.contains("dark"));
  await page.waitForFunction(
    () => getComputedStyle(document.body).backgroundColor === "rgb(2, 6, 23)",
  );
  await page.getByRole("button", { name: /Hệ thống/ }).click();
  console.log("Theme light/dark/system: OK");

  const originalVersion = await page.evaluate(async () => {
    const token = localStorage.getItem("ct_access_token");
    const response = await fetch("/api/v1/settings", {
      headers: { Authorization: `Bearer ${token}` },
    });
    return (await response.json()).data.scoring.version;
  });

  await page.getByRole("link", { name: "Settings" }).click();
  await page.getByRole("heading", { name: "Settings" }).waitFor();
  await page.getByRole("button", { name: "Preview impact" }).click();
  await page.getByRole("heading", { name: "Preview impact" }).waitFor();
  const previewBody = await page.locator("body").innerText();
  assert(previewBody.includes("đổi band"), "Preview không có thống kê band");
  await page.getByRole("button", { name: "Lưu version mới" }).click();
  await page.getByText("Đã tạo version mới").waitFor();
  await page.evaluate(async (version) => {
    const token = localStorage.getItem("ct_access_token");
    await fetch(`/api/v1/settings/rollback/${version}`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
  }, originalVersion);
  console.log("Settings preview/save/rollback: OK");

  await page.getByRole("link", { name: "Data Health" }).click();
  await page.getByRole("heading", { name: "Data Health" }).waitFor();
  await page.getByRole("heading", { name: "Universe theo tier" }).waitFor();
  const health = await page.locator("body").innerText();
  assert(
    health.toLowerCase().includes("collector đang bật"),
    "Thiếu trạng thái collector",
  );
  assert(health.includes("L0 — Universe scan"), "Thiếu bảng lần chạy");
  console.log("Data Health render: OK");

  await page.getByRole("link", { name: "Screener" }).click();
  await page.getByRole("heading", { name: "Screener" }).waitFor();
  await page.getByText(/trader khớp/).waitFor();
  const screenerBody = await page.locator("body").innerText();
  assert(screenerBody.includes("High"), "Screener thiếu tier High");
  assert(screenerBody.includes("Score"), "Screener thiếu cột Score");
  console.log("Screener render: OK");

  const compareIds = await page.evaluate(async () => {
    const token = localStorage.getItem("ct_access_token");
    const response = await fetch("/api/v1/traders?page_size=4", {
      headers: { Authorization: `Bearer ${token}` },
    });
    const json = await response.json();
    return json.data.items.map((item) => item.id).join(",");
  });
  await page.goto(`${base}/compare?ids=${compareIds}`, { waitUntil: "domcontentloaded" });
  await page.getByRole("heading", { name: "Compare" }).waitFor();
  await page.getByRole("heading", { name: "Correlation" }).waitFor();
  const compareBody = await page.locator("body").innerText();
  assert(compareBody.includes("estimated"), "Correlation thiếu disclaimer");
  assert(!compareBody.includes("undefined") && !compareBody.includes("NaN"), "Compare có undefined/NaN");
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - window.innerWidth,
  );
  assert(overflow <= 4, `Compare vỡ layout ngang (${overflow}px)`);
  console.log("Compare render: OK");

  await page.getByRole("link", { name: "Risk" }).click();
  await page.getByRole("heading", { name: "Risk Monitor" }).waitFor();
  await page.getByText(/event/).first().waitFor();
  const riskBody = await page.locator("body").innerText();
  assert(riskBody.includes("open positions"), "Risk thiếu ghi chú open positions");
  assert(!riskBody.includes("undefined") && !riskBody.includes("NaN"), "Risk có undefined/NaN");
  await page.locator("article button").first().click();
  await page.getByText("Evidence", { exact: true }).waitFor();
  console.log("Risk Monitor render: OK");

  async function pickTrader(tier) {
    return page.evaluate(async (value) => {
      const token = localStorage.getItem("ct_access_token");
      const response = await fetch(`/api/v1/universe/traders?tier=${value}&page_size=1`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const json = await response.json();
      return json.data.items[0]?.id ?? null;
    }, tier);
  }

  const qualifiedId = await pickTrader("qualified");
  assert(Boolean(qualifiedId), "Không có trader qualified trong universe");
  const aiReport = {
    id: 1,
    trader_id: qualifiedId,
    model_role: "primary",
    model_used: "fake-model",
    prompt_version: "v1",
    summary: "Trader có ROI dương, MDD trong ngưỡng và dữ liệu đủ để tham khảo.",
    strengths: ["ROI 90D dương"],
    weaknesses: ["Thiếu benchmark"],
    risk_flags: ["R02: MDD > 20%"],
    missing_data: ["missing_benchmark"],
    evidence_ids: ["id", "roi_90d", "R02"],
    prompt_tokens: 100,
    completion_tokens: 200,
    cost_usd: 0,
    latency_ms: 1200,
    status: "success",
    created_at: new Date().toISOString(),
  };
  await page.route("**/api/v1/ai/reports/**", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ data: { items: [aiReport], total: 1 }, meta: {}, error: null }),
    }),
  );
  await page.route("**/api/v1/ai/analyze/**", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        data: { report: aiReport, cached: false, ai_configured: true },
        meta: {},
        error: null,
      }),
    }),
  );
  await page.goto(`${base}/traders/${qualifiedId}`, { waitUntil: "domcontentloaded" });
  await page.getByRole("heading", { name: "10 chỉ số cốt lõi" }).waitFor();
  await page.getByRole("heading", { name: /AI Report/i }).waitFor();
  let body = await page.locator("body").innerText();
  const tooltips = await page.locator('[title*="nguồn:"]').count();
  assert(tooltips >= 10, `Thiếu tooltip nguồn (${tooltips})`);
  assert(body.includes("ROI 90D"), "Thiếu ROI 90D");
  assert(body.toLowerCase().includes("qualified"), "Thiếu badge tier");
  assert(body.toLowerCase().includes("ai report"), "Thiếu khối AI Report");
  await page.getByText(/primary/i).first().waitFor();
  body = await page.locator("body").innerText();
  assert(body.toLowerCase().includes("primary"), "Thiếu badge model primary");
  assert(body.includes("roi_90d"), "Thiếu evidence AI");
  assert(!body.includes("undefined") && !body.includes("NaN"), "UI có undefined/NaN");
  console.log("Trader qualified render + AI: OK");

  const excludedId = await pickTrader("excluded");
  assert(Boolean(excludedId), "Không có trader excluded trong universe");
  await page.goto(`${base}/traders/${excludedId}`, { waitUntil: "domcontentloaded" });
  await page.getByRole("heading", { name: "10 chỉ số cốt lõi" }).waitFor();
  body = await page.locator("body").innerText();
  assert(body.includes("Trader bị loại khỏi shortlist"), "Thiếu banner excluded");
  assert(body.includes("ROI 90D"), "Thiếu chỉ số");
  console.log("Trader excluded render: OK");

  await page.getByRole("button", { name: "Đăng xuất" }).click();
  await page.getByRole("heading", { name: "Đăng nhập" }).waitFor();
  console.log("Đăng xuất: OK");

  assert(consoleErrors.length === 0, `Console error: ${consoleErrors.join(" | ")}`);
  console.log("E2E frontend: PASS");
} finally {
  await browser.close();
}
