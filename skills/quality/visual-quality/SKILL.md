---
name: visual-quality
description: >
  The front door to the two interface dimensions: read whichever reports are on disk, say
  whether this project has an interface to grade at all, cross-read them, and give one
  graded verdict on the rendered UI.
disable-model-invocation: true
---

Two dimensions, each named for what it measures rather than the tool that measured it:

| Dimension | The question it answers | Measured against | Filled by |
| --- | --- | --- | --- |
| **Access** | can everyone operate the interface, keyboard and screen reader included | the rendered page | `/visual-accessibility` |
| **Signature** | did anybody decide anything, or is this the default template | the rendered page | `/visual-slop` |

Two is a small set and the right one, because both share a precondition nothing else in the
quality family has: **a page that renders in a browser.** Neither can be read out of source. A
focus ring nobody can see, a tab order that jumps the page, an icon in a tinted tile above a row
of tag chips — none of it exists until the pixels do.

They answer the two halves of one question. Access asks whether a person can use the interface;
signature asks whether they would remember it. The common case is a page that fails both while
looking fine to whoever built it.

**Two sets sit outside this skill.** `/code-quality` covers the seven measured against the code
and its suite; `/release-quality` the five that need a running system. Name both at the end of
the report so nobody reads two green rows as a whole-system pass.

Three rules hold throughout.

**Relevance comes before measurement.** A project that renders nothing has no interface to
grade, and saying so is the whole answer. Grading it unproven manufactures a failure.

**The verdict is a floor, not an average.** Two dimensions makes this sharper: an operable page
nobody would remember is exactly as unfinished as a beautiful one nobody can tab through.

**Absent evidence is never good news.** No report, a skipped one, and a stale one all read as
**unproven** — and with two dimensions, one unproven is half the assessment.

## 1. Find the reports

Search every `.reports/` folder in the repository. The two siblings write
`accessibility-report-` and `slop-report-`, timestamped, one file per run, per module. Take the
newest of each kind, per module — on a fix run a sibling writes a before and an after, and the
after is the one that describes the interface as it stands.

Both siblings also write **screenshots** beside their reports — `/visual-slop` into
`slop-<timestamp>/`, and `/visual-accessibility` alongside its findings. Find those folders and
link them. A tell about a shape or a seam is unarguable with the picture and unprovable without
it, and the same is true of a focus ring.

Set your own past reports aside. `visual-quality-report-*` files are this skill's own output and
they are the **comparison** in step 6, never a dimension.

Leave the other two phases' reports alone as dimensions too. `code-quality-report-*`,
`release-quality-report-*`, and their sibling reports belong to `/code-quality` and
`/release-quality`. Note in step 5 that they exist — a `bdd-report-` full of green scenarios
changes what a keyboard trap means — but never grade one here.

Read anything else in there too. A design review, a Lighthouse run, a user testing write-up:
each becomes an extra dimension in step 4 rather than a file you stepped over.

**Done when:** you have every report found with its kind, module, timestamp, and the commit
named in its header; its screenshot folder located; a note of which of the two kinds turned up
nothing; and the newest `visual-quality-report-*` held aside as the comparison.

## 2. Check each report is still evidence

A report describes the commit in its header, not the commit you are standing on. For each one:

```sh
git rev-list --count <report commit>..HEAD
git diff --stat <report commit>..HEAD -- <the report's scope>
```

| State | Test | Weight |
| --- | --- | --- |
| **Current** | the report's commit is HEAD, and no file in scope has changed since | full evidence |
| **Near** | commits since, but none touching the report's scope | full evidence |
| **Stale** | files in scope changed since | a lead, not evidence |
| **Unusable** | the commit is unknown to this repo | no evidence |

**"In scope" is wider here than the pages named.** A rendered page is the product of its own
template plus the design system under it plus whatever the global stylesheet says. A commit to
a shared `Button` component or a token file invalidates every report that rendered a button,
whether or not the page's own file changed. So include in each report's scope: the routes it
walked, the components those routes render, and the shared style layer. When in doubt, rate it
Stale — re-rendering a page is cheap, and both siblings do it themselves.

**Then check what the run covered.** A report is only evidence about what it rendered, on four
axes:

