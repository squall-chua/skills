# What backs the numbers

Everything [`dry-test`](SKILL.md) claims, and how it was measured. Nothing here changes what a
run does — it is what to read when a score, the threshold, or a missing finding is questioned.

## Why 0.76, and why one number for fourteen languages

This port keeps more structure than dry4go — field names, and the variables of a `range` loop,
which dry4go drops — so 0.82 here is a stricter cut than 0.82 there. Swept against dry4go over
Go's `net/http`, 2,178 units:

| Threshold | 0.72 | 0.74 | **0.76** | 0.78 | 0.80 | 0.82 |
| --- | --- | --- | --- | --- | --- | --- |
| **Of dry4go's 150** | 100% | 100% | **100%** | 97% | 96% | 96% |
| **Extra candidates** | 35 | 31 | **27** | 16 | 12 | 8 |

That sweep is Go only, but the threshold is **not a per-language constant**. Flipping one operator
inside real functions — the tightest near-miss there is — the language barely moves the score,
while the shape of the code moves it a lot (Python and Go 400 units each, C 41):

| Near-miss score, one operator flipped | Python | Go | C |
| --- | --- | --- | --- |
| **Median** | 0.79 | 0.81 | 0.83 |
| **Middle half of the range** | 0.68–0.86 | 0.73–0.88 | 0.76–0.85 |

Those three medians span 0.04. The middle half of a *single* language spans 0.14, and 14 scores
drawn from one language span more than the whole 14-language fixture spread in ~100% of draws.
Between-language variation is not distinguishable from within-language noise. Where a near-miss
lands is set by how deep in the tree the difference sits and how large the unit is — code shape,
not language. Fourteen tuned thresholds would fit that noise.

`check_fixtures.py` walks that ladder in all fourteen at once, flipping one operator in a fixture
clone, then two, then three. The decay is monotone in every language and the fourteen stay within
0.20 of each other at every rung — but 0.76 sits **inside** that band, and the first rung shows
it. After a single flip Rust reads 0.7778 and is still a duplicate, while the other thirteen have
already fallen below. That is the mechanism above, measured: a flip costs whatever it rewrites on
the way to the unit root, and on the same fixture with the same 32 fingerprints Go loses 6 — its
`expression_list` and `statement_list` sit between the operator and the function — where Rust's
`binary_expression < let_declaration < block` loses 4. One number is still the honest choice. The
suite pins the exception by name, so a grammar upgrade that moves a second language across the
line is reported rather than absorbed.

## What `check_fixtures.py` asserts

The four self-checks run against whatever is in scope, so on a mixed scan thirteen languages can
ride on the fourteenth. The same four also run against one committed fixture per language, and
that is what keeps the fourteen aligned.

Each `fixtures/<lang>/` holds `clone.*` — two functions of identical shape sharing no name and no
literal value, which must yield exactly one family at 1.0000 — plus `kinds.*`, `interp.*` and
`ops.*` where the clone shape cannot reach some entry on its own. Those assertions gate all three
per-language tables, and here *unproven* is not accepted as a pass. The expected `UNITS` entries
are listed in the runner itself rather than read from `dry.py`: a check that takes its expectation
from the code under test cannot notice that code shrinking, and deleting a table entry would
simply stop it looking. Every one of the **29 `UNITS` entries across the 14 languages** is reached
by a fixture, so no entry is dead weight and none can be dropped unnoticed.

**Literal opacity** rewrites every literal value outright and requires the fingerprints not to
move. That is dry4go's normaliser rule stated directly — it turns each literal into one childless
`literal/KIND` node and never reads the value — and unlike the escape mutation it holds in Go,
whose grammar gives an escape no node of its own. Sabotaging each `SPELLING` entry in turn, it
fails in 13 of the 14; only Kotlin stays outside it, folding an entire escaped body into one node,
so nothing there can leak and nothing there can be caught.

