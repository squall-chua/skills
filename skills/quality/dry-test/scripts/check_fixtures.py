#!/usr/bin/env python3
"""Per-language conformance suite for dry.py.

Every language in `UNITS` gets one fixture holding the same shape: two functions that
are structurally identical but share no name and no literal value. Each fixture must
produce exactly two units and exactly one family scoring 1.0000.

That single assertion gates all three per-language tables at once:

    UNITS      — wrong node type, and the unit count stops being two
    OP_*       — operators normalised away, and the operator check stops failing
    SPELLING   — literal spelling leaking in, and the escape check stops passing

On top of dry.py's own four, this adds a fifth: `literal_opacity` rewrites every literal
value outright and requires the fingerprints not to move. That is dry4go's normaliser
rule stated directly, and unlike the escape mutation it is provable in Go and Kotlin,
whose grammars never expose an escape as a node of its own.

The mutation checks are dry.py's own `self_check`, run once per language instead of
once per scan. The point of running them here is that a check reported as *unproven*
is not a pass: on a mixed scan self_check stops at the first file that can prove a
thing, so thirteen languages can ride on the fourteenth. Here each one must prove it
for itself, or be named in UNPROVABLE with the grammar reason.

Six more passes follow the per-language one, and none is about coverage.

`family_shapes` covers what a two-unit fixture cannot: a family of three, built from
hand-made fingerprint sets. A family is a connected component rather than a clique, and
`max_score` is a maximum over the edges that exist — neither is visible with two members.

`scan_scope` covers the two ways a run yields nothing rather than something wrong: a
project skipped wholesale because it lives under a directory named `build`, and one unit
too deep to fingerprint taking the whole process down with it.

`threshold_transfer` walks a clone away from its twin one operator at a time, in all
fourteen. Go's 0.76 came from dry4go; the other thirteen inherit it, and inheriting it is
only sound if the same divergence costs about the same score everywhere.

`pair_equivalence` holds `pairs_indexed` to what `pairs_brute` returns. Nothing else in
the repository executes `pairs_brute`; it is the definition of the answer, and the two
prefilters are an optimisation trusted to be exact.

`cli_contract` runs dry.py as a command over every language at once and reads back the
JSON the skill's own steps read. It is the only check that exercises the real main().

`sabotage` breaks dry.py on purpose, one entry of its table at a time, and requires
some check above to fail every time. Everything above it proves the engine is
currently right. Only this proves the suite would notice it going wrong — and a suite
that passes on a broken engine is worse than no suite, because it gets read as evidence.

Co-change is not tested here. It reads git rather than source, so it lives in the sibling
`check_cochange.py`.

    .venv/bin/python scripts/check_fixtures.py

Needs the same pinned grammar pack as dry.py: tree-sitter-language-pack==1.14.3.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import random
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import dry  # noqa: E402

FIXTURES = HERE.parent / "fixtures"

# Checks that cannot run in a given language, and why. This list is the honest record
# of what is NOT proven — every other language/check pair must reach "passed".
UNPROVABLE = {
    ("kotlin", "spelling"): "grammar folds escape sequences into string_content, so no "
                            "escape can add a node to test with",
    ("go", "spelling"): "same — the escape stays inside "
                        "interpreted_string_literal_content",
}

# Passing is not the same as gating. Sabotaging each SPELLING entry in turn, the literal
# check below fails in 13 of the 14 — every language except Kotlin, whose grammar folds
# an entire escaped body into one `string_content` node. Nothing there can leak, and by
# the same token nothing there can be caught: Kotlin's SPELLING behaviour is a property
# of the grammar rather than of this table.

# Languages with no interpolation for an interp.* fixture to test, and why. Stated as a
# set because "no fixture" and "nothing to test" are different facts and only one of them
# is acceptable: `interpolation_visible` reports mere absence as "not applicable", and
# check() reads that as a pass, so a language that HAS interpolation and no fixture was
# silently ungated. PHP was exactly that — it interpolates, it had no fixture, and its
# invariant was resting on nothing.
NO_INTERPOLATION = {
    "go": "fmt.Sprintf takes the value as an argument; the literal interpolates nothing",
    "java": "concatenation only — string templates were withdrawn before release",
    "c": "printf takes the value as an argument",
    "cpp": "same as c",
    "rust": 'format!("{x}") is a macro and the braces stay inside the string token, so the '
            "grammar exposes no interpolation node to test",
}

# A literal body that is a different length from any fixture's, and that carries escape
# sequences — the thing Swift's grammar splits into `str_escaped_char` nodes.
NEW_STRING_BODY = b"zz\\r\\n\\tzz"
NEW_NUMBER = b"987654"


def nodes_of(parser, blob: bytes, lang: str) -> list:
    root = parser.parse(blob).root_node
    kinds = dry.UNITS[lang]
    stack, found = [root], []
    while stack:
        n = stack.pop()
        if n.type in kinds:
            found.append(n)
            continue
        stack.extend(reversed(n.named_children))
    found.sort(key=lambda n: (n.start_point[0], n.start_byte))
    return found


# What each language's fixtures are built to contain, stated independently of `dry.UNITS`.
# A check that reads its expectation out of the code under test cannot notice that code
# shrinking: delete an entry from UNITS and a self-referential check simply stops looking
# for it and still reports full coverage. Adding a language means adding a row here too —
# that duplication is the point, not an oversight.
EXPECTED_KINDS = {
    "c": {"function_definition"},
    "cpp": {"function_definition"},
    "csharp": {"method_declaration", "constructor_declaration", "local_function_statement"},
    "go": {"function_declaration", "method_declaration"},
    "java": {"method_declaration", "constructor_declaration"},
    "javascript": {"function_declaration", "function_expression", "arrow_function", "method_definition"},
    "kotlin": {"function_declaration"},
    "php": {"function_definition", "method_declaration"},
    "python": {"function_definition"},
    "ruby": {"method", "singleton_method"},
    "rust": {"function_item"},
    "swift": {"function_declaration"},
    "tsx": {"function_declaration", "function_expression", "arrow_function", "method_definition"},
    "typescript": {"function_declaration", "function_expression", "arrow_function", "method_definition"},
}


def unit_kinds(lang: str, files: list[Path], kinds: set[str]) -> tuple[set[str], list[str]]:
    """Which of `kinds` the scan actually reaches across this language's fixtures.

    Deliberately uses the engine's own traversal, which stops descending once it finds a
    unit. An entry that only ever appears *inside* another unit is unreachable and would
    be dead weight in the table — this reports what `dry.py` can really see, not what the
    grammar merely contains. `kinds` is passed in rather than read from `dry.UNITS` so a
    node type deleted from the table is still searched for.
    """
    from tree_sitter_language_pack import get_parser

    parser = get_parser(lang)
    seen: set[str] = set()
    problems: list[str] = []
    for path in files:
        blob = path.read_bytes()
        root = parser.parse(blob).root_node
        if root.has_error:
            problems.append(f"{lang}: {path.name} does not parse cleanly")
            continue
        stack, found = [root], []
        while stack:
            n = stack.pop()
            if n.type in kinds:
                found.append(n)
                continue
            stack.extend(reversed(n.named_children))
        seen.update(n.type for n in found)
    return seen, problems


def literal_opacity(lang: str, files: list[Path]) -> tuple[str, list[str]]:
    """dry4go's rule, asserted directly: a literal's value never reaches a fingerprint.

    Its normaliser turns every literal into one childless `literal/KIND` node and every
    identifier into one childless `ident` node — the kind is kept, the value is never
    read. Here that is `SPELLING`'s job, and Swift broke it: it names its escapes
    `str_escaped_char` and its string body `line_str_text`, so `"x"` scored 0.69 against
    `"x\\n"` instead of 1.0000.

    Rewriting the value rather than nudging it is what makes this provable in Go and
    Kotlin, whose grammars never expose an escape as its own node — there is nothing for
    the escape mutation to bite on, but the value can still be replaced wholesale.
    """
    from tree_sitter_language_pack import get_parser

    parser = get_parser(lang)
    for path in files:
        src = path.read_bytes()
        spans = []
        stack = [parser.parse(src).root_node]
        while stack:
            n = stack.pop()
            if n.end_byte > n.start_byte:
                if n.type.endswith(dry.STR_TEXT):
                    spans.append((n.start_byte, n.end_byte, NEW_STRING_BODY))
                elif n.named_child_count == 0 and n.text.isdigit():
                    spans.append((n.start_byte, n.end_byte, NEW_NUMBER))
            stack.extend(n.named_children)
        if not spans:
            continue

        out = bytearray(src)
        for start, end, rep in sorted(spans, reverse=True):
            out[start:end] = rep
        base, after = nodes_of(parser, src, lang), nodes_of(parser, bytes(out), lang)

        if len(base) != len(after):
            return f"unproven — rewriting literals in {path.name} changed the unit count", []
        bad_shape = [a for a, b in zip(base, after) if dry.shape(a) != dry.shape(b)]
        if bad_shape:
            return "", [f"{lang}: rewriting a literal value in {path.name} changed the tree shape — "
                        f"literal spelling is structural here, so it is leaking into the fingerprints"]
        worst = min(dry.score(dry.fingerprint(a)[0], dry.fingerprint(b)[0]) for a, b in zip(base, after))
        if worst != 1.0:
            return "", [f"{lang}: rewriting literal values in {path.name} moved a score to {worst:.4f}, "
                        f"expected 1.0000 — a literal's value is reaching the fingerprints"]
        return f"passed on {path.name} ({len(spans)} literals)", []
    return "unproven — no literal inside a unit in this scope", []


def interpolation_visible(lang: str, d: Path) -> tuple[str, list[str]]:
    """An interpolation holds code, so it must NOT be dropped the way spelling is.

    `SPELLING` drops what a string *says*. `"${x + 1}"` is not that — it is an expression
    that happens to sit inside quotes, and two functions differing only there differ for
    real. The `interp.*` fixture is built so its one flippable operator is the one inside
    the interpolation; flipping it must move the score. If the interpolation were being
    treated as spelling the flip would still be found in the source and change nothing at
    all, which is exactly the failure this catches.
    """
    from tree_sitter_language_pack import get_parser

    interp = [f for f in sorted(d.iterdir()) if f.is_file() and f.stem.lower() == "interp"]
    if not interp:
        return "not applicable — no interp fixture for this language", []

    parser = get_parser(lang)
    src = interp[0].read_bytes()
    if parser.parse(src).root_node.has_error:
        return "", [f"{lang}: {interp[0].name} does not parse cleanly"]
    base = nodes_of(parser, src, lang)
    if not base:
        return "", [f"{lang}: {interp[0].name} holds no unit"]

    flips = dry.flip_candidates(src, base, limit=1)
    if not flips:
        return "", [f"{lang}: no operator found inside the interpolation in {interp[0].name} — "
                    f"the interpolated expression is not reaching the tree at all"]
    after = nodes_of(parser, flips[0], lang)
    if len(after) != len(base):
        return "", [f"{lang}: flipping the interpolated operator in {interp[0].name} broke the parse"]
    worst = min(dry.score(dry.fingerprint(a)[0], dry.fingerprint(b)[0]) for a, b in zip(base, after))
    if worst == 1.0:
        return "", [f"{lang}: flipping an operator inside an interpolation in {interp[0].name} changed "
                    f"nothing — interpolated code is being normalised away as if it were spelling"]
    return f"passed on {interp[0].name} (flip moved a score to {worst:.4f})", []


# Two shapes `OP_CHARS` alone cannot see: an operator written with letters (`in`,
# `instanceof`), and a chained comparison, which hangs two operator tokens off one node.
# Both were live bugs. In Python's standard library `assertIn`, `assertNotIn` and
# `assertIs` scored 1.0000 against each other — three assertions with three different
# meanings, reported as verbatim duplicates.
#
# The `operator` self-check cannot reach this. It flips operators `operator_token` has
# already found, so an operator that function cannot see is invisible to its own
# detector. Hence a check of its own, with its own fixture.
#
# Stated per language and independently of `dry.OP_WORDS`, for the same reason
# `EXPECTED_KINDS` is stated independently of `dry.UNITS`: a check that reads its
# expectation out of the code under test cannot notice that code shrinking. Empty
# `OP_WORDS` and a self-referential check would look for nothing and find it.
#
# What these fixtures gate is the invariant — the operator reaches a tag — and not one
# route to it. Emptying `OP_WORDS` is caught in csharp, java, kotlin, python and rust
# only; the other seven are silent because their grammars name an `operator` field, so
# `child_by_field_name` hands the word back before `OP_WORDS` is ever consulted. Those
# seven are not blind, they are unaffected: with `OP_WORDS` empty their operators still
# reach the tags, which is the whole of what is claimed here.
#
# The fixtures deliberately hold functions of two or three lines, below `MIN_LINES`.
# This check reads them through the parser directly, while the mixed CLI scan applies
# the floors — so units that differ by one operator, which score high by construction,
# never reach the scan to disturb its "one family per language, and it is clone.*"
# assertion.
EXPECTED_OPS = {
    "cpp": {"and", "or"},
    # `a is not string` is a negated pattern, so the grammar gives `is` and `not` as two
    # nodes rather than one `is not` token the way Python does.
    "csharp": {"as", "is", "not"},
    "java": {"instanceof"},
    "javascript": {"in", "instanceof"},
    # `!in` and `!is` arrive as two anonymous tokens under one node, so they are only
    # visible at all because every anonymous child is tested and the results joined.
    "kotlin": {"in", "is", "! in", "! is"},
    "php": {"and", "instanceof", "or", "xor"},
    "python": {"and", "in", "is", "is not", "not in", "or", "< <", "> >", "< >"},
    "ruby": {"and", "or"},
    "rust": {"as"},
    "swift": {"is"},
    "tsx": {"in", "instanceof"},
    "typescript": {"in", "instanceof"},
}

# Languages with no word operator for an ops.* fixture to test, and why. A set rather
# than mere absence, for the reason NO_INTERPOLATION is: "no fixture" and "nothing to
# test" are different facts, and only one of them is acceptable.
NO_WORD_OPERATORS = {
    "c": "every operator is punctuation; the word spellings live in <iso646.h> and are "
         "macros, so the grammar never sees one",
    "go": "every operator is punctuation; Go has no keyword operator at all",
}


def word_operators(lang: str, d: Path) -> tuple[str, list[str]]:
    """An operator written with letters must reach the fingerprints like any other.

    Two things are asserted, because either alone has a hole. Every operator the
    fixture is built around must appear as a tag — which is the only gate available to
    a language like Java, whose single word operator has nothing to collide with. And no
    two units may fingerprint alike — which is what catches a chain, where both `< <`
    and `> >` can vanish together and leave the tags agreeing.
    """
    from tree_sitter_language_pack import get_parser

    ops = [f for f in sorted(d.iterdir()) if f.is_file() and f.stem.lower() == "ops"]
    if not ops:
        return "not applicable — no ops fixture for this language", []

    parser = get_parser(lang)
    src = ops[0].read_bytes()
    if parser.parse(src).root_node.has_error:
        return "", [f"{lang}: {ops[0].name} does not parse cleanly"]
    units = nodes_of(parser, src, lang)
    if len(units) < 2:
        return "", [f"{lang}: {ops[0].name} holds {len(units)} unit(s), expected at least 2"]

    problems: list[str] = []
    found = set()
    for u in units:
        stack = [u]
        while stack:
            n = stack.pop()
            tag = dry.operator_token(n)
            if tag:
                found.add(tag)
            stack.extend(n.children)

    declared = EXPECTED_OPS.get(lang)
    if declared is None:
        problems.append(f"{lang}: an ops.* fixture ran but no EXPECTED_OPS row says which "
                        f"operators it must put into the fingerprints")
    else:
        missing = sorted(declared - found)
        if missing:
            problems.append(f"{lang}: {ops[0].name} is written around {', '.join(repr(m) for m in missing)} "
                            f"but no fingerprint carries it — the operator is being dropped, so two "
                            f"functions that differ only there read as duplicates")

    shapes = defaultdict(list)
    for u in units:
        shapes[dry.fingerprint(u)[2]].append(u.start_point[0] + 1)
    for lines in shapes.values():
        if len(lines) > 1:
            problems.append(f"{lang}: the units at line {', '.join(str(n) for n in lines)} of "
                            f"{ops[0].name} fingerprint identically — they differ in an operator, "
                            f"so that operator is not reaching the tags")
    return f"passed on {ops[0].name} ({len(units)} units, {len(declared or found)} operators)", problems


def check(lang: str, d: Path) -> list[str]:
    """Return the problems found in one language's fixture. Empty means it conformed."""
    bad: list[str] = []
    files = sorted(f for f in d.iterdir() if f.is_file())
    if not files:
        return [f"{lang}: no fixture file in {d}"]

    for f in files:
        # The extension must still route to the language this directory is named for.
        # A pack upgrade that remaps an extension would otherwise silently drop the
        # fixture from the scan, and an empty scan finds no duplicates, which reads
        # exactly like a pass.
        detected = dry.language_of(f)
        if detected != lang:
            bad.append(f"{lang}: {f.name} detected as {detected!r}, expected {lang!r}")
    if bad:
        return bad

    # `clone.*` carries the planted pair and every mutation check. Any other file exists
    # only to reach UNITS entries the clone shape cannot express — a method, a
    # constructor, an arrow function — so it is kept out of the scoring assertions.
    clone_files = [f for f in files if f.stem.lower() == "clone"]
    if len(clone_files) != 1:
        return [f"{lang}: expected exactly one clone.* fixture, got {len(clone_files)}"]

    expected = EXPECTED_KINDS.get(lang)
    if expected is None:
        bad.append(f"{lang}: no EXPECTED_KINDS row — add one naming the UNITS entries its fixtures cover")
    else:
        # Search for the union, so an entry deleted from UNITS is still looked for and its
        # absence from the table is reported rather than quietly satisfied.
        reached, kind_problems = unit_kinds(lang, files, expected | dry.UNITS[lang])
        bad.extend(kind_problems)
        unreached = sorted(expected - reached)
        if unreached:
            bad.append(f"{lang}: no fixture reaches {', '.join(unreached)} — untested, and an "
                       f"entry the scan can never reach is dead weight in the table")
        if dry.UNITS[lang] != expected:
            gone = sorted(expected - dry.UNITS[lang])
            new = sorted(dry.UNITS[lang] - expected)
            detail = []
            if gone:
                detail.append(f"missing from UNITS: {', '.join(gone)}")
            if new:
                detail.append(f"in UNITS but not covered by a fixture: {', '.join(new)}")
            bad.append(f"{lang}: UNITS and the fixtures disagree — {'; '.join(detail)}")

    opts = argparse.Namespace(min_lines=dry.MIN_LINES, min_nodes=dry.MIN_NODES)
    notes: dict[str, list] = {"parse_errors": [], "too_deep": [], "unreadable": []}

    files = clone_files
    units = list(dry.scan(clone_files[0], lang, opts, notes))

    for kind, entries in notes.items():
        if entries:
            bad.append(f"{lang}: {kind}: {', '.join(entries)}")
    if bad:
        return bad

    if len(units) != 2:
        return [f"{lang}: expected 2 units, got {len(units)} "
                f"(--min-lines {dry.MIN_LINES} / --min-nodes {dry.MIN_NODES} may have cut them)"]

    found = dry.sort_pairs(dry.pairs_indexed(units, dry.THRESHOLD))
    fams = dry.families(found, units)
    if len(fams) != 1:
        bad.append(f"{lang}: expected 1 family, got {len(fams)} — the planted clone was not found")
    else:
        f = fams[0]
        if f["size"] != 2:
            bad.append(f"{lang}: family size {f['size']}, expected 2")
        if f["max_score"] != 1.0:
            bad.append(f"{lang}: planted clone scored {f['max_score']:.4f}, expected 1.0000 — "
                       f"a name or a literal value is leaking into the fingerprints")

    problems, checks = dry.self_check(units, opts)
    bad.extend(f"{lang}: {p}" for p in problems)

    checks["literal"], lit_problems = literal_opacity(lang, files)
    bad.extend(lit_problems)

    checks["interpolation"], interp_problems = interpolation_visible(lang, d)
    bad.extend(interp_problems)

    absent = checks["interpolation"].startswith("not applicable")
    if absent and lang not in NO_INTERPOLATION:
        bad.append(f"{lang}: no interp.* fixture and no NO_INTERPOLATION row — this language "
                   f"interpolates, so the invariant is resting on nothing")
    elif not absent and lang in NO_INTERPOLATION:
        bad.append(f"{lang}: an interp.* fixture ran, but NO_INTERPOLATION says this language has "
                   f"nothing to interpolate — drop the row")

    checks["word operators"], op_problems = word_operators(lang, d)
    bad.extend(op_problems)

    absent = checks["word operators"].startswith("not applicable")
    if absent and lang not in NO_WORD_OPERATORS:
        bad.append(f"{lang}: no ops.* fixture and no NO_WORD_OPERATORS row — this language "
                   f"spells an operator with letters, so nothing proves it reaches a fingerprint")
    elif not absent and lang in NO_WORD_OPERATORS:
        bad.append(f"{lang}: an ops.* fixture ran, but NO_WORD_OPERATORS says this language has "
                   f"no word operator — drop the row")

    for name in ("rename", "operator", "spelling", "literal", "interpolation", "word operators"):
        if checks.get(name, "").startswith("not applicable"):
            continue
        verdict = checks.get(name, "missing")
        if verdict.startswith("passed"):
            continue
        if (lang, name) in UNPROVABLE:
            continue
        bad.append(f"{lang}: {name} check did not pass — {verdict}")
    return bad


