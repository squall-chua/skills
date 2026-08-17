---
name: clean-code
description: >
  Read the paths you name against the clean code rules, rank each break by the smell it
  causes, and report it with a fix diff.
disable-model-invocation: true
---

A linter checks the code against a grammar. This skill checks it against a **reader**. No
tool can tell you a function does two things, that a name lies about what it holds, or that
a comment repeats the line under it.

The danger is the mirror of a linter's. A linter buries you in 4,000 findings; a rule list
invites you to flag every 30-line function and hand over a page of taste. The cut is the
**smell**: a break no reader ever suffers for is not a finding. Step 3 records every break
it sees, cut or not; step 4 applies the six smells and counts what it dropped.

## This skill reports

Steps 1 to 4 produce a report and change no code. That report is the whole deliverable.

Steps 5 and 6 run only on a **fix signal**: "fix them", "apply the fixes", "clean it up",
"go ahead". The step 4 report is the *before*, so it is written on a fix run too, and
written before any code is touched.

## 1. Pin the scope

The paths the user named are the scope, exactly as given. Expand each to its file list and
count it, so the report can say what was read.

Named no paths? Take the files changed against the default branch, and say in the report
that this was your choice. A repo may use `master` or `develop`, and `origin/HEAD` is often
absent:

```sh
base=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null)
if [ -z "$base" ]; then
  for c in origin/main origin/master origin/develop main master; do
    git rev-parse --verify --quiet "$c" >/dev/null && base=$c && break
  done
fi
[ -n "$base" ] && git diff --name-only "$base"...HEAD
```

Two empties mean different things and neither is "nothing changed". An empty `$base` is no
branch to compare against: say so and ask. An empty *diff* against a good base is a branch
already merged, or work still in the working tree — the common case when somebody types the
skill's name on `main` after an afternoon's editing. Fall back there to `git diff
--name-only HEAD` plus `git status --porcelain` for untracked files, and where that is empty
too, say the tree is clean and ask.

Then run the test suite. It gates the *fixing*, not the reading:

| What you find | What it means for this run |
| --- | --- |
| **Green suite** | everything below is available, including the fix run |
| **Red suite** | read anyway — the findings stand alone. Record the failures; a fix run is then limited to what a passing build can verify, since a red suite cannot tell you a split was safe |
| **No suite at all** | read anyway and say so. A fix run is limited the same way |

**Done when:** you have the explicit file list, its count, the fact that the scope came from
a default where it did, and the suite's state written down for step 5.

## 2. Learn the project's own conventions first

The first clean code rule is *follow standard conventions*, and the project's conventions
are the standard here. Read the style guide, the `CONTRIBUTING` file, the linter and
formatter configs, and — where those are silent — the shape the surrounding code keeps.

**The project's convention beats the rule list.** A codebase that names its interfaces
`IThing` everywhere is consistent, and one file changed to `Thing` is the finding, not the
other forty. Where a rule contradicts a written project convention, the convention wins and
the rule goes in the report as a note.

Then strike these off. They belong to tools the project already runs:

| Owned by | Rules you leave alone |
| --- | --- |
| **Formatter** | line length, horizontal alignment, indentation |
| **Linter** | dead code, unused variables, import order, naming case |
| **`/static-analysis`** | type errors, real bugs, security findings |
| **`/dry-test`** | duplication across files — say "see `/dry-test`" and move on |

**Done when:** the project's conventions are written down, and the rules owned by its tools
are struck off the list you read against.

## 3. Read the code against the rules

Read every file in the scope against all 56 rules.

