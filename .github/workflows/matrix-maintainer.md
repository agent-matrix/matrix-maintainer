---
on:
  schedule:
    - cron: "0 3 * * *"

permissions:
  contents: write
  pull-requests: write

engine:
  id: copilot
  model: gpt-5.2-codex

safe-outputs:
  create-pull-request: {}

tools:
  github:
    toolsets: [default, pull_requests]
---

# Autonomous Maintenance Agent

Maintain the repository with controlled and safe repository improvements.

## Tasks
- Fix failing tests
- Update dependencies
- Improve lint issues

## Rules
- Never break tests
- Always create a PR
- Keep changes small

## Process
1. Analyze repository state
2. Apply safe fix
3. Run validation checks
4. Open PR if successful
