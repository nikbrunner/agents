import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";

const KEY = "nik/model-price";

type ZentuiCapability = { supported: boolean; active: boolean; key: string };

const formatPrice = (perMillion: number): string => {
	const fixed = perMillion.toFixed(3).replace(/0+$/, "").replace(/\.$/, "");
	const needsTwoDecimals = perMillion < 1 && !/\.\d{2}/.test(fixed);
	return `$${needsTwoDecimals ? Number(fixed).toFixed(2) : fixed}`;
};

const formatRates = (ctx: ExtensionContext): string | undefined => {
	const cost = ctx.model?.cost;
	if (!cost) return undefined;

	const parts = [`${formatPrice(cost.input ?? 0)} / ${formatPrice(cost.output ?? 0)} per 1M`];

	const cache = [
		cost.cacheRead ? `read ${formatPrice(cost.cacheRead)}` : undefined,
		cost.cacheWrite ? `write ${formatPrice(cost.cacheWrite)}` : undefined,
	].filter(Boolean);
	if (cache.length > 0) parts.push(`cache ${cache.join(" / ")}`);

	return parts.join(" · ");
};

export default function modelPrice(pi: ExtensionAPI): void {
	const publish = (ctx: ExtensionContext) => {
		const text = formatRates(ctx);

		const capability: ZentuiCapability = { supported: false, active: false, key: KEY };
		pi.events.emit("zentui:variable-capability", capability);

		if (capability.supported) {
			if (capability.active) pi.events.emit("zentui:variable", { key: KEY, text });
			return;
		}

		ctx.ui.setStatus(KEY, text ?? "");
	};

	pi.on("session_start", (_event, ctx) => {
		publish(ctx);
		for (const delay of [1500, 4000]) setTimeout(() => publish(ctx), delay);
	});
	pi.on("model_select", (_event, ctx) => publish(ctx));
}
