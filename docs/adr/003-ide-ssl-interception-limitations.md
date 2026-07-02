# ADR 003: IDE SSL Interception & Telemetry Capture Limitations

**Status:** Accepted
**Date:** 2026-05-31

## Context
A key objective of the Sprawl Gateway (Milestone MS-2) was to intercept, decrypt, and log outbound AI completions traffic from proprietary AI code editors (specifically Cursor AI) running on local workstations. The goal was to perform transparent, zero-config PII scanning and prompt auditing before forwarding requests to LLM providers. 

Because Cursor operates over proprietary encrypted subdomains (`api.cursor.sh`, `api2.cursor.sh`, `api3.cursor.sh`, `metrics.cursor.sh`, and `marketplace.cursorapi.com`), we attempted to design a local SSL Man-in-the-Middle (MITM) proxy server to decrypt and capture this secure IDE traffic.

## Solutions Attempted

We engineered a dual-component intercept stack:
1. **SSL CONNECT MITM Proxy (`sprawl_mitm_proxy.py`)**: A multi-threaded, zero-dependency Python proxy listening on port `5000` designed to capture the secure `CONNECT` handshakes. It parsed the subdomains, dynamically split traffic (using transparent TCP pass-through for metrics/marketplace and decryption blocks for completion endpoints), performed local SSL wrap handshakes using signed certificates, and attempted to route clean requests to our local Sprawl Gateway (port `4000`).
2. **CA & Environment Launcher (`launch_cursor_mitm.sh`)**: A wrapper script that compiled a custom Certificate Authority (`sprawl-ca.pem`) with strict `basicConstraints = CA:true` and `keyUsage` extensions. It generated a unified server certificate signed with Subject Alternative Names (SAN) covering all relevant subdomains (including wildcards like `*.cursor.sh`, `*.cursorapi.com`, and `localhost`). It then booted the Cursor editor, injecting proxy parameters (`HTTPS_PROXY=http://127.0.0.1:5000`) and SSL trust paths (`NODE_EXTRA_CA_CERTS`, `NODE_TLS_REJECT_UNAUTHORIZED="0"`).

## Why They Failed

Despite implementing a cryptographically perfect certificate chain and verified TLS 1.3 handshake negotiation (validated successfully via `curl` loopback tests), the native completions integration inside Cursor failed with recurring TLS alerts:
* `[SSL Handshake Failed]: [SSL: SSLV3_ALERT_ILLEGAL_PARAMETER] sslv3 alert illegal parameter`
* `[SSL Handshake Failed]: [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol`

These failures occurred due to two insurmountable runtime barriers:

1. **Sandboxed Electron Containerization**:
   On modern Pop!_OS and Ubuntu environments, Cursor is frequently deployed via **AppImages, Snaps, or Flatpaks**. These packaging models isolate the application within a read-only container sandbox. The sandbox mounts a separate, container-specific CA trust bundle, completely ignoring host-level certificates added to `/usr/local/share/ca-certificates/` or `/etc/ssl/certs/`.
2. **Native C++ Compiled Binary and Certificate Pinning**:
   Cursor's primary AI autocomplete and chat communications are handled by a **compiled native C++/Rust binary wrapper** rather than the standard Node.js/Electron environment. Because it is a native binary:
   - It bypasses all Node-specific variables (`NODE_TLS_REJECT_UNAUTHORIZED` and `NODE_EXTRA_CA_CERTS`).
   - It enforces **Strict Certificate Pinning** directly in the compiled code, checking the public key signatures of `api*.cursor.sh` endpoints against hardcoded keys. It rejects any proxy-generated certificate, even if signed by a trusted system CA.

## Decisions & Consequences

As a consequence of these strict sandbox and certificate pinning architectures, **transparent local SSL interception of proprietary AI editor completion traffic is rejected as a viable deployment strategy.**

### Pivot & Alternative Product Architecture
To maintain the value proposition of the Sprawl Security Gateway (secure credentials management, PII scrubbing, and license validation) without breaking the IDE or requiring fragile OS-level hacks:

1. **Native Provider Endpoint Overrides**:
   Instead of intercepting proprietary closed-source endpoints, Sprawl will officially route traffic via **Native OpenAI-compatible base URL overrides** supported by open extensions and open IDE architectures (e.g., standard VS Code/VSCodium or the configurable `Continue.dev` autopilot).
2. **Workstation Integration Protocol**:
   Developers configure their AI extension's base URL directly to point to the local Sprawl Gateway (`http://localhost:4000/v1`).
3. **Decoupled Architecture**:
   The Sprawl proxy command (`sprawl gateway`) remains a standard HTTP gateway, securely pulling API keys from the local database (`sprawl vault`) and executing PII scans natively on plain HTTP REST streams. This eliminates all local SSL proxy complexity and ensures robust, production-ready stability.