# --- brute vs indexed ------------------------------------------------------------

# Seeded, so the corpora are the same set of corpora on every machine and every run.
#
# 500 is not a round number picked for comfort. Against two deliberately broken
# prefilters — a prefix one element short, and a size bound 5% too strict — 200
# corpora missed entirely on some seeds, 500 caught both on every seed tried, and
# 1000 only bought margin. These filters are near-tight, so an off-by-one shows up
# in few corpora; that is the reason for the count, not thoroughness for its own sake.
FUZZ_SEED = 20260810
FUZZ_CORPORA = 500
FUZZ_THRESHOLDS = (0.50, 0.76, 0.90)


def pair_key(found) -> set:
    """A pair set that does not care which member was listed first."""
    return {(s,) + tuple(sorted(((a.file, a.start), (b.file, b.start)))) for s, a, b in found}


def pair_equivalence() -> list[str]:
    """`pairs_indexed` must return exactly what `pairs_brute` returns.

    Nothing else executes `pairs_brute`. It is not a slower alternative kept for
    nostalgia — it is the definition of the answer, and `pairs_indexed` is an
    optimisation trusted to be exact. Both of its prefilters are proved exact on
    paper, and a prefilter that is wrong drops findings silently: fewer duplicates
    reported reads exactly like a cleaner codebase.

    The fixtures hold two units per language, which exercises the filters barely at
    all, so a seeded fuzz over synthetic fingerprint sets carries the real weight.
    """
    bad: list[str] = []
    opts = argparse.Namespace(min_lines=dry.MIN_LINES, min_nodes=dry.MIN_NODES)
    notes: dict[str, list] = {"parse_errors": [], "too_deep": [], "unreadable": []}

    by_lang: dict[str, list] = defaultdict(list)
    for d in sorted(FIXTURES.iterdir()):
        if d.is_dir() and d.name in dry.UNITS:
            for f in sorted(d.iterdir()):
                if f.is_file():
                    by_lang[d.name].extend(dry.scan(f, d.name, opts, notes))

    for lang, units in sorted(by_lang.items()):
        for t in FUZZ_THRESHOLDS:
            if pair_key(dry.pairs_brute(units, t)) != pair_key(dry.pairs_indexed(units, t)):
                bad.append(f"{lang}: the prefilters change the answer on the fixtures at threshold {t}")

    # Sizes and overlaps that the fixtures never produce: sets small enough for the
    # size bound to bite, drawn from a pool small enough that they genuinely overlap.
    rng = random.Random(FUZZ_SEED)
    for n in range(FUZZ_CORPORA):
        units = [
            dry.Unit(f"f{i}", i, i, 0, {rng.randrange(30) for _ in range(rng.randrange(3, 16))}, "python")
            for i in range(12)
        ]
        for t in FUZZ_THRESHOLDS:
            brute, indexed = pair_key(dry.pairs_brute(units, t)), pair_key(dry.pairs_indexed(units, t))
            if brute != indexed:
                bad.append(f"random corpus {n} at threshold {t}: prefilters missed "
                           f"{len(brute - indexed)} pair(s), invented {len(indexed - brute)}")

    # A pair landing exactly on the threshold, which the fuzz above cannot reach: both
    # bounds are derived from `threshold * size`, and that product only misses an integer
    # by a float hair when it should land on one — `0.55 * 100` is 55.00000000000001. The
    # fuzz draws 3 to 15 fingerprints, so no seed of it can ever produce the sizes where
    # this bites. Swept rather than sampled: a hundredth of a percent apart, the bad
    # thresholds have nothing in common, so a needle is the only thing to look for.
    for hundredths in range(50, 100):
        t = hundredths / 100
        # `inner` sits wholly inside `outer`, so their score is exactly `t`, and every
        # such pair is a duplicate that brute force reports and the index must not lose.
        units = [dry.Unit("outer.py", 1, 1, 0, set(range(100)), "python"),
                 dry.Unit("inner.py", 1, 1, 0, set(range(100 - hundredths, 100)), "python")]
        brute, indexed = pair_key(dry.pairs_brute(units, t)), pair_key(dry.pairs_indexed(units, t))
        if brute != indexed:
            bad.append(f"a pair scoring exactly {t} was reported by brute force and "
                       f"{'missed' if brute - indexed else 'invented'} by the prefilters")
    return bad


