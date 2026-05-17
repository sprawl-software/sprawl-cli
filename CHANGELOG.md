# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-05-02

### Added
- **Open Source Launch:** The Sprawl CLI Engine (Atomic Agentic Fabric) is now officially open-source and ready for enterprise adoption.
- **Instantaneous Syncs:** The synchronization engine now performs MD5 hash checking, aggressively skipping identical files to dramatically speed up `.agents` workspace orchestration.
- **Enterprise-Grade Security:** Workspaces are now strictly sanitized against path traversal attacks, guaranteeing your host OS remains isolated and unpolluted during creation.
- **Automated CI/CD:** Fully automated GitHub Actions workflow integrated to enforce testing standards on all community contributions.
- **Native Test Suite Rigor:** Added a comprehensive Python `unittest` suite containing hostile test scenarios for robust security validation.
- **Refactored Architecture:** Extracted core logic categories to prevent duplicated schema definitions, drastically reducing the framework footprint.

### Removed
- **Telemetry Stripped:** Removed legacy MITM proxy features and remote telemetry endpoints to fully enforce the Zero-Trust, local-first operational mandate.
