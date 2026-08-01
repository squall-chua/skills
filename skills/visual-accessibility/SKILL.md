---
name: visual-accessibility
description: >
  Drive the running UI in a browser, check it against WCAG at the level you name, rank
  every barrier by what it stops a person doing, and report each one with the evidence
  and a fix.
disable-model-invocation: true
---

A rules engine sees about a third of WCAG, and it is not the third that stops people. Missing
alt text a scanner finds. A focus ring nobody can see, a tab order that jumps the page, a
modal the keyboard cannot leave, an error message that never reaches a screen reader — those
need the page **driven**. This skill drives it, with the `vibium` browser CLI.

The word that sorts the findings is **barrier**: what a person cannot do because of it. A
contrast failure on a disabled footer link is a violation. A keyboard trap in the checkout
modal is a barrier, and it is the one that costs somebody the purchase. Every finding here
names the barrier, or says plainly that there is none.

Findings come from the **rendered page** — the accessibility tree, the computed style, the
element focused after a keypress — rather than from reading the source. A finding somebody can
reproduce in their own browser is a finding its owner can fix.

## What this skill writes

One report and the screenshots behind it. The interface stays as it is: an accessibility fix
changes what users see, so the fixes are diffs for their owner.

## 1. Pin the target, the pages, and the states

Get the base URL of a **running** instance and the pages in scope. Named none? Take the routes
the app declares and say so.

Then list the **states**, because a page has more states than it has URLs and the barriers hide
in the states: a modal open, a menu expanded, a form showing its errors, a table after sorting,
a toast just fired, a list mid-load. Each state gets the `vibium` commands that reach it, so
every finding is reproducible by somebody who does not have this session.

Name the standard: **WCAG 2.2 level AA** unless the user names another version or level, and
write which one the run used. Then write down what stands outside the scope — a third-party
widget, an iframe another team owns, a page behind a paywall. An unstated gap reads as a clean
bill of health for ground nobody looked at.

**Done when:** the scope is a counted list of page-and-state pairs, each with the commands that
reach it; the WCAG version and level are named; and everything left out is written down.

## 2. Open the page and prove it is the page

```sh
vibium start                 # --headless once the run is settled; visible while you set it up
vibium go <url>
vibium title && vibium url
```

Confirm one element you expect to be there. A run against a login wall, a cookie banner, or an
error page otherwise reports that page's accessibility instead of the product's.

Where the pages need a session, log in with `vibium fill` and `vibium click`, or restore one
with `vibium storage`. Credentials come from the environment and stay out of the report.

Record the viewport with `vibium viewport` — half the checks in step 4 depend on it, and a run
at an unrecorded size cannot be repeated.

**Done when:** the browser is on the first in-scope page with its title and one expected element
confirmed, the viewport is recorded, and every state from step 1 has been reached at least once
by its commands.

## 3. Run a rules engine over every state

Prefer the engine the project already has — check the manifest, the test setup, and the CI
workflows before reaching for a new one. Otherwise:

| Where it runs | Tool |
| --- | --- |
| Injected into the live page | `axe-core` through `vibium eval --stdin` |
| Inside the test suite | `jest-axe`, `vitest-axe`, `cypress-axe`, `@axe-core/playwright` |
| From the command line, over a URL | `@axe-core/cli`, Pa11y, Lighthouse's accessibility category |
| A service the project already pays for | axe DevTools, and its own reporting |

### Nothing installed?

Look before you install: the manifest and its lockfile, the CI workflows, the test setup, and
the binary on `PATH`. A tool declared in the manifest but missing from the environment needs the
project's own install command, not a new dependency.

An accessibility sweep is one-shot, so `npx @axe-core/cli`, `npx pa11y`, or `npx lighthouse`
runs it without touching the manifest at all. Reach for that first.

Where the project should own the engine permanently — a suite-level check is the usual reason —
put the setup to the user in one message: the tool, why it fits this project, the exact install
command, the config with its contents, the command this skill will then run, and what it costs
in download size and first-run time. Wait for the go-ahead, then install exactly that, leave the
config in the repo, and commit nothing.

Where the user declines, the report marks the automated pass **not run** with what it would have
covered, and step 4 carries the whole run alone.

Two things decide whether the output is usable. Ask for **JSON** and read the file rather than
the console summary. And run the engine **in every state**, not once per URL: a scanner pointed
at an address sees the page before the modal opened, and reports the state nobody complained
about.

**Done when:** the engine ran in every state from step 1 with its version, its command, and its
JSON output recorded — or the automated pass is marked not run with its reason.

## 4. Drive what no scanner sees

This is the two-thirds a rules engine cannot reach. Work every state from step 1 through every
check:

| Check | Drive it | It fails when |
| --- | --- | --- |
| **Tab order** (2.4.3) | `vibium keys Tab` through the state, reading `document.activeElement` at each stop | the order leaves the visual order, skips a control, or lands on something invisible |
| **Focus visible** (2.4.7) | at each stop, the computed `outline`, `box-shadow`, and `border` of the focused element | nothing changes visibly, or the indicator sits behind another element |
| **No keyboard trap** (2.1.2) | `Tab` and `Shift+Tab` out of every modal, menu, date picker, and embedded widget | focus cannot leave without a mouse |
| **Keyboard operable** (2.1.1) | every control `vibium map` lists, reached by keyboard and activated with `Enter` or `Space` | a control answers a click and ignores a key |
| **Accessible name** (1.1.1, 2.4.6, 2.5.3) | `vibium a11y-tree`, then `vibium find role <role> --name "<the visible label>"` | the name is absent, is a file name or `button`, or does not contain the visible label |
| **Structure** (1.3.1, 2.4.1) | the same tree: heading levels, landmarks, list and table roles | headings skip a level, no `main` landmark, a table built from `div`s |
| **Contrast as rendered** (1.4.3, 1.4.11) | the computed colour of the text against what is actually painted behind it | under 4.5:1 for body text, 3:1 for large text and UI parts. Text over an image or a gradient is where scanners give up |
| **Reflow** (1.4.10) | `vibium viewport 320 512` | the page scrolls horizontally, or content is cut off |
| **Zoom** (1.4.4) | `vibium viewport 640 360 --dpr 2` — half the width at twice the density is the standard proxy for 200% | text clips or overlaps at 200% |
| **Text spacing** (1.4.12) | `vibium eval` setting `line-height: 1.5`, `letter-spacing: 0.12em`, `word-spacing: 0.16em`, and paragraph spacing at `2em` on every element | content clips or overlaps |
| **Reduced motion** (2.3.3) | `vibium media --reduced-motion reduce` | the animation, parallax, or auto-carousel runs anyway |
| **Forced colours** (1.4.1) | `vibium media --forced-colors active` | a control vanishes, or meaning carried by colour alone is lost |
| **Dark scheme** (1.4.3) | `vibium media --color-scheme dark` | contrast that passed in light fails in dark |
| **Status messages** (4.1.3) | act, then re-read the tree for the live region | a toast, an error count, or a loading state never reaches the tree |
| **Errors** (3.3.1, 3.3.3) | submit a form with an invalid field | the error is colour only, is not tied to its field, or does not say how to fix it |
| **Target size** (2.5.8) | the bounding box of every control | under 24×24 CSS px with no spacing exemption |

`vibium eval` prints objects in Go's map format, so return a JSON string and read that:

```sh
vibium eval "JSON.stringify([...document.querySelectorAll('button')].map(b => {
  const r = b.getBoundingClientRect(), s = getComputedStyle(b)
  return { name: b.textContent.trim(), w: r.width, h: r.height, outline: s.outlineStyle }
}))"
```

`vibium media` and `vibium viewport` hold for the rest of the session. Put each one back before
the next check, or that check runs under the last one's conditions and reports a barrier that
only your overrides created.

Screenshot every failure as you find it — `vibium screenshot -o <path>` — and for a focus or
contrast failure that is the only evidence anybody can read.

**Done when:** every check carries a verdict in every state, with the command and the value
behind it; every failure carries its screenshot; and every media and viewport override was put
back.

## 5. Verify each finding on the page

A rules engine reports the DOM it was handed. Reproduce every one of its findings in the browser
before it enters the report: a contrast rule fires on text nobody can see, a duplicate id comes
from a template rendered twice, a landmark rule fires inside a third-party widget you do not
own. A finding you could not reproduce gets dropped with the argument written down.

Then merge. The same element failing the same criterion in the automated pass and the driven
pass is one finding carrying both sources — agreement between them is worth keeping, and two
rows for one barrier inflates the total into noise.

**Done when:** every finding was reproduced on the page or dropped with its argument, and each
one carries its criterion, its element, its state, and its evidence.

## 6. Rank by the barrier

Give every finding one state:

- **Blocks** — a person using a keyboard, a screen reader, or magnification cannot complete the
  task. Write out where they stop.
- **Degrades** — they complete it, slower or by guessing. Write out what they have to do
  instead.
- **Violates** — the criterion fails and nobody is stopped or slowed.

Then bucket, on the barrier first and the criterion's level second:

- **P1** — blocks, on a task a user has to complete. Every keyboard trap, every control with no
  keyboard path, every unnamed control on the path through a form.
- **P2** — degrades, or blocks on a path a user can go round.
- **P3** — violates without stopping anybody.

