# Report shape

A web app example. The tables, grades, and dimensions are what transfers — swap in your own
routes and paths. Tables are shown with one or two rows; a real report lists them all.

````markdown
# Visual Quality Report

| | |
| --- | --- |
| **Run** | <YYYY-MM-DD HH:MM:SS> |
| **Commit** | `a1b2c3d` (clean) |
| **Pages** | `/`, `/pricing`, `/checkout`, `/checkout/confirm` — 4 routes |
| **Widths** | slop: 1440, 768, 390 · light and dark. Accessibility: 1280 plus its reflow overrides, theme not recorded |
| **States** | resting, modal open, form in error, cart empty — 22 of 22 walked |
| **Standard** | WCAG 2.2 AA (the team's commitment), the pols.dev slop law fetched 2026-08-01 |
| **Overrides** | purple is the brand colour, set by the user |
| **Phase** | visual — the rendered interface. Not a code or release verdict |
| **Starting position** | thin — both dimensions measured, both Fragile |
| **Previous** | [`visual-quality-report-2026-07-23-140218.md`](./visual-quality-report-2026-07-23-140218.md) |

## Verdict

# 🔴 Fragile — 0 of 2 dimensions unproven

**Can everyone use it?** No. A person using a keyboard cannot leave the checkout modal — focus
stays inside it and Escape does nothing, so the only way out is closing the tab. Two other P1
barriers sit on the same flow.

**Would anyone remember it?** No. The landing page scores zero of the seven parts of the
signature formula: two-column hero, three icon-tile feature cards, pricing trio, gradient CTA
slab, four-column footer. Every block is its own entry in the law and the order is the template.
Recolouring it would change nothing.

Access set the floor. Last week's verdict was 🟡 Thin, on the same four routes — the keyboard
trap arrived with the new modal component.

**Not covered here.** These two describe the rendered interface. Nothing above says how much of
the code runs under test or what the code reads like — run `/code-quality`. Nothing above says
whether the API keeps its contract, survives a broken dependency, or carries the load — run
`/release-quality`.

## Dimensions

| Dimension | Relevance | Grade | The numbers | Evidence | Behind HEAD |
| --- | --- | --- | --- | --- | --- |
| Access | applies | 🔴 Fragile | 3 P1 barriers, criteria coverage 72.0%, 22 of 22 states, keyboard and focus driven | [accessibility](./accessibility-report-2026-08-01-141005.md) | 0 commits |
| Signature | applies | 🔴 Fragile | no signature, 34 tells, 2 of them P1, worst stack 6 on the hero card, law coverage 100% | [slop](./slop-report-2026-08-01-153311.md) · [screenshots](./slop-2026-08-01-153311/) | 0 commits |

Both are at the floor, so the verdict is 🔴 Fragile.

## What the signals say together

| The pair | The findings | What it means |
| --- | --- | --- |
| A P1 barrier on the element carrying the worst stack | the checkout modal — keyboard trap, and 6 stacked tells | one rebuild fixes both. Rebuilding it around what it is for removes the trap on the way ([shot](./slop-2026-08-01-153311/checkout-modal-1440-dark.png)) |
| A contrast tell and a contrast barrier on the same text | the `#8B8B9A` helper text on `#0B0F17` — 3.1:1 | two laws agreeing about one colour. Fix once and both move |
| Green suite, a P1 access barrier *(crosses into `/code-quality`)* | 412 tests green, the checkout modal traps focus | the tests reach the close button by calling it. A person using a keyboard cannot reach it at all |

## The next moves

**Start here:** rebuild the checkout modal. It carries a P1 keyboard trap and the worst tell
stack on the site, and it is one component rather than two fixes. It renders on 4 pages —
`git grep -l '<Modal' -- '*.tsx'`.

The rest of the list keeps. Run `/visual-quality` again when that one is done and it will name
the move after it.

| # | Do this | Why it is here | Costs | Pages reached | Command |
| --- | --- | --- | --- | --- | --- |
| 1 | Rebuild the checkout modal — focus trap with an Escape route, and one thing carrying the card instead of six | a P1 barrier and the worst stack on one element | a day | 4 | `/visual-accessibility`, `/visual-slop` |
| 2 | Raise the helper text to `#A8A8B8` | 3.1:1 against AA's 4.5:1, and a slop tell on the same pixels | minutes | all | — |
| 3 | Decide one signature artifact for the landing page and build it | removing the 34 tells leaves a blank template. Nothing here can be pasted onto another product until something is put in | a week | 1 | `/visual-slop` |

## Next phase

| Phase | Dimensions | Command |
| --- | --- | --- |
| Development | verified behaviour, test strength, change risk, specified behaviour, construction, single source, readability | `/code-quality` |
| Release | promised behaviour, proven seams, resilience, headroom, exposure | `/release-quality` |
````

Drop any empty section, and lead the body with the verdict and the two plain-language answers.

**Where the project renders nothing**, the report is four lines and no tables: what the project
ships, that neither dimension has a surface here, that this is not a gap, and the two commands
for the phases that do apply. Do not write the shape above for a JSON API.
