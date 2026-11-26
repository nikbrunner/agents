---
name: nbr-secrets
description:
  "Wire a secret from Nik's Proton Pass into the one consumer that needs it: a CLI or script, an MCP
  stdio server in Claude Code or Codex, or a tool with its own credential file. Use when a command,
  server or config needs an API key, token or password, or to check whether one is set."
compatibility: Requires pass-cli.
---

# nbr-secrets

Secrets live in Proton Pass: vault `Nik`, item `.env`, one hidden field per variable. Address each
as `pass://Nik/.env/<FIELD>`. The one consumer that needs a secret resolves the reference when it
runs.

## Wire a consumer

| Consumer                          | How                                                                                                                             |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| CLI or script                     | `VAR=pass://Nik/.env/VAR pass-cli run -- <cmd>`                                                                                 |
| MCP stdio server (Claude, Codex)  | `sh -c 'VAR=$(pass-cli item view pass://Nik/.env/VAR) \|\| exit 1; export VAR; exec <server>'`                                  |
| Tool with its own credential file | its command hook if it has one (pi `auth.json`: `"key": "!pass-cli item view pass://Nik/.env/VAR"`), else its own login command |

`pass-cli run` sits between the client and the server's stdout. That breaks TUIs and the MCP
handshake of Codex. The MCP form resolves the secret first and then gets out of the way.

## Codex

A Pass lookup takes a few seconds. Give each Codex MCP entry that resolves a secret
`startup_timeout_sec = 30`. `codex exec` starts its turn before such servers are ready.

## Guardrails

- Never export a secret globally: no shell rc, no mise `[env]`, no launchd.
- Never write a secret's value into a tracked file.
- Never print a secret. Check it by length, `grep -c` or comparison.
- A redacting filter is no exception for files that hold secrets. Pattern-based redaction misses
  formats.
