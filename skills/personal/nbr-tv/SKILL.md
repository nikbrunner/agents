---
name: nbr-tv
description: >-
  Manage Nik's LG OLED TV: its CleanYourTV launcher, themes, wallpapers, apps, inputs, notifications
  and root shell. Use when a task touches the TV rather than this computer, or names CleanYourTV,
  the launcher, a TV theme or a wallpaper on the TV.
compatibility: The TV reachable on the LAN, and the `tv` MCP server in pi. Root shell needs python3.
---

# TV

Nik's TV is an **LG OLED65C17LB** (2021 C1) on webOS 6.5.3, firmware `03.53.45`, on the LAN as
`lgwebostv.local` (mDNS, so it follows the DHCP lease). It is rooted with Homebrew Channel 0.7.3,
and the **CleanYourTV** launcher stands in for LG's Home: `home-standin.sh` is bind-mounted over
`/usr/bin/com.webos.app.home`.

Firmware updates are blocked at `/var/luna/preferences/webosbrew_block_updates`. Every firmware
newer than `03.53.45` closes the exploit, so an update ends root and CleanYourTV with it.

## Three doors

Take the highest door that answers the question.

1. **MCP `tv`** at `http://lgwebostv.local:8802/mcp`, 21 tools: `tv_list_apps`, `tv_launch_app`,
   `tv_switch_input`, `tv_show_notification`, `tv_get_current_app`, `tv_navigate`, `tv_get_volume`,
   `tv_info`, `tv_most_used_apps`, `tv_get_weather`, `tv_theme`, `tv_remote_buttons`,
   `tv_close_app`, `tv_list_running_apps`, plus `androidbox`, `icons`, `agent`. The token lives in
   `~/.config/cytv/bearer` and `~/.pi/agent/mcp.json` reads it with `!cat`. Destructive tools such
   as `tv_power_off` are refused to network callers, so a spoken yes on the TV is the only way
   through.
2. **The launcher's HTTP API** on `127.0.0.1:8765`: apps, config, themes, wallpapers, screensaver,
   add-ons. Loopback only, so reach it through door 3. `GET /api/apps` returns the app list with the
   resolved theme in `config.theme`; `POST /api/config`, `POST /api/theme/set`,
   `POST /api/addons/restart` and `POST /api/wallpapers/pair` are the useful writes.
3. **Root shell** on telnet port 23, no password, `uid=0`. Send one command per call:
   `python3 scripts/tvsh.py '<command>'`. The service is `node helper.js` in
   `/media/developer/cleanyourtv`, watched by the boot scripts; a stop and start takes about 15
   seconds and the watchdog covers the gap.

## Everyday jobs

- **Remove a store app**:
  `luna-send -n 1 -f luna://com.webos.appInstallService/remove '{"id":"<id>","subscribe":false}'`,
  then poll the folder under `/media/cryptofs/apps/usr/palm/applications/` until it is gone, about
  20 seconds. The `dev/remove` variant stalls on store apps; it is for apps under
  `/media/developer`.
- **Hide an app**: `POST 127.0.0.1:8765/api/config` with `{"hidden": [...]}`. It replaces the whole
  list, so read `config.json` first. Unhiding is in the launcher's Customise.
- **Wallpaper**: `POST /api/wallpapers/pair` returns a code, then
  `POST -H "x-code: <code>" --data-binary @photo.jpg 127.0.0.1:8791/api/upload`, then
  `POST /api/wallpapers/pair {"stop":true}`. JPEG, PNG or WebP, 4K at most.
- **Theme**: `POST /api/theme/set {"id":"<id>"}`, `{"id":"classic"}` to leave, `{"action":"revert"}`
  is `POST /api/theme/revert`. A theme that is not in their catalogue still works from
  `/media/developer/cleanyourtv/themes/<id>/`.
- **Card on screen**: `tv_show_notification`, or `POST 127.0.0.1:8765/api/notify` with `title`,
  `text`, `image`, `seconds` and `position`.
- **App title**: a store app's name is its own `appinfo.json` `title`, which the app manager
  re-reads after a reboot. Edit it there, back it up first.

## Theme work

A theme is data only: `themes/<id>/theme.json` with keys from `helper/themeschema.js`, nothing else.
Wording and ranges are in the checkout's `docs/themes.md`.

1. **Look before shipping.** `node tools/theme-preview.mjs <id> --out /tmp/preview` writes
   `rest.png`, `grid.png` and `menu.png` at 1920x1080 through headless Chrome, with made-up apps.
   The fake icons are neutral grey, so what you see is the theme.
2. **Ship it.** Copy `theme.json` (and its font, at most 400 KB) to
   `/media/developer/cleanyourtv/themes/<id>/`, `POST /api/addons/restart` so the service drops its
   theme cache, then `POST /api/theme/set` and relaunch Home:
   `luna-send -n 1 -f luna://com.webos.applicationManager/closeByAppId '{"id":"com.webos.app.home"}'`
   then `launch`. Reloading is the step that applies a theme, since the page reads it once at start.

**A page or helper change needs a reboot.** `app/index.html` is read when the launcher starts and
`themeschema.js` when the service starts. Copy both, run
`sh /media/developer/cleanyourtv/stage-home.sh` to restage the overlay, then reboot the TV. Copying
alone leaves the old page running.

## Where the patches are

Six theme settings, a boot-script edit and an app title on this TV exist only here, because upstream
does not have them. Read [references/local-patches.md](references/local-patches.md) before touching
`app/index.html`, `themeschema.js`, a boot script or a theme, and to roll any of them back.
