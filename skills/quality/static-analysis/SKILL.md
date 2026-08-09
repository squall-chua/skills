---
name: static-analysis
description: >
  Run the type checker, linter, and dead code finder over the paths you name, cut the
  noise, and report each finding with a fix diff.
disable-model-invocation: true
---

A static analyzer reads the code without running it, so it finds what tests never
reach — the branch nobody takes, the error nobody handles, the export nothing imports.
It also finds **noise**: naming opinions, rules the team never agreed to,
warnings the analyzer is wrong about. A run that hands over 4,000 findings has said
nothing. Separating the two is the whole job.

## This skill reports

Steps 1 to 7 produce a report and change no code. That report is the whole deliverable.

Steps 8 and 9 run only on a **fix signal**: "fix them", "apply the fixes", "clean it
up", "go ahead". The step 7 report is the *before*, so it is written on a fix run too,
and written before any code is touched.

## 1. Pin the scope

The paths the user named are the scope, exactly as given. Expand each to its file list
and count it, so the report can say what was read.

Named no paths? Take the files changed against the default branch, and say in the report
that this was your choice. Discover the branch — a repo may use `master` or `develop`,
and `origin/HEAD` is often absent:

```sh
base=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null)
if [ -z "$base" ]; then
  for c in origin/main origin/master origin/develop main master; do
    git rev-parse --verify --quiet "$c" >/dev/null && base=$c && break
  done
fi
[ -n "$base" ] && git diff --name-only "$base"...HEAD
```

Three details earn their place:

- The three-dot form already diffs from the merge base, so a separate `git merge-base`
  call is dead work.
- `git rev-parse --verify --quiet` prints nothing on a missing ref, where `--abbrev-ref
  origin/HEAD` echoes `origin/HEAD` to stdout and hands you a value that looks valid and
  diffs against nothing.
- An empty `$base` means there is no branch to compare against. Say so and ask for the
  scope, because a silent empty diff reads as "nothing changed".

Analyzers also report outside the scope — a type error in a file yours imports, a rule
firing project-wide. Count those, say how many, leave them out of triage.

**Done when:** you have the explicit file list, its count, and — where the scope came
from a default — that fact written down.

## 2. Check the tree builds

Build or type-check the project. Record the command and the result.

An analyzer that cannot resolve an import gives up on the file and reports what it
half-understood, so a broken build turns into a page of findings that vanish once it is
fixed. **A broken build is where this skill stops** — report it as the finding, because
nothing downstream can be trusted.

Then find the test suite and run it. The suite gates the *fixing*, not the analysis:

| What you find | What it means for this run |
| --- | --- |
| **Green suite** | everything below is available, including the fix run |
| **Red suite** | analyse anyway — the findings stand alone, and one may be why the suite is red. Record the failures; a fix signal is blocked until green, since a red suite cannot tell you an autofix was safe |
| **No suite at all** | analyse anyway and say so. This is the one signal that works on untested code, and often the only evidence a bare codebase has. A fix run is then limited to changes the analyzer itself can verify |

**Done when:** the build passes with its command written down, the suite has been run or
its absence established, and the suite's state is recorded for step 8.

## 3. Pick the analyzers and read the project's rules

Three kinds of tool answer three questions; running one answers a third:

| Kind | What it finds |
| --- | --- |
| **Type checker** | the code contradicts itself — wrong argument, missing case, impossible narrowing |
| **Linter / bug finder** | the code does other than it says — ignored return, unreachable branch, resource leak |
| **Dead code finder** | exports, files, and dependencies nothing reaches |

Security sits outside this run: ranking a vulnerability needs the dependency tree, the git
history, and a live target — evidence a code read does not hold. Where the project's own
config emits a security finding anyway, step 5 records and passes it on.

Prefer the tools the project already has, in its configs and CI. Fill gaps from here:

| Language | Lint / bug | Types | Dead code |
| --- | --- | --- | --- |
| JavaScript / TypeScript | ESLint, Biome | `tsc --noEmit` | knip |
| Python | Ruff, pylint | mypy, pyright | vulture |
| Go | `go vet`, staticcheck, golangci-lint | compiler | `deadcode` |
| Java / Kotlin | SpotBugs, PMD, Error Prone, detekt | compiler | — |
| C# / .NET | Roslyn analyzers, SonarAnalyzer | compiler | — |
| Rust | `cargo clippy` | compiler | `cargo-udeps` |
| PHP | PHPStan, Psalm | PHPStan, Psalm | — |
| Ruby | RuboCop | Sorbet, Steep | — |
| Swift | SwiftLint | compiler | periphery |
| C / C++ | clang-tidy, cppcheck | compiler | — |

### Nothing installed?

Look before you install: the manifest and its lockfile, the CI workflows, the project's own
config files, and the binary on `PATH`. A tool declared in the manifest but missing from the
environment needs the project's own install command, not a new dependency.

Where the project genuinely has none, put all three proposals to the user in one message —
per kind: the tool and why it fits this project, the exact install command, the config file
with its contents, the command this skill will then run, and what it costs in download size
and first-run time — and wait for the go-ahead. A new dependency changes the manifest and the
lockfile, which is the user's call, and one message lets them take some kinds and leave
others. Install exactly what they accepted, leave the config in the repo, and commit nothing.
Record every kind they decline as a gap in the report rather than a clean result, since a
kind nobody ran found nothing by definition.

Read each tool's own docs for current flags — names drift between versions, and a config
written from memory fails in ways that look like broken code.

**The project's config is the project's decision.** Where one exists, run with it and
leave it alone; a run that overrides it reports on a codebase nobody is writing.

Where none exists, this single choice decides whether the report is worth reading: turn
on correctness and bug-finding rules, leave style rules off. Style belongs to a formatter,
and 3,000 quote-mark complaints bury the null dereference on page 40. Write down the
rule set you chose and why.

Ask each tool for machine-readable output — SARIF, else JSON or checkstyle XML — written
to a file. You read that, not the terminal.

**Done when:** each of the three kinds is running, or written down as unavailable for this
language or declined by the user; the rule set is the project's config or a recorded choice
of your own; and every tool writes a machine-readable file.

## 4. Run and capture

Run each tool over the scope. Capture stdout, stderr, the exit code, and the report file.

A tool exiting non-zero because it *found* something worked. One exiting non-zero because
it *crashed* did not, and its findings are missing rather than absent. Tell those apart by
reading the error, and record which tools completed.

**Done when:** every tool has a machine-readable file or a recorded reason it could not
run, and each finding carries a file, a line, a rule ID, and its tool.

## 5. Triage every finding

Group by **rule**, not by line. One rule firing 200 times is one decision, usually fixed
once in a config or a codemod; a list of 200 lines hides that.

Then categorise:

| Category | What it means |
| --- | --- |
| 🐛 **Bug** | already does the wrong thing — null dereference, wrong comparison, unreachable branch, leaked handle |
| 🔒 **Security** | injection, committed secret, weak crypto, unsafe deserialization. Recorded and passed on — see below |
| ⚠️ **Correctness risk** | right today, wrong on a plausible input — ignored error, swallowed exception, missing default |
| 🧹 **Maintainability** | complexity, duplication, dead code. Real, not urgent |
| 🎨 **Style** | formatting, naming, import order. A formatter's job |
| ⚪ **False positive** | the analyzer is wrong here. Needs a written argument, not a hunch |

A tool's severity is its opinion about a rule in general, not about your code — every
linter calls everything an error. Re-rank by what the code decides:

- **P1** — any bug finding. Also anything in code that moves money, checks permissions, or
  writes data.
- **P2** — a correctness risk, or maintainability in a file changed 5+ times in 6 months:
  ```sh
  git log --since='6 months ago' --name-only --format= -- <path> | grep . | sort | uniq -c | sort -rn
  ```
  The `grep .` matters: `--name-only` prints a blank line between commits, and without it
  the blank sorts to the top as your busiest file.
- **P3** — everything else, style included.

A security finding takes no bucket. It goes to its own section of the report with its rule,
its file and line, and the tool that raised it, and is handed on for a run that can weigh it
against the dependency tree, the history, and a live target.