# --- families --------------------------------------------------------------------

def fake_units(*sets: set) -> list:
    """Units that exist only to have fingerprints. `families` reads nothing else."""
    return [dry.Unit(f"f{i}.py", 1, 9, len(s), s, "python") for i, s in enumerate(sets)]


def family_shapes() -> list[str]:
    """Everything above tests families of exactly two. The interesting ones have three.

    A family is a connected component, not a clique, and the whole reason to report
    families rather than pairs is that three clones make three pairs but only one
    thing to fix. Two properties follow, and neither has been asserted anywhere:

      * A and C belong together when each matches B, even if A and C never matched
        each other. Report them as two findings and somebody fixes the same knowledge
        twice.
      * `max_score` is a maximum over the edges that exist. On a chain there is no
        A–C edge at all, so any summary that reads like a floor for the family is
        describing a measurement that was never taken.

    Sets are built by hand rather than parsed, so the scores are arithmetic rather
    than whatever the grammar happens to produce.
    """
    bad: list[str] = []
    t = dry.THRESHOLD

    # A chain: A–B and B–C clear the threshold, A–C does not. The two edges are
    # deliberately unequal — with a symmetric chain the weakest edge and the strongest
    # are the same number, and "max_score is a maximum" stops being a claim at all.
    a, b, c = set(range(0, 100)), set(range(6, 106)), set(range(18, 118))
    ab, bc, ac = dry.score(a, b), dry.score(b, c), dry.score(a, c)
    if not (ab >= t and bc >= t and ac < t and ab != bc):
        return [f"the chain corpus no longer forms a chain of two unequal edges at threshold {t}: "
                f"A-B {ab:.4f}, B-C {bc:.4f}, A-C {ac:.4f} — fix the sets, not the assertion"]

    units = fake_units(a, b, c)
    fams = dry.families(dry.sort_pairs(dry.pairs_indexed(units, t)), units)
    if len(fams) != 1:
        bad.append(f"a chain of three made {len(fams)} families, expected 1 — a family is a "
                   f"connected component, so the ends belong together even though they never matched")
    elif fams[0]["size"] != 3:
        bad.append(f"a chain of three made a family of {fams[0]['size']}, expected 3")
    elif fams[0]["max_score"] != max(ab, bc):
        bad.append(f"the chain's max_score is {fams[0]['max_score']:.4f}, expected {max(ab, bc):.4f} — "
                   f"the maximum over the edges that exist, never the unmeasured A-C pair")

    # Three identical units: three pairs, still one family.
    same = set(range(100))
    units = fake_units(same, set(same), set(same))
    fams = dry.families(dry.sort_pairs(dry.pairs_indexed(units, t)), units)
    if len(fams) != 1 or fams[0]["size"] != 3 or fams[0]["max_score"] != 1.0:
        bad.append(f"three identical units made {len(fams)} family/families "
                   f"{[f['size'] for f in fams]}, expected one of size 3 at 1.0000")

    # Two unrelated pairs stay two families, and a unit that matched nothing is in none.
    far = set(range(1000, 1100))
    units = fake_units(same, set(same), far, set(far), set(range(2000, 2100)))
    fams = dry.families(dry.sort_pairs(dry.pairs_indexed(units, t)), units)
    if [f["size"] for f in fams] != [2, 2]:
        bad.append(f"two unrelated pairs plus a loner made families {[f['size'] for f in fams]}, "
                   f"expected [2, 2] — a unit matching nothing belongs to no family")

    # The sort the report depends on: best score first, then the larger family. Three
    # families are needed, drawn from pools far enough apart that they cannot merge —
    # one family cannot be out of order with itself, and a corpus that collapses into a
    # single family passes this no matter how it is sorted.
    big = [set(range(1000, 1100)) for _ in range(3)]                 # 1.0000, size 3
    pair = [set(range(0, 100)) for _ in range(2)]                    # 1.0000, size 2
    chain = [set(range(2000 + n, 2100 + n)) for n in (0, 5, 10)]     # 0.9048, size 3
    units = fake_units(*big, *pair, *chain)
    fams = dry.families(dry.sort_pairs(dry.pairs_indexed(units, t)), units)
    order = [(round(f["max_score"], 4), f["size"]) for f in fams]
    if len(order) != 3:
        bad.append(f"the sort corpus made {len(order)} families, expected 3 — it cannot test an "
                   f"order it does not have")
    elif order != sorted(order, key=lambda x: (-x[0], -x[1])):
        bad.append(f"families came back in the order {order}, expected highest score first "
                   f"then largest family — the report reads them in this order")
    return bad