| Group | Rule | The break to look for |
| --- | --- | --- |
| General | Follow standard conventions | this file does it differently from its neighbours |
| General | Keep it simple | a simpler shape does the same work |
| General | Boy scout rule | the change made the file worse than it found it |
| General | Always find the root cause | a symptom patched at the call site, cause still there |
| Design | Keep configurable data high | a constant buried deep, that a caller should pass in |
| Design | Prefer polymorphism to `if`/`switch` | the same type test repeated in several places |
| Design | Separate multi-threading code | locks and business logic in one function |
| Design | Prevent over-configurability | a setting nobody ever sets to a second value |
| Design | Use dependency injection | a collaborator built inside the thing that uses it |
| Design | Follow the Law of Demeter | `a.getB().getC().doThing()` — reaching through a neighbour |
| Understandability | Be consistent | two ways of doing the same thing in one codebase |
| Understandability | Use explanatory variables | a long condition or expression with no name on it |
| Understandability | Encapsulate boundary conditions | `+ 1` and `- 1` spread over several lines |
| Understandability | Prefer value objects to primitives | a `string` that is really an email, an id, or a currency |
| Understandability | Avoid logical dependency | a method that only works if another ran first |
| Understandability | Avoid negative conditionals | `if (!isNotReady)` — a test that has to be unpicked |
| Names | Descriptive and unambiguous | `data`, `handle`, `process`, `tmp`, `mgr` |
| Names | Meaningful distinction | `account` beside `accountInfo` beside `accountData` |
| Names | Pronounceable | `dtRcrd102` |
| Names | Searchable | a name so short or so common that grep is useless |
| Names | Named constants over magic numbers | a bare `86400` or `0.15` in the logic |
| Names | No encodings | `strName`, `m_count`, `IShape` — type or scope on the front |
| Functions | Small | you cannot hold the whole function in your head at once |
| Functions | Do one thing | the name needs an "and" to be honest |
| Functions | Descriptive names | the name says less than the body does |
| Functions | Fewer arguments | four or more, or two of the same type next to each other |
| Functions | No side effects | the name promises a read and the body writes |
| Functions | No flag arguments | `render(true)` — the flag is two functions in a coat |
| Comments | Explain yourself in code | a comment that a better name would have replaced |
| Comments | Not redundant | the comment repeats the line below it |
| Comments | No obvious noise | `// constructor`, `// increment i` |
| Comments | No closing brace comments | `} // end for` |
| Comments | No commented-out code | dead code kept in a comment. Delete it; git has it |
| Comments | Explain intent | *missing* where the code says what but never why |
| Comments | Clarify code | *missing* beside an expression the reader cannot decode |
| Comments | Warn of consequences | *missing* beside a slow, unsafe, or order-dependent call |
| Structure | Separate concepts vertically | two unrelated ideas run together with no blank line |
| Structure | Related code vertically dense | one idea broken up by blank lines and stray comments |
| Structure | Declare variables close to use | declared at the top, used eighty lines down |
| Structure | Dependent functions close | the callee sits in another region of the file |
| Structure | Similar functions close | siblings scattered through the file |
| Structure | Functions in downward direction | you must scroll up to read what comes next |
| Objects | Hide internal structure | a getter that hands out the live internal list |
| Objects | Prefer data structures | a plain record dressed up in behaviour it does not need |
| Objects | Avoid hybrids | half object, half data — public fields plus real behaviour |
| Objects | Small | the class does not fit on a screen |
| Objects | Do one thing | the class name needs an "and", or ends in `Manager` or `Util` |
| Objects | Few instance variables | fields that only some methods ever touch |
| Objects | Base knows nothing of derived | a parent that names or type-tests its children |
| Objects | Many functions over a selector | `doThing(mode)` switching on `mode` inside |
| Objects | Non-static over static | a static method that should have belonged to an instance |
| Tests | One assert per test | a test asserting several unrelated things |
| Tests | Readable | you cannot tell what the test proves from its name and body |
| Tests | Fast | a unit test that sleeps, or reaches the network or the disk |
| Tests | Independent | it passes alone but fails when the order changes |
| Tests | Repeatable | it depends on the clock, a random value, or a shared database |

For each break, record the file, the line, the rule, and one sentence on **what a reader
pays for it**. Not the rule text — the cost. "`apply()` validates, charges, and writes the
audit row, so a change to the audit format means re-reading the charging logic" is useful;
"function too long" is the rule copied out.

**Done when:** every file in the scope has been read, every break carries its file, line,
rule and one-sentence cost, and every rule struck off in step 2 stayed off.

## 4. Rank by smell, then write the report

A break with no smell behind it is taste, and taste does not go in the report. Give each one
the smell it causes:

| Smell | What the reader or the next change pays |
| --- | --- |
| 🧱 **Rigidity** | a small change forces a cascade of other changes |
| 💥 **Fragility** | one change breaks things in places that look unrelated |
| 📦 **Immobility** | the part cannot be reused elsewhere without dragging its world along |
| 🌀 **Needless complexity** | structure serving a need the project does not have |
| 🔁 **Needless repetition** | the same knowledge written out more than once |
| 🌫️ **Opacity** | the code is simply hard to understand |

