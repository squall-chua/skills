---
name: static-analysis
description: >
  Run the type checker, linter, security scanner, and dead code finder over the
  paths you name, cut the noise, and report each finding with a fix diff.
disable-model-invocation: true
---

A static analyzer reads the code without running it, so it finds what tests
never reach — the branch nobody takes, the error nobody handles, the secret
nobody meant to commit. It also finds a great deal of **noise**: an opinion
about naming, a rule the team never agreed to, a warning the analyzer is simply
wrong about. A run that hands over 4,000 findings has said nothing.

The whole job is separating the two. This skill ends with the findings ranked,
the noise named as noise, and each real finding carrying a fix.

## This skill reports

It runs the analyzers and writes up what they found. The code stays exactly as
it is. A report the user did not ask to act on is the whole deliverable — run
steps 1 to 7 and hand it over.

Apply the fixes only when the user gives a **fix signal**: "fix them", "apply
the fixes", "clean it up", "go ahead". Steps 8 and 9 then follow, and they end
in a second report that sits beside the first. The step 7 report is the before,
so it gets written on a fix run too, and it gets written before any code is
touched.

## 1. Pin the scope

The paths the user named are the scope, exactly as given — a module, a package,
a folder, a list of files. Expand each one to the file list it covers and count
them, so the report can say what was read.

When the user named no paths, take the files changed against the default branch,
and say in the report that this is what you chose. Discover that branch rather
than assuming `main` — a repo may call it `master` or `develop`, and `origin/HEAD`
is often absent:

```sh
base=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null)
if [ -z "$base" ]; then
  for c in origin/main origin/master origin/develop main master; do
    git rev-parse --verify --quiet "$c" >/dev/null && base=$c && break
  done
fi
[ -n "$base" ] && git diff --name-only "$base"...HEAD
```

Three details in there earn their place. The three-dot form already diffs from the
merge base, so a separate `git merge-base` call is dead work. Every probe goes
through `git rev-parse --verify --quiet`, which prints nothing and returns
non-zero on a missing ref — where `git rev-parse --abbrev-ref origin/HEAD` prints
the error to stderr *and* echoes `origin/HEAD` to stdout, handing you a value that
looks valid and diffs against nothing. And when `$base` ends up empty the repo has
no branch to compare against: say so and ask the user for the scope, because a
silent empty diff reads as "nothing changed".

Analyzers report outside the scope as well: a type error in a file that yours
imports, a rule that fires project-wide. Count those and say how many, then
leave them out of the triage. A finding the user did not ask about is a footnote,
not a section.

**Done when:** you have the explicit file list, its count, and — where the scope
came from a default rather than the user — that fact written down.

## 2. Check the tree builds

Build the project, or type-check it. Record the command and the result.

An analyzer that cannot resolve an import gives up on the file and reports
whatever it half-understood. A broken build turns into a page of findings that
vanish the moment the build is fixed. Establish that the tree is sound first, or
the report measures the build.

A broken build is where this skill stops. Report it as the finding, because
nothing downstream of it can be trusted.

Then find the test suite and run it, and take whatever you find:

| What you find | What it means for this run |
| --- | --- |
| **Green suite** | everything below is available, including the fix run |
| **Red suite** | analyse anyway. The findings stand on their own, and one of them may well be the reason the suite is red. Record the failures, and treat a fix signal as blocked until the suite is green, since a red suite cannot tell you an autofix was safe |
| **No suite at all** | analyse anyway, and say so in the report. This is the one signal that works on untested code, and it is often the only evidence a bare codebase has. A fix run is limited to changes you can verify by re-running the analyzer |

The suite is not a gate on the analysis. It is a gate on the *fixing*, because
a fix run edits code and a green suite is the only thing that will tell you the
edits were safe.

**Done when:** the build or type-check passes and its command is written down; the
suite has been run or its absence established; and the suite's state is recorded
for step 8 to read.

## 3. Pick the analyzers and read the project's rules

Four kinds of tool answer four different questions, and running one of them
answers a quarter of the question:

| Kind | What it finds |
| --- | --- |
| **Type checker** | the code contradicts itself — wrong argument, missing case, impossible narrowing |
| **Linter / bug finder** | the code does something other than what it says — ignored return, unreachable branch, resource leak |
| **Security scanner** | injection, hardcoded secrets, weak crypto, unsafe deserialization |
| **Dead code finder** | exports, files, and dependencies nothing reaches |

