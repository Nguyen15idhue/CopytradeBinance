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

const base = process.env.BASE_URL ?? "http://localhost:8080";
const browser = await chromium.launch({ executablePath, headless: true });
const page = await browser.newPage();
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
    const response = await fetch("/api/v1/traders?page_size=2", {
      headers: { Authorization: `Bearer ${token}` },
    });
    const json = await response.json();
    return json.data.items.map((item) => item.id).join(",");
  });
  await page.goto(`${base}/compare?ids=${compareIds}`, { waitUntil: "domcontentloaded" });
  await page.getByRole("heading", { name: "Compare" }).waitFor();
  await page.getByRole("heading", { name: "Correlation" }).waitFor();
  const compareBody = await page.locator("body").innerText();
  assert(compareBody.includes("Correlation"), "Compare thiếu correlation");
  assert(compareBody.includes("estimated"), "Correlation thiếu disclaimer");
  console.log("Compare render: OK");

  await page.getByRole("link", { name: "Risk" }).click();
  await page.getByRole("heading", { name: "Risk Monitor" }).waitFor();
  await page.getByText(/event/).first().waitFor();
  const riskBody = await page.locator("body").innerText();
  assert(riskBody.includes("open positions"), "Risk thiếu ghi chú open positions");
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
  await page.goto(`${base}/traders/${qualifiedId}`, { waitUntil: "domcontentloaded" });
  await page.getByRole("heading", { name: "10 chỉ số cốt lõi" }).waitFor();
  let body = await page.locator("body").innerText();
  assert(body.includes("ROI 90D"), "Thiếu ROI 90D");
  assert(body.toLowerCase().includes("qualified"), "Thiếu badge tier");
  assert(!body.includes("undefined") && !body.includes("NaN"), "UI có undefined/NaN");
  console.log("Trader qualified render: OK");

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
