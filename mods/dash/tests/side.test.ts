import { expect, test } from "claude-code/testing";

test("/dash side opens the pane, /dash closes it again", async ($, on) => {
  const calls: string[] = [];
  on("ui.open", (_, e) => (calls.push(`open ${e.id}`), { value: { isPlaced: true } }));
  on("ui.close", (_, e) => (calls.push(`close ${e.id}`), { value: undefined }));
  const run = (args: string) =>
    $.command.run({ command: "dash", args } as never) as Promise<unknown>;
  expect(await run("side")).toMatchObject({ text: "Dash moved to the side." });
  expect(await run("")).toMatchObject({ text: "Dash hidden." });
  expect(calls).toEqual(["open dash", "close dash"]);
});