For every P1 and P2, read the code and write one sentence naming the **consequence**, not
the rule text. "A refund with no `orderId` throws before the guard runs, so the caller
gets a 500 rather than a validation error" is useful; "`no-unsafe-member-access` on line
44" is the tool's output copied out.

Write the fix as a diff and note whether the tool can apply it itself. Knowing 480 of 530
findings fix themselves changes what a person decides to do.

A false positive gets its argument written down and an inline suppression carrying that
reason — never a rule switched off project-wide. One suppression explains one line; a
disabled rule silently covers every line you have not read.

**Done when:** every finding carries a category, and a bucket unless it is security; every
security finding is listed with its rule, file, line, and tool; every P1 and P2 also carries
its one-sentence consequence, a fix diff, and an autofix yes or no; and every false positive
carries its written argument.

## 6. Work out the baseline

Recommend a **baseline**: today's findings recorded and grandfathered, CI failing on
anything new. Most tools support it directly — ESLint's `--suppressions`, PHPStan's and
Psalm's baseline files, SpotBugs' exclude filter, `golangci-lint --new-from-rev`. Where a
tool has none, run it over the changed lines only.

A baseline is what makes a large existing codebase gateable. A rule turned on across
3,000 old findings fails every build until someone turns it off, and then there is no gate
at all.

Also recommend the config changes the triage exposed: a rule that only made noise and
should come off, a rule that caught a real bug and should be promoted to error, a whole
category the project is not running.

Both go in the report as the exact file and the exact setting. Config and CI files are
edited only on a fix signal.

**Done when:** the report carries the recommended baseline, the tool it belongs to, and
every recommended rule change with a reason drawn from the findings.

## 7. Write the report

Header: the timestamp from `date '+%Y-%m-%d-%H%M%S'`, the commit from `git rev-parse
--short HEAD`, and a note if the working tree is dirty — the run then covers code that
commit does not hold.

Write to `<module>/.reports/static-analysis-report-<timestamp>.md`. `<module>` is the
nearest directory at or above the scope holding the project's manifest (`package.json`,
`go.mod`, `pyproject.toml`, `pom.xml`, `Cargo.toml`, `composer.json`, `Gemfile`,
`*.csproj`); a scope spanning several writes to the repository root. Create the folder if
missing, add `.reports/` to the root `.gitignore` if nothing there covers it, one file per
run, never overwrite an older one.

Write this report on a fix run too, and *before* you touch any code. This is the before;
without it there is nothing to compare against, and a count you remember is not a count
you can show.

Use the shape below and put the data in tables — every count, path, rule ID, category, and
bucket belongs in a cell where it can be scanned. The prose left over is the
one-sentence consequence, the false positive argument, and a short note under a table
saying what the numbers mean.

Then tell the user the file path, the P1 count, and the one finding to fix first. On a
report-only run, say the report is all this run changed, so they can ask for the fixes
next.

**Done when:** the report sits in the module's `.reports` folder, `.reports/` is
git-ignored, no older report was overwritten, and it holds every section of the shape below
— including every P1 and P2 finding with its consequence, fix diff and autofix flag, and the
baseline recommendation.

## 8. Apply the fixes — on a fix signal

Without the signal the work finished at step 7. Read the suite's state from step 2 first,
because it decides how far a fix run can go:

| Suite state | How far the fixing goes |
| --- | --- |
| **Green** | everything below |
| **Red or absent** | only what you can verify without it — the analyzer re-run showing the finding gone, and the build still passing. Autofix passes wait, since nothing here can say a mechanical edit kept the behaviour. Say plainly which fixes you held back and why |

With a green suite, take the autofixable findings first, one pass per tool: they are
mechanical and they are the bulk. Then run the build and the full suite from step 2 — an
autofix can change behaviour, as when a rule drops an "unused" call along with its side
effect. Keep that pass in its own commit; a hundred mechanical edits mixed with six
considered ones is a diff nobody can review.

Then work the hand fixes, P1 first, then P2, one at a time:

1. Apply the diff from step 5.
2. Re-run the tool over that file. The finding is gone and no new one replaced it.
3. Run the suite and confirm green. With no suite, confirm the build still passes — that
   is the whole verification available, so keep each such fix small enough to read.

Send style findings to the formatter, as its own commit. Then apply the baseline and rule
changes from step 6.

**Fix the finding, not the report.** A count reduced by switching a rule off, widening an
ignore file, or a blanket file-level suppression is a number that lies to the next reader.
Where the only way to clear a finding is to change what the code does, that finding is a
bug report — write it up and move on.

**Done when:** every P1 and P2 finding from step 5 is one of four things — fixed with the
build passing and the suite green where one exists, suppressed inline with its argument,
raised as a bug report, or deferred with a stated reason. Where the suite was red or
absent, the fixes held back are listed with that reason. None are simply unmentioned.

## 9. Write the after report — on a fix signal

Re-run every tool from step 3 over the same scope. Fresh timestamp, second file in the
same `.reports` folder; the step 7 report stays untouched, so anyone can read the before
for themselves.

Lead the body with a "What moved" section naming the step 7 file, and give each of these
its own table:

- findings before and after, by category and by bucket;
- what happened to them — fixed, suppressed, raised, deferred, still open;
- which modules cleared and which did not move;
- any finding that appeared during the fix run. A fix that raises a new finding is the
  first thing the reader needs.

Then tell the user both file paths, the two P1 counts, and what is still open.

**Done when:** both reports sit side by side, the after report names the before file and
states the change per category, every P1 and P2 finding from step 7 appears with its
outcome, and the build and suite are recorded green at the end.

---

# Report shape

A TypeScript after-report. The tables, columns, and categories are what transfers — swap in
your own tools, paths, and rule IDs. Every table here is shown with one data row; a real
report lists them all.

````markdown
# Static Analysis Report

| | |
| --- | --- |
| **Run** | <YYYY-MM-DD HH:MM:SS> |
| **Scope** | `src/domain/`, `src/http/` — 46 files (as asked) |
| **Commit** | `<short sha>` (dirty working tree) |
| **Build** | `pnpm build` — passed, 22s |
| **Suite** | `pnpm test` — 412 passed, 0 failed, 3 skipped |
| **Before** | [`static-analysis-report-2026-07-30-091412.md`](./static-analysis-report-2026-07-30-091412.md) |

## What moved

Against the before report, taken before any code was touched.

| Category | Before | After | Change |
| --- | --- | --- | --- |
| 🐛 Bug | 14 | **0** | **−14** |
| **Total** | **530** | **115** | **−415** |

| Outcome | P1 | P2 | P3 |
| --- | --- | --- | --- |
| 🟢 Fixed | 15 | 49 | 356 |
| 🔇 Suppressed with a reason | 2 | 4 | 0 |
| 🔧 Raised as a bug report | 0 | 1 | 0 |
| ⏸️ Deferred | 0 | 3 | 0 |
| 🔴 Still open | 1 | 12 | 96 |
| **Total before** | **18** | **69** | **452** |

Modules cleared: `src/domain/refunds` 96 → 4. Did not move: `src/http`, 88.
**New findings raised by the fixes:** none. **Build and suite:** green.

## Totals

| Category | P1 | P2 | P3 | Total | Autofixable |
| --- | --- | --- | --- | --- | --- |
| 🐛 Bug | 14 | 0 | 0 | 14 | 2 |
| ⚠️ Correctness risk | 1 | 60 | 0 | 61 | 18 |
| 🧹 Maintainability | 0 | 9 | 119 | 128 | 31 |
| 🎨 Style | 0 | 0 | 324 | 324 | 324 |
| **Total** | **15** | **69** | **443** | **527** | **375** |

375 of 527 fix themselves. The 152 left need a person. Three security findings sit outside
this table, below.

## By tool

| Tool | Version | Rules | Findings | Ran |
| --- | --- | --- | --- | --- |
| ESLint | 9.12.0 | 218 (project config) | 498 | ✅ |
| knip | 5.30.2 | — | 0 | ❌ crashed on a circular import — findings missing, not absent |

