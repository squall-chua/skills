---
name: visual-slop
description: >
  Check a running UI against the pols.dev anti-slop design law, rank every tell by what
  it stacks with, and propose the signature that replaces it.
disable-model-invocation: true
---

**Slop** is generic, look-the-same output: an interface where nothing was decided. The law
that defines it lives at <https://pols.dev/slop.md>, and this skill runs that law — fetched
fresh each time and walked point by point. It names about 150 **tells**, the individual
signatures of a generated interface.

Two of its rules shape the whole run.

**Tells stack.** Any one can be argued on its own. An icon in a tinted tile, a category pill,
a row of tag chips, a hairline divider, and a glowy button are each defensible; piled into one
card they are the clearest slop signature there is. What sorts the findings here is not how
bad a tell is alone but what it sits beside.

**Removing a tell is not designing.** The law's deepest point: you can dodge every entry and
still ship slop, because a checklist makes work less wrong rather than good. So every finding
carries the **signature** that replaces it — what goes in, not only what comes out.

## This skill reports

Steps 1 to 8 read, rank, and write up. The interface stays exactly as it is and the step 7
proposals are left on the page for a person to accept or reject. That report and its
screenshots are the whole deliverable.

Steps 9 and 10 run only on a **fix signal**: "fix the slop", "apply it", "build that
signature", "go ahead". The step 8 report is the *before*, so it is written on a fix run too,
and written before anything in the interface is touched.

## 1. Read the law, and take the user's overrides

```sh
curl -sSL https://pols.dev/slop.md -o <scratch>/slop.md
grep -c '^## ' <scratch>/slop.md
```

Read the whole file before looking at the interface. It runs to about 1,600 lines across
seven parts — the tells, the slop layouts, the deeper tell of avoiding them, what premium
actually looks like, the signature formula, a kit of premium moves, and field notes. A review
run from memory of it is a review of your own taste wearing the law's name.

Where the fetch fails, stop and tell the user. The law is the standard this skill measures
against; without the file there is nothing to measure.

Then take the **overrides**. The law states that a specific instruction from the user beats
any default in it, and their direction wins outright. A brand that owns purple owns purple; a
team that has licensed Inter has licensed Inter; a product whose users expect a countdown gets
a countdown. Ask for them once, here, and record each against the heading it suspends. A tell
the user has already chosen is not a finding.

**Done when:** the file is on disk with its heading count recorded, and every override is
written down beside the heading it suspends.

## 2. Pin the scope and open it

Get the base URL of a **running** instance and the pages in scope. Named none? Take the routes
the app declares and say so.

Then the **states**, because the tells hide in them: a card before and after its hover, a nav
scrolled and at rest, an accordion open, a form in its error state, a section after its
entrance animation should have fired. Each state gets the `vibium` commands that reach it.

```sh
vibium start
vibium go <url>
vibium viewport 1440 900 && vibium screenshot --full-page -o <dir>/<page>-1440.png
```

Take a full-page screenshot of every state at **1440, 768, and 390** wide. Several tells live
at one width only — text jammed against the rim, a ragged comparison grid, cramped display
type, a headline that breaks onto a dangling accent word. Where the site has a theme toggle,
repeat in both: `vibium media --color-scheme dark`.

**Done when:** every page-and-state pair has a full-page screenshot at each of the three
widths, in each scheme the site offers, with every file path recorded.

## 3. Sweep the computed styles

Many tells are mechanically visible, and this pass finds them faster and more completely than
an eye does. It produces candidates; step 5 decides.

| Tell | What to read |
| --- | --- |
| The named slop faces | `fontFamily` on headings, body, labels, buttons, and the footer — against every family the law names |
| Blue-to-purple gradient | `backgroundImage` holding a `linear-gradient` whose stops sit between hue 200 and 300 |
| Gradient-filled headline | `backgroundClip` or `webkitBackgroundClip` set to `text` |
| Glow | `boxShadow` with a large blur radius and a colour that is not neutral |
| Glass | `backdropFilter` holding a `blur` |
| Pill | `borderRadius` at or above half the element's own height |
| Hairline border on boxes | a `1px` border at low opacity, counted across every card |
| Tinted chips | small elements with a rounded radius, a tinted background, and one short string |
| The invisible-content trap | elements holding text still at `opacity: 0`, or translated away, after load with JS running |
| Icon pack | `lucide-react` or a sibling in the manifest, and how many of its components are imported |
| Monospace as the house voice | `fontFamily` resolving to a mono on anything that is not data |
| Grid background | a repeating `linear-gradient` on a section-sized element |
| Em dashes | the rendered text of the page |

