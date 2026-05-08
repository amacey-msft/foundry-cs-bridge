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
- `.env.sample` with Copilot Studio Direct Line token endpoint for the
  existing Sterling OMS "Order Management System Agent" (parent of a 6-agent
  generative-orchestration system).

### Changed
- **Phase 1 revised:** existing Copilot Studio agents from
  `SterlingOMS_Template` are reused. No CS provisioning, no in-repo mock
  orders API. Parent agent verified live via Direct Line token endpoint
  probe (2026-05-08).
- Plan's `orders_api/` scaffold removed; OMS data lives in Dataverse via
  Sterling solution.
