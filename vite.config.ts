import { defineConfig } from "vite-plus";

export default defineConfig({
  fmt: {
    proseWrap: "always",
    ignorePatterns: [
      // Skills and the lock file their own tools install and overwrite.
      "home/.agents/skills/*/**",
      "home/.agents/.skill-lock.json",
      // Pi extensions are project-local and carry their own formatter config.
      "home/.pi/agent/extensions/**",
      // Claude Code writes these through symlinks, so its formatting wins.
      ".agents/**",
      ".claude/**",
    ],
  },
});