| Coverage question | Why it matters |
| --- | --- |
| **Which routes?** | a clean report on the marketing page says nothing about checkout |
| **Which widths?** | a tab order that works at 1440 can be unreachable at 390, where the nav collapses |
| **Light and dark?** | contrast is a property of a theme, not of a page |
| **Which states?** | a modal open, a form in error, a list empty, a row selected. Barriers live in states, and a page walked only in its resting state was barely walked |

**The two siblings do not record the same axes, and reading them as if they did is the mistake
to avoid here.** Read each one's own fields:

| Axis | `visual-accessibility` | `visual-slop` |
| --- | --- | --- |
| Routes | **Scope** — pages and states | **Widths** row names the run; the page walked is in **Scope** |
| States | **Scope** — "6 pages, 22 states" | not recorded per state |
| Widths | **Viewport** — one primary, plus the reflow overrides its own step 4 adds | **Widths** — the full set, e.g. "1440, 768, 390" |
| Themes | **not recorded** | **Widths** row carries them, e.g. "light and dark" |

So the theme axis has one source, not two. `visual-accessibility` does not say which theme it
ran in, and that is its own design rather than an incomplete header — do not mark it as one.
Record instead that any contrast result in the accessibility report belongs to whichever theme
the run happened to be in, and say so beside that finding. Where the two reports disagree about
a colour, the theme is usually why.

Record all four axes per report against the table above. An axis a sibling records and shows as
skipped is a real gap. An axis a sibling never records is a gap in what can be known, and the
report names it as that.

Every sibling writes "dirty working tree" into its header when the tree was dirty. Compare
against the working tree instead: `git status --porcelain -- <the report's scope>`, and rate the
report **Current** when nothing in its scope has been touched since.

**Done when:** every report carries a state and its commit distance, its scope was widened to
include the shared components and style layer, and its coverage is recorded against the four
axes using that sibling's own fields — an axis it records and skipped marked as a gap, an axis
it never records marked as unknowable from this report rather than as an incomplete header.

## 3. Judge relevance, then settle the gaps

This step is one question, and on most projects it is answered in a sentence.

**Does this project render an interface?** Read its manifest, its entry points, and what it
ships:

| The project | Applies | Does not apply |
| --- | --- | --- |
| A front end, a web app, a site | both | — |
| A service that serves pages | both | — |
| A service that serves only JSON | — | both — nothing renders |
| A CLI, a batch job, a library | — | both — nothing renders |
| A component library with a storybook or docs site | both, against that site | — |
| A design system with no rendered example anywhere | — | both, and say so: there is nothing to point a browser at. Standing up one page is the move |

Say **not applicable** plainly and stop, where it is. This is the one skill in the quality
family whose most common correct answer is "this project has no interface". A JSON API graded
⚫ Unproven on access reads as a gap somebody left; it is not one.

**Then, where both apply, which pages?** A rendered interface is not one thing. Ask for the
routes, and where the user has not said, propose the set and let them confirm:

- Every route a person can reach without an account, and the sign-in that gates the rest.
- The one flow that carries the money, or the sign-up, or whatever the product is for.
- The pages people are on longest, if anybody knows which those are.

That list is the scope, and the report names it. Both siblings are run per page, so a scope of
"the app" is not a scope — it is a project.

Then give each dimension one relevance:

- **Applies** — the project renders something, so an unproven grade here is a real gap.
- **Not applicable** — nothing renders. Both leave the counts, and the report says so in a line.
- **Deferred** — something renders, the team has decided not to check it before this release,
  and somebody owns that decision. Name the person and the date. It stays in the unproven count.

There is no *by choice* here, and signature is the one people try to put there. "We do not care
how it looks" is a decision about priority, not about the property: an interface nobody decided
still reads as generated to every person who sees it, whether or not anybody measured. Record
that as **deferred**, with a name against it.

Neither dimension is ever *out of scope* the way the release dimensions are at module scope —
if a page renders, both can be run against it, whatever folder you were pointed at.

Where an applicable dimension is unproven, name the precondition:

| Precondition | Met when | The dimensions |
| --- | --- | --- |
| a page that renders, and a browser driver | the app runs locally or somewhere you can point at, and `vibium` is available | both |
| the pages behind a login | you have credentials for a test account | both, for anything gated |

