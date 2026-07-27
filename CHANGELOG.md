# Changelog

All notable changes are documented here.

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