Then rank:

- **P1** — rigidity or fragility. Also anything in code that moves money, checks
  permissions, or writes data.
- **P2** — immobility, needless complexity, or needless repetition. Also opacity in a file
  changed 5 or more times in 6 months:
  ```sh
  git log --since='6 months ago' --name-only --format= -- <path> | grep . | sort | uniq -c | sort -rn
  ```
  The `grep .` matters: `--name-only` prints a blank line between commits, and without it
  the blank sorts to the top as your busiest file.
- **P3** — opacity anywhere else.
- **Dropped** — no smell. Count these and give the number, so the reader knows what you
  chose not to say. Never list them.

Write the fix as a diff for every P1 and P2. A finding with no diff is a complaint.

Header: the timestamp from `date '+%Y-%m-%d-%H%M%S'`, the commit from `git rev-parse --short
HEAD`, and a note if the working tree is dirty — the run then covers code that commit does
not hold.

Write to `<module>/.reports/clean-code-report-<timestamp>.md`. `<module>` is the nearest
directory at or above the scope holding the project's manifest (`package.json`, `go.mod`,
`pyproject.toml`, `pom.xml`, `Cargo.toml`, `composer.json`, `Gemfile`, `*.csproj`); a scope
spanning several writes to the repository root. Create the folder if missing, add
`.reports/` to the root `.gitignore` if nothing there covers it, one file per run, never
overwrite an older one.

Write this report on a fix run too, and *before* you touch any code. This is the before;
without it there is nothing to compare against.

Then tell the user the file path, the P1 count, and the one finding to fix first. On a
report-only run, say the report is all this run changed, so they can ask for the fixes next.

**Done when:** the report sits in the module's `.reports` folder, `.reports/` is git-ignored,
no older report was overwritten, every P1 and P2 carries its smell, its cost sentence and a
fix diff, and the dropped count is stated.

## 5. Apply the fixes — on a fix signal

Without the signal the work finished at step 4. Read the suite's state from step 1 first:

| Suite state | How far the fixing goes |
| --- | --- |
| **Green** | everything below |
| **Red or absent** | only renames and comment edits, verified by a passing build. Splits, extractions and signature changes wait, because nothing here can say the behaviour survived. Say plainly which fixes you held back and why |

With a green suite, work P1 first, then P2, one finding at a time: apply the diff from step
4, then run the suite and confirm green. With no suite, confirm the build still passes —
that is the whole verification available, so keep each such fix small enough to read.

Keep pure renames in their own commit. A rename touching forty files mixed with six
considered splits is a diff nobody can review.

**Every fix keeps the behaviour.** This skill changes how code reads, never what it does. A
fix that needs the behaviour to change is a bug report — write it up and move on.

**Done when:** every P1 and P2 finding from step 4 is one of four things — fixed with the
suite green where one exists, raised as a bug report, deferred with a stated reason, or held
back because the suite was red or absent. None are simply unmentioned.

## 6. Write the after report — on a fix signal

Re-read the same scope. Fresh timestamp, second file in the same `.reports` folder; the step
4 report stays untouched, so anyone can read the before for themselves.

Lead the body with a "What moved" section naming the step 4 file, and give each of these its
own table:

- findings before and after, by smell and by bucket;
- what happened to them — fixed, raised, deferred, held back, still open;
- which files cleared and which did not move;
- any break the fixes introduced. A fix that breaks another rule is the first thing the
  reader needs.

Then tell the user both file paths, the two P1 counts, and what is still open.

**Done when:** both reports sit side by side, the after report names the before file and
states the change per smell, every P1 and P2 finding from step 4 appears with its outcome,
and the build is recorded passing at the end — with the suite green too, where step 1 found
a green one.

---

# Report shape

A TypeScript after-report. The tables, columns and smells are what transfers — swap in your
own paths and rules. Every table is shown with one data row; a real report lists them all.

````markdown
# Clean Code Report

| | |
| --- | --- |
| **Run** | <YYYY-MM-DD HH:MM:SS> |
| **Scope** | `src/domain/`, `src/http/` — 46 files (as asked) |
| **Commit** | `<short sha>` (dirty working tree) |
| **Suite** | `pnpm test` — 412 passed, 0 failed |
| **Conventions read** | `CONTRIBUTING.md`, `eslint.config.js`, `.prettierrc` |
| **Before** | [`clean-code-report-2026-08-10-091412.md`](./clean-code-report-2026-08-10-091412.md) |