# --- what the walk collects, and what it survives --------------------------------

def scan_scope() -> list[str]:
    """Which files a scan picks up, and whether one bad unit can take the run down.

    Both of these fail by producing nothing rather than by producing something wrong,
    which is the failure mode this whole engine is built to refuse.

      * `SKIP_DIRS` must be matched against the path *below the scanned root*. Matched
        against the whole path, a project that merely lives under a directory called
        `build`, `dist`, `target` or `venv` has every one of its files skipped.
      * `scan` records a unit too deep to fingerprint and moves on. `self_check` walks
        the same files again from source, so it meets that unit too — and it must not
        take the process out over a unit the report was never going to mention.
    """
    bad: list[str] = []
    clone = (FIXTURES / "python" / "clone.py").read_bytes()

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "build" / "app"          # a real project under a skipped name
        (root / "node_modules").mkdir(parents=True)
        (root / "clone.py").write_bytes(clone)
        (root / "node_modules" / "vendored.py").write_bytes(clone)

        found = {p.name for p in dry.source_files([str(root)])}
        if "clone.py" not in found:
            bad.append("a project directory living under a folder named 'build' was skipped "
                       "entirely — SKIP_DIRS is matching the scanned root's own path")
        if "vendored.py" in found:
            bad.append("node_modules inside the scanned tree was not skipped")

        # A unit too deep for the fingerprint walk, next to an ordinary one. The limit is
        # lowered rather than the nesting raised: the file stays small and the parse fast,
        # and it is the same guard either way.
        deep = b"(" * 900 + b"1" + b")" * 900
        (root / "deep.py").write_bytes(clone + b"\n\ndef deepy(x):\n    y = " + deep +
                                       b"\n    z = y + 1\n    w = z * 2\n    return w + z\n")
        opts = argparse.Namespace(min_lines=dry.MIN_LINES, min_nodes=dry.MIN_NODES)
        notes: dict[str, list] = {"parse_errors": [], "too_deep": [], "unreadable": []}
        limit = sys.getrecursionlimit()
        try:
            sys.setrecursionlimit(600)
            units = dry.scan(root / "deep.py", "python", opts, notes)
            if not notes["too_deep"]:
                bad.append("the deep unit was fingerprinted after all — this case no longer "
                           "tests what it is here to test, deepen it")
            elif not units:
                bad.append("the ordinary units in the deep file were dropped too, so self_check "
                           "is never handed the file — deepen only the one function")
            else:
                dry.self_check(units, opts)
        except RecursionError:
            bad.append("a unit too deep to fingerprint took self_check down with it — scan "
                       "skips that unit, and a run must survive what the report omits")
        finally:
            sys.setrecursionlimit(limit)

    # A path that is neither a file nor a directory must be reported, not dropped. Half
    # a scope scanned in silence still prints a report, and the report is read as
    # covering everything that was asked for.
    notes = {"parse_errors": [], "too_deep": [], "unreadable": [], "missing": []}
    found = dry.source_files([str(FIXTURES / "python"), str(FIXTURES / "no-such-dir")], notes)
    if not found:
        bad.append("the real half of a half-typo scope found nothing, so this case proves nothing")
    if not notes["missing"]:
        bad.append("a path that does not exist was dropped in silence — the report then covers "
                   "less than it was asked for and says so nowhere")
    return bad