**Interpolation visibility** is its mirror. `"${x + 1}"` is not what a string *says*, it is code
that happens to sit inside quotes, so it must survive where spelling does not. The `interp.*`
fixture is built with its one flippable operator inside the interpolation; flipping it must move
the score. Nine languages can express this. The other five — Go, Java, C, C++, Rust — have no
interpolation for it to test, and each is named in `NO_INTERPOLATION` with the reason. Absence is
not accepted on its own: a language that interpolates and has no fixture is a failure, because
"not applicable" used to read as a pass and PHP sat in that hole with its invariant resting on
nothing. Rust is in the list because `format!("{x}")` is a macro — the braces stay inside the
string token, so the grammar exposes no interpolation node at all.

**Word operators and chained comparisons** are the two shapes the operator rule cannot see by
character alone. `in`, `is not` and `instanceof` are letters, and `lo < x < hi` hangs two operator
tokens off one node. Both were real: in Python's standard library `assertIn`, `assertNotIn` and
`assertIs` scored 1.0000 against each other — three assertions with three different meanings,
reported as verbatim duplicates. The **operator** self-check cannot reach this, because it flips
operators the engine has already found, so an operator the engine cannot see is invisible to its
own detector.

So each language gets an `ops.*` fixture whose functions differ in one operator and nothing else,
and two things are asserted of it. Every operator the fixture is built around must appear as a
tag, which is the only gate available to Java, whose single word operator has nothing to collide
with. And no two of its units may fingerprint alike, which is what catches a chain, where `< <`
and `> >` can vanish together and leave the tags agreeing. Twelve languages have such a fixture;
C and Go are named in `NO_WORD_OPERATORS`, because every operator they have is punctuation. The
fixture functions are kept below `MIN_LINES` on purpose — this check reads them through the parser
directly, so units that differ by one operator never reach the mixed scan to disturb it.

What that gates is the invariant, not one route to it. Emptying `OP_WORDS` is caught in C#, Java,
Kotlin, Python and Rust; the other seven stay silent because their grammars name an `operator`
field and hand the word back before `OP_WORDS` is consulted. They are unaffected rather than blind.

**Prefilter equivalence** requires `pairs_indexed` to return exactly what `pairs_brute` returns,
on the fixtures and on 500 seeded random corpora. Both prefilters are exact, and one that is
wrong drops findings in silence — fewer duplicates reported reads exactly like a cleaner codebase.
The random corpora are followed by a swept one: both bounds are computed from `threshold * size`,
and a pair landing exactly on the threshold is where that float lets go — `0.55 * 100` is
55.00000000000001, which shortened the prefix by one and lost the pair. Every threshold from 0.50
to 0.99 is checked against a pair that scores exactly it. The fuzz cannot find this by drawing
corpora, because the sizes it draws are far too small for the product to reach a whole number.

**Family shapes** covers the members the fixtures cannot: everything above tests families of two,
and the interesting ones have three. A family is a connected component, not a clique, so A and C
belong together when each matches B even though A and C never matched each other — report them
separately and somebody fixes the same knowledge twice. And `max_score` is a maximum over the
edges that *exist*: on a chain there is no A–C edge, so any summary reading like a floor for the
family describes a measurement never taken. Both are asserted on hand-built fingerprint sets,
where the scores are arithmetic rather than whatever the grammar happens to produce.

**The whole pipeline** then runs as the command, over a tree holding all fourteen languages at
once. Two things only a mixed run can get wrong: units of different grammars compared against
each other, whose node vocabularies make the score meaningless, and a self check that passes for
the scan as a whole because one language proved something the other thirteen never did. It reads
back the JSON the steps read — one family per language, none mixing two, and the `kinds.*` and
`interp.*` functions in no family at all, which is the only place ordinary non-duplicate code is
asserted to stay unreported. TypeScript and TSX share a node vocabulary, so they are what merges
first if the grouping ever breaks. It also reads the text report, which must name what was
scanned and what the self-checks said, not findings alone.

**Sabotage** is the suite checking itself. It breaks `dry.py` 25 ways on purpose — a `SPELLING`
entry removed, the operator tables emptied, a `UNITS` entry deleted or mistyped, fingerprints made
to carry identifier text, the prefilter bounds rounded straight off the float — and every break
must make some check above fail. It asserts only that something caught it, never how many
languages did: a grammar upgrade moves which languages carry a node type, and a pinned count would
read that as a regression. Without this, the suite proves the engine is currently right and proves
nothing about whether it would notice the engine going wrong.

