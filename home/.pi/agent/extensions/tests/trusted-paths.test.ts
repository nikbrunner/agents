import { isUnderTrustedPath, parseTrustedPaths } from "../lib/trusted-paths.ts";

Deno.test("reads one path per line and drops blank lines and trailing slashes", () => {
	const paths = parseTrustedPaths("/home/me/repos/work/\n\n  /home/me/client\n");
	if (paths.join(",") !== "/home/me/repos/work,/home/me/client") {
		throw new Error(`Unexpected paths: ${paths.join(",")}`);
	}
});

Deno.test("trusts a listed folder and the folders beneath it", () => {
	const paths = ["/home/me/repos/work"];
	if (!isUnderTrustedPath("/home/me/repos/work", paths)) {
		throw new Error("Expected the listed folder to be trusted.");
	}
	if (!isUnderTrustedPath("/home/me/repos/work/app/frontend", paths)) {
		throw new Error("Expected a nested folder to be trusted.");
	}
});

Deno.test("leaves sibling folders with a shared prefix undecided", () => {
	if (isUnderTrustedPath("/home/me/repos/workshop", ["/home/me/repos/work"])) {
		throw new Error("Expected a sibling with a shared prefix to stay untrusted.");
	}
});

Deno.test("trusts nothing without a trusted-paths file", () => {
	if (isUnderTrustedPath("/home/me/repos/work", parseTrustedPaths(""))) {
		throw new Error("Expected no trust from an empty list.");
	}
});