# --- the threshold across languages ----------------------------------------------

# Go is the only language with an independent oracle: dry4go finds 150 families in
# net/http and this engine finds all 150, at 0.76. The other thirteen inherit that
# number, and inheriting it is only sound if the same divergence costs about the same
# score everywhere. That is what this measures — not recall, which would need a second
# implementation per language, and there is not one.
#
# Observed spread across the fourteen, one flip: 0.643 (javascript) to 0.778 (rust).
# Two flips: 0.484 to 0.641. Three: 0.333 to 0.488. The bound is set above the widest
# of those with room, so a grammar upgrade that shifts one language a little does not
# fail, but one language drifting apart from the rest does.
TRANSFER_SPREAD = 0.20

# The band is narrow, but 0.76 falls inside it, so the same edit can land on either
# side of the threshold depending on the language. Measured: one flipped operator in
# these fixtures reads as "no longer a duplicate" in thirteen languages and as "still
# a duplicate" in Rust, at 0.7778.
#
# That is the grammar, not the engine. Flipping an operator rewrites the fingerprint
# of that node and of every enclosing one, so the cost is how many nodes sit between
# the operator and the unit root. For the same fixture and the same 32 fingerprints,
# Go wraps its `value + 1` in `expression_list` and `statement_list` on the way up and
# loses 6 fingerprints; Rust's chain is `binary_expression < let_declaration < block`
# and loses 4.
#
# Recorded here rather than asserted away, and stated as an exact set: this is the
# limit of what "0.76, inherited from Go" is worth, and a grammar upgrade that moves a
# second language across the line should be reported, not absorbed.
TRANSFER_ABOVE = {"rust"}
FLIP_SWAPS = {"+": b"-", "-": b"+", "==": b"!=", "!=": b"==", "<": b">", ">": b"<", "*": b"/", "&&": b"||"}