Both share the same precondition, which makes the question simple. Ask it once:

| Dimension | Relevance | State | To fill it | Costs | Skipping it means |
| --- | --- | --- | --- | --- | --- |
| Access | applies | no report | `/visual-accessibility` ← start here | under an hour per page | somebody cannot buy the thing, and nobody knows |
| Signature | applies | stale, 14 commits behind | `/visual-slop` | under an hour per page | the product looks like every other product, and that is a decision nobody made |

Mark **← start here** on access, and it is access every time there is a choice: a barrier stops
a person doing something today, and a slop tell costs distinctiveness. A defect beats a
judgment.

The sibling skills are the user's to run — neither fires on its own, so hand over the commands
and let them type them. Then they call `/visual-quality` again with the fresh reports on disk.

**Done when:** the project's relevance is settled and stated, the pages in scope are named and
confirmed, every applicable unproven dimension names its precondition, anything deferred carries
a name and a date, and where nothing renders the report says so in one line rather than grading
anything.

## 4. Read each dimension

Read each applicable dimension from its report:

| Dimension | Read from |
| --- | --- |
| **Access** | accessibility report — criteria coverage, state coverage, P1 barriers, the WCAG level checked |
| **Signature** | slop report — the signature verdict, law coverage, the P1 count, the worst stack count and where it sits |

Grade each. Every band is exhaustive: read top down and take the first that matches.

| Grade | Access | Signature |
| --- | --- | --- |
| 🔴 **Fragile** | any P1 barrier, or criteria coverage < 50% | no signature — the page scores nothing on the seven-part formula — or any P1 tell, the ones that read as broken to anybody |
| 🟡 **Thin** | any P2 barrier, or criteria coverage 50–79%, or a rules-engine pass with no driven checks | any P2 — three or more tells stacked in one element, section, or page skeleton |
| 🟢 **Sound** | no P1 or P2 barrier, criteria coverage ≥ 80%, the keyboard and focus checks driven | a signature named and present, no P1 or P2, law coverage 100% |
| ⚫ **Unproven** | no usable report | no usable report |

Four results override the numbers beside them, whatever those numbers say:

| Result | What it forces | Why |
| --- | --- | --- |
| A rules-engine pass with nothing driven | access capped at 🟡 Thin | an engine sees about a third of WCAG, and it is not the third that stops people. A clean automated pass is a clean pass on the easy third |
| **No signature**, with zero tells found | signature 🔴 Fragile | a page with nothing wrong with it and nothing decided about it is boring, not clean. The slop law says this outright, and a zero tell count reads as a pass unless the verdict overrides it |
| Law coverage below 100% | signature **Unproven** | the walk did not finish, so the report describes the headings it reached and is silent on the rest while looking complete |
| A run that **records** a width or theme axis and shows it skipped | that dimension capped at 🟡 Thin, and the report names what was skipped | contrast is a property of a theme and tab order a property of a layout. A page walked at one width in one theme was walked once. This fires on a `visual-slop` run listing one width, never on `visual-accessibility` for having no theme row — that sibling records no theme by design, and capping Access for it would cap every conforming report |

These bands are a default. Where the project has its own standard — a WCAG level it has
committed to, a published design language, a brand override the slop run was told about — that
is the project's own standard and it wins. Say in the report which you used, and name any
override: `/visual-slop` records these in its header, and an override read as a finding is a
finding against the brand.

**The WCAG level matters and belongs in the report.** AA and AAA are different questions, and a
🟢 at AA is not a 🟢 at AAA. Name the level every grade was measured at.

**Done when:** both dimensions carry a grade and the numbers behind them, the WCAG level is
named, every brand override is named, and any grade drawn from a project standard rather than
the default band says so.

## 5. Cross-read the signals

Two reports about the same rendered pixels say things neither says alone, and these pairs are
tighter than in the other phases because both dimensions looked at the same screen:

