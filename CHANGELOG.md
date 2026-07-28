# Changelog

All notable changes are documented here.

## 0.4.0 - 2026-07-28

### Added

- Chrome Web Store icons, screenshots, promo tile, listing copy, privacy fields, review instructions, and submission checklist.
- Deterministic Chrome Web Store ZIP builder with manifest, permission, icon, and remote-script validation.
- A concise local-data disclosure in the extension popup.

### Changed

- Removed the unnecessary `tabs`, `activeTab`, and `localhost` permissions.
- Reduced the manifest to `scripting`, Amazon.co.jp, and the fixed IPv4 loopback receiver.
- Expanded the public privacy policy in Japanese and English with Chrome Web Store Limited Use disclosures.

## 0.3.0 - 2026-07-28

### Added

- Root-level Windows launcher with a Japanese environment diagnostic.
- Reproducible Release ZIP builder and SHA-256 checksum output.
- Detailed installation, update, removal, release, support, roadmap, and conduct documentation.
- Feature request template and private security-reporting link.
- Product-focused README badges and three-step release installation path.

### Changed

- The dashboard now opens after the receiver has started, avoiding a misleading initial connection error.
- The health response no longer exposes absolute local database or dashboard paths.
- CI now smoke-tests diagnostics and the distributable ZIP on every supported Python version.

## 0.2.0 - 2026-07-27

### Added

- One-click incremental sync using the latest local order date with a 14-day overlap.
- Explicit year and start/end date capture.
- Editable item categories with remembered title overrides.
- Local sync-state API and clearer Batch progress.
- Public-release safety scan, CI, privacy policy, and security policy.

### Changed

- Batch completion is now shown as success instead of the misleading `page_done` stop message.
- The Batch tab reports reading, saving, navigation, completion, and failure states in plain language.
- The dashboard no longer displays absolute local filesystem paths.
- Removed the unused second pagination implementation from the page capture script.

### Security

- Receiver binding is restricted to loopback.
- Browser origins and Host headers are validated.
- Write endpoints require JSON objects.
- Dashboard responses include restrictive security headers.
