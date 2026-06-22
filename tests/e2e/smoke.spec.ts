import { expect, test, type Page } from "@playwright/test";

function watchConsoleErrors(page: Page) {
  const consoleErrors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") {
      consoleErrors.push(message.text());
    }
  });
  page.on("pageerror", (error) => consoleErrors.push(error.message));

  return consoleErrors;
}

test("home page, methodology, and desktop layout load without horizontal overflow", async ({
  page,
}) => {
  const consoleErrors = watchConsoleErrors(page);
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /Atlas/ })).toBeVisible();
  await expect(page.getByRole("link", { name: /Enter Atlas/ })).toBeVisible();
  await expect(page.getByRole("link", { name: "Fruit 水果" })).toBeVisible();
  await page.getByRole("link", { name: /METHOD/ }).click();
  await expect(
    page.getByRole("navigation", { name: /Method sections/ }),
  ).toBeVisible();
  await expect(page.getByText(/descriptor is not observation/)).toBeVisible();

  const hasHorizontalOverflow = await page.evaluate(
    () => document.documentElement.scrollWidth > window.innerWidth + 1,
  );
  expect(hasHorizontalOverflow).toBe(false);
  expect(consoleErrors).toEqual([]);
});

test("atlas search, aliases, map navigation, and comparison work", async ({
  page,
}) => {
  const consoleErrors = watchConsoleErrors(page);
  await page.goto("/atlas?view=index");
  await expect(page.getByText(/visible descriptors/)).toBeVisible();

  await page.getByLabel(/Search English/).fill("茉莉");
  await expect(
    page.getByRole("link", { name: "茉莉", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: /Compare Jasmine/ }).click();

  await page.getByLabel(/Search English/).fill("cacao");
  await expect(
    page.getByRole("link", { name: "黑巧克力", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: /Compare Dark Chocolate/ }).click();
  await expect(
    page.getByRole("heading", { name: /Descriptor comparison/ }),
  ).toBeVisible();
  await expect(page.getByText(/^差异最大:/)).toBeVisible();
  await page.getByRole("button", { name: /Close comparison/ }).click();

  await page.getByLabel(/Search English/).fill("lemon");
  await page.getByRole("button", { name: "MAP" }).click();
  await expect(
    page.getByRole("img", { name: /Sensory association map/ }),
  ).toBeVisible();
  await page.getByRole("link", { name: /Open Lemon detail page/ }).click();
  await expect(page).toHaveURL(/\/flavor\/lemon/);
  await expect(page.getByRole("heading", { name: /柠檬/ })).toBeVisible();
  expect(consoleErrors).toEqual([]);
});

test("mobile atlas layout avoids horizontal overflow", async ({ page }) => {
  const consoleErrors = watchConsoleErrors(page);
  await page.setViewportSize({ width: 390, height: 900 });
  await page.goto("/atlas?category=fruit&view=map");
  await expect(
    page.getByRole("img", { name: /Sensory association map/ }),
  ).toBeVisible();

  const hasHorizontalOverflow = await page.evaluate(
    () => document.documentElement.scrollWidth > window.innerWidth + 1,
  );
  expect(hasHorizontalOverflow).toBe(false);
  expect(consoleErrors).toEqual([]);
});