The fixture suite found two real faults on its first run: Swift scored `"x"` against `"x\n"` at
0.69, because Swift names its escapes `str_escaped_char` and its string body `line_str_text`,
neither of which the spelling table knew; and the rename check reported passed on PHP having
renamed nothing, because PHP calls the identifier token `name`. Both are fixed.

## What `check_cochange.py` asserts

It builds a repository with fixed commit dates and an absolute `--since`, so the counts cannot
drift with the wall clock, and pins each answer — including the ones that must never come back as
a number: a family inside one file is `same-file`, a missing repository or a path outside it is
`unknown`, a file renamed inside the window is `renamed`, and a file git does not track is
`untracked`. One case runs the same scan from a subdirectory. A real path-resolution bug once
scored every family at zero co-change from anywhere but the repo root, and that is the only case
that catches it. Three more cases stage what a real repository cannot: a `git log` that times out,
one that fails after `git rev-parse` had already succeeded, and a `git rev-parse` that succeeds
while printing an empty root. The search for a repository is fenced with
`GIT_CEILING_DIRECTORIES`, or the "not a repository" case would be a fact about where the machine
puts its temporary files rather than about this code.

## The two reference implementations disagree

There are two: [dry4go](https://github.com/unclebob/dry4go) and
[dry4java](https://github.com/unclebob/dry4java). The **metric** is identical in both —
fingerprint every subtree, Jaccard over the sets, threshold 0.82, floors 4 lines and 20 nodes,
and the same sort order. The **normaliser** is not, and the gap is large.

Both READMEs say names and literals "normalize away". dry4go replaces each with a placeholder
node it keeps in the tree; dry4java deletes the node outright. So in dry4java a call collapses
to a bare `MethodCallExpr` — its arguments and its receiver are gone. Measured, running both
tools on the same four methods that differ only in the call inside one `if`:

| The pair | dry4go | dry4java | this port |
| --- | --- | --- | --- |
| `log(a)` vs `log(a, b, c)` | 0.43 | **1.00** | 0.40 |
| `log(a)` vs `sink.write(a)` | 0.38 | **1.00** | 0.46 |
| `log(a)` vs `log("text")` | 0.39 | **1.00** | 0.40 |

Argument count, receiver, and name-versus-literal are all invisible to dry4java and all visible
to dry4go. **This port follows dry4go**, which is the stricter and more informative of the two.

They also disagree on what a unit is. dry4go compares functions and methods. dry4java compares
ten kinds of declaration — classes, records, enums, annotations, methods, constructors, fields,
initializers, enum constants, and lambdas — nested ones included, which is why it needs a guard
against reporting a method against the class containing it. This port uses dry4go's model
everywhere. Measured on Google's gson, against dry4java's 54 findings:

| | |
| --- | --- |
| Reported as the same pair | 27 |
| Reported inside a coarser pair — same duplication, one row instead of two | 4 |
| **Not surfaced at all** | **23** |

Almost all of the 23 are one shape: the duplicated thing is a field holding an anonymous class,
or a whole class, whose individual methods are each too small to clear `--min-lines 4` and
`--min-nodes 20`. gson's four identical `ReflectionAccessFilter` constants are real duplication
this port does not see. Two exception classes with the same constructor ceremony are also in
there, and merging those would be wrong — so the missing findings are a mix of signal and noise,
not a clean loss.

## Where the port differs from dry4go

All 150 of dry4go's `net/http` findings come back; these explain the rest:

- **`range` variables.** dry4go drops a range loop's key and value, so `for _, f := range xs`
  and `for f := range xs` are identical to it. This keeps them — that one difference scored a
  real `net/http` clone pair 0.79 where dry4go said 1.00.
- **The node floor lands differently.** dry4go counts nodes in its own normalised tree, this
  counts named tree-sitter nodes, so `--min-nodes 20` cuts elsewhere. That is most of the 27
  extra candidates at 0.76 — small functions dry4go filtered out.
- **Roles are named, not positional.** dry4go pads a fixed slot per child with `nil`; this uses
  the grammar's own field names to keep the same role information.
- **Grammars know a few names.** `make(T)` reads its argument as a type only because the callee
  is literally `make`. A little name sensitivity lives in the grammar, below this script.