| The pair | What it means |
| --- | --- |
| A P1 barrier on the element carrying the worst stack | the element nobody decided is also the element nobody can operate. One rebuild fixes both, and rebuilding it around what it is for tends to remove the barrier on the way |
| A contrast tell and a contrast barrier on the same text | two laws agreeing about one colour. This is the least arguable finding either report produces — fix once and both move |
| No signature, access Sound | operable and forgettable. Every control reachable, nothing anybody would recognise tomorrow. This is the most common shape and the easiest one to mistake for done |
| Signature Sound, a P1 barrier | somebody decided how this looks and nobody checked who can use it. The bespoke element is usually the one that broke it — a custom control has no built-in semantics, and that is the trade the signature was bought with |
| Barriers concentrated in one flow, tells spread evenly | the barriers are a bug in one place; the tells are a habit everywhere. Different work, and the report should not merge the two lists |
| Both Sound at 1440 light, neither run at 390 or dark | the page was checked once and graded as if it were checked four ways |
| A glowy or low-contrast button in the slop tells, no matching access finding | the accessibility run did not reach that state. Hover and focus styling is where the two reports most often disagree, and a disagreement is a gap in one of them |
| Law coverage 100%, criteria coverage under 80% | the design law was walked end to end and WCAG was not. The weaker number is the verdict |

### If the other phases have reports on disk

Do not grade them. Read them for these pairs only, and label each one as crossing a phase
boundary:

| The pair | What it means |
| --- | --- |
| Green suite, a P1 access barrier (`bdd-report-`, `coverage-report-`) | the tests reach the control by calling it, and a person using a keyboard cannot reach it at all. Covering a control says nothing about operating it |
| Clean static analysis, P1 barriers (`static-analysis-report-`) | the analyzer checks the code, and a barrier is a property of the rendered page. No linter finds a tab order |
| A 🔴 clone family across the component files (`dry-report-`) | the same control copied several times, and a barrier fixed in one copy stays in the others. Check whether the P1 barrier appears in every sibling |
| Readability P1 in the components the barriers sit in (`clean-code-report-`) | the component nobody can follow is the one nobody will fix correctly. The access fix is the reason to do the readability one |

**Done when:** every pair in the first table that both its signals support has been checked,
each one that fires is written up with its two findings and a screenshot link, and any
cross-phase pair that fired is marked as such.

## 6. Give the verdict

One verdict for the interface, by these rules, in this order:

1. Both applicable dimensions unproven → **Unproven**. With two dimensions this is the only
   count that reaches the "two or more" bar, so one unproven and one graded still produces a
   verdict — stated with the missing half named beside it.
2. Otherwise the verdict is the **worse** of the two grades. Never the average.
3. State the count beside it, always: "Thin, 1 of 2 dimensions unproven". Where the project
   renders nothing, there is no verdict at all — say **not applicable**, name the surface that
   is missing, and stop.

**One graded and one unproven is the shape to be most careful with**, because half an assessment
reads like a whole one. "🟢 Sound on access; signature unproven" is not a green interface. Put
the unproven half in the same sentence as the grade, never in a table below it.

Then write the verdict out in two sentences: what the interface is, and the one thing that most
needs attention. Lead with the dimension that set the floor.

**Then answer the two questions a reader actually has, in one line each:**

| Question | Answered by |
| --- | --- |
| **Can everyone use it?** | access. Name the barrier and what it stops somebody doing — "a person using a keyboard cannot leave the checkout modal", not "3 P1 findings" |
| **Would anyone remember it?** | signature. Name what is there instead — "the two-column hero, three icon tiles, pricing trio, gradient CTA. Recolouring it would change nothing" |

A barrier described as a count is a barrier nobody will prioritise. Describe it as the thing a
person cannot do.

Where a previous visual quality report sits beside this one, say which way the verdict moved and
which dimension moved it. Say whether the same pages, widths, and themes were walked: a
signature verdict that improved because a different page was checked is not an improvement.

**A verdict can fall because the walk widened rather than because the interface did.** When the
previous report covered fewer pages, widths, or states, and the new verdict is worse only
because of something the old walk never reached, say so in the same breath.

**Done when:** the verdict follows the three rules, the dimension that set the floor is named,
an unproven half is stated beside the graded one rather than below it, both plain-language
questions are answered, the pages and widths walked are named, the two phases outside this skill
are named as not covered, and a verdict that fell only because the walk widened says so.

## 7. Chart the next moves

Name the starting position, then order the moves.

