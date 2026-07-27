# Security Policy

## Security model

- The receiver binds only to `127.0.0.1` or `localhost`.
- Browser requests are restricted to the local dashboard and Chrome extension origins.
- POST endpoints require JSON and use parameterized SQLite statements.
- The extension has no credential, cookie, payment, download, or remote-code permissions.
- Generated dashboard responses block framing, referrers, external resources, and MIME sniffing.

This significantly reduces exposure, but a local application cannot protect a
computer that is already compromised. Keep Chrome and Python updated, review
extension permissions, and never publish files from `data/`.

## Reporting a vulnerability

Use GitHub's private vulnerability reporting when available. If it is not
available, open an issue containing no real order data, credentials, cookies,
addresses, names, or screenshots of a signed-in Amazon page. Ask the maintainer
for a private contact channel before sharing sensitive reproduction details.

## Supported versions

Security fixes are applied to the latest release only.
