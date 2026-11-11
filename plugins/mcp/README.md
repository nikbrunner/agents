# mcp

The MCP servers every Claude Code login on this machine gets. `settings.json` is shared between `~/.claude` and `~/.claude-work` and enables this plugin, so both logins load the servers in [`.mcp.json`](.mcp.json).

Add or change a server there, never with `claude mcp add -s user`: a user-scope server lives in one login's `.claude.json` only.

Tools are named `mcp__plugin_mcp_<server>__<tool>`. Permission rules in `settings.json` use that form.

Secrets stay out of `.mcp.json`. A server that needs one resolves it from Proton Pass when it starts, as `exa` does.
