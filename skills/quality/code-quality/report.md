# Report shape

A TypeScript example. The tables, grades, and dimensions are what transfers — swap in your
own tools and paths. Tables are shown with one or two rows; a real report lists them all.

````markdown
# Code Quality Report

| | |
| --- | --- |
| **Run** | <YYYY-MM-DD HH:MM:SS> |
| **Commit** | `a1b2c3d` (clean) |
| **Scope** | `src/**` — 84 files |
| **Phase** | development — the code and its suite. Not a release verdict |
| **Starting position** | thin — 6 of 6 applicable dimensions measured, 3 of them Fragile |
| **Bands** | project gates where set, defaults otherwise |
| **Previous** | [`code-quality-report-2026-07-23-140218.md`](./code-quality-report-2026-07-23-140218.md) |

## Verdict

# 🔴 Fragile — 0 of 6 applicable dimensions unproven, 1 set aside by choice

The tests reach most of the code and check very little of it: 78% line coverage sits behind
a 61% mutation score, and two survivors were in the refund path when it was last measured —
`refund.ts` has changed since, so that pair needs re-running before it is acted on. Change risk is the more
urgent half — `applyRefund` scores 148.6 and cannot be brought under by testing alone, so
every fix to the refund path lands in a function nobody can safely edit.

Last week's verdict was 🟡 Thin. Test strength set the floor then and change risk sets it now,
on a function that grew by 40 lines in the interim.

**Not covered here.** These seven describe the code and its suite. Nothing above says whether
the deployed API keeps its contract, whether a real database is ever touched, what happens when
it fails, how much load it takes, or what an attacker can reach — run `/release-quality` for
those five. Access and signature need a rendered interface — run `/visual-quality`.

## Dimensions

| Dimension | Relevance | Grade | The numbers | Evidence | Behind HEAD |
| --- | --- | --- | --- | --- | --- |
| Verified behaviour | applies | 🟡 Thin | lines 78.4%, branches 60.8%, 3 files at 0% | [coverage](./coverage-report-2026-07-30-142205.md) | 0 commits — current |
| Test strength | applies | 🔴 Fragile on 37 of 40 files | score 61.4%, 12 survivors, 3 no-coverage | [mutation](./mutation-report-2026-07-30-091412.md) | 2 commits — partial |
| Change risk | applies | 🔴 Fragile | 9 functions over 30, 1 needs splitting, worst `applyRefund` at 148.6 | [CRAP](./crap-report-2026-07-30-160244.md) | 0 commits |
| Specified behaviour | by choice | — | — | none | — |
| Construction | applies | 🔴 Fragile | 14 bug — 3 in the refund path — 61 risk findings | [static analysis](./static-analysis-report-2026-07-30-153001.md) | 0 commits |
| Single source | applies | 🟡 Thin | 2 🟠 families, 0 🔴, 14 files unsupported (`.sql`) | [DRY](./dry-report-2026-07-30-162811.md) | 0 commits |
| Readability | applies | 🟡 Thin | 0 P1, 36 P2, worst smell 🌀 needless complexity (18) | [clean code](./clean-code-report-2026-07-30-171522.md) | 0 commits |

Test strength, change risk, and construction are jointly at the floor, so the verdict is
🔴 Fragile.

The mutation report is **partial**: `refund.ts`, `ledger.ts`, and `tax.ts` changed since it
ran, so its 61.4% describes the other 37 files. Re-running it needs those three files only,
not the module.

**One of those three is `refund.ts`, and the refund path is what set the floor.** So the two
survivors named in the verdict are a lead, not evidence — they were found in a version of that
file which no longer exists, and nothing here says whether the edit killed them or added more.
A partial report that still covers everything except the code somebody is editing today is the
weakest evidence in this table, whatever its percentage.

## What is not graded here

| Dimension | Relevance | Why | Decision |
| --- | --- | --- | --- |
| Specified behaviour | by choice | no `.feature` files; the team was offered `/to-bdd` and declined a written spec | their decision, recorded on 2026-07-28. Not a gap in the code, and not counted against the verdict. Having no requirements written down would not have put it on this table — `/to-bdd` drafts those |

## What the signals say together

| The pair | The numbers | What it means |
| --- | --- | --- |
| High coverage, low mutation score | 78.4% covered, 61.4% killed | the tests run the code and check about six lines in ten of it |
| 🔴 CRAP functions and P1 rigidity in the same functions | `applyRefund` at 148.6, and 4 of the 12 rigidity breaks are in it | one split fixes both. Neither dimension moves until it happens |
| Functions over 30 in the same files as the P1 bugs | 6 of the 9 sit in `src/billing/`, as do 3 of the 14 bugs | two independent signals agree on one folder. That is where the next defect comes from |
| Green suite, breaking contract drift *(crosses into `/release-quality`)* | 412 tests green, `GET /orders/{id}` returns `total` as a string | the suite checks the code against itself. The promise to callers broke and nothing in CI noticed. Graded there, not here |

## Dimensions to cover next

| Dimension | Relevance | Run | Costs | What it would tell you |
| --- | --- | --- | --- | --- |
| Specified behaviour | by choice | `/to-bdd`, `/wire-bdd`, `/run-bdd` | an afternoon or more | whether the code does what it is supposed to, rather than what it happens to do. Nothing else here asks that. No requirements are written down, which is what `/to-bdd` mines a draft for; nothing is wrong with the code for lacking it |

## The next moves

**Start here:** split `applyRefund`. It is the 🔴 CRAP function and the home of 4 of the 12
rigidity breaks, and no amount of testing brings it under 30 while it stays one function.

The rest of the list keeps. Run `/code-quality` again when that one is done and it will name
the move after it.

Thin start, so the pair of signals decides the order. Strength before breadth: coverage is
78% and the mutation score is 61%, so the tests already reach the code and adding more of the
same would move the wrong number.

| # | Do this | Why it is here | Costs | Command |
| --- | --- | --- | --- | --- |
| 1 | Split `applyRefund` into the three decisions it makes | 🔴 on change risk and the worst readability cluster in one function | a day | — |
| 2 | Re-run mutation on the 3 changed files, then kill what survives | the refund-path survivors were found before `refund.ts` changed, so the current count is unknown | minutes to re-run, half a day to kill | `/mutation-test` |

## Next phase

| Phase | Dimensions | Command |
| --- | --- | --- |
| Release | promised behaviour, proven seams, resilience, headroom, exposure | `/release-quality` |
| Visual | access, signature | `/visual-quality` |
````

Drop any empty section, and lead the body with the verdict. The dimension that set the floor
is named in the verdict and appears first among the moves that are not outright defects.

A **bare** codebase's report is the same shape with two differences: the verdict is
"Unproven — untested", and the moves table holds the step 7 ladder in that order rather than a
merge of sibling lists, with move 6 naming the actual high-churn modules and their commit
counts. It closes on the two things step 7 says a bare plan must state: that this is a body of
work rather than an afternoon, and that all eight moves still leave the release and visual
phases ungraded.