Prefer the tools the project already has, in its config files and its CI. Then
fill the gaps from here:

| Language | Lint / bug | Types | Security | Dead code |
| --- | --- | --- | --- | --- |
| JavaScript / TypeScript | ESLint, Biome | `tsc --noEmit` | Semgrep, `npm audit` | knip |
| Python | Ruff, pylint | mypy, pyright | bandit, Semgrep | vulture |
| Go | `go vet`, staticcheck, golangci-lint | compiler | gosec | `deadcode` |
| Java / Kotlin | SpotBugs, PMD, Error Prone, detekt | compiler | FindSecBugs | — |
| C# / .NET | Roslyn analyzers, SonarAnalyzer | compiler | Security Code Scan | — |
| Rust | `cargo clippy` | compiler | `cargo audit` | `cargo-udeps` |
| PHP | PHPStan, Psalm | PHPStan, Psalm | Psalm taint analysis | — |
| Ruby | RuboCop | Sorbet, Steep | Brakeman | — |
| Swift | SwiftLint | compiler | — | periphery |
| C / C++ | clang-tidy, cppcheck | compiler | clang static analyzer | — |

Semgrep and CodeQL work across languages and are the fallback when a language
has no strong native tool.

Read each tool's own documentation for its current flags and config schema. Names
drift between versions, and a config written from memory fails in ways that look
like broken code.

**The project's config is the project's decision.** When a config file exists,
run with it and leave it alone. Those rules are what the team agreed to, and a
run that overrides them reports on a codebase nobody is writing.

When no config exists, this is the single choice that decides whether the report
is worth reading. Turn on the correctness and security rules; leave the style
rules off. Style belongs to a formatter, and a report that opens with 3,000
quote-mark complaints buries the null dereference on page 40. Write down the
rule set you chose and why.

Ask each tool for machine-readable output — SARIF where it is offered, otherwise
JSON or checkstyle XML — written to a file. You will read that, not the terminal
output.

**Done when:** each of the four kinds is either running or written down as
unavailable for this language, the rule set is either the project's config or a
recorded choice of your own, and every tool writes a machine-readable file.

## 4. Run and capture

Run each tool over the scope. Capture stdout, stderr, the exit code, and the
report file for each.

A tool that exits non-zero because it found something has worked. A tool that
exits non-zero because it crashed has not, and its findings are missing rather
than absent. Tell those two apart now, by reading the error, and record which
tools completed.

**Done when:** every tool has either a machine-readable file with its findings
or a recorded reason it could not run, and each finding carries a file, a line,
a rule ID, and the tool that raised it.

## 5. Triage every finding

Start by grouping the findings by **rule**, not by line. One rule firing 200
times is one decision, not 200 problems — and it is usually fixed once, in a
config or a codemod. A report listing 200 lines hides that.

Then give every finding a category:

| Category | What it means |
| --- | --- |
| 🐛 **Bug** | the code already does the wrong thing — null dereference, wrong comparison, unreachable branch, leaked handle |
| 🔒 **Security** | injection, a committed secret, weak crypto, unsafe deserialization, a known-vulnerable dependency |
| ⚠️ **Correctness risk** | right today, wrong on a plausible input — an ignored error, a swallowed exception, a missing default |
| 🧹 **Maintainability** | complexity, duplication, dead code. Real, and not urgent |
| 🎨 **Style** | formatting, naming, import order. A formatter's job, not a report's |
| ⚪ **False positive** | the analyzer is wrong about this code. Needs a written argument, not a hunch |

The tool's own severity is its opinion about a rule in general, not about your
code. Every linter calls everything an error. Re-rank by what the code decides:

- **P1** — a bug or a security finding, anywhere. Also anything in code that
  moves money, checks permissions, or writes data.
- **P2** — a correctness risk, or maintainability in a file changed 5 or more
  times in the last 6 months:
  ```sh
  git log --since='6 months ago' --name-only --format= -- <path> | grep . | sort | uniq -c | sort -rn
  ```
  The `grep .` matters: `--name-only` prints a blank line between commits, and
  without it the blank is counted and sorts to the top as your busiest file.
- **P3** — everything else, style included.

