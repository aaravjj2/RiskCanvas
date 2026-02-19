/**
 * test-w41-w48-unit.spec.ts
 * Wave 41-48 — Enterprise Layer: Tenancy, Artifacts, Attestations, Compliance, Judge v2
 * v4.98.0 → v5.21.0
 *
 * ALL selectors use data-testid ONLY.
 * No waitForTimeout. retries=0. workers=1.
 */
import { test, expect } from "@playwright/test";

const BASE = process.env.PLAYWRIGHT_TEST_BASE_URL || "http://localhost:4177";

// ── WAVE 41: Tenant Navigation ─────────────────────────────────────────────

test.describe("Wave 41 — AppLayout nav items for Enterprise pages", () => {
  test("nav-admin is present in sidebar", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 15_000 });
    await page.getByTestId("nav-admin").evaluate((el: HTMLElement) =>
      el.scrollIntoView({ block: "center", behavior: "instant" })
    );
    await expect(page.getByTestId("nav-admin")).toBeVisible();
  });

  test("nav-artifacts is present in sidebar", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 15_000 });
    await page.getByTestId("nav-artifacts").evaluate((el: HTMLElement) =>
      el.scrollIntoView({ block: "center", behavior: "instant" })
    );
    await expect(page.getByTestId("nav-artifacts")).toBeVisible();
  });

  test("nav-attestations is present in sidebar", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 15_000 });
    await page.getByTestId("nav-attestations").evaluate((el: HTMLElement) =>
      el.scrollIntoView({ block: "center", behavior: "instant" })
    );
    await expect(page.getByTestId("nav-attestations")).toBeVisible();
  });

  test("nav-compliance is present in sidebar", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 15_000 });
    await page.getByTestId("nav-compliance").evaluate((el: HTMLElement) =>
      el.scrollIntoView({ block: "center", behavior: "instant" })
    );
    await expect(page.getByTestId("nav-compliance")).toBeVisible();
  });

  test("clicking nav-admin navigates to /admin", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 15_000 });
    await page.getByTestId("nav-admin").evaluate((el: HTMLElement) =>
      el.scrollIntoView({ block: "center", behavior: "instant" })
    );
    await page.getByTestId("nav-admin").click();
    await expect(page.getByTestId("admin-page")).toBeVisible({ timeout: 15_000 });
  });

  test("clicking nav-artifacts navigates to /artifacts", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 15_000 });
    await page.getByTestId("nav-artifacts").evaluate((el: HTMLElement) =>
      el.scrollIntoView({ block: "center", behavior: "instant" })
    );
    await page.getByTestId("nav-artifacts").click();
    await expect(page.getByTestId("artifacts-page")).toBeVisible({ timeout: 15_000 });
  });

  test("clicking nav-attestations navigates to /attestations", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 15_000 });
    await page.getByTestId("nav-attestations").evaluate((el: HTMLElement) =>
      el.scrollIntoView({ block: "center", behavior: "instant" })
    );
    await page.getByTestId("nav-attestations").click();
    await expect(page.getByTestId("attestations-page")).toBeVisible({ timeout: 15_000 });
  });

  test("clicking nav-compliance navigates to /compliance", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 15_000 });
    await page.getByTestId("nav-compliance").evaluate((el: HTMLElement) =>
      el.scrollIntoView({ block: "center", behavior: "instant" })
    );
    await page.getByTestId("nav-compliance").click();
    await expect(page.getByTestId("compliance-page")).toBeVisible({ timeout: 15_000 });
  });
});

// ── WAVE 41: TenantSwitcher ────────────────────────────────────────────────

test.describe("Wave 41 — TenantSwitcher component", () => {
  test("tenant-switcher renders in sidebar", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("tenant-switcher")).toBeVisible();
  });

  test("tenant-current shows a tenant name", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("tenant-current")).toBeVisible();
    const text = await page.getByTestId("tenant-current").textContent();
    expect((text ?? "").length).toBeGreaterThan(0);
  });

  test("tenant-switcher opens dropdown on click", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 15_000 });
    await page.getByTestId("tenant-switcher").click();
    // At least one tenant-option should appear
    const options = page.locator("[data-testid^='tenant-option-']");
    await expect(options.first()).toBeVisible({ timeout: 5_000 });
  });
});