`vibium eval` prints objects in Go's map format, so return a JSON string and read that:

```sh
vibium eval "JSON.stringify([...document.querySelectorAll('*')].filter(e => {
  const s = getComputedStyle(e)
  return s.backgroundImage.includes('gradient') || s.backdropFilter !== 'none'
}).map(e => {
  const s = getComputedStyle(e)
  return { sel: e.tagName + '.' + e.className, bg: s.backgroundImage, bd: s.backdropFilter }
}))"
```

The **count** matters as much as the match. One pill is a choice; every label on the page in a
pill is the tell, and the same goes for hairline borders, tinted chips, and tracked-out caps.
Record how many elements each query hit.

**Done when:** every query has run on every page and state, and each candidate carries its
selector, its value, and the number of elements that match.

## 4. Look at the screenshots, then click

The tells no query catches: composition, proportion, and whether the thing looks alive. Read
every screenshot from step 2 against each row.

| Look at | The tells under it |
| --- | --- |
| The page whole | the SaaS meta-skeleton, a run of stacked slop layouts, the same skeleton recolored |
| The hero | the split hero, the default hero stack, a hero that does not own the first screen, a fake app or code window, crude CSS illustrations |
| The background | a flat fill, a faint grid, a background glow, drifting gradient blobs, grain sitting over the content |
| Every repeated set | ragged comparison columns, feature lists starting at different heights, a button floating up in the short column |
| Every edge and corner | content sliced by a clip or a fixed height, text jammed against the rim, hard colour seams between sections, a glow cut off by an overflow |
| The type | cramped display type, one label treatment on every small string, a neutral grotesque carrying the whole identity |
| The signature | whether one focal object here could not be pasted onto another site |

Zoom into each clipped edge and corner rather than judging at page scale. The law is explicit
that a notch can crop a real word and you will not see it at normal zoom.

Then click. Every tab, accordion, toggle, slider, and button gets a real `vibium click` and its
response read. A control that looks live and answers nothing is a defect rather than a matter
of taste, and the law asks for a real pointer on each one before anything is reported.

**Done when:** every screenshot has been read against every row, every clipped edge was
inspected at zoom, and every interactive control was clicked with its response recorded.

## 5. Walk the law point by point

Take every `##` heading in the fetched file, in order, and give it one verdict:

- **Present** — the tell is here. Name the element, the page, the state, and the screenshot.
- **Absent** — checked, and not here.
- **Overridden** — the user asked for it in step 1, so it is not a finding.
- **Not applicable** — the page has no such surface. A pricing-block tell on a page with no
  pricing.

The law asks for exactly this walk before anything is called done, and a review that stops at
the tells it happened to notice is the review it warns against.

**Done when:** every heading in the fetched file carries one of the four verdicts, and the
number of verdicts equals the heading count from step 1.

## 6. Rank by the stack

Bucket every **present** tell:

- **P1 — broken.** Reads as broken to anybody, slop-aware or not: content still hidden behind
  an entrance animation that never fired, content sliced by an edge, text under its contrast,
  a ragged comparison grid, a dead control, botched glass, a fill animation that stops
  half-way. These are defects, and they outrank every question of taste.
- **P2 — stacked.** Three or more tells in one element, one section, or one page skeleton. The
  kitchen-sink card and the SaaS meta-skeleton live here, because a page is not the sum of
  individually acceptable blocks.
- **P3 — a single tell.** One, standing alone, arguable on its own.

Give every element and every section its **stack count** and put the number in the report. An
element carrying five tells and an element carrying one need different work, and the count is
what says which.

Then one verdict on the page itself: has it a **signature** — one focal artifact that could
not be pasted onto another site? Score it against the law's formula, which is a signature
artifact plus atmosphere, layered depth, a character display face, one bespoke silhouette, a
treated nav, and real specifics. A page that scores nothing there is boring with zero tells
against it, and the report says so rather than reporting a clean pass.

**Done when:** every present tell carries a bucket, every element and section carries its
stack count, and the page carries a signature verdict scored against all seven parts of the
formula.

## 7. Propose the signature, not the removal