For every P1 and P2 finding, read the code and write one sentence naming what
goes wrong — the consequence, not the rule text. "A refund with no `orderId`
throws before the guard runs, so the caller gets a 500 rather than a validation
error" is useful. "`no-unsafe-member-access` on line 44" is the tool's output
copied out.

Then write the fix as a diff, and note whether the tool can apply it itself.
Most linters fix the mechanical half automatically, and knowing that 480 of 530
findings fix themselves changes what a person decides to do.

A false positive needs its argument written down and an inline suppression with
that reason next to it, never a rule switched off across the project. One
suppression explains one line; a disabled rule silently covers every line you
have not read.

**Done when:** every finding carries a category and a bucket, every P1 and P2
finding also carries its one-sentence consequence, a fix diff, and an autofix
yes or no, and every false positive carries its written argument.

## 6. Work out the baseline

Recommend a **baseline**: the findings that exist today are recorded and
grandfathered, and CI fails on anything new. Most tools support this directly —
ESLint's `--suppressions`, PHPStan's and Psalm's baseline files, SpotBugs'
exclude filter, `golangci-lint --new-from-rev`. Where a tool has none, run it
over the changed lines only.

A baseline is what makes a large existing codebase gateable. A rule turned on
across 3,000 old findings fails every build until someone turns it off again,
and then there is no gate at all.

Also recommend the config changes the triage exposed: a rule that only ever
produced noise and should come off, a rule that caught a real bug and should be
promoted to an error, a whole category the project is not running.

Both are recommendations, and they go in the report as the exact file and the
exact setting. Edit the config and the CI files only on a fix signal.

**Done when:** the report carries the recommended baseline, the tool it belongs
to, and every recommended rule change with a reason drawn from the findings.

## 7. Write the report

Run `date '+%Y-%m-%d-%H%M%S'` for the timestamp and `git rev-parse --short HEAD`
for the commit. Both go in the header. Note a dirty working tree there too,
since the run then covers code that commit does not hold.

Write the report to `<module>/.reports/static-analysis-report-<timestamp>.md`,
where `<module>` is the root of the module the scope covered — the nearest
directory at or above it that holds the project's manifest (`package.json`,
`go.mod`, `pyproject.toml`, `pom.xml`, `Cargo.toml`, `composer.json`, `Gemfile`,
a `*.csproj`). A scope spanning several modules writes to the repository root.

Create the folder if it is missing, and keep it out of version control: add
`.reports/` to the repository's root `.gitignore` when nothing there covers it
already. One file per run, and no run ever overwrites an older file.

Write this report even on a fix run, and write it *before* you touch any code.
This is the before. Without it there is nothing to compare the after against,
and a count you remember is not a count you can show.

Use the shape below, and put the data in tables. Every count, path, rule ID,
category, and bucket belongs in a table cell where it can be scanned and
compared. The prose left over is the one-sentence consequence, the false
positive argument, and the short note under a table that says what the numbers
mean.

Then tell the user the file path, the P1 count, and the single finding they
should fix first. On a report-only run, say that the report is all this run
changed, so they can ask for the fixes to be applied if they want that next.

**Done when:** the report file sits in the module's `.reports` folder, `.reports/`
is ignored by git, no older report was overwritten, and the report holds the
totals by category and bucket, the per-tool table, the per-rule table,
the per-module and per-file tables, every P1 and P2 finding with its
consequence, fix diff, and autofix flag, and the baseline recommendation.

## 8. Apply the fixes — on a fix signal

Without the signal, the work is finished at step 7. Hand over the report.

Read the suite's state from step 2 first, because it decides how far a fix run
can go:

| Suite state | How far the fixing goes |
| --- | --- |
| **Green** | everything below |
| **Red or absent** | changes you can verify without it — a re-run of the analyzer showing the finding gone, and the build still passing. Autofix passes wait, since nothing here can tell you a mechanical edit kept the behaviour. Say plainly which fixes you held back and why |

With a green suite, take the autofixable findings first, in one pass per tool.
They are mechanical and they are the bulk. Then run the build and the full suite
from step 2. An autofix can change behaviour — a rule that drops an "unused" call
also drops its side effect — so the suite is what stands between a tidy diff and
a broken one.

Keep that pass in its own commit. A hundred mechanical edits mixed with six
considered ones is a diff nobody can review.

