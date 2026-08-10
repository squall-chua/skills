---
name: dry-test
description: >
  Find structurally duplicated functions across a codebase with a deterministic
  clone finder, separate the real duplication from code that only rhymes using git
  co-change history, and report each clone family with the knowledge it holds.
disable-model-invocation: true
---

DRY is about **knowledge**, not text. "Every piece of knowledge must have a single,
unambiguous, authoritative representation." Two functions can be identical character for
character and still hold two pieces of knowledge that merely look alike today — merging those
makes the code worse, because the next change pulls them apart again.

So this skill measures what can be measured and refuses to guess the rest. A script finds
every pair of functions with the same **shape**. Git says whether those places have been
**edited together**. Both are evidence, neither is a verdict, and the last step is a person's.

## The engine

[`scripts/dry.py`](scripts/dry.py) ports Robert C. Martin's
[dry4go](https://github.com/unclebob/dry4go) onto tree-sitter grammars, so one metric runs on
fourteen languages. Each function is one unit; its syntax tree becomes one S-expression per
subtree — node types and operators, never a name, never a literal's value — and two units are
scored by Jaccard similarity over those fingerprint sets:

```
score = shared fingerprints / all fingerprints seen in either unit
```

| | |
| --- | --- |
| **Languages** | Python, Go, JavaScript, TypeScript, TSX, Java, Kotlin, Swift, C#, PHP, Ruby, Rust, C, C++ |
| **Needs** | `pip install tree-sitter-language-pack` — one dependency, prebuilt wheels, Python ≥ 3.10 |
| **Defaults** | `--threshold 0.76`, `--min-lines 4`, `--min-nodes 20`, `--since 12.months` |
| **Speed** | 9,061 units of the Python standard library in 7 seconds |

0.76 is measured, not inherited. This port keeps more structure than dry4go, so 0.82 here is a
stricter cut than 0.82 there; swept over Go's `net/http`, **0.76 is where all 150 of dry4go's
findings come back**. It is one number for all fourteen languages because between-language
variation is not distinguishable from within-language noise — where a near-miss lands is set by
code shape, not language. One language does sit above the line after a single flipped operator,
Rust at 0.7778, and the suite pins that exception by name so a grammar upgrade cannot absorb it.

Read [`evidence.md`](evidence.md) when a score, the threshold, or a finding this did not report
is questioned: it holds the calibration sweeps, what each suite check asserts and the 25
sabotages proving they would catch the engine going wrong, and where this port disagrees with
dry4go and dry4java.

Steps 1 to 6 measure and write up, and no source file is edited. That matters more here than
in most skills: **the fix for duplication is often wrong**, because merging two things that
only rhyme couples them forever. Steps 7 and 8 run only on a fix signal **naming families** —
"merge family 1", "go ahead on the first three". A bare "fix it" is not a fix signal; ask
which.

## 1. Fix the scope and the commit

Record the paths, `git rev-parse --short HEAD`, and whether the tree is dirty. Co-change comes
from git history, so scanning uncommitted code is scanning with the second input missing.

**Done when:** the scope paths, the commit, and the dirty flag are written down.

## 2. Pin the engine

```sh
python3 -m venv .venv && .venv/bin/pip install 'tree-sitter-language-pack==1.14.3'
```

Grammars are fetched on first use and cached under a path carrying the pack version, so **the
pack version is part of every score** — a new grammar can rename a node type and every number
moves. Two reports from different pack versions cannot be compared, which is why the script
records it in `run.engine`. For an offline run, warm the cache first:

```sh
.venv/bin/python -c "from tree_sitter_language_pack import prefetch; prefetch(['go','python'])"
```

**Done when:** the pinned version is installed and the languages in scope are cached.

## 3. Run it

```sh
.venv/bin/python scripts/dry.py <paths> --format json --since 12.months > dry.json
```

Four self-checks run first, against the repo's own code, and a failure stops the run before a
single score prints:

| Check | The mutation | What it proves |
| --- | --- | --- |
| **units** | none | the language table matched something at all |
| **rename** | append a suffix to every identifier | names are not in the fingerprints |
| **operator** | flip one `+` to `-`, one `==` to `!=` | operators still are |
| **spelling** | add an escape inside a string | what a message *says* is not structure |

A clone finder that quietly parsed nothing reports "no duplicates found", which reads exactly
like good news — that is the failure these prevent.

A check that cannot run here is recorded as **unproven**, not passed: a scope with no string
literal inside a function proves nothing about spelling, and the report says so. A mutation that
changed no bytes is unproven too — it would otherwise score 1.0 by construction and report a pass.

Those four run against whatever is in scope, so on a mixed scan thirteen languages can ride on
the fourteenth. Two committed suites keep the fourteen aligned. Both must be green before a score
is worth reading, and both must be re-run after any table edit:

```sh
.venv/bin/python scripts/check_fixtures.py     # 14 languages end to end, about 2.3s
python3 scripts/check_cochange.py              # 15 git cases against a throwaway repo
```

**Done when:** `dry.json` exists and all four checks read passed or unproven, with any unproven
one carried into the report.

## 4. Reconcile before reading a single score

From `run`: units found, units per language, `files_unsupported` with its per-extension
breakdown, `files_unreadable`, `units_with_parse_errors`, and `units_too_deep`.

**Unsupported files** are files this engine has no grammar for — a repo that is half Elixir
has half a report, and "no duplicates in the Elixir" would be a lie; the extension breakdown
says which. **Parse errors** are usually a grammar meeting a newer language version, and they
silently shrink the denominator. **Unreadable files** were skipped entirely. The floors do the
same on purpose: nothing under 4 lines or 20 nodes is a unit, so a codebase of tiny functions
comes back almost empty — a fact about the floors, not the code.

**Done when:** all six counts are written down, and every language in scope is either scanned
or named as unscanned.

## 5. Sort the families with the fixed table

The script already grouped clones into families (connected components — three copies are one
problem, not three pairs) and counted, per family, the commits in the window that touched two
or more of its files.

That co-change count is the second measurement, and it is what separates duplication from
coincidence. Two handlers with one shape edited in the same commit four times are one piece of
knowledge in two places. Two that never moved together in a year are two pieces that rhyme. A
family inside one file reports `same-file`: git has no finer granularity, so those are decided
on the code alone. A family holding a file that was renamed inside the window reports `renamed`
rather than a count. git filters history on the name a commit used, so everything the file did
under its old name is invisible, and any number would be an undercount printed as a measurement.
A family holding a file git does not track reports `untracked` for the same reason — and that is
the ordinary case, not an exotic one, because a clone added on a branch and not yet committed has
no history at all. Reporting it as "changed together zero times" would file the freshest
duplication in the repository under 🟡 and tell you to leave it alone.

**Take the first row that matches, reading top down.** The rows overlap on purpose — a family at
1.00 also has a co-change count — and without an order a verbatim family inside one file matches
two rows at once and lands in whichever bucket the reader noticed first.

| Score | Co-changed | Bucket |
| --- | --- | --- |
| 1.00 | 0 in the window | 🟡 **Incidental** — one shape, and a history that says they are independent |
| 1.00 | anything else | 🔴 **Verbatim** — treat as one knowledge until shown otherwise |
| ≥ threshold | 3+ | 🔴 **Duplication** — they move together |
| ≥ threshold | 1–2 | 🟠 **Unsettled** — the code decides |
| ≥ threshold | 0 in the window | 🟡 **Incidental** — same shape, different reasons |
| ≥ threshold | not a number | 🟠 **Unsettled** — co-change has no opinion here |

The last row is every verdict that is not a count: `same-file`, `renamed`, `untracked` and
`unknown`. None of them is evidence of anything, and the difference between them is *why* git
could not answer, which belongs in the report next to the family. Only `0` means "measured, and
they never moved together".

Order inside each bucket by score, then family size, then path. The rank is arithmetic.

**Done when:** every family carries a co-change count or a named reason git could not give one,
and sits in exactly one bucket, ordered.

## 6. Name the knowledge, then write the report

This is the one judgement in the skill, bounded to a single question per family:

> Write one sentence naming what this function knows. Does the same sentence describe every
> member?

"How to build an HTTP request for one verb" describes all of `get`, `post`, `put`, `delete` —
one knowledge, four homes. "How to register the big5 codec" does not describe `cp1006`,
however identical the code. Answer for 🔴 and 🟠 families, reading the code; 🟡 is counted, not
read.

**The bucket sorts, the sentence decides.** When they disagree, say so in the report — that
disagreement is the most useful line in it.

Header: the timestamp from `date '+%Y-%m-%d-%H%M%S'`, the commit, a dirty-tree note, and the
pack version from `run.engine`. Write to `<module>/.reports/dry-report-<timestamp>.md`.
`<module>` is the nearest directory at or above the scope holding the project's manifest
(`package.json`, `go.mod`, `pyproject.toml`, `pom.xml`, `Cargo.toml`, `composer.json`,
`Gemfile`, `*.csproj`); a run spanning several writes to the repository root. Create the folder
if missing, add `.reports/` to the root `.gitignore` if nothing there covers it, one file per
run, never overwrite an older one. Put `dry.json` beside it with the same timestamp — without
it the table cannot be replayed.

Use the tables in [`report.md`](report.md) — every section of that shape, in that order. Then
tell the user the path, the counts per bucket, and the one family worth merging first.

**Done when:** the report sits beside its JSON, `.reports/` is git-ignored, no older report was
overwritten, and every 🔴 and 🟠 family carries its knowledge sentence and a proposal.

## 7. Remove it — on a fix signal naming families

One family at a time, only the ones named:

1. Write the shared thing once — a function, a table, a parameter.
2. Replace each member with a call to it.
3. Run the suite. Green before, green after.
4. Re-run the scan over that family's files and confirm it is gone.

The parameter is the tell: if collapsing four functions needs three flags, they were not one
knowledge. A merge that grows a flag per caller has traded duplication for coupling, which is
the worse of the two — stop and say so.

**Done when:** every named family is merged with the suite green, or left with a stated reason.

## 8. Write the after report — on a fix signal

Re-run step 3 with the **same script and the same pinned pack**: a changed engine and a changed
number cannot be told apart.

Fresh timestamp, second file beside the first. Lead with "What moved" — families before and
after, which were merged, and any family whose score **rose**, meaning the merge introduced new
duplication.

Then the gate: run the scan in CI over changed files only, failing on a new family above the
threshold. A whole-repo family count is a dishonest gate — deleting a clone passes the build
while an untouched file fails it.

**Done when:** both reports sit side by side, the after report names the before file and the
pack version, and every named family appears with its outcome.

---

## What it cannot see

Say these in the report — a reader takes silence for absence:

- **Duplicated knowledge with different shapes.** Two implementations of one rule, written
  differently, score near zero. This finds copy-paste, not concepts.
- **Anything under the floors** — 4 lines, 20 nodes. Most duplicated one-liners.
- **Anything outside a function** — config, SQL, templates, IaC, schemas, and the duplication
  between a struct and the migration mirroring it. Type declarations too: two identical classes
  or structs are invisible, because the unit is the function.
- **A keyword operator outside `OP_WORDS`** that the grammar does not put in an `operator` field.
  Operators written as letters are recognised from a fixed list — `in`, `is`, `not`, `and`, `or`,
  `xor`, `as`, `instanceof`, `typeof`. A language with another one drops it out of the fingerprints,
  and two functions differing only there read as identical. Each language's `ops.*` fixture pins
  the operators it is known to have, so this is a gap that only opens for an operator nobody
  wrote a fixture line for.
- **Cross-language duplication.** Units are compared only within one language; each grammar has
  its own node vocabulary, so the scores are not the same measurement.
- **A difference deep in the tree costs every fingerprint above it.** Each subtree's fingerprint
  contains its descendants, so one changed leaf inside a loop invalidates the loop, the block,
  and the function root. In a small function that is a large fraction of the score, and
  near-identical code can land below the threshold.
