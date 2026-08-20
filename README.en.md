# HT Dark

*[Version française](README.md)*

A dark theme for [Hattrick](https://www.hattrick.org) that **keeps each team's colour as an
accent** instead of flattening it. CSS only — not a single line of JavaScript.

## What sets it apart

**No JavaScript.** The extension's manifest contains nothing but a list of CSS files. With no
executable code, it has no technical means of reading anything on the pages or sending anything
anywhere. It requests no permissions, makes no network requests, and stores no data.

**Your team's colour is preserved.** Hattrick itself injects, page by page, a `<style>` block that
applies the displayed club's colours to `#menu`, `.boxHead` and `.header-icon`. The theme
deliberately leaves those selectors untouched: the team accent keeps working as it always did, for
your own club as for an opponent's, and it survives a theme change in the game settings.

**Contrasts are measured, not guessed.** Every rule was written after taking a WCAG contrast
reading in the page. The target is 4.5:1 on body text. The rare accepted shortfalls are documented
in the comments, with their measured value.

### About the permission warning

Your browser will display "Read and change your data on hattrick.org". This is unavoidable and it
is not a mistake: every content script, even a purely cosmetic one, triggers that warning, because
the manifest format does not distinguish reading from decorating. The `manifest.json` holds nothing
but a `css` array — that takes three seconds to verify.

## Installation

### Firefox

Install from [addons.mozilla.org](https://addons.mozilla.org) *(listing pending)*.

To load a development build: `about:debugging` → **This Firefox** → "Load Temporary Add-on" →
select `manifest.firefox.json`.

### Chrome

1. Go to `chrome://extensions`
2. Enable **Developer mode**
3. **Load unpacked** → select this folder

After updating the files, click the reload icon on the extension's card, then press `Ctrl+F5` on the
page — browsers cache extension resources.

## Architecture

| File | Purpose |
|---|---|
| `css/01-palette.css` | CSS variables — the single source of truth for colours |
| `css/02-base.css` | Page background, text, links, native controls |
| `css/03-components.css` | Components found across the whole site |
| `css/04-pages.css` | Fixes specific to a single page |
| `css/05-foxtrick.css` | Rules targeting the FoxTrick extension |
| `css/06-dhth.css` | Rules targeting the dhth extension |
| `css/07-skillvalue.css` | Rules targeting the SkillValue CHPP modules |

The last three files are **inert** when the matching extension is not installed: their selectors
then match nothing in the page.

Files are injected in manifest order, before the page renders: no white flash on load.

The `matches` pattern `https://*.hattrick.org/*` covers `www.hattrick.org` as well as the numbered
servers.

### The single hardest-working line

```css
:root { color-scheme: dark; }
```

It flips native controls, scrollbars and the default background all at once. It only drives
**native** controls — a `select` replaced by an extension escapes it.

## Principles

**`!important` on colour only.** Hattrick's own stylesheets load *after* the content script's CSS;
at equal specificity, theirs win. `!important` is therefore necessary on background and colour
properties — but never on layout, and every use carries a comment naming the site rule it
neutralises.

**No layout changes.** The theme fixes colours. Borders go through `box-shadow: inset` rather than
`border`: on a site this dense, one pixel of border shifts the whole page.

**Semantic colours are preserved.** The yellow of a bookmarked thread, the pink of a deleted post,
the home/away blue are *information*, not decoration. They are darkened, never flattened.

**No global image filter.** Inverting every image is what makes most dark themes ugly. Only icon
sets identified as unreadable get a targeted filter, case by case.

## Verification

- **No white flash**: reload with `Ctrl+F5`; the background must be dark from the first painted
  frame.
- **Contrast** ≥ 4.5:1 on body text, measured rather than estimated.
- **The test that settles everything**: switch from one team to another. The background must stay
  identical and the accent must change — enough to know where you are without reading the team name.
- **Clean removal**: disable the extension and Hattrick must return to exactly its original
  appearance. No residue is possible — no storage, no script.

## Legitimacy

Hattrick itself published a tutorial explaining how to restyle the site: "Dark theme for Hattrick
website" (Hattrick Press, `ArticleID=22846`, by vlar3, 13 Jan 2023). Restyling is purely local,
sends no requests and automates nothing.

This theme redistributes no Hattrick imagery or branding — it contains only CSS rules and its own
icons.

## Licence

[MPL-2.0](LICENSE).

---

*Hattrick is a trademark of Extra Living AB. This project is neither affiliated with nor endorsed by
Hattrick. FoxTrick and dhth are independent third-party projects.*