Outside the scope: 61 findings, not triaged.

## By rule — most fired first

| Rule | Tool | Category | Count | Files | Autofix |
| --- | --- | --- | --- | --- | --- |
| `quotes` | ESLint | 🎨 style | 291 | 44 | yes |

## By module

| Module | Files | P1 | P2 | P3 | Total | Worst rule |
| --- | --- | --- | --- | --- | --- | --- |
| `src/domain/refunds` | 12 | 9 | 21 | 66 | 96 | `no-unsafe-optional-chaining` |

## By file — worst first

| File | P1 | P2 | P3 | Churn 6mo | Worst finding |
| --- | --- | --- | --- | --- | --- |
| `src/domain/refunds/apply.ts` | 5 | 8 | 12 | 11 | 🐛 `no-unsafe-optional-chaining:44` |

Showing the 20 worst of 46 files with a finding.

---

## 🔴 P1 — fix these first

### 1. `src/domain/refunds/apply.ts:44` — 🐛 bug

| | |
| --- | --- |
| **Rule** | `@typescript-eslint/no-unsafe-optional-chaining` (ESLint) |
| **Churn** | 11 commits in 6 months |
| **Consequence** | `order?.total` is `undefined` for a missing order, and `undefined - refund` is `NaN`, so the guard below passes and a refund of any size is approved |
| **Autofix** | no |
| **Outcome** | 🟢 fixed |

```diff
- const remaining = order?.total - alreadyRefunded
+ if (!order) throw new OrderNotFound(orderId)
+ const remaining = order.total - alreadyRefunded
```

### 2. `src/http/refund.ts:88` — 🐛 bug

Same table, one row per line: the rule, the churn, the consequence, the autofix flag, the
outcome, and the diff beneath it.

---

## 🔒 Security findings — passed on

Raised by rules already in the project's config. Unranked and unfixed here: weighing these
needs the dependency tree, the git history, and a live target.

| File · line | Rule | Tool | What it says |
| --- | --- | --- | --- |
| `src/http/session.ts:18` | `no-hardcoded-credentials` | ESLint | a signing key literal in the source |
| `src/db/report.ts:41` | `sql-injection` | Semgrep | a query built by interpolation |

---

## 🟠 P2 — worth a person's time

| File · line | Rule | Category | Churn | Consequence | Fix | Autofix | Outcome |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `src/domain/pricing/apply.ts:61` | `no-floating-promises` | ⚠️ risk | 7 | the audit write is never awaited, so a failure is lost and the response returns before the row exists | `await auditLog.write(...)` | no | 🟢 fixed |

---

## ⚪ P3 — the rest

| Category | Rules | Findings | Autofixable |
| --- | --- | --- | --- |
| 🎨 Style | 6 | 324 | 324 |

443 findings, not listed one by one. All 324 style findings go to the formatter.

---

## 🔇 False positives

### 1. `src/db/query.ts:88` — `sql-injection` (Semgrep)

| | |
| --- | --- |
| **Argument** | the interpolated value is a table name from a frozen string-literal union, never from a request. Semgrep tracks the variable but not the type. |
| **Suppressed** | inline at `src/db/query.ts:87`, with this reason |

---

## Findings for the code

| File · line | Finding | Suggested action |
| --- | --- | --- |
| `src/domain/refunds/legacy.ts:150` | dead — nothing imports `legacyRefund`, and knip agrees | delete the file, or say what should call it |

---

## The baseline and the rules

| Change | Value | Where | State |
| --- | --- | --- | --- |
| ESLint baseline | 115 findings recorded | `eslint-suppressions.json` | applied |
| `no-floating-promises` | `warn` → `error` | `eslint.config.js` | applied |
| `max-lines` | off — fired 96 times, caught nothing real | `eslint.config.js` | not applied |
````

Every finding appears in exactly one section. Drop any empty section, and lead the body with
P1.

The before report is the same shape, shorter: no "Before" row, no "What moved", no "Outcome"
rows or columns, and every baseline row reads "not applied".