| Starting position | Test |
| --- | --- |
| **Unwalked** | neither dimension measured on the pages in scope |
| **Thin** | some measured, and one or more grade Thin or Fragile |
| **Walked** | both measured across the pages, widths, themes, and states in scope, neither Fragile |

### From unwalked

Two moves, in this order, and the order never changes:

1. **`/visual-accessibility`** on the flow that carries the money, or the sign-up, or whatever
   the product is for — not the marketing page. Needs a running instance and the `vibium`
   driver, under an hour per page, and what it finds is stopping somebody today.

   **One flow, not the app.** Both siblings are per-page, and a walk of twenty routes produces a
   report nobody reads. The other pages come round next pass.
2. **`/visual-slop` on the same pages.** It fetches the law fresh and walks it point by point,
   so it costs about the same and answers the other half. Same pages is what makes step 5's
   pairs possible — two reports about different screens cross-read into nothing.

Then hand over move 1 alone.

### From thin

Order the individual moves across both reports by these three, in order:

1. **P1 barriers.** Somebody cannot do a thing. Each is a defect, and each has a right answer
   rather than a proposal.
2. **P1 tells** — the ones that read as broken to anybody, slop-aware or not: content hidden
   behind an animation that never fires, an unreadable overlap, a control that cannot be
   distinguished from text. These are defects too, and they sit here rather than with the rest
   of the signature work.
3. **The stacked elements, worst stack first**, and then the signature itself. This is design
   work rather than defect work, and it is proposed rather than prescribed: `/visual-slop` names
   what goes *in*, not just what comes out. A page that has had every tell removed and nothing
   put in its place is still 🔴 — removal alone cannot produce a signature.

**Where a P1 barrier and the worst stack sit on the same element, that element is move 1**, and
the work is one rebuild rather than two fixes. Step 5's first pair exists to find exactly this.

**Fix the shared component, not the page.** A barrier in a `Button` is a barrier on every page
that renders one, and the report should say how many that is:

```sh
git grep -l '<Button' -- '*.tsx' | wc -l
```

### From walked

The siblings' own P1 and P2 lists, merged and ordered by those three rules. Add the gates each
proposed — the accessibility gates in CI, the slop check on any new page or component — because
a walked interface with no gate drifts back fastest of the three phases, since every new feature
ships a new screen.

Add a second: **widen the walk before re-running the same pages.** Two dimensions Sound on three
routes is a smaller claim than it looks.

Close with the pointer to the other two phases: `/code-quality`, `/release-quality`.

**Done when:** the starting position is named, exactly one opening move is named and it is a P1
barrier where one exists or `/visual-accessibility` where nothing is measured, every move is one
thing a person can do, every fix names whether it belongs in a shared component and how many
pages that reaches, signature work reads as a proposal rather than a removal list, and the two
phases outside this skill are named with their commands.

## 8. Write the report

Header: `date '+%Y-%m-%d-%H%M%S'` for the timestamp, `git rev-parse --short HEAD` for the
commit, a note if the working tree is dirty, **and the pages, widths, themes, and states walked**
— a visual verdict without those is a verdict about an unnamed screen.

Write to `<module>/.reports/visual-quality-report-<timestamp>.md`, where `<module>` is the
nearest directory at or above the module assessed holding the project's manifest
(`package.json`, `go.mod`, `pyproject.toml`, `pom.xml`, `Cargo.toml`, `composer.json`,
`Gemfile`, a `*.csproj`). An assessment spanning several modules writes to the repository root.
Create the folder if missing and add `.reports/` to the root `.gitignore` if nothing there covers
it. One file per run; never overwrite an older one.

Every source report is named and linked, with its commit distance — **and every finding that has
a screenshot links to it.** This is the one phase where the evidence is a picture, and a finding
without its picture is the one a reader argues with.

Use the tables in [`report.md`](report.md) — every section of that shape, in that order. The
prose left over is the verdict, the two plain-language answers, and one sentence per cross-read
pair.

Then tell the user four things and stop: the file path, the verdict with the two plain-language
answers, the one next move with what it costs, and that calling `/visual-quality` again
afterwards picks the one after it.

**Done when:** the report sits in the module's `.reports` folder, `.reports/` is git-ignored, no
older report was overwritten, every finding with a screenshot links to it, and it holds every
section of [`report.md`](report.md).