Every P1 and P2 gets a proposal that names what goes **in**:

| The finding | What the proposal names |
| --- | --- |
| A single tell | the specific replacement and the reason from the brief — this face because this brand, this shape because this product |
| A stacked element | what the element is for, then the one or two pieces that carry it. The rest goes |
| A stacked page skeleton | the section order rebuilt from the brief, not the same order recolored |
| A P1 defect | the fix, since a defect has a right answer rather than a proposal |
| No signature | the one focal artifact, decided first, and what the rest of the page does to support it |

The law names two opposite failures and the run has to steer between them. Stacking every
premium move at once — a serif headline and a character field and glass and a gradient mark
and a full-bleed scene — makes noise. Leaving the page flat when it plainly calls for a
signature is the boring failure. **Cohesion** decides between them: every choice belongs to
one system, and a technique that fights the rest of the page is worse than not using it.

A proposal earns its place when the page could not be swapped, block for block, onto another
product. Swapping a trendy face for a tasteful one, recoloring the same skeleton, ruling
instead of bordering, deleting every icon to be safe — each dodges a heading and invents
nothing, and the law counts all four as slop.

**Done when:** every P1 and P2 carries a proposal naming what goes in with its reason from the
brief, one signature artifact is proposed for the page and named first, and every proposal was
checked against the cohesion rule.

## 8. Write the report

Header: the timestamp from `date '+%Y-%m-%d-%H%M%S'`, the commit from `git rev-parse --short
HEAD`, and a note if the working tree is dirty. Record the law's own fetch date and heading
count beside them, because the file changes and a verdict is only against the version read.

Write to `<module>/.reports/slop-report-<timestamp>.md`. `<module>` is the nearest directory at
or above the scope holding the project's manifest (`package.json`, `go.mod`, `pyproject.toml`,
`pom.xml`, `Cargo.toml`, `composer.json`, `Gemfile`, `*.csproj`); a run spanning several writes
to the repository root. Create the folder if missing, add `.reports/` to the root `.gitignore`
if nothing there covers it, one file per run, never overwrite an older one.

Screenshots go beside it in `<module>/.reports/slop-<timestamp>/` and are linked from the
finding they belong to. A tell about a shape or a seam is unarguable with the picture and
unprovable without it.

Report one number and one verdict:

> **law coverage = headings given a verdict ÷ headings in the file**

and the signature verdict from step 6. Coverage below 100% means the walk did not finish, and
the report says which headings were left.

Use the shape below and put the data in tables. The prose left over is the proposal on each
stacked element and the signature paragraph.

Then tell the user the report path, the P1 count, the worst stack and where it sits, and
whether the page has a signature.

**Done when:** the report sits in the module's `.reports` folder, `.reports/` is git-ignored,
no older report was overwritten, every heading from step 5 appears with its verdict, every
present tell appears in exactly one bucket with its screenshot, and every P1 and P2 carries
its proposal.

## 9. Apply the fixes — on a fix signal

Without the signal the work finished at step 8.

**The signature is built first, before any tell is removed.** It is the one creative decision
here and every other change has to belong to the system it sets up: strip 34 tells from a page
with no signature and what is left is a cleaner page with nothing decided in it, which is the
failure the law is written about. So put the step 7 proposal to the user, build the one they
pick, and let it settle the palette, the display face, the silhouette, and the nav before the
rest of the list is touched.

Then work in this order:

1. **P1 defects.** Broken is broken, and each has a right answer rather than a proposal.
2. **The signature artifact**, with the type, palette, and silhouette it decides.
3. **Stacked elements, worst stack first.** Rebuild each around what it is for, now that there
   is a system for it to belong to.
4. **Single tells**, where they still stand after the rebuild. Many will already be gone.
5. **The token and style sweep** — the faces, the gradients, the radii, the borders — as its
   own commit, because a hundred mechanical edits mixed with six considered ones is a diff
   nobody can review.

Every change gets checked three ways before you move on:

- **Re-run the step 3 sweep** on the changed element. The tell's value is gone.
- **Re-screenshot** at all three widths and both schemes, into a new folder. Look at it: a
  design fix is verified with the eye, and the query only says the property changed.
- **Re-walk the headings** the change could touch. This is the one that matters — replacing a
  glow with a hairline border trades one heading for another, and a fix that raises a new tell
  has moved the problem rather than solved it.

