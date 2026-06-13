# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **SelfRepair control-plane sender**: `matrix-codex submit-maintenance` + daily cron submit dry-run maintenance requests (`POST /v1/plans`) per inventory repo (pilot: `agent-matrix/network.matrixhub`); `GitPilotAgent` now calls GitPilot's bearer-gated coder API.

- Standardized repository governance files (SECURITY.md, CODE_OF_CONDUCT.md,
  CODEOWNERS, .editorconfig, .gitattributes) as part of the Agent-Matrix
  alive-system synchronization.