## What moved

| Outcome | P1 | P2 | P3 |
| --- | --- | --- | --- |
| 🟢 Fixed | 11 | 27 | — |
| 🔧 Raised as a bug report | 0 | 1 | — |
| ⏸️ Deferred | 0 | 3 | — |
| 🔴 Still open | 1 | 5 | 26 |
| **Total before** | **12** | **36** | **26** |

P3 has no outcome rows: fix diffs are written for P1 and P2 only, so every P3 finding is
still open by design. Files cleared: `src/domain/refunds/apply.ts` 14 → 0. Did not move:
`src/http/legacy.ts`, 9. **Breaks introduced by the fixes:** none. **Build and suite:** green.

## Totals

| Smell | P1 | P2 | P3 | Before | After |
| --- | --- | --- | --- | --- | --- |
| 🧱 Rigidity | 9 | 0 | 0 | 9 | **1** |
| 💥 Fragility | 3 | 0 | 0 | 3 | 0 |
| 📦 Immobility | 0 | 4 | 0 | 4 | 2 |
| 🌀 Needless complexity | 0 | 18 | 0 | 18 | 4 |
| 🔁 Needless repetition | 0 | 6 | 0 | 6 | 3 |
| 🌫️ Opacity | 0 | 8 | 26 | 34 | 26 |
| **Total** | **12** | **36** | **26** | **74** | **36** |

31 further breaks carried no smell and were dropped. Duplication across files is not counted
here — see `/dry-test`.

## By rule — most broken first

| Rule | Group | Breaks | Files | Worst smell |
| --- | --- | --- | --- | --- |
| Do one thing | Functions | 14 | 11 | 🧱 rigidity |

## By file — worst first

| File | P1 | P2 | P3 | Churn 6mo | Worst finding |
| --- | --- | --- | --- | --- | --- |
| `src/domain/refunds/apply.ts` | 5 | 8 | 1 | 11 | 🧱 Functions · do one thing:44 |

Showing the 20 worst of 46 files with a finding.

## 🔴 P1 — fix these first

### 1. `src/domain/refunds/apply.ts:44` — Functions · do one thing

| | |
| --- | --- |
| **Smell** | 🧱 rigidity |
| **Churn** | 11 commits in 6 months |
| **Cost** | `apply()` validates the request, charges the card, and writes the audit row. Changing the audit format means reading and re-testing the charging logic, so every audit change is a payments change |
| **Outcome** | 🟢 fixed |

```diff
-  if (!req.orderId) throw new BadRequest()
+  validate(req)
   const charge = await gateway.refund(req.orderId, req.amount)
-  await db.audit.insert({ kind: 'refund', at: Date.now(), charge })
+  await recordRefund(charge)
```

One such block per P1 finding: the table, then the diff.

## 🟠 P2 — worth a person's time

| File · line | Rule | Smell | Churn | Cost | Fix | Outcome |
| --- | --- | --- | --- | --- | --- | --- |
| `src/domain/pricing/tier.ts:61` | Design · prefer polymorphism | 🌀 complexity | 7 | the same `switch (tier)` appears in four files, so a new tier means finding all four | one `Tier` interface, one class per tier | 🟢 fixed |

## ⚪ P3 — the rest

| Rule | Group | Breaks | Files |
| --- | --- | --- | --- |
| Use explanatory variables | Understandability | 12 | 9 |

26 findings, not listed one by one. All are 🌫️ opacity in files with low churn.

## Notes — rule against convention

| Rule | What the project does | Where it is written |
| --- | --- | --- |
| Names · no encodings | interfaces are prefixed `I` throughout | `CONTRIBUTING.md`, "Naming" |

## Findings for the code

| File · line | Finding | Suggested action |
| --- | --- | --- |
| `src/domain/refunds/apply.ts:52` | the audit row is written before the charge is confirmed | behaviour change — raised, not fixed here |
````

Every finding appears in exactly one section. Drop any empty section, and lead the body with
P1.

The before report is the same shape, shorter: no "Before" row, no "What moved", no "After"
column, and no "Outcome" rows.