Then work the hand fixes, P1 first, then P2, one finding at a time:

1. Apply the diff from step 5.
2. Re-run the tool over that file. The finding is gone, and no new finding has
   taken its place.
3. Run the suite and confirm it is green. Where there is no suite, confirm the
   build still passes — that is the whole verification available, so keep each
   such fix small enough to read.

Send style findings to the formatter rather than fixing them by hand, and run it
as its own commit too.

Then apply the baseline and the rule changes from step 6.

Fix the finding, not the report. A count reduced by switching a rule off, by
widening an ignore file, or by a blanket suppression at the top of a file is a
number that lies to the next reader. When the only way to clear a finding is to
change what the code does, that finding is a bug report — write it up and move
to the next one.

**Done when:** every P1 and P2 finding from step 5 is one of four things — fixed
with the build passing and the suite green where one exists, suppressed inline
with its written argument, raised as a bug report about behaviour, or deferred
with a stated reason. Where the suite was red or absent, the fixes held back for
want of verification are listed with that reason. None are simply unmentioned.

## 9. Write the after report — on a fix signal

Re-run every tool from step 3 over the same scope. Take a fresh timestamp and
write a second file into the same `.reports` folder. The step 7 report
stays where it is, untouched. Two files, so the move is on the record and anyone
can read the before for themselves.

Lead the body with a "What moved" section that names the step 7 file, and give
each of these its own table:

- findings before and after, by category and by bucket;
- what happened to them — fixed, suppressed, raised, deferred, still open;
- which modules cleared, and which did not move;
- any finding that appeared during the fix run. A fix that raises a new finding
  is the first thing the reader needs.

Then tell the user both file paths, the two P1 counts, and what is still open.

**Done when:** both report files exist side by side, the after report names the
before file and states the change per category, every P1 and P2 finding from the
step 7 report appears in it with its outcome, and the build and suite are
recorded green at the end.

---

# Report shape

The example below is a TypeScript project. The tables, the columns, and the
categories are what transfers — swap in the tools, the paths, and the rule IDs
your language actually uses.

````markdown
# Static Analysis Report

| | |
| --- | --- |
| **Run** | <YYYY-MM-DD HH:MM:SS> |
| **Scope** | `src/domain/`, `src/http/` — 46 files (as asked) |
| **Commit** | `<short sha>` (dirty working tree) |
| **Build** | `pnpm build` — passed, 22s |
| **Suite** | `pnpm test` — 412 passed, 0 failed, 3 skipped, 42s |
| **Duration** | 3m 11s |
| **Before** | [`static-analysis-report-2026-07-30-091412.md`](./static-analysis-report-2026-07-30-091412.md) |

## What moved

Against `static-analysis-report-2026-07-30-091412.md`, taken before any code was
touched.

| Category | Before | After | Change |
| --- | --- | --- | --- |
| 🐛 Bug | 14 | **0** | **−14** |
| 🔒 Security | 3 | **1** | **−2** |
| ⚠️ Correctness risk | 61 | 12 | −49 |
| 🧹 Maintainability | 128 | 96 | −32 |
| 🎨 Style | 324 | 0 | −324 |
| ⚪ False positive | 0 | 6 | +6 |
| **Total** | **530** | **115** | **−415** |

| Outcome | P1 | P2 | P3 |
| --- | --- | --- | --- |
| 🟢 Fixed | 15 | 49 | 356 |
| 🔇 Suppressed with a reason | 2 | 4 | 0 |
| 🔧 Raised as a bug report | 0 | 1 | 0 |
| ⏸️ Deferred | 0 | 3 | 0 |
| 🔴 Still open | 1 | 12 | 96 |
| **Total before** | **18** | **69** | **452** |

| Module | Before | After | Change |
| --- | --- | --- | --- |
| `src/domain/refunds` | 96 | 4 | −92 |
| `src/domain/pricing` | 71 | 18 | −53 |
| `src/http` | 88 | 88 | 0 |

**New findings raised by the fixes:** none. **Build and suite:** green.

## Totals

