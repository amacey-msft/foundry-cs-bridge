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
- `.env.sample` placeholder for Phase 1 (CS agent provisioning + mock orders
  API endpoints, populated as Phase 1 progresses).

### Reverted
- Briefly considered reusing the SterlingOMS_Template CS agents on
  2026-05-08 (commit `24c75b2`); reverted same day. Original plan stands:
  greenfield `awm_contosoorders` CS agent + in-repo mock orders API +
  Granite Peak ski/bike SKUs end-to-end. Sterling reuse blocked by data
  mismatch (Sterling product catalog ≠ Granite Peak ski/bike).