Then click every control on the page again, not only the ones you touched. A layout rebuild is
the commonest way a working control becomes a dead one.

**Remove the tell, not the element.** Deleting the pricing card clears three headings and the
page's ability to sell. And a swap is not a fix — the four dodges in step 7 count as slop here
too. Every fix is checked against the brief, not against the heading it closes.

Where a fix needs a decision only the owner can make — a brand colour, a licensed face, real
photography in place of gradient initials — write it up as a decision waiting and move on.

**Done when:** the signature artifact is built and named, every P1 and P2 from step 6 is one of
four things — fixed and verified all three ways, left standing with a stated reason, raised as
a decision waiting on the owner, or deferred with its reason — every control on every changed
page was clicked, and no fix raised a new heading that is still open. None are simply
unmentioned.

## 10. Write the after report — on a fix signal

Re-run steps 3, 4, and 5 over the same pages and states. Fresh timestamp, second file in the
same `.reports` folder, screenshots in their own folder; the step 8 report and its screenshots
stay untouched, so anyone can read the before for themselves.

Lead the body with a "What moved" section naming the step 8 file, and give each of these its
own table:

- the heading verdicts before and after, and the tell count by bucket;
- what happened to each present tell — fixed, left standing, waiting on a decision, deferred;
- the signature formula scored again, part by part, against the seven it scored before;
- any heading that turned **present** during the fix run. A fix that raises a new tell is the
  first thing the reader needs.

Put the before and after screenshots of each rebuilt element side by side. On this skill that
pair is the finding: a table saying a stack went from six tells to one proves less than the two
pictures do.

Then tell the user both file paths, the two tell counts, the signature verdict now, and what is
still waiting on a decision.

**Done when:** both reports sit side by side with their own screenshot folders, the after
report names the before file, every present tell from step 6 appears with its outcome, the
signature formula is scored again part by part, and every rebuilt element carries its before
and after picture.

---

# Report shape

A marketing site. The tables, buckets, and the formula are what transfers — swap in your own
pages and paths. Every table is shown with one or two data rows; a real report lists them all.

````markdown
# Visual Slop Report

| | |
| --- | --- |
| **Run** | <YYYY-MM-DD HH:MM:SS> |
| **Commit** | `<short sha>` (dirty working tree) |
| **Target** | `http://localhost:3000` — 4 pages, 11 states |
| **Law** | <https://pols.dev/slop.md>, fetched <date> — 147 headings |
| **Widths** | 1440, 768, 390 · light and dark |
| **Driver** | `vibium 26.5.31` |
| **Screenshots** | [`slop-2026-08-01-153311/`](./slop-2026-08-01-153311/) |
| **Overrides** | purple is the brand colour, set by the user. Suspends "Purple, and blue-to-purple gradients" for flat fills, not for gradients |

## The verdict

# No signature — 34 tells present, 2 of them broken

The landing page is the SaaS meta-skeleton: two-column hero, three icon-tile feature cards,
pricing trio, FAQ, gradient CTA slab, four-column footer. Every block is its own entry in the
law and the order is the template. Recoloring it would change nothing.

Nothing here could not be pasted onto another product. That is the finding above all the
others: the page scores zero of the seven parts of the signature formula, so it would still
read as generated with every tell below removed.

## Law coverage

| | Value |
| --- | --- |
| **Law coverage** | **100%** — 147 of 147 headings given a verdict |
| **Present** | 34 · **Absent** 97 · **Overridden** 1 · **Not applicable** 15 |

## The signature formula

| Part | Present | What is there instead |
| --- | --- | --- |
| One signature artifact | ❌ | a rounded panel holding a fake app window |
| Atmosphere | ❌ | flat `#0B0F17` behind every section |

Zero of seven. Decide the signature artifact first; the rest of this report supports it.

---

## 🔴 P1 — broken

### 1. The testimonial row renders empty — "Never hide content behind an entrance animation"

| | |
| --- | --- |
| **Where** | `/` → scrolled to testimonials, all three widths |
| **What happens** | the three cards carry `initial={{opacity:0}}` and the reveal is stranded at its initial frame in a full-page screenshot. The section renders as 420px of void |
| **Evidence** | `getComputedStyle(card).opacity === "0"` after load with JS running |
| **Screenshot** | [`home-testimonials-1440.png`](./slop-2026-08-01-153311/home-testimonials-1440.png) |
| **Fix** | render the cards visible and animate something already on screen. Content is visible by default; an entrance reveal is only safe when the no-JS fallback still shows it |