def flip_sites(unit) -> list[tuple[int, int, bytes]]:
    """Every flippable binary operator in one unit, in source order.

    dry.flip_candidates returns one source per flip; this needs them applied together,
    so the sites are collected here instead. Every replacement is the same length as
    what it replaces, so applying several does not move the later offsets.
    """
    hits, stack = [], [unit]
    while stack:
        n = stack.pop()
        op = dry.operator_token(n)
        if op in FLIP_SWAPS and n.named_child_count >= 2:
            for child in n.children:
                if not child.is_named and child.text.decode("utf-8", "replace") == op:
                    hits.append((child.start_byte, child.end_byte, FLIP_SWAPS[op]))
                    break
        stack.extend(n.named_children)
    return sorted(hits)


def threshold_transfer() -> list[str]:
    """One threshold, fourteen languages: does a given divergence cost the same score?

    Each `clone.*` holds two functions that score 1.0000. Flipping operators in the
    first one, one at a time, walks it away from the second by a divergence that means
    the same thing in every language: k fewer matching operations. Three things must
    hold, or 0.76 is a Go number being quoted at thirteen other languages.
    """
    from tree_sitter_language_pack import get_parser

    bad: list[str] = []
    curves: dict[str, list[float]] = {}
    for lang in sorted(dry.UNITS):
        d = FIXTURES / lang
        clone = [f for f in sorted(d.iterdir()) if f.is_file() and f.stem.lower() == "clone"] if d.is_dir() else []
        if not clone:
            bad.append(f"{lang}: no clone fixture to walk away from")
            continue
        parser = get_parser(lang)
        src = clone[0].read_bytes()
        base = nodes_of(parser, src, lang)
        if len(base) != 2:
            bad.append(f"{lang}: {clone[0].name} holds {len(base)} units, expected 2")
            continue
        target = dry.fingerprint(base[1])[0]
        sites = flip_sites(base[0])
        if len(sites) < 2:
            bad.append(f"{lang}: {clone[0].name} has {len(sites)} flippable operator(s) in its first "
                       f"unit, need 2 — there is no ladder to walk down")
            continue

        curve = []
        for k in range(1, len(sites) + 1):
            out = bytearray(src)
            for start, end, rep in reversed(sites[:k]):
                out[start:end] = rep
            after = nodes_of(parser, bytes(out), lang)
            if len(after) != len(base):
                bad.append(f"{lang}: flipping {k} operator(s) in {clone[0].name} broke the parse")
                break
            curve.append(dry.score(dry.fingerprint(after[0])[0], target))
        else:
            curves[lang] = curve

    above = {lang for lang, curve in curves.items() if curve[0] >= dry.THRESHOLD}
    if above != TRANSFER_ABOVE:
        joined = sorted(above - TRANSFER_ABOVE)
        left = sorted(TRANSFER_ABOVE - above)
        detail = []
        if joined:
            detail.append(f"{', '.join(joined)} now stays above it too")
        if left:
            detail.append(f"{', '.join(left)} no longer does")
        bad.append(f"one flipped operator falls below {dry.THRESHOLD} in every language except "
                   f"{', '.join(sorted(TRANSFER_ABOVE))}, and that has changed — {'; '.join(detail)}")

    for lang, curve in sorted(curves.items()):
        if any(x <= y for x, y in zip(curve, curve[1:])):
            bad.append(f"{lang}: the score does not fall with every extra flip: "
                       f"{', '.join(f'{s:.4f}' for s in curve)}")

    depth = max((len(c) for c in curves.values()), default=0)
    for k in range(depth):
        at_k = {lang: c[k] for lang, c in curves.items() if len(c) > k}
        if len(at_k) < 2:
            continue
        spread = max(at_k.values()) - min(at_k.values())
        if spread > TRANSFER_SPREAD:
            low = min(at_k, key=at_k.get)
            high = max(at_k, key=at_k.get)
            bad.append(f"after {k + 1} flip(s) the languages disagree by {spread:.4f} "
                       f"(> {TRANSFER_SPREAD}): {low} {at_k[low]:.4f} to {high} {at_k[high]:.4f} — "
                       f"one threshold cannot mean the same thing in both")
    return bad


# --- the whole pipeline, as the skill runs it -------------------------------------