The level describes the criterion in the abstract; the bucket describes it in *this* interface.
A level A failure that stops nobody is P3, and a level AA failure that stops everybody is P1.
Where the two disagree the bucket wins, the report shows both, and one sentence explains the gap.

Then build the criteria table the other way round: for each criterion at the target level, what
checked it and how. That is where the blind spots show. A criterion nothing checked is a gap
rather than a pass, and it is the honest half of the coverage number.

**Done when:** every finding carries a barrier state, a bucket, and its criterion; and every
criterion at the target level carries either the check that covered it or a note that nothing
did.

## 7. Write the fix

Every P1 and P2 gets a fix its owner can apply:

| Finding | The fix |
| --- | --- |
| Missing or wrong name | the markup — a real `<label>`, an `aria-label` that contains the visible text, alt text saying what the image conveys, or `alt=""` where it conveys nothing |
| Keyboard trap | focus moved into the container on open, `Escape` closing it, focus returned to the control that opened it |
| No keyboard path | a real `<button>` or `<a>` in place of the handler on a `<div>` — the element brings the role, the focus, and the key handling with it |
| No focus indicator | a visible indicator at 3:1 against its background. Restoring the browser default beats inventing one |
| Contrast | the colour value or design token that reaches the ratio, with the ratio it reaches |
| Structure | the heading level or landmark, in the component that renders it |
| Status message | `role="status"` or a live region, and the message written into it where the state changes |
| Target size | the size, or the spacing that earns the exemption |

Where the real fix is a design change — a palette, a navigation pattern, a component library
that ships inaccessible primitives — say so and give the mitigation that holds until it lands.
A design change presented as a one-line patch gets applied badly and closed.

A fix counts when the barrier is gone. Hiding the control from the accessibility tree removes
the finding and leaves the person exactly where they were, so check each fix against the barrier
in step 6 rather than against the rule text.

**Done when:** every P1 and P2 carries a fix — a diff, or a named design change with its interim
mitigation — and each one was checked against its barrier.

## 8. Work out the gates

Four, and the third is the one people miss:

| Gate | Runs | Judged on |
| --- | --- | --- |
| Rules engine in the component or e2e suite | every pull request | no new violation |
| The step 4 keyboard and focus checks | pull requests that touch a page in scope | no new P1 |
| Contrast at the token level | whenever the palette changes | every token pair in use reaches its ratio |
| Full sweep across every state | on a schedule | no new P1 or P2 |

The token-level check matters because a palette change is one commit that moves every screen at
once, and a per-page gate catches it one page at a time, long after it shipped.

Nothing is applied here, so every gate is reported as recommended.

**Done when:** all four are written down with the file each would live in, and no CI file has
been edited.

## 9. Write the report

Header: the timestamp from `date '+%Y-%m-%d-%H%M%S'`, the commit from `git rev-parse --short
HEAD`, and a note if the working tree is dirty.

Write to `<module>/.reports/accessibility-report-<timestamp>.md`. `<module>` is the nearest
directory at or above the scope holding the project's manifest (`package.json`, `go.mod`,
`pyproject.toml`, `pom.xml`, `Cargo.toml`, `composer.json`, `Gemfile`, `*.csproj`); a run
spanning several writes to the repository root. Create the folder if missing, add `.reports/` to
the root `.gitignore` if nothing there covers it, one file per run, never overwrite an older one.

Screenshots go beside it in `<module>/.reports/accessibility-<timestamp>/` and are linked from
the finding they belong to. A screenshot from a logged-in session shows somebody's data: crop it
to the component, and keep names, addresses, and tokens out of the file.

Report two numbers side by side:

> **criteria coverage = criteria checked ÷ criteria at the target level**
>
> **state coverage = states driven ÷ states in scope**

A clean result over 4 of 22 states has proved almost nothing, and one blended percentage is how
that gets hidden.

Use the shape below and put the data in tables. The prose left over is the barrier sentence on
each P1 and the argument on each dropped finding.

Then tell the user the report path, both numbers, the P1 count, and the single barrier to take
first.

**Done when:** the report sits in the module's `.reports` folder, `.reports/` is git-ignored, no
older report was overwritten, every finding from steps 3 and 4 appears in exactly one bucket with
its evidence, every criterion at the target level carries how it was checked, and no personal
data from a logged-in session is written into the file or its screenshots.

---

# Report shape

A React app. The tables, states, and buckets are what transfers — swap in your own tools, pages,
and standard. Every table is shown with one or two data rows; a real report lists them all.

````markdown
# Accessibility Report

