# Agent Guide

## Project Status

This repository has been reset and is being rebuilt from scratch.

The current source of truth is:

- `docs/PRD_v0.6.4_c_review.md`
- `docs/Kimi_API_Usage_Guide_v1.md`

## Rebuild Rules

- Do not restore legacy `skill_engine` code or old PomeFi MVP structures.
- Build new functionality under `pomefi/`.
- Treat `scripts/probe_moonshot_sdk.py` as the initial reference implementation for the new core loop.
- Keep Formula usage aligned with Moonshot official guidance.
- Keep financial numeric conclusions traceable to tool outputs.

## Current Phase Boundary

- Step 1 completed: legacy project cleared
- Step 2 completed: skeleton and source documents restored
- Step 3 completed: config, Formula client, and core loop extracted from the probe script
- Do not implement Step 4+ work unless explicitly requested
