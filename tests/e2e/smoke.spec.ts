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

async function expectSearchParams(
  page: Page,
  expected: Record<string, string | null>,
) {
  await expect
    .poll(() => {
      const params = new URL(page.url()).searchParams;
      return Object.fromEntries(
        Object.keys(expected).map((key) => [key, params.get(key)]),
      );
    })
    .toEqual(expected);
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
  await expectSearchParams(page, {
    view: "index",
    q: "茉莉",
    compare: "jasmine",
  });
  await expect(page.getByText(/Jasmine selected/)).toBeVisible();

  await page.getByLabel(/Search English/).fill("cacao");
  await expectSearchParams(page, {
    view: "index",
    q: "cacao",
    compare: "jasmine",
  });
  await expect(
    page.getByRole("link", { name: "黑巧克力", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: /Compare Dark Chocolate/ }).click();
  await expectSearchParams(page, {
    view: "index",
    q: "cacao",
    compare: "jasmine,dark-chocolate",
  });
  await expect(
    page.getByRole("heading", { name: /Descriptor comparison/ }),
  ).toBeVisible();
  await expect(page.getByText(/^差异最大:/)).toBeVisible();
  await page.getByRole("button", { name: /Close comparison/ }).click();
  await expectSearchParams(page, {
    view: "index",
    q: "cacao",
    compare: null,
  });
  await expect(
    page.getByRole("heading", { name: /Descriptor comparison/ }),
  ).toBeHidden();

  await page.getByLabel(/Search English/).fill("lemon");
  await expectSearchParams(page, {
    view: "index",
    q: "lemon",
    compare: null,
  });
  await page.getByRole("button", { name: "MAP" }).click();
  await expectSearchParams(page, {
    view: "map",
    q: "lemon",
    compare: null,
  });
  await expect(
    page.getByRole("img", { name: /Sensory association map/ }),
  ).toBeVisible();
  await page.getByRole("link", { name: /Open Lemon detail page/ }).click();
  await expect(page).toHaveURL(/\/flavor\/lemon/);
  await expect(page.getByRole("heading", { name: /柠檬/ })).toBeVisible();
  expect(consoleErrors).toEqual([]);
});

test("comparison selection survives an immediate search-param update", async ({
  page,
}) => {
  const consoleErrors = watchConsoleErrors(page);
  await page.goto("/atlas?view=index");

  await page.getByLabel(/Search English/).fill("茉莉");
  await expect(
    page.getByRole("link", { name: "茉莉", exact: true }),
  ).toBeVisible();

  await page.getByRole("button", { name: /Compare Jasmine/ }).click();
  await page.getByLabel(/Search English/).fill("cacao");
  await expect(
    page.getByRole("link", { name: "黑巧克力", exact: true }),
  ).toBeVisible();
  await expectSearchParams(page, {
    view: "index",
    q: "cacao",
    compare: "jasmine",
  });

  await page.getByRole("button", { name: /Compare Dark Chocolate/ }).click();
  await expectSearchParams(page, {
    view: "index",
    q: "cacao",
    compare: "jasmine,dark-chocolate",
  });
  await expect(
    page.getByRole("heading", { name: /Descriptor comparison/ }),
  ).toBeVisible();
  await expect(page.getByText(/^差异最大:/)).toBeVisible();
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

test("project status is generated, keyboard reachable, and reduced-motion aware", async ({
  page,
  request,
}) => {
  const consoleErrors = watchConsoleErrors(page);
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/methodology#project-status");

  await expect(
    page.getByRole("heading", { name: /evidence before adjectives/i }),
  ).toBeVisible();
  await expect(page.getByText("NOT_STARTED", { exact: true })).toHaveCount(2);
  await expect(
    page.getByRole("link", { name: /Try the 5\+3 prototype/ }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: /Download public status JSON/ }),
  ).toBeVisible();

  const reducedMotion = await page.evaluate(
    () => window.matchMedia("(prefers-reduced-motion: reduce)").matches,
  );
  expect(reducedMotion).toBe(true);

  await page.goto("/");
  await page.keyboard.press("Tab");
  await expect(
    page.getByRole("link", { name: /Skip to content/ }),
  ).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.locator("#main-content")).toBeFocused();

  const statusResponse = await request.get("/project-status.json");
  expect(statusResponse.ok()).toBe(true);
  const status = await statusResponse.json();
  expect(status.ml.model_status).toBe("NOT_TRAINED");
  expect(status.pwa.public_claim_allowed).toBe(true);
  expect(status.first_party_user_research.user_data_collected).toBe(false);

  const hasHorizontalOverflow = await page.evaluate(
    () => document.documentElement.scrollWidth > window.innerWidth + 1,
  );
  expect(hasHorizontalOverflow).toBe(false);
  expect(consoleErrors).toEqual([]);
});

test("deterministic prototype completes C0, seven-level C1, Q1-Q4, and 5+3 output", async ({
  page,
}) => {
  const consoleErrors = watchConsoleErrors(page);
  await page.goto("/prototype");
  await expect(
    page.getByRole("heading", { name: /Evidence-connected candidates/ }),
  ).toBeVisible();
  await page.getByLabel("Filter / 手冲").check();
  await page.getByRole("group", { name: /C1/ }).getByLabel("3").check();
  await page
    .getByRole("group", { name: /Q1/ })
    .getByLabel(/Jasmine/)
    .check();
  await page
    .getByRole("group", { name: /Q2/ })
    .getByLabel(/Red Berries/)
    .check();
  await page.getByRole("group", { name: /Q3/ }).getByLabel(/Honey/).check();
  await page.getByRole("group", { name: /Q4/ }).getByLabel(/Cedar/).check();
  await expect(
    page.getByRole("heading", { name: "Five primary candidates" }),
  ).toBeVisible();
  await expect(
    page.locator(".candidate-list").first().locator("li"),
  ).toHaveCount(5);
  await expect(page.locator(".candidate-list--secondary li")).toHaveCount(3);
  await expect(page.getByText(/No calibrated probabilities/)).toBeVisible();
  expect(consoleErrors).toEqual([]);
});

test("PWA manifest, public snapshot, local consent default, and offline shell are available", async ({
  page,
  context,
  request,
}) => {
  const manifestResponse = await request.get("/manifest.webmanifest");
  expect(manifestResponse.ok()).toBe(true);
  const manifest = await manifestResponse.json();
  expect(manifest.display).toBe("standalone");
  expect(manifest.icons).toHaveLength(2);
  const snapshot = await request.get("/knowledge/round4a-public-v1.json");
  expect(snapshot.ok()).toBe(true);
  expect((await snapshot.json()).restricted_source_material_included).toBe(
    false,
  );

  await page.goto("/prototype/");
  await expect(
    page.getByText("NO_REMOTE_COLLECTION", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: /Create export preview/ }),
  ).toBeDisabled();
  await page.evaluate(() => navigator.serviceWorker.ready);
  await page.reload();
  await context.setOffline(true);
  await page.goto("/prototype/");
  await expect(
    page.getByRole("heading", { name: /Evidence-connected candidates/ }),
  ).toBeVisible();
  await context.setOffline(false);
});
