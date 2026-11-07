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
  await page.getByRole("heading", { name: "Trader mẫu" }).waitFor();
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

  await page.getByRole("link", { name: "Cài đặt" }).click();
  await page.getByRole("heading", { name: "Cài đặt" }).waitFor();
  await page.getByRole("button", { name: "Xem trước ảnh hưởng" }).click();
  await page.getByRole("heading", { name: "Xem trước ảnh hưởng" }).waitFor();
  const previewBody = await page.locator("body").innerText();
  assert(previewBody.includes("đổi mức điểm"), "Preview không có thống kê mức điểm");
  await page.getByRole("button", { name: "Lưu phiên bản mới" }).click();
  await page.getByText("Đã tạo phiên bản mới").waitFor();
  await page.evaluate(async (version) => {
    const token = localStorage.getItem("ct_access_token");
    await fetch(`/api/v1/settings/rollback/${version}`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
  }, originalVersion);
  console.log("Settings preview/save/rollback: OK");

  await page.getByRole("link", { name: "Bảng xếp hạng" }).click();
  await page.getByRole("heading", { name: "Bảng xếp hạng" }).waitFor();
  await page.getByText(/phiên bản cấu hình v/).waitFor();
  const rankingBody = await page.locator("body").innerText();
  assert(rankingBody.includes("Tổng hợp"), "Ranking thiếu tab Tổng hợp");
  assert(rankingBody.includes("Rủi ro thấp"), "Ranking thiếu tab Rủi ro thấp");
  await page.getByRole("button", { name: "Rủi ro thấp" }).click();
  await page.getByText(/phiên bản cấu hình v/).waitFor();
  console.log("Ranking render: OK");

  await page.getByRole("link", { name: "Hướng dẫn" }).click();
  await page.getByRole("heading", { name: "Hướng dẫn" }).waitFor();
  const helpHeadings = await page.getByRole("heading", { level: 2 }).count();
  assert(helpHeadings >= 8, `Help thiếu mục (${helpHeadings})`);
  const figures = await page.locator("figure").count();
  assert(figures >= 4, `Help thiếu hình minh hoạ (${figures})`);
  const tocLinks = await page
    .getByRole("navigation", { name: "Mục lục hướng dẫn" })
    .getByRole("link")
    .count();
  assert(tocLinks >= 8, `Mục lục thiếu mục (${tocLinks})`);
  await page.getByRole("link", { name: /Từ điển thuật ngữ/ }).click();
  await page.waitForTimeout(400);
  assert(page.url().endsWith("#glossary"), "Anchor mục lục không đổi URL");
  await page.getByPlaceholder("Tìm trong hướng dẫn...").fill("Sharpe");
  await page.waitForTimeout(300);
  const filtered = await page.getByRole("heading", { level: 2 }).count();
  assert(filtered >= 1 && filtered < helpHeadings, "Search help không lọc");
  await page.getByPlaceholder("Tìm trong hướng dẫn...").fill("");
  console.log("Help render/search: OK");

  await page.locator('a[href="/technical"]').first().click();
  await page.getByRole("heading", { name: "CopytradeBinance" }).waitFor();
  const techHeadings = await page.getByRole("heading", { level: 2 }).count();
  assert(techHeadings >= 20, `Technical docs thiếu mục (${techHeadings})`);
  const techTocLinks = await page
    .getByRole("navigation", { name: "Mục lục tài liệu kỹ thuật" })
    .getByRole("link")
    .count();
  assert(techTocLinks >= 20, `Technical TOC thiếu mục (${techTocLinks})`);
  await page
    .getByRole("navigation", { name: "Mục lục tài liệu kỹ thuật" })
    .getByRole("link", { name: /Phễu sàng lọc và Tier/ })
    .first()
    .click();
  await page.waitForTimeout(300);
  assert(page.url().endsWith("#tier"), "Technical anchor không đổi URL");
  await page.getByPlaceholder("Tìm trong tài liệu...").fill("tier");
  await page.waitForTimeout(300);
  const techFiltered = await page.getByRole("heading", { level: 2 }).count();
  assert(techFiltered >= 1 && techFiltered < techHeadings, "Search technical không lọc");
  await page.getByPlaceholder("Tìm trong tài liệu...").fill("");
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole("button", { name: "Mục lục" }).click();
  await page
    .getByRole("navigation", { name: "Mục lục tài liệu kỹ thuật" })
    .waitFor();
  await page.getByRole("button", { name: "Ẩn mục lục" }).click();
  const techOverflow = await page.evaluate(
    () => document.documentElement.scrollWidth - window.innerWidth,
  );
  assert(techOverflow <= 4, `Technical docs vỡ layout ngang (${techOverflow}px)`);
  await page.setViewportSize({ width: 1440, height: 900 });
  const techBody = await page.locator("body").innerText();
  assert(!techBody.includes("undefined") && !techBody.includes("NaN"), "Technical docs có undefined/NaN");
  console.log("Technical docs render/TOC/search: OK");

  await page.getByRole("link", { name: "Sức khỏe dữ liệu" }).click();
  await page.getByRole("heading", { name: "Sức khỏe dữ liệu" }).waitFor();
  await page.getByRole("heading", { name: "Universe theo nhóm" }).waitFor();
  const health = await page.locator("body").innerText();
  const healthLower = health.toLowerCase();
  assert(
    healthLower.includes("bộ thu thập") &&
      (healthLower.includes("đang bật") || healthLower.includes("công tắc dừng")),
    "Thiếu trạng thái bộ thu thập",
  );
  assert(health.includes("L0 — Quét universe"), "Thiếu bảng lần chạy");
  console.log("Data Health render: OK");

  await page.getByRole("link", { name: "Bộ lọc trader" }).click();
  await page.getByRole("heading", { name: "Bộ lọc trader" }).waitFor();
  await page.getByText(/trader khớp/).waitFor();
  const screenerBody = await page.locator("body").innerText();
  assert(screenerBody.includes("Cao (A)"), "Screener thiếu nhóm Cao (A)");
  assert(screenerBody.includes("Điểm"), "Screener thiếu cột Điểm");
  for (const code of ["high_upper", "qualified_upper", "excellent", "low_sample", "hf0", "fallback"]) {
    assert(!screenerBody.includes(code), `Screener lọt mã thô ${code}`);
  }
  console.log("Screener render: OK");

  const banner = page.getByText("Mới bắt đầu?");
  if (await banner.count()) {
    await page.getByRole("button", { name: "Đã hiểu" }).click();
    await page.reload({ waitUntil: "domcontentloaded" });
    await page.getByRole("heading", { name: "Bộ lọc trader" }).waitFor();
  }
  const bannerAfter = await page.getByText("Mới bắt đầu?").count();
  assert(bannerAfter === 0, "Banner onboarding không dismiss vĩnh viễn");
  console.log("Onboarding banner dismiss: OK");

  const compareIds = await page.evaluate(async () => {
    const token = localStorage.getItem("ct_access_token");
    const response = await fetch("/api/v1/traders?page_size=4", {
      headers: { Authorization: `Bearer ${token}` },
    });
    const json = await response.json();
    return json.data.items.map((item) => item.id).join(",");
  });
  await page.goto(`${base}/compare?ids=${compareIds}`, { waitUntil: "domcontentloaded" });
  await page.getByRole("heading", { name: "So sánh" }).waitFor();
  await page.getByRole("heading", { name: "Tương quan" }).waitFor();
  const compareBody = await page.locator("body").innerText();
  assert(compareBody.includes("ước tính"), "Tương quan thiếu disclaimer");
  assert(!compareBody.includes("undefined") && !compareBody.includes("NaN"), "Compare có undefined/NaN");
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - window.innerWidth,
  );
  assert(overflow <= 4, `Compare vỡ layout ngang (${overflow}px)`);
  console.log("Compare render: OK");

  await page.getByRole("link", { name: "Cảnh báo rủi ro" }).click();
  await page.getByRole("heading", { name: "Cảnh báo rủi ro" }).waitFor();
  await page.getByText(/cảnh báo/).first().waitFor();
  const riskBody = await page.locator("body").innerText();
  assert(riskBody.includes("vị thế đang mở"), "Risk thiếu ghi chú vị thế đang mở");
  assert(!riskBody.includes("undefined") && !riskBody.includes("NaN"), "Risk có undefined/NaN");
  await page.locator("article button").first().click();
  await page.getByText("Bằng chứng", { exact: true }).waitFor();
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
    prompt_version: "v2",
    summary:
      "ROI 90D 20,00% cao hơn ngưỡng 0 nhưng MDD 10,00% vẫn trong ngưỡng cảnh báo 20%; độ tin cậy 0,90 cho thấy dữ liệu khá đầy đủ.",
    strengths: ["ROI 90D 20,00% cao hơn 0, cho thấy hiệu suất dương trong 90 ngày."],
    weaknesses: ["Độ tin cậy 0,90 chưa đạt 1,0 nên vẫn còn khoảng trống dữ liệu."],
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
  await page.getByRole("heading", { name: /Nhận định AI/i }).waitFor();
  let body = await page.locator("body").innerText();
  const tooltips = await page.locator('[title*="nguồn:"]').count();
  assert(tooltips >= 10, `Thiếu tooltip nguồn (${tooltips})`);
  assert(body.includes("ROI 90D"), "Thiếu ROI 90D");
  const detailBodyLower = body.toLowerCase();
  assert(
    detailBodyLower.includes("cao (a)") || detailBodyLower.includes("đạt (b)"),
    "Thiếu badge nhóm tiếng Việt",
  );
  assert(body.toLowerCase().includes("nhận định ai"), "Thiếu khối Nhận định AI");
  await page.getByText(/Model chính/i).first().waitFor();
  body = await page.locator("body").innerText();
  assert(body.toLowerCase().includes("model chính"), "Thiếu badge model chính");
  assert(body.includes("roi_90d"), "Thiếu bằng chứng AI");
  for (const code of ["qualified_upper", "fallback", "hf0"]) {
    assert(!body.includes(code), `Detail lọt mã thô ${code}`);
  }
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

  await page.route("**/api/v1/agent/sessions", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ data: { items: [] }, meta: {}, error: null }),
    }),
  );
  const sseBody = [
    'event: citation',
    'data: {"items": [{"source_type": "database", "ref": "roi_90d"}]}',
    "",
    "event: done",
    'data: {"session_id": 1, "message_id": 2, "answer": "ROI 90D là 19,19% theo dữ liệu.", "model": "mock", "usage": {}}',
    "",
    "",
  ].join("\n");
  await page.route("**/api/v1/agent/chat", (route) =>
    route.fulfill({
      status: 200,
      contentType: "text/event-stream",
      body: sseBody,
    }),
  );
  await page.getByRole("button", { name: "Mở trợ lý AI" }).click();
  await page.getByRole("dialog", { name: "Trợ lý AI" }).waitFor();
  await page.getByRole("button", { name: /Top 10 trader an toàn/ }).click();
  await page.getByText("ROI 90D là 19,19%").waitFor();
  await page.getByText("database: roi_90d").waitFor();
  body = await page.locator("body").innerText();
  assert(!body.includes("undefined") && !body.includes("NaN"), "Agent UI có undefined/NaN");
  await page.keyboard.press("Escape");
  await page.getByRole("button", { name: "Mở trợ lý AI" }).waitFor();
  console.log("Agent chat mock SSE: OK");

  await page.getByRole("button", { name: "Đăng xuất" }).click();
  await page.getByRole("heading", { name: "Đăng nhập" }).waitFor();
  console.log("Đăng xuất: OK");

  await page.getByLabel("Email").fill("viewer@example.com");
  await page.getByLabel("Mật khẩu").fill("Viewer123!ChangeMe");
  await page.getByRole("button", { name: "Đăng nhập" }).click();
  await page.waitForURL(`${base}/`);
  assert(
    (await page.getByRole("button", { name: "Mở trợ lý AI" }).count()) === 0,
    "Viewer vẫn thấy icon agent",
  );
  console.log("Agent ẩn với viewer: OK");

  assert(consoleErrors.length === 0, `Console error: ${consoleErrors.join(" | ")}`);
  console.log("E2E frontend: PASS");
} finally {
  await browser.close();
}
