Rules:
- Determinism: same input => same output. No random seeds unless fixed.
- Never mark a milestone complete unless tests pass with 0 failed, 0 skipped, 0 retries.
- Playwright selectors: ONLY data-testid.
- E2E: retries=0, workers=1.
- Prefer small commits.
