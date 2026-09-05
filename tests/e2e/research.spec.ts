import { expect, test, type Page } from "@playwright/test";
import { readFileSync } from "node:fs";
import type { SessionExport } from "../../packages/flavor-data/src/research/session";

const enabled = process.env.VITE_COFFEE_RESEARCH === "1";
async function begin(page: Page, id = "R3O-001") {
  await page.goto("/research/user-study");
  await page.getByLabel("研究编号").fill(id);
  await page.getByLabel("你与咖啡的接触").selectOption("novice");
  await page.getByRole("button", { name: "开始任务", exact: true }).click();
  await expect(
    page.getByText(
      "回答几个关于这杯咖啡的问题，找一些词来描述你闻到、喝到的感觉。",
    ),
  ).toBeVisible();
  await page.getByRole("button", { name: "读完了" }).click();
  await page.getByLabel("研究者记录").selectOption("correct");
  await page.getByRole("button", { name: "继续", exact: true }).click();
  await page.getByRole("radio", { name: /手冲 \/ 滴滤/ }).check();
  await page.getByRole("button", { name: "继续", exact: true }).click();
  await expect(page.getByRole("radio")).toHaveCount(8);
  await page.getByRole("radio", { name: "不确定 / 包装没有写" }).check();
  await page.getByRole("button", { name: "开始风味问题" }).click();
}
async function exportRecord(page: Page) {
  await page.getByRole("button", { name: "完成后续反馈" }).click();
  await page.locator('select[name="helpfulness"]').selectOption("3");
  await page.locator('select[name="comprehension"]').selectOption("partial");
  await page.locator('select[name="partial"]').selectOption("accept");
  await page.locator('select[name="reuse"]').selectOption("maybe");
  await page.locator('select[name="help"]').selectOption("yes");
  await page.locator('select[name="difficulty"]').selectOption("wording");
  await page.getByRole("button", { name: "生成本地研究记录" }).click();
  const pending = page.waitForEvent("download");
  await page.getByRole("link", { name: "下载本次记录 JSON" }).click();
  const download = await pending;
  // The page validates and replays the session before creating this download;
  // schema rejection is covered independently by the pure-engine unit tests.
  return JSON.parse(
    readFileSync((await download.path())!, "utf8"),
  ) as SessionExport;
}

test("research route is absent unless explicitly enabled", async ({ page }) => {
  test.skip(
    enabled,
    "This build intentionally enables the local research route",
  );
  await page.goto("/research/user-study");
  // Static preview serves the SPA fallback with HTTP 200; the router owns 404 UI.
  await expect(
    page.getByRole("heading", { name: "404 Not Found", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "开始任务", exact: true }),
  ).toHaveCount(0);
});

test("research A multi-select produces layered results and local export without network writes", async ({
  page,
}, testInfo) => {
  test.skip(!enabled, "Research flag is disabled in this build");
  const errors: string[] = [];
  const writes: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("console", (m) => {
    if (m.type() === "error") errors.push(m.text());
  });
  page.on("request", (r) => {
    if (!["GET", "HEAD"].includes(r.method())) writes.push(r.url());
  });
  await begin(page);
  await expect(page.getByRole("checkbox")).toHaveCount(4);
  await expect(page.getByRole("button", { name: "确认选择" })).toBeDisabled();
  for (const box of await page.getByRole("checkbox").all()) await box.check();
  await page.screenshot({
    path: testInfo.outputPath("research-question.png"),
    fullPage: true,
  });
  await page.getByRole("button", { name: "确认选择" }).click();
  for (const box of await page.getByRole("checkbox").all()) await box.check();
  await page.getByRole("button", { name: "确认选择" }).click();
  await expect(
    page.getByRole("heading", { name: "目前的风味联想" }),
  ).toBeVisible();
  await expect(page.locator(".research-results li")).toHaveCount(3);
  await expect(
    page.getByRole("heading", { name: "还可以继续留意" }),
  ).toHaveCount(0);
  await page.getByRole("button", { name: "展开更多联想" }).click();
  await expect(
    page.getByRole("heading", { name: "还可以继续留意" }),
  ).toBeVisible();
  await page.screenshot({
    path: testInfo.outputPath("research-results.png"),
    fullPage: true,
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth + 1,
    ),
  ).toBe(true);
  await page
    .getByRole("checkbox", { name: "我想描述的感觉在这些方向之外" })
    .check();
  await expect(page.locator(".research-results li")).toHaveCount(0);
  await page
    .getByRole("checkbox", { name: "我想描述的感觉在这些方向之外" })
    .uncheck();
  const record = await exportRecord(page);
  expect(record.openSet).toBe(false);
  expect(record.earlyStopReason).not.toBe("PARTICIPANT_REPORTED_OPEN_SET");
  expect(record.languageVariant).toBe("A");
  expect(record.totalQuestionCount).toBe(2);
  expect(record.questions[0]?.allOptionsSelected).toBe(true);
  expect(record.expandClicked).toBe(true);
  expect(record.c1Unsure).toBe(true);
  expect(record.headlineResultCount).toBe(3);
  expect(record.questions.every((q) => q.responseTimeMs >= 0)).toBe(true);
  expect(writes).toEqual([]);
  expect(errors).toEqual([]);
});

test("research B branching and Q5 acceptance followed by partial exit remain exportable", async ({
  page,
}) => {
  test.skip(!enabled, "Research flag is disabled in this build");
  await begin(page, "R3O-002");
  await expect(page.getByRole("checkbox")).toHaveCount(3);
  await page.getByRole("checkbox", { name: /像水果或花/ }).check();
  await page.getByRole("button", { name: "确认选择" }).click();
  await expect(
    page.getByRole("heading", { name: "再分开想想，哪些例子比较接近？" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "先看当前结果" }).click();
  const first = await exportRecord(page);
  expect(first.languageVariant).toBe("B");
  await begin(page, "R3O-004");
  for (let i = 0; i < 4; i++)
    await page.getByRole("button", { name: "不确定", exact: true }).click();
  await page.getByRole("button", { name: "再回答一题，让结果更具体" }).click();
  await expect(page.getByText("第 5 道风味问题")).toBeVisible();
  await page.getByRole("button", { name: "先看当前结果" }).click();
  const partial = await exportRecord(page);
  expect(partial.totalQuestionCount).toBe(4);
  expect(partial.q5Accepted).toBe(true);
  expect(partial.q5Offered).toBe(true);
});

test("Q5 answer completes exactly five questions and does not offer a sixth", async ({
  page,
}) => {
  test.skip(!enabled, "Research flag is disabled in this build");
  await begin(page);
  for (let i = 0; i < 4; i++)
    await page.getByRole("button", { name: "跳过", exact: true }).click();
  await page.getByRole("button", { name: "再回答一题，让结果更具体" }).click();
  await page.getByRole("checkbox").first().check();
  await page.getByRole("button", { name: "确认选择" }).click();
  await expect(
    page.getByRole("button", { name: "再回答一题，让结果更具体" }),
  ).toHaveCount(0);
  const record = await exportRecord(page);
  expect(record.totalQuestionCount).toBe(5);
  expect(record.q5Accepted).toBe(true);
});