// ── WAVE 41: AdminPage ────────────────────────────────────────────────────

test.describe("Wave 41 — AdminPage", () => {
  test("admin-page renders on /admin", async ({ page }) => {
    await page.goto(`${BASE}/admin`);
    await expect(page.getByTestId("admin-page")).toBeVisible({ timeout: 15_000 });
  });

  test("tenants-table-ready appears after load", async ({ page }) => {
    await page.goto(`${BASE}/admin`);
    await expect(page.getByTestId("tenants-table-ready")).toBeVisible({ timeout: 20_000 });
  });

  test("tenant-row-0 renders in the tenants table", async ({ page }) => {
    await page.goto(`${BASE}/admin`);
    await expect(page.getByTestId("tenants-table-ready")).toBeVisible({ timeout: 20_000 });
    await expect(page.getByTestId("tenant-row-0")).toBeVisible();
  });

  test("members-table-ready appears after selecting a tenant", async ({ page }) => {
    await page.goto(`${BASE}/admin`);
    await expect(page.getByTestId("tenants-table-ready")).toBeVisible({ timeout: 20_000 });
    await page.getByTestId("tenant-row-0").click();
    await expect(page.getByTestId("members-table-ready")).toBeVisible({ timeout: 15_000 });
  });

  test("member-row-0 renders after selecting tenant", async ({ page }) => {
    await page.goto(`${BASE}/admin`);
    await expect(page.getByTestId("tenants-table-ready")).toBeVisible({ timeout: 20_000 });
    await page.getByTestId("tenant-row-0").click();
    await expect(page.getByTestId("members-table-ready")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("member-row-0")).toBeVisible();
  });

  test("invite-btn is present on admin page", async ({ page }) => {
    await page.goto(`${BASE}/admin`);
    await expect(page.getByTestId("admin-page")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("invite-btn")).toBeVisible();
  });

  test("admin-audit-tab is present on admin page", async ({ page }) => {
    await page.goto(`${BASE}/admin`);
    await expect(page.getByTestId("admin-page")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("admin-audit-tab")).toBeVisible();
  });

  test("clicking admin-audit-tab shows audit-list-ready", async ({ page }) => {
    await page.goto(`${BASE}/admin`);
    await expect(page.getByTestId("admin-page")).toBeVisible({ timeout: 15_000 });
    await page.getByTestId("admin-audit-tab").click();
    await expect(page.getByTestId("audit-list-ready")).toBeVisible({ timeout: 15_000 });
  });

  test("audit-row-0 renders in audit tab", async ({ page }) => {
    await page.goto(`${BASE}/admin`);
    await expect(page.getByTestId("admin-page")).toBeVisible({ timeout: 15_000 });
    await page.getByTestId("admin-audit-tab").click();
    await expect(page.getByTestId("audit-list-ready")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("audit-row-0")).toBeVisible();
  });
});

// ── WAVE 42: ArtifactsPage ────────────────────────────────────────────────

test.describe("Wave 42 — ArtifactsPage", () => {
  test("artifacts-page renders on /artifacts", async ({ page }) => {
    await page.goto(`${BASE}/artifacts`);
    await expect(page.getByTestId("artifacts-page")).toBeVisible({ timeout: 15_000 });
  });

  test("artifact-row-0 renders after data loads", async ({ page }) => {
    await page.goto(`${BASE}/artifacts`);
    await expect(page.getByTestId("artifacts-page")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("artifact-row-0")).toBeVisible({ timeout: 20_000 });
  });

  test("clicking artifact-row-0 opens detail drawer", async ({ page }) => {
    await page.goto(`${BASE}/artifacts`);
    await expect(page.getByTestId("artifact-row-0")).toBeVisible({ timeout: 20_000 });
    await page.getByTestId("artifact-row-0").click();
    await expect(page.getByTestId("artifact-drawer-ready")).toBeVisible({ timeout: 10_000 });
  });

  test("artifact-verify-btn is present in drawer", async ({ page }) => {
    await page.goto(`${BASE}/artifacts`);
    await expect(page.getByTestId("artifact-row-0")).toBeVisible({ timeout: 20_000 });
    await page.getByTestId("artifact-row-0").click();
    await expect(page.getByTestId("artifact-drawer-ready")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByTestId("artifact-verify-btn")).toBeVisible();
  });
});