| | |
| --- | --- |
| **Run** | <YYYY-MM-DD HH:MM:SS> |
| **Commit** | `<short sha>` (dirty working tree) |
| **Target** | `http://localhost:5173` — local dev build |
| **Standard** | WCAG 2.2, level AA — 50 criteria at this level |
| **Scope** | 6 pages, 22 states |
| **Viewport** | 1280×720 at dpr 1, plus the step 4 overrides |
| **Engine** | `axe-core 4.10.2` through `vibium eval`, run in all 22 states |
| **Driver** | `vibium 26.5.31`, headless |
| **Screenshots** | [`accessibility-2026-08-01-141005/`](./accessibility-2026-08-01-141005/) |
| **Previous** | [`accessibility-report-2026-07-24-093012.md`](./accessibility-report-2026-07-24-093012.md) |

## The two numbers

| | Value | Previous | Change |
| --- | --- | --- | --- |
| **Criteria coverage** | **72.0%** — 36 of 50 criteria at AA | 48.0% | +24.0 |
| **State coverage** | **100%** — 22 of 22 states | 63.6% | +36.4 |

Fourteen criteria were not checked by anything. They are listed below as gaps, not as passes.

## Where it stands

| Bucket | Count | Previous | Change |
| --- | --- | --- | --- |
| 🔴 **P1** — blocks a task | 3 | 1 | +2 |
| 🟠 **P2** — degrades, or blocks a path with a way round | 9 | 12 | −3 |
| ⚪ **P3** — violates, stops nobody | 31 | 28 | +3 |

The automated pass raised 61 raw violations. After reproducing each one and merging with the
driven pass, 43 findings remain. Two P1s are new since the last run and both are in checkout.

## What checked each criterion

| Criterion | Checked by | Findings |
| --- | --- | --- |
| 2.1.2 No Keyboard Trap | step 4, by hand — no engine covers it | 1 P1 |
| 2.4.11 Focus Not Obscured | **nothing** — gap | — |

Most of the fourteen need a person to judge meaning rather than a command to run.

---

## 🔴 P1 — take these first

### 1. The checkout modal traps the keyboard — 2.1.2

| | |
| --- | --- |
| **State** | `/checkout` → "Change address" clicked, modal open |
| **Found by** | step 4, keyboard trap check |
| **Barrier** | blocks — a keyboard user who opens the modal cannot reach the Pay button, or anything else on the page, without a mouse. The order cannot be completed |
| **Evidence** | 40 consecutive `vibium keys Tab` presses cycle between the two inputs and the close icon; `Escape` does nothing; `Shift+Tab` stays inside |
| **Screenshot** | [`checkout-modal-trap.png`](./accessibility-2026-08-01-141005/checkout-modal-trap.png) |
| **Fix** | make `Escape` close the modal, and return focus to the "Change address" button. The dialog already renders in a portal, so `<dialog>` with `showModal()` brings the trap boundary and the `Escape` handling for free |

```sh
vibium go http://localhost:5173/checkout
vibium click "button[data-testid=change-address]"
vibium keys Tab   # ×40 — focus never leaves the dialog
vibium keys Escape
vibium eval "document.activeElement.outerHTML.slice(0,80)"
```

---

## 🟠 P2 — degrades, or has a way round

| # | Finding | Criterion | State | Barrier | Fix |
| --- | --- | --- | --- | --- | --- |
| 1 | The order table is built from `div`s with no row or cell roles | 1.3.1 | `/orders` | degrades — a screen reader reads 240 unrelated strings with no column headings, so a customer can find their order only by reading the whole page | render a `<table>`, or add `role="table"` with row and cell roles on the existing markup |

---

## ⚪ P3 — violates, stops nobody

| Finding | Criterion | State | The argument |
| --- | --- | --- | --- |
| Footer link contrast 4.2:1 against the footer background | 1.4.3 | every page | fails AA by 0.3, on links duplicated in the header at 7.1:1. Nobody is stopped; still worth the token change |

30 more, listed in `.reports/axe-2026-08-01-141005.json`.

## Dropped

| Reported | By | Why it is not a finding |
| --- | --- | --- |
| `color-contrast` on the cookie banner text | axe-core | the banner is `display: none` in this state; the rule ran against a hidden node |

## The gates

| Gate | Runs | Judged on | Where | State |
| --- | --- | --- | --- | --- |
| axe in the e2e suite | every pull request | no new violation | `.github/workflows/ci.yml` | recommended |
| Keyboard and focus checks | pull requests touching `src/pages/**` | no new P1 | `.github/workflows/ci.yml` | recommended |
| Token contrast check | on a change to `tokens.css` | every pair in use reaches its ratio | `.github/workflows/ci.yml` | recommended |
| Full sweep, all states | nightly | no new P1 or P2 | `.github/workflows/a11y-nightly.yml` | recommended |
````

Every finding appears in exactly one bucket. Drop any empty section, keep both numbers and the
criteria table even when they are perfect, and lead the body with P1. Where no older report sits
beside this one, drop the "Previous" row and the "Previous" and "Change" columns.
