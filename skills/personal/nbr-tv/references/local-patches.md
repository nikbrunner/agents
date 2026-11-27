# Local patches on the TV

These live on the TV and in no release. A CleanYourTV update replaces all of them.

The exception is `/media/developer/tv-quiet/`, which silences four LG daemons and hooks in from
`/var/lib/webosbrew/init.d/20-tv-quiet`: it sits outside CleanYourTV and survives a launcher update.
The skill's "Quieting the TV's own daemons" covers it.

## Five theme settings

Their schema has no switch for any of these. Each is a `SCHEMA` row in `helper/themeschema.js`, an
attribute emitted in `resolve()`, the attribute name in the page's `themeAttrs` list in
`app/src/js/theme.js`, and CSS in `app/src/css/home.css`.

| Setting      | Values                 | What it does                                                                                                                |
| ------------ | ---------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `tile.names` | `off`, `under`, `only` | The app name on the tile, alone or under the icon. Names-only hides the icon. `app/src/js/tiles.js` adds the `.nm` element. |
| `tile.tint`  | `icon`, `flat`         | `flat` paints every tile the theme panel colour instead of the app icon's colour.                                           |
| `bar.layout` | `row`, `column`        | The top buttons as a stack. `app/src/js/input.js` maps Up and Down to the stack while the focus is in that row.             |
| `bar.icons`  | `true`, `false`        | `false` leaves the labels and drops the icons and their padding.                                                            |
| `bar.focus`  | `fill`, `underline`    | The focused top button as a 3 px underline, with no scale bump.                                                             |

Two tests follow the markup. `tools/test/tile-retry.test.js` counts fallback elements, not children:
the name element is a child too. `docs/themes.md` is regenerated with `node tools/theme-docs.js`,
since the table comes from `SCHEMA`.

## Boot script

`10-cleanyourtv-home` also opens Home when the TV starts on `com.webos.app.membership`, LG's account
app. Without it a cold boot sat on that screen until the Home key was pressed.

## App title

The Spotify store app's `appinfo.json` `title` reads `Spotify` instead of
`Spotify - Music and Podcasts`. An app update brings the full title back.

## Backups

| File                                               | Copy                                        |
| -------------------------------------------------- | ------------------------------------------- |
| `/media/developer/cleanyourtv/app/index.html`      | `index.html.orig`, the released 1.5.25 page |
| `/media/developer/cleanyourtv/themeschema.js`      | `themeschema.js.bak`                        |
| `/media/developer/cleanyourtv/10-cleanyourtv-home` | `10-cleanyourtv-home.bak`                   |
| `spotify-beehive/appinfo.json`                     | `appinfo.json.bak`                          |

## Rolling back

The page: copy `app/index.html.orig` over `app/index.html`, run
`sh /media/developer/cleanyourtv/stage-home.sh`, reboot.

The helper: copy `themeschema.js.bak` over `themeschema.js`, then `POST /api/addons/restart`.

The boot script: copy `10-cleanyourtv-home.bak` over it, reboot.

Everything: `sh /media/developer/cleanyourtv/undo-home.sh` puts LG's Home back and removes the boot
scripts. The manager app also has the switch.

## Reapplying after an update

An update ships its own page, helper and boot scripts. The custom theme keeps working, because
unknown theme keys are dropped. The tiles show icons again, and a cold boot stops on the account
app. Reapply means copying the patched `app/index.html` and `themeschema.js` in, running
`stage-home.sh`, and rebooting.

## These stay local

Nik keeps these on his own TV for now, and a CleanYourTV update means reapplying them. The settings
are small enough to offer upstream later: schema rows, the attribute list, CSS, the tiles and input
changes, the regenerated theme table and the adjusted test, with `sh tools/check.sh` green apart
from `scripts.test.js`, which wants a running service and fails on this Mac without one.