// ── WAVE 43: AttestationsPage ─────────────────────────────────────────────

test.describe("Wave 43 — AttestationsPage", () => {
  test("attestations-page renders on /attestations", async ({ page }) => {
    await page.goto(`${BASE}/attestations`);
    await expect(page.getByTestId("attestations-page")).toBeVisible({ timeout: 15_000 });
  });

  test("attestation-row-0 renders after data loads", async ({ page }) => {
    await page.goto(`${BASE}/attestations`);
    await expect(page.getByTestId("attestations-page")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("attestation-row-0")).toBeVisible({ timeout: 20_000 });
  });

  test("clicking attestation-row-0 opens detail drawer", async ({ page }) => {
    await page.goto(`${BASE}/attestations`);
    await expect(page.getByTestId("attestation-row-0")).toBeVisible({ timeout: 20_000 });
    await page.getByTestId("attestation-row-0").click();
    await expect(page.getByTestId("attestation-drawer-ready")).toBeVisible({ timeout: 10_000 });
  });

  test("attestation-prev-link renders in drawer", async ({ page }) => {
    await page.goto(`${BASE}/attestations`);
    await expect(page.getByTestId("attestation-row-0")).toBeVisible({ timeout: 20_000 });
    await page.getByTestId("attestation-row-0").click();
    await expect(page.getByTestId("attestation-drawer-ready")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByTestId("attestation-prev-link")).toBeVisible();
  });
});

// ── WAVE 44: CompliancePage ───────────────────────────────────────────────

test.describe("Wave 44 — CompliancePage", () => {
  test("compliance-page renders on /compliance", async ({ page }) => {
    await page.goto(`${BASE}/compliance`);
    await expect(page.getByTestId("compliance-page")).toBeVisible({ timeout: 15_000 });
  });

  test("compliance-generate-btn is visible", async ({ page }) => {
    await page.goto(`${BASE}/compliance`);
    await expect(page.getByTestId("compliance-page")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("compliance-generate-btn")).toBeVisible();
  });

  test("clicking generate-btn triggers pack generation and shows packs-ready", async ({
    page,
  }) => {
    await page.goto(`${BASE}/compliance`);
    await expect(page.getByTestId("compliance-page")).toBeVisible({ timeout: 15_000 });
    await page.getByTestId("compliance-generate-btn").click();
    await expect(page.getByTestId("compliance-packs-ready")).toBeVisible({ timeout: 30_000 });
  });

  test("compliance-pack-row-0 renders after generation", async ({ page }) => {
    await page.goto(`${BASE}/compliance`);
    await expect(page.getByTestId("compliance-page")).toBeVisible({ timeout: 15_000 });
    await page.getByTestId("compliance-generate-btn").click();
    await expect(page.getByTestId("compliance-packs-ready")).toBeVisible({ timeout: 30_000 });
    await expect(page.getByTestId("compliance-pack-row-0")).toBeVisible();
  });

  test("compliance-verify-btn is present after pack row", async ({ page }) => {
    await page.goto(`${BASE}/compliance`);
    await expect(page.getByTestId("compliance-page")).toBeVisible({ timeout: 15_000 });
    await page.getByTestId("compliance-generate-btn").click();
    await expect(page.getByTestId("compliance-packs-ready")).toBeVisible({ timeout: 30_000 });
    await expect(page.getByTestId("compliance-verify-btn")).toBeVisible();
  });
});