def cli_contract() -> list[str]:
    """Run dry.py the way the skill's own steps run it, over all fourteen at once.

    Everything else in this file calls the engine's parts directly. This calls the
    command, on a tree holding every language, and reads the JSON the workflow reads.
    Two things only a mixed run can get wrong: units of different languages compared
    against each other, which their node vocabularies make meaningless, and a self
    check that passes on the scan as a whole because one language proved a thing the
    other thirteen never did.

    Being a subprocess, this is the one check the sabotage pass below cannot see —
    patching this process does not reach into another one.
    """
    bad: list[str] = []
    proc = subprocess.run([sys.executable, str(HERE / "dry.py"), str(FIXTURES), "--format", "json"],
                          capture_output=True, text=True, timeout=300)
    if proc.returncode != 0:
        return [f"dry.py over all fixtures exited {proc.returncode}: {proc.stderr.strip()[:400]}"]
    report = json.loads(proc.stdout)
    run = report["run"]

    langs = {d.name for d in FIXTURES.iterdir() if d.is_dir()}
    if set(run["by_language"]) != langs:
        bad.append(f"the mixed scan reported languages {sorted(run['by_language'])}, "
                   f"expected {sorted(langs)}")
    if sum(run["by_language"].values()) != run["units"]:
        bad.append(f"by_language sums to {sum(run['by_language'].values())}, not the {run['units']} units")
    for kind in ("units_with_parse_errors", "units_too_deep", "files_unreadable"):
        if run[kind]:
            bad.append(f"the mixed scan reported {run[kind]} {kind}")
    for name, verdict in run["checks"].items():
        if not verdict.startswith(("passed", "unproven")):
            bad.append(f"the mixed scan's {name} check reported {verdict!r}")

    fams = report["families"]
    # One planted clone per language, and nothing else. The kinds.* and interp.*
    # functions are ordinary code that happens to sit in the same tree: if any of them
    # turned up in a family, the engine is pairing things that are not duplicates.
    by_lang = defaultdict(list)
    for f in fams:
        dirs = {Path(m["file"]).parent.name for m in f["members"]}
        if len(dirs) != 1:
            bad.append(f"a family mixes languages: {sorted(dirs)} — units of different grammars "
                       f"do not share a node vocabulary, so their score is not a measurement")
            continue
        where = dirs.pop()
        by_lang[where].append(f)
        if f["language"] != where:
            bad.append(f"a family of {where} fixtures is reported as {f['language']}")
        stems = {Path(m["file"]).stem.lower() for m in f["members"]}
        if stems != {"clone"}:
            bad.append(f"a family in {f['language']} covers {sorted(stems)}, expected only the "
                       f"planted clone.* pair")
        if "cochange" not in f:
            bad.append(f"a family in {f['language']} has no cochange field — the report prints one")
    for lang in sorted(langs):
        got = by_lang.get(lang, [])
        if len(got) != 1 or got[0]["size"] != 2 or got[0]["max_score"] != 1.0:
            bad.append(f"{lang}: the mixed scan found {[(f['size'], round(f['max_score'], 4)) for f in got]}, "
                       f"expected exactly one family of size 2 at 1.0000")

    # The text format is what a human reads, and nothing else executes it.
    proc = subprocess.run([sys.executable, str(HERE / "dry.py"), str(FIXTURES / "python")],
                          capture_output=True, text=True, timeout=300)
    if proc.returncode != 0 or "DUPLICATE score=1.00 size=2" not in proc.stdout:
        bad.append(f"the text report over fixtures/python did not name the planted clone: "
                   f"{proc.stdout.strip()[:200]!r}")
    # The text format must say what it scanned and what the self-checks found, not only
    # what it found. Printing findings alone means a run where every file failed to parse
    # prints "No duplicate candidates found." — the same sentence a clean repo gets, with
    # the evidence that the answer was worthless sitting in JSON nobody asked for.
    missing = [want for want in ("scanned ", "units", "operator: passed", "rename: passed")
               if want not in proc.stdout]
    if missing:
        bad.append(f"the text report does not show {', '.join(missing)} — a reader cannot tell "
                   f"a clean scan from one where nothing parsed")
    return bad


# --- sabotage --------------------------------------------------------------------

# Everything above proves dry.py is currently right. None of it proves this suite
# would notice if that stopped being true — a suite that passes on a broken engine
# is worse than no suite, because it is read as evidence.
#
# So each entry below breaks dry.py on purpose, in a way a careless table edit really
# could, and the suite above must fail on at least one language. The assertion is
# "caught somewhere", never a count: a grammar upgrade can move which languages carry
# a node type, and pinning the count would make that upgrade look like a regression.


def drop_suffix(suffix: str):
    return lambda d: setattr(d, "SPELLING_SUFFIX", tuple(s for s in d.SPELLING_SUFFIX if s != suffix))


def drop_unit(lang: str, kind: str):
    return lambda d: d.UNITS[lang].discard(kind)


def interpolation_as_spelling(d) -> None:
    """Treat `${x + 1}` as something a string merely says, rather than as code."""
    inner = d.structural
    d.structural = lambda n: inner(n) and "interpolat" not in n.type and "substitution" not in n.type


def normalise_operators_away(d) -> None:
    d.OP_FIELDS = ()
    d.OP_CHARS.clear()
    d.OP_WORDS.clear()


def one_anonymous_operator(d) -> None:
    """The rule before chains: an operator is a node's *one* anonymous child, or nothing.

    Reimplemented whole rather than patched, because the difference is one clause and a
    reader should be able to hold both versions side by side. `operator_like` is left
    alone, so word operators still work and only the chain goes blind — the two ways
    this can rot are two entries, not one.
    """
    def operator_token(node):
        for field in d.OP_FIELDS:
            child = node.child_by_field_name(field)
            if child is not None and not child.is_named:
                return child.text.decode("utf-8", "replace")
        anon = [c.text.decode("utf-8", "replace") for c in node.children if not c.is_named]
        if len(anon) == 1 and d.operator_like(anon[0]):
            return anon[0]
        return None

    d.operator_token = operator_token


def families_never_connect(d) -> None:
    """Report pairs rather than components: every pair becomes its own family."""
    real = d.families
    d.families = lambda found, units: [f for s, a, b in found for f in real([(s, a, b)], units)]


def families_report_weakest(d) -> None:
    """Summarise a family by its worst edge instead of its best."""
    real = d.families
    def families(found, units):
        out = real(found, units)
        for f in out:
            members = {(m["file"], m["start_line"]) for m in f["members"]}
            edges = [s for s, a, b in found
                     if {(a.file, a.start), (b.file, b.start)} <= members]
            f["max_score"] = min(edges) if edges else f["max_score"]
        return out
    d.families = families


def families_sorted_backwards(d) -> None:
    """Put the weakest family at the top, where the report reads the strongest."""
    real = d.families
    def families(found, units):
        out = real(found, units)
        out.sort(key=lambda f: (f["max_score"], f["size"]))
        return out
    d.families = families


def skip_dirs_absolute(d) -> None:
    """Match SKIP_DIRS against the absolute path, root prefix included."""
    def source_files(paths):
        seen = set()
        for raw in paths:
            p = Path(raw)
            if p.is_file():
                seen.add(p)
            elif p.is_dir():
                for child in p.rglob("*"):
                    if child.is_file() and not (d.SKIP_DIRS & set(child.parts)):
                        seen.add(child)
        return sorted(seen)
    d.source_files = source_files


def leak_identifiers(d) -> None:
    """`fingerprint`, rewritten to put the identifier's text into the tag.

    Reimplemented rather than patched: this is the failure the whole design exists to
    prevent, so it is worth stating as a whole function that a reader can compare
    against the real one line by line.
    """
    def fingerprint(node):
        fps: set[int] = set()
        count = 0

        def walk(n, field):
            nonlocal count
            count += 1
            tag = n.type
            op = d.operator_token(n)
            if op is not None:
                tag += "/" + op
            if n.type.endswith("identifier") or n.type == "name":
                tag += "=" + n.text.decode("utf-8", "replace")
            if field:
                tag = field + ":" + tag
            parts = [tag]
            for child, child_field in d.kids(n):
                parts.append(walk(child, child_field))
            sexp = "(" + " ".join(parts) + ")"
            fps.add(int.from_bytes(hashlib.blake2b(sexp.encode(), digest_size=8).digest(), "big"))
            return sexp

        return fps, count, walk(node, None)

    d.fingerprint = fingerprint