---

## 🟠 P2 — stacked

### 1. The pricing card — 6 tells in one element

| | |
| --- | --- |
| **Where** | `/pricing` → the middle card |
| **Stack** | icon in a tinted tile · "MOST POPULAR" pill on the top edge · glowing gradient border · tag chips on each feature · hairline border · glowy pill CTA with a bottom shadow |
| **Headings** | the three-tier pricing block, the kitchen-sink card, glowy pill buttons, hairline light border on boxes, labels as tinted pill chips, background glow |
| **Screenshot** | [`pricing-card-1440.png`](./slop-2026-08-01-153311/pricing-card-1440.png) |

**The proposal.** The card is for one job: showing what a tier costs and what it includes. The
price and the feature list carry that, so cut the tile, the chips, the glow, and the gradient
border. In their place, one bespoke silhouette — the card cut as a receipt with a torn bottom
edge, the product's own metaphor and not pasteable onto another site. "Most popular" moves into
the type rather than a pill on the border.

---

## ⚪ P3 — single tells

| Tell | Heading | Where | Proposal |
| --- | --- | --- | --- |
| Two-letter initials on a blue-purple gradient circle | Gradient-circle initials avatar | `/` testimonials, 3 instances | real photographs, or drop the avatar and let the name and company carry it |

26 more, listed with their headings and elements below.

---

## Checked and absent

| Heading | Verdict |
| --- | --- |
| Countdown timer | absent |
| Botched glass | not applicable — no translucent surface on any page |

## The signature to build first

One artifact, decided before anything below it changes: the product moves invoices, so the hero
object is a real populated invoice — actual line items, a real total, tilted with depth and
bleeding off the bottom edge, over an atmosphere rather than the flat `#0B0F17`. The receipt
silhouette on the pricing card is the same idea carried through, which makes it a language
rather than a move. Type: a character display face for the signature line, body neutral. Nav
contained in a pill so it stops reading as a default row.
````

Drop any empty section, and lead the body with the signature verdict rather than the tell
count — a page with no signature and no tells is still the failure the law is written about.

The after report from step 10 is that same shape, with a **Before** row in its header pointing
at the step 8 file, an **Outcome** row on every finding, and this section leading the body —
the four tables step 10 names, in that order, then the before-and-after screenshot pairs:

````markdown
## What moved

Against [`slop-report-2026-08-01-153311.md`](./slop-report-2026-08-01-153311.md), written
before anything in the interface was touched.

| | Before | After | Change |
| --- | --- | --- | --- |
| **Present** | 34 | **6** | −28 |
| **🔴 P1 — broken** | 2 | 0 | −2 |
| **🟠 P2 — stacked** | 5 | 1 | −4 |
| **⚪ P3 — single** | 27 | 5 | −22 |
| **Law coverage** | 100% — 147 headings | 100% — 147 headings | — |

| Tell | Outcome | What replaced it |
| --- | --- | --- |
| The pricing card — 6 tells | 🟢 fixed | rebuilt on the receipt silhouette. Price and feature list only; "most popular" is carried in the type, not a pill on the border |
| Gradient-circle initials avatar | ⏳ waiting on a decision | real photography needs the customers' permission, which is the owner's call |

| Signature formula | Before | After | What is there now |
| --- | --- | --- | --- |
| One signature artifact | ❌ | ✅ | a populated invoice — real line items, tilted with depth, bleeding off the bottom edge |
| Real specifics | ❌ | ❌ | still "Northwind Labs" and "velocity jumped 32%", waiting on real customer names |

**5 of 7, from 0 of 7.** Atmosphere, layered depth, the display face, and the treated nav
came with the artifact.

| Turned present during the fix run | Where | Raised by |
| --- | --- | --- |
| none — every changed element was re-walked against the headings its change could touch | — | — |

| Element | Before | After |
| --- | --- | --- |
| The pricing card | [`pricing-card-1440.png`](./slop-2026-08-01-153311/pricing-card-1440.png) | [`pricing-card-1440.png`](./slop-2026-08-01-171902/pricing-card-1440.png) |
````

Everything below that section is the shape above, re-run. The before report is never edited to
match it.
