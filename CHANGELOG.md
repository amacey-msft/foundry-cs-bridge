# Changelog

All notable changes to this repo are documented here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions track
demo milestones, not semver release cadence.

## [Unreleased]

### Added
- Initial repo scaffold: `.gitignore`, `README.md`, `CHANGELOG.md`, `plan.md`
  (full delivery plan recovered from prior session).
- Phase 0 done: GitHub repo `amacey-msft/foundry-cs-bridge` (private), branch
  `feat/initial-scaffold`, draft PR #1.
- **Phase 1 mock orders API** (`orders_api/`): FastAPI app with Granite Peak
  Outfitters catalog (6 winter + 6 summer SKUs), single demo customer
  Riley Carter (`GP-1001`), 6 seeded orders covering all status paths
  (Delivered eligible, Delivered ineligible, Processing, Shipped), 1 seeded
  return. Endpoints: `/healthz`, `/catalog`, `/customers/{id}`,
  `/customers/{id}/orders`, `/customers/{id}/returns`, `/orders/{id}`,
  `/orders/{id}/return-eligibility`, POST `/returns`, `/returns/{id}`,
  `/returns?customer_id=&order_id=`, `/policies/return`. Smoke-tested
  against `uvicorn` (2026-05-08).
- `requirements.txt` (FastAPI + uvicorn + pydantic), `Dockerfile.orders_api`,
  `docker-compose.yml`, devtunnel scripts (`scripts/devtunnel-*.ps1` +
  README).
- `docs/02-cs-orders-setup.md` — manual Studio provisioning recipe for the
  Granite Peak Orders Agent (4 topics, 5 HTTP tools, system instructions,
  smoke prompts), targeting Power Platform env
  `63b4b29b-b3b0-ed70-9136-524a53a22e06`.
- `.env.sample` updated with env reference comments.

### Reverted
- Briefly considered reusing the SterlingOMS_Template CS agents on
  2026-05-08 (commit `24c75b2`); reverted same day. Original plan stands:
  greenfield `awm_contosoorders` CS agent + in-repo mock orders API +
  Granite Peak ski/bike SKUs end-to-end. Sterling reuse blocked by data
  mismatch (Sterling product catalog ≠ Granite Peak ski/bike).
