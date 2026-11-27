export function parseTrustedPaths(text: string): string[] {
	return text
		.split("\n")
		.map((line) => line.trim())
		.filter((line) => line !== "")
		.map((line) => line.replace(/\/+$/, ""));
}

export function isUnderTrustedPath(cwd: string, trustedPaths: string[]): boolean {
	return trustedPaths.some((path) => cwd === path || cwd.startsWith(`${path}/`));
}
