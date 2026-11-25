import { expect, test } from "claude-code/testing";

test("/dash alternates between hiding and showing", async ($, on) => {
  on("ui.open", () => ({ value: { isPlaced: true } }));
  on("ui.close", () => ({ value: undefined }));
  const run = () => $.command.run({ command: "dash", args: "" } as never) as Promise<unknown>;
  expect(await run()).toMatchObject({ text: "Dash hidden." });
  expect(await run()).toMatchObject({ text: "Dash shown." });
  expect(await run()).toMatchObject({ text: "Dash hidden." });
});
