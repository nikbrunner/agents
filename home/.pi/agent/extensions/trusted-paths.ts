import { readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { isUnderTrustedPath, parseTrustedPaths } from "./lib/trusted-paths";

// Trusts projects under the folders listed in ~/.config/agents/trusted-paths, one per line,
// without saving the decision to trust.json. Without that file, Pi's own trust flow decides.
const TRUSTED_PATHS_FILE = join(homedir(), ".config", "agents", "trusted-paths");

function readTrustedPaths(): string[] {
	try {
		return parseTrustedPaths(readFileSync(TRUSTED_PATHS_FILE, "utf-8"));
	} catch {
		return [];
	}
}

export default function trustedPathsExtension(pi: ExtensionAPI): void {
	pi.on("project_trust", (event) => ({
		trusted: isUnderTrustedPath(event.cwd, readTrustedPaths()) ? "yes" : "undecided",
	}));
}