| Category | P1 | P2 | P3 | Total | Autofixable |
| --- | --- | --- | --- | --- | --- |
| 🐛 Bug | 14 | 0 | 0 | 14 | 2 |
| 🔒 Security | 3 | 0 | 0 | 3 | 0 |
| ⚠️ Correctness risk | 1 | 60 | 0 | 61 | 18 |
| 🧹 Maintainability | 0 | 9 | 119 | 128 | 31 |
| 🎨 Style | 0 | 0 | 324 | 324 | 324 |
| **Total** | **18** | **69** | **443** | **530** | **375** |

375 of 530 fix themselves. The 155 left are the ones that need a person.

## By tool

| Tool | Version | Rules | Findings | Ran |
| --- | --- | --- | --- | --- |
| `tsc --noEmit` | 5.6.2 | — | 4 | ✅ |
| ESLint | 9.12.0 | 218 (project config) | 498 | ✅ |
| Semgrep | 1.89.0 | `p/typescript`, `p/secrets` | 28 | ✅ |
| knip | 5.30.2 | — | 0 | ❌ crashed on a circular import — findings missing, not absent |

Outside the scope: 61 findings, not triaged.

## By rule — most fired first

One rule is one decision. Fix it once.

| Rule | Tool | Category | Count | Files | Autofix |
| --- | --- | --- | --- | --- | --- |
| `quotes` | ESLint | 🎨 style | 291 | 44 | yes |
| `@typescript-eslint/no-floating-promises` | ESLint | ⚠️ risk | 47 | 19 | no |
| `no-unsafe-optional-chaining` | ESLint | 🐛 bug | 12 | 5 | no |
| `javascript.lang.security.audit.hardcoded-secret` | Semgrep | 🔒 security | 2 | 1 | no |

## By module

| Module | Files | P1 | P2 | P3 | Total | Worst rule |
| --- | --- | --- | --- | --- | --- | --- |
| `src/domain/refunds` | 12 | 9 | 21 | 66 | 96 | `no-unsafe-optional-chaining` |
| `src/domain/pricing` | 9 | 2 | 18 | 51 | 71 | `no-floating-promises` |
| `src/http` | 25 | 7 | 30 | 51 | 88 | `quotes` |

## By file — worst first

| File | P1 | P2 | P3 | Churn 6mo | Worst finding |
| --- | --- | --- | --- | --- | --- |
| `src/domain/refunds/apply.ts` | 5 | 8 | 12 | 11 | 🐛 `no-unsafe-optional-chaining:44` |
| `src/http/session.ts` | 2 | 3 | 9 | 4 | 🔒 hardcoded secret:18 |

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

```ts
const remaining = order?.total - alreadyRefunded   // NaN when order is missing
if (remaining >= amount) approve()
```

```diff
- const remaining = order?.total - alreadyRefunded
+ if (!order) throw new OrderNotFound(orderId)
+ const remaining = order.total - alreadyRefunded
```

### 2. `src/http/session.ts:18` — 🔒 security

| | |
| --- | --- |
| **Rule** | `javascript.lang.security.audit.hardcoded-secret` (Semgrep) |
| **Churn** | 4 commits in 6 months |
| **Consequence** | the signing key is in the source, so every fork and every clone of this repo can mint a valid session token |
| **Autofix** | no |
| **Outcome** | 🔴 open — the key must be rotated before the code changes |

```diff
- const SIGNING_KEY = 'sk_live_8f3a...'
+ const SIGNING_KEY = requireEnv('SESSION_SIGNING_KEY')
```

Rotate the key first. Removing it from the source leaves it in the git history,
so treat it as leaked.

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
| 🧹 Maintainability | 14 | 119 | 31 |

443 findings, not listed one by one. All 324 style findings go to the formatter.

---

## 🔇 False positives

### 1. `src/db/query.ts:88` — `sql-injection` (Semgrep)

| | |
| --- | --- |
| **Argument** | the interpolated value is a table name drawn from a frozen string-literal union, never from a request. Semgrep tracks the variable but not the type. |
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
| Semgrep on pull requests | changed files only | `.github/workflows/ci.yml` | not applied |

The baseline records what exists today, so CI fails on anything new without
failing on the past.
````

Every finding appears in exactly one section. Drop any section with no entries,
and lead the body with P1.

The before report is the same shape, shorter: no "Before" row, no "What moved",
no "Outcome" rows or columns, and every baseline row reads "not applied".

On a fix run, the after report adds the **Outcome** row to each P1 entry and the
**Outcome** column to the P2 table.
