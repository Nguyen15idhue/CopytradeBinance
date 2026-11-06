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

  await page.getByRole("link", { name: /Qualified Fixture/ }).click();
  await page.getByRole("heading", { name: "10 chỉ số cốt lõi" }).waitFor();
  let body = await page.locator("body").innerText();
  assert(body.includes("Qualified"), "Thiếu badge Qualified");
  assert(body.includes("19.19%"), "Thiếu ROI 90D");
  assert(body.includes("8.54%"), "Thiếu MDD 90D");
  assert(!body.includes("undefined") && !body.includes("NaN"), "UI có undefined/NaN");
  console.log("Trader qualified render: OK");

  await page.goto(`${base}/`, { waitUntil: "domcontentloaded" });
  await page.getByRole("link", { name: /Excluded Fixture/ }).click();
  await page.getByRole("heading", { name: "10 chỉ số cốt lõi" }).waitFor();
  body = await page.locator("body").innerText();
  assert(body.includes("Trader bị loại khỏi shortlist"), "Thiếu banner excluded");
  assert(body.includes("Runtime < 30 ngày"), "Thiếu lý do runtime");
  assert(body.includes("N/A"), "Thiếu N/A cho field null");
  console.log("Trader excluded render: OK");

  await page.getByRole("button", { name: "Đăng xuất" }).click();
  await page.getByRole("heading", { name: "Đăng nhập" }).waitFor();
  console.log("Đăng xuất: OK");

  assert(consoleErrors.length === 0, `Console error: ${consoleErrors.join(" | ")}`);
  console.log("E2E frontend: PASS");
} finally {
  await browser.close();
}