SABOTAGE = [
    ("SPELLING drops str_escaped_char", lambda d: d.SPELLING.discard("str_escaped_char")),
    ("SPELLING drops escape_sequence", lambda d: d.SPELLING.discard("escape_sequence")),
    ("SPELLING drops comment", lambda d: d.SPELLING.discard("comment")),
    ("SPELLING_SUFFIX drops _content", drop_suffix("_content")),
    ("SPELLING_SUFFIX drops _fragment", drop_suffix("_fragment")),
    ("SPELLING_SUFFIX drops _str_text", drop_suffix("_str_text")),
    ("SPELLING_SUFFIX drops _comment", drop_suffix("_comment")),
    ("an interpolation is treated as spelling", interpolation_as_spelling),
    ("operators are normalised away", normalise_operators_away),
    ("OP_WORDS is empty, so a word operator is not one", lambda d: d.OP_WORDS.clear()),
    ("an operator must be a node's only anonymous child", one_anonymous_operator),
    ("rename_identifiers renames nothing", lambda d: setattr(d, "rename_identifiers", lambda src, root: src)),
    ("UNITS loses arrow_function (javascript)", drop_unit("javascript", "arrow_function")),
    ("UNITS loses method_declaration (go)", drop_unit("go", "method_declaration")),
    ("UNITS loses singleton_method (ruby)", drop_unit("ruby", "singleton_method")),
    ("UNITS loses local_function_statement (csharp)", drop_unit("csharp", "local_function_statement")),
    ("UNITS loses constructor_declaration (java)", drop_unit("java", "constructor_declaration")),
    ("UNITS loses function_definition (python)", drop_unit("python", "function_definition")),
    ("UNITS mistypes method as methodX (ruby)", lambda d: d.UNITS.__setitem__("ruby", {"methodX", "singleton_method"})),
    ("fingerprints leak identifier text", leak_identifiers),
    ("families are pairs, never connected components", families_never_connect),
    ("a family is summarised by its weakest edge", families_report_weakest),
    ("families are sorted weakest first", families_sorted_backwards),
    ("SKIP_DIRS is matched against the whole path", skip_dirs_absolute),
    ("the prefilter bounds are rounded straight off the float", lambda d: setattr(d, "EPS", 0.0)),
]


def catcher(dirs: dict) -> str | None:
    """The first part of the suite that objects to whatever dry.py currently is.

    Languages first, then the engine-level checks cheapest first, and it stops at the
    first objection: the question here is yes or no, and running the rest costs time
    to learn nothing. `cli_contract` is not in the list — it runs dry.py in another
    process, where a patch applied to this one does not reach.
    """
    for lang, d in sorted(dirs.items()):
        if lang not in dry.UNITS:
            continue
        try:
            if check(lang, d):
                return lang
        except Exception as err:  # a crash is a failure too, and just as loud
            return f"{lang} ({type(err).__name__})"
    for name, fn in (("families", family_shapes), ("scope", scan_scope),
                     ("transfer", threshold_transfer),
                     ("prefilters", pair_equivalence)):
        try:
            if fn():
                return name
        except Exception as err:
            return f"{name} ({type(err).__name__})"
    return None


def sabotage(dirs: dict) -> list[str]:
    """Break dry.py one way per table entry; every break must fail some check above.

    `dry` is reloaded before each one, or the damage compounds and a later sabotage
    is "caught" by the wreckage left by an earlier one. Reload returns the same module
    object, so every `dry.X` reference in this file keeps working.
    """
    missed: list[str] = []
    for label, patch in SABOTAGE:
        importlib.reload(dry)
        patch(dry)
        caught = catcher(dirs)
        print(f"{'ok  ' if caught else 'MISS'}  caught by {caught or '— NOTHING':<12}  {label}")
        if not caught:
            missed.append(f"nothing caught it when {label}")
    importlib.reload(dry)  # leave the module as it was found
    return missed


def main() -> int:
    if not FIXTURES.is_dir():
        print(f"no fixtures directory at {FIXTURES}", file=sys.stderr)
        return 2

    dirs = {d.name: d for d in sorted(FIXTURES.iterdir()) if d.is_dir()}

    # Every language the engine claims to support needs a fixture, or "aligned across
    # languages" is a claim about whichever ones somebody remembered to cover.
    missing = sorted(set(dry.UNITS) - set(dirs))
    extra = sorted(set(dirs) - set(dry.UNITS))

    failures: list[str] = []
    for lang, d in dirs.items():
        if lang not in dry.UNITS:
            continue
        bad = check(lang, d)
        failures.extend(bad)
        print(f"{'FAIL' if bad else 'ok  '}  {lang}")

    for lang in missing:
        failures.append(f"{lang}: in UNITS but has no fixture directory")
    for lang in extra:
        failures.append(f"{lang}: has a fixture directory but is not in UNITS")

    failures.extend(family_shapes())
    failures.extend(scan_scope())
    failures.extend(threshold_transfer())
    failures.extend(pair_equivalence())
    failures.extend(cli_contract())

    print()
    if failures:
        for f in failures:
            print("FAIL: " + f, file=sys.stderr)
        print(f"\n{len(failures)} problem(s) across {len(dirs)} languages", file=sys.stderr)
        return 1

    # Last, because it takes dry.py apart. Only meaningful once everything above passes:
    # asking whether a broken engine would be caught is not a question about a suite
    # that is already failing.
    missed = sabotage(dirs)
    print()
    if missed:
        for m in missed:
            print("FAIL: " + m, file=sys.stderr)
        print(f"\n{len(missed)} sabotage(s) went unnoticed — the suite above is not gating "
              f"what it appears to gate", file=sys.stderr)
        return 1

    unproven = ", ".join(f"{lang}/{name}" for lang, name in sorted(UNPROVABLE))
    print(f"all {len(dirs)} languages conform")
    print("families of three hold together, and are summarised by an edge that exists")
    print(f"the languages stay within {TRANSFER_SPREAD} of each other as a clone is walked "
          f"away, but {dry.THRESHOLD} sits inside that band:")
    print(f"  one flipped operator reads as a duplicate still in {', '.join(sorted(TRANSFER_ABOVE))}, "
          f"and as no longer one in the other {len(dry.UNITS) - len(TRANSFER_ABOVE)}")
    print(f"prefilters agree with brute force on the fixtures and on "
          f"{FUZZ_CORPORA} seeded random corpora")
    print(f"one mixed scan over all {len(dirs)}: one family per language, none mixing two")
    print(f"all {len(SABOTAGE)} sabotages were caught")
    print(f"escape mutation not expressible by the grammar: {unproven}")
    print("  go is covered instead by the literal check; kotlin folds an escaped body into")
    print("  one node, so its spelling behaviour cannot leak and cannot be gated here")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
