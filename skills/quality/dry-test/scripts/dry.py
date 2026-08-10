#!/usr/bin/env python3
"""dry.py — structural duplication finder, the dry4go algorithm over tree-sitter grammars.

Each function or method becomes one unit. Its syntax tree is serialised into one
S-expression per subtree, reading node types and operators but never a name or a
literal value. Two units are compared by Jaccard similarity over those fingerprint
sets:

    score = shared fingerprints / all fingerprints seen in either unit

Ported from Robert C. Martin's dry4go (https://github.com/unclebob/dry4go), which
does the same over Go's own AST. The thresholds and the sort order are his.

Needs: pip install tree-sitter-language-pack
"""

from __future__ import annotations

import argparse
import functools
import hashlib
import json
import math
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

# Node types that count as one comparable unit, per language. A unit nested inside
# another unit is never its own unit — a closure belongs to the function holding it,
# exactly as dry4go treats a Go func literal.
UNITS: dict[str, set[str]] = {
    "python": {"function_definition"},
    "go": {"function_declaration", "method_declaration"},
    "javascript": {"function_declaration", "function_expression", "arrow_function", "method_definition"},
    "typescript": {"function_declaration", "function_expression", "arrow_function", "method_definition"},
    "tsx": {"function_declaration", "function_expression", "arrow_function", "method_definition"},
    "java": {"method_declaration", "constructor_declaration"},
    "kotlin": {"function_declaration"},
    "swift": {"function_declaration"},
    "csharp": {"method_declaration", "constructor_declaration", "local_function_statement"},
    "php": {"function_definition", "method_declaration"},
    "ruby": {"method", "singleton_method"},
    "rust": {"function_item"},
    "c": {"function_definition"},
    "cpp": {"function_definition"},
}

SKIP_DIRS = {".git", "vendor", "target", "node_modules", "__pycache__", "dist", "build", ".venv", "venv"}

# Spelling, not structure. Grammars expose the inside of a string — its text runs and
# its escape sequences — as child nodes, so `"a\r\n\r\n"` and `"a\n"` would come out
# structurally different. Go's own AST hands dry4go one opaque literal, and that is
# the behaviour to match. Interpolations are not in this list: `${x}` holds code.
#
# Grammars disagree on what to call the characters inside a string: python, go, kotlin,
# ruby, c, rust and php say `*_content`, JS/TS say `*_fragment`, and Swift says
# `line_str_text` / `multi_line_str_text`. Swift also gives its escapes their own name,
# `str_escaped_char`, rather than the `escape_sequence` everyone else uses.
STR_TEXT = ("_content", "_fragment", "_str_text")
SPELLING = {"escape_sequence", "str_escaped_char", "string_start", "string_end", "comment"}
SPELLING_SUFFIX = STR_TEXT + ("_comment",)


# Operators are anonymous tokens, so they must be read back deliberately or `a + b`
# and `a - b` become the same shape. Most grammars name the field `operator`, Swift
# says `op`, and Kotlin names nothing — there the operator is in the node's anonymous
# children. Requiring *every* anonymous child to look like an operator keeps braces,
# commas and semicolons out, while still reading a chain: `lo < x < hi` has two, and
# joining them is what separates it from `lo > x > hi`.
#
# Do not add `operators` (plural, the field tree-sitter-python gives a chain) to
# OP_FIELDS: child_by_field_name returns only the first match, which throws the
# distinction away again.
OP_FIELDS = ("operator", "op")
OP_CHARS = set("+-*/%<>=!&|^~")
OP_NOT = {"->", "=>"}
# Operators the grammars spell as keywords, so the character test never sees them.
OP_WORDS = {"in", "is", "not", "and", "or", "xor", "as", "instanceof", "typeof"}


def operator_like(text: str) -> bool:
    # `not in` and `is not` arrive as one token whose text carries a space, so the test
    # is per word, not on the whole string.
    words = text.split()
    if words and all(w in OP_WORDS for w in words):
        return True
    return 0 < len(text) <= 3 and set(text) <= OP_CHARS and text not in OP_NOT


def operator_token(node) -> str | None:
    for field in OP_FIELDS:
        child = node.child_by_field_name(field)
        if child is not None and not child.is_named:
            return child.text.decode("utf-8", "replace")
    anon = [c.text.decode("utf-8", "replace") for c in node.children if not c.is_named]
    if anon and all(operator_like(t) for t in anon):
        return " ".join(anon)
    return None


def structural(node) -> bool:
    return not (node.type in SPELLING or node.type.endswith(SPELLING_SUFFIX))


def kids(node) -> list:
    """Named children that carry structure, with their field names."""
    out = []
    for i in range(node.named_child_count):
        child = node.named_child(i)
        if structural(child):
            out.append((child, node.field_name_for_named_child(i)))
    return out

# dry4go's default is 0.82 against its own normaliser. This one keeps a little more
# structure — field names, and the variables of a `range` loop, which dry4go drops —
# so the same number is a stricter cut. Swept against dry4go over Go's net/http
# (2,178 units), 0.76 is where every one of its 150 findings comes back. Calibrated
# on Go only; for other languages the number is inherited, not measured.
THRESHOLD = 0.76
# Wide enough to swallow the float error in `threshold * size` at any size a repo can
# reach, small enough never to move a bound that was not already on an integer.
EPS = 1e-9
MIN_LINES = 4
MIN_NODES = 20
SINCE = "12.months"

# At module scope, not inside main(): `fingerprint` is the one recursive function here,
# and the conformance suite imports this module and calls it directly. Raising the limit
# only for CLI runs would let the suite call a deeply nested unit too_deep while the tool
# fingerprints it happily — the suite and the tool disagreeing about the same input.
sys.setrecursionlimit(20000)


# --- fingerprints ----------------------------------------------------------------

def fingerprint(node) -> tuple[set[int], int, str]:
    """Fingerprint set, node count, and the root S-expression, built bottom up.

    Every subtree contributes one fingerprint. Named children only — tree-sitter
    also reports commas and braces, and counting those measures punctuation.
    Operators are anonymous, so they are read back from the `operator` field and
    kept in the tag: `binary_expression/+` never matches `binary_expression/-`.
    """
    fps: set[int] = set()
    count = 0

    def walk(n, field: str | None) -> str:
        nonlocal count
        count += 1
        tag = n.type
        op = operator_token(n)
        if op is not None:
            tag += "/" + op
        if field:
            tag = field + ":" + tag
        parts = [tag]
        for child, child_field in kids(n):
            parts.append(walk(child, child_field))
        sexp = "(" + " ".join(parts) + ")"
        fps.add(int.from_bytes(hashlib.blake2b(sexp.encode(), digest_size=8).digest(), "big"))
        return sexp

    root = walk(node, None)
    return fps, count, root


def score(a: set[int], b: set[int]) -> float:
    shared = len(a & b)
    union = len(a) + len(b) - shared
    return shared / union if union else 0.0


# --- scanning --------------------------------------------------------------------

class Unit:
    __slots__ = ("file", "start", "end", "nodes", "fps", "lang")

    def __init__(self, file, start, end, nodes, fps, lang):
        self.file, self.start, self.end = file, start, end
        self.nodes, self.fps, self.lang = nodes, fps, lang

    def loc(self) -> dict:
        return {"file": self.file, "start_line": self.start, "end_line": self.end}


def source_files(paths: list[str], notes: dict | None = None) -> list[Path]:
    seen: set[Path] = set()
    for raw in paths:
        p = Path(raw)
        if p.is_file():
            # Named outright, so it is wanted — SKIP_DIRS is about what a walk wanders
            # into, not about overruling a path somebody typed.
            seen.add(p)
        elif p.is_dir():
            for child in p.rglob("*"):
                # Relative to the scanned root, never the whole path. `~/build/myproj`
                # is somebody's project directory that happens to live under a folder
                # called build; matching the absolute parts drops every file in it.
                if child.is_file() and not (SKIP_DIRS & set(child.relative_to(p).parts)):
                    seen.add(child)
        elif notes is not None:
            # Neither a file nor a directory. Dropping it in silence lets `dry.py src srcc`
            # report on half the scope and say nothing about the half that was a typo, and
            # the report is then read as covering what was asked for.
            notes["missing"].append(str(p))
    return sorted(seen)


def language_of(path: Path) -> str | None:
    from tree_sitter_language_pack import detect_language_from_path

    try:
        lang = detect_language_from_path(str(path))
    except Exception:
        return None
    return lang if lang in UNITS else None


def scan(path: Path, lang: str, opts, notes: dict) -> list[Unit]:
    from tree_sitter_language_pack import get_parser

    try:
        blob = path.read_bytes()
    except OSError as err:
        notes["unreadable"].append(f"{path}: {err.strerror or err}")
        return []
    root = get_parser(lang).parse(blob).root_node
    kinds = UNITS[lang]
    out: list[Unit] = []
    # Depth-first in source order; a unit's subtree is not searched for more units.
    stack = [root]
    found = []
    while stack:
        n = stack.pop()
        if n.type in kinds:
            found.append(n)
            continue
        stack.extend(reversed(n.named_children))
    found.sort(key=lambda n: (n.start_point[0], n.start_byte))
    for n in found:
        start, end = n.start_point[0] + 1, n.end_point[0] + 1
        if end - start + 1 < opts.min_lines:
            continue
        # tree-sitter's own flag, not a hand-rolled walk: an inserted MISSING token is
        # usually anonymous, so walking named children only would score a unit built
        # from a mis-parsed tree and report zero parse errors while doing it.
        if n.has_error:
            notes["parse_errors"].append(f"{path}:{start}-{end}")
            continue
        try:
            fps, nodes, _ = fingerprint(n)
        except RecursionError:
            notes["too_deep"].append(f"{path}:{start}-{end}")
            continue
        if nodes < opts.min_nodes:
            continue
        out.append(Unit(str(path).replace("\\", "/"), start, end, nodes, fps, lang))
    return out


# --- pairing ---------------------------------------------------------------------

def pairs_brute(units: list[Unit], threshold: float) -> list[tuple[float, Unit, Unit]]:
    out = []
    for i in range(len(units)):
        for j in range(i + 1, len(units)):
            s = score(units[i].fps, units[j].fps)
            if s >= threshold:
                out.append((s, units[i], units[j]))
    return out


def pairs_indexed(units: list[Unit], threshold: float) -> list[tuple[float, Unit, Unit]]:
    """Same answer as pairs_brute, less work. Both filters are exact.

    Size bound: Jaccard can never exceed min(|A|,|B|) / max(|A|,|B|).
    Prefix filter: order fingerprints rarest first; two sets scoring at or above the
    threshold must share one fingerprint inside their prefixes.
    """
    freq: dict[int, int] = defaultdict(int)
    for u in units:
        for fp in u.fps:
            freq[fp] += 1
    rank = {fp: i for i, fp in enumerate(sorted(freq, key=lambda f: (freq[f], f)))}

    order = sorted(range(len(units)), key=lambda i: (len(units[i].fps), units[i].file, units[i].start))
    index: dict[int, list[int]] = defaultdict(list)
    out = []
    for pos, i in enumerate(order):
        u = units[i]
        size = len(u.fps)
        # Both bounds come from a float threshold, so they are nudged down before
        # rounding. Erring low only widens the floor or lengthens the prefix — the extra
        # candidates are scored exactly and dropped — while erring high loses a pair in
        # silence. `0.55 * 100` is 55.00000000000001, so a 55-fingerprint unit sitting
        # wholly inside a 100-fingerprint one failed both tests and never reached score().
        floor = threshold * size - EPS  # anything smaller than this cannot reach the threshold
        ordered = sorted(u.fps, key=lambda f: rank[f])
        prefix_len = max(1, size - math.ceil(threshold * size - EPS) + 1)
        seen: set[int] = set()
        for fp in ordered[:prefix_len]:
            for j in index[fp]:
                if j not in seen and len(units[j].fps) >= floor:
                    seen.add(j)
        for j in seen:
            s = score(u.fps, units[j].fps)
            if s >= threshold:
                a, b = (units[j], u) if (units[j].file, units[j].start) <= (u.file, u.start) else (u, units[j])
                out.append((s, a, b))
        for fp in ordered[:prefix_len]:
            index[fp].append(i)
    return out


def sort_pairs(found):
    return sorted(found, key=lambda p: (-p[0], p[1].file, p[1].start, p[2].file, p[2].start))


# --- families --------------------------------------------------------------------

def families(found, units):
    """Connected components over the pair graph. Three clones make three pairs and
    one family; the family is what somebody actually has to fix."""
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    key = {id(u): n for n, u in enumerate(units)}
    for s, a, b in found:
        union(key[id(a)], key[id(b)])

    # Both ends of an edge are in one component by construction, so its root is the whole
    # membership test — bucket the scores by root in one pass. Filtering every pair
    # against a freshly built `set(ms)` once per family made this quadratic in the amount
    # of duplication, so the repos with the most to report were the slowest to report it.
    groups, edges = defaultdict(list), defaultdict(list)
    for n in list(parent):
        groups[find(n)].append(n)
    for s, a, b in found:
        edges[find(key[id(a)])].append(s)

    out = []
    for root, members in groups.items():
        ms = sorted(members, key=lambda n: (units[n].file, units[n].start))
        pair_scores = edges[root]
        # max only. A family is a connected component, so two of its members may never
        # have been scored against each other at all — a minimum over the edges that
        # happen to exist would read as a floor for the family, which it is not.
        out.append({
            "size": len(ms),
            "max_score": max(pair_scores),
            "language": units[ms[0]].lang,
            "members": [units[n].loc() | {"nodes": units[n].nodes} for n in ms],
            "files": sorted({units[n].file for n in ms}),
        })
    out.sort(key=lambda f: (-f["max_score"], -f["size"], f["members"][0]["file"], f["members"][0]["start_line"]))
    return out


# --- co-change -------------------------------------------------------------------

@functools.lru_cache(maxsize=None)
def repo_root(anchor: str) -> str | None:
    """The repository root containing `anchor`, or None if there is not one.

    Asked from the scanned file's own directory, not the working directory: the scan
    may well be pointed at a repo from outside it. Cached because a report asks it once
    per family and every family in one checkout gets the same answer — a few hundred
    families meant a few hundred walks up the directory tree for a value that cannot
    change during a run. Tests that build a repository where one did not exist must call
    `repo_root.cache_clear()`.
    """
    try:
        root = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True,
                              text=True, check=True, timeout=30, cwd=anchor).stdout.strip()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return None
    # An empty answer is not a root. Reading it as one makes every path below "outside
    # the repository", and the whole report silently becomes "unknown".
    return root or None


def repo_relative(files: list[str]) -> tuple[str, set[str]] | None:
    """Map each scanned path onto the name git uses for it.

    `git log --name-only` always prints paths from the repository root, while these
    paths are however the user typed them — relative to the working directory, or
    absolute. Match the two directly and a run from any subdirectory scores every
    family at zero co-change, which the report then presents as a measurement.
    """
    try:
        anchor = str(Path(files[0]).resolve().parent)
    except OSError:
        return None
    root = repo_root(anchor)
    if root is None:
        return None
    out = set()
    for f in files:
        try:
            out.add(Path(f).resolve().relative_to(Path(root).resolve()).as_posix())
        except (ValueError, OSError):
            return None  # a path outside the repository: say nothing rather than zero
    return root, out


def git_log(root: str, since: str, *args: str) -> str | None:
    """`git log` over the window, from the repository root, or None if git could not say.

    From the root, so the repo-relative pathspecs mean what they say.

    quotePath: git C-quotes any path with a byte over 0x7f, so `pkg/café.py` comes back
    as `"pkg/caf\\303\\251.py"` and never matches what was asked for. Every commit then
    looks like it touched one file, the count comes out 0, and 0 is a verdict — the
    triage table reads it as "same shape, different reasons".

    literal-pathspecs: these are filenames, not patterns, and a `[` in one would
    otherwise be read as a character class.
    """
    try:
        return subprocess.run(
            ["git", "-c", "core.quotePath=false", "--literal-pathspecs",
             "log", f"--since={since}", "--format=%x00%H", *args],
            capture_output=True, text=True, check=True, timeout=120, cwd=root,
        ).stdout
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return None


def renames_of(line: str) -> str | None:
    """The destination of a `R100 <old> <new>` name-status line, if it is one."""
    parts = line.split("\t")
    return parts[2] if len(parts) == 3 and parts[0].startswith("R") else None


def tracked_files(root: str, paths: list[str]) -> set[str] | None:
    """Which of `paths` git actually has, so a file it has never heard of is not scored.

    An untracked file has no history, and `git log` reports that the same way it reports
    a file that simply never moved: with silence. The count then comes out 0, and 0 is a
    verdict — the triage table reads it as "same shape, different reasons" and says leave
    it alone. That is exactly backwards for the most common case there is, a clone just
    added on a branch and not yet committed.
    """
    try:
        out = subprocess.run(
            ["git", "-c", "core.quotePath=false", "--literal-pathspecs",
             "ls-files", "-z", "--"] + paths,
            capture_output=True, text=True, check=True, timeout=120, cwd=root,
        ).stdout
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return None
    return {p for p in out.split("\0") if p}


def history(root: str, paths: list[str], since: str) -> tuple[list[set[str]], set[str]] | None:
    """Every commit in the window that touched any of `paths`, and every renamed path.

    One walk serves every family in the repository, so this is called once per root
    rather than once per family.

    `--full-history` because the default simplification drops commits a merge made look
    redundant, and a commit that edited two of these files together is not redundant to
    the question being asked.
    """
    counted = git_log(root, since, "--full-history", "-M", "--name-status", "--", *paths)
    if counted is None:
        return None
    commits = []
    for block in counted.split("\x00")[1:]:
        touched = set()
        for line in block.splitlines()[1:]:
            if line:
                touched.add(renames_of(line) or line.split("\t")[-1])
        commits.append(touched)

    # Renames are looked for without a pathspec, on purpose. git applies the pathspec
    # before it detects renames, so a walk limited to `new` never sees `old` being
    # deleted and the rename arrives as an ordinary add — the walk above cannot find
    # this about itself. Narrowed to rename commits instead, which are few.
    #
    # ponytail: this diffs every commit in the window. If that ever costs too much,
    # drop to `--follow`, which tracks renames properly but takes one path at a time
    # and so costs a subprocess per file.
    moved = git_log(root, since, "--diff-filter=R", "-M", "--name-status")
    if moved is None:
        return None
    renamed = {dst for line in moved.splitlines() if (dst := renames_of(line))}
    return commits, renamed


def cochange_all(groups: list[list[str]], since: str) -> list[int | str]:
    """One verdict per family, in a single history walk per repository.

    Structural similarity says two places look alike. This says whether they have
    historically been edited together, which is the evidence that they hold one
    piece of knowledge rather than two that happen to rhyme.

    Batched because it used to cost one `git rev-parse` and one twelve-month walk of
    the same history per family: a report with a few hundred families paid for a few
    hundred walks to answer a few hundred questions about one repository.
    """
    out: list[int | str] = ["unknown"] * len(groups)
    resolved: dict[int, tuple[str, set[str]]] = {}
    for i, files in enumerate(groups):
        if len(files) < 2:
            out[i] = "same-file"
            continue
        tracked = repo_relative(files)
        if tracked is not None:
            resolved[i] = tracked  # anything else stays "unknown"

    # Grouped by root, so a scan spanning two checkouts still answers per repository
    # instead of asking one of them about the other's paths.
    wanted_by_root: dict[str, set[str]] = defaultdict(set)
    for root, wanted in resolved.values():
        wanted_by_root[root] |= wanted
    walked = {root: history(root, sorted(paths), since) for root, paths in wanted_by_root.items()}
    known = {root: tracked_files(root, sorted(paths)) for root, paths in wanted_by_root.items()}

    for i, (root, wanted) in resolved.items():
        seen = walked[root]
        if seen is None or known[root] is None:
            continue
        commits, renamed = seen
        if wanted - known[root]:
            # git has never heard of one of these files, so it has no opinion to report.
            # A tracked file that merely did not move inside the window is a different
            # thing, and 0 is the honest answer for that one.
            out[i] = "untracked"
        elif renamed & wanted:
            # A count here would be an undercount, and the report prints it as a
            # measurement. Say the history moved rather than name a number that is wrong.
            out[i] = "renamed"
        else:
            out[i] = sum(1 for touched in commits if len(touched & wanted) >= 2)
    return out


def cochange(files: list[str], since: str) -> int | str:
    """One family's verdict. A report uses `cochange_all`, which walks history once."""
    return cochange_all([files], since)[0]


# --- self-check ------------------------------------------------------------------

def rename_identifiers(src: bytes, root) -> bytes:
    """Append a suffix to every identifier token. Language-free: the grammar says
    which spans are identifiers.

    Only plain names starting with a letter are touched. Go's blank `_` is its own
    node type, and renaming it would move it into a different one — that changes the
    tree honestly and would fail this check for the wrong reason.

    Most grammars end the node type in `identifier`. PHP is the one that does not: it
    calls the token `name`, and is the only one of the fourteen with a bare `name` node,
    so matching it here is unambiguous. Without it nothing in a PHP file is renamed and
    the check passes having proved nothing.
    """
    spans = []
    stack = [root]
    while stack:
        n = stack.pop()
        if n.type.endswith("identifier") or n.type == "name":
            text = n.text.decode("utf-8", "replace")
            if text[:1].isalpha() and text.replace("_", "").isalnum():
                spans.append((n.start_byte, n.end_byte))
        stack.extend(n.named_children)
    out = bytearray(src)
    for start, end in sorted(spans, reverse=True):
        out[start:end] = out[start:end] + b"_q"
    return bytes(out)


def shape(node) -> list[str]:
    """Node types in pre-order. Two shapes that match mean the mutation did not
    change how the source parsed."""
    out, stack = [], [node]
    while stack:
        n = stack.pop()
        out.append(n.type)
        stack.extend(reversed([c for c, _ in kids(n)]))
    return out


def raw_size(node) -> int:
    """Named nodes in the subtree, spelling included. The spelling check needs this:
    the filtered shape is exactly what must not move, so proving the mutation landed
    has to be done on the unfiltered tree."""
    out, stack = 0, [node]
    while stack:
        n = stack.pop()
        out += 1
        stack.extend(n.named_children)
    return out


def flip_candidates(src: bytes, units: list, limit: int = 20) -> list[bytes]:
    """Sources with one operator turned into its opposite, inside a unit.

    Two restrictions, both learned the hard way. Module-level code is no use — the
    comparison only looks at units. And the node must have two operands: Go's
    pointer type `*T` carries a lone `*`, and flipping that writes `/T`, which is
    not a different program but a broken one.
    """
    swaps = {"+": b"-", "-": b"+", "==": b"!=", "!=": b"==", "<": b">", ">": b"<", "*": b"/", "&&": b"||"}
    hits = []
    for unit in units:
        stack = [unit]
        while stack:
            n = stack.pop()
            op = operator_token(n)
            if op in swaps and n.named_child_count >= 2:
                for child in n.children:
                    if not child.is_named and child.text.decode("utf-8", "replace") == op:
                        hits.append((child.start_byte, child.end_byte, swaps[op]))
                        break
            stack.extend(n.named_children)
    return [src[:start] + rep + src[end:] for start, end, rep in sorted(hits)[:limit]]


def respell_candidates(src: bytes, units: list, limit: int = 20) -> list[bytes]:
    """Sources with one escape sequence added inside a string literal in a unit.

    An escape is what discriminates. Grammars hand back the inside of a string as
    child nodes, and `\\n` becomes a node of its own — so `"a"` and `"a\\n"` differ
    structurally unless the SPELLING rule drops that whole layer. Adding a plain
    letter would prove nothing: it changes the text without changing a node.
    """
    hits = []
    for unit in units:
        stack = [unit]
        while stack:
            n = stack.pop()
            if n.type.endswith(STR_TEXT) and n.end_byte > n.start_byte:
                hits.append(n.end_byte)
            stack.extend(n.named_children)
    return [src[:at] + b"\\n" + src[at:] for at in sorted(hits)[:limit]]


def self_check(units: list[Unit], opts) -> tuple[list[str], dict]:
    """Assertions before any score is believed. A clone finder that parsed nothing
    reports 'no duplicates', which reads exactly like good news.

    A check that cannot run is recorded as unproven rather than failed — on a scope
    too small to hold a binary operator there is nothing to conclude either way.
    """
    from tree_sitter_language_pack import get_parser

    problems: list[str] = []
    checks = {"units": "passed", "rename": "unproven", "operator": "unproven", "spelling": "unproven"}
    if not units:
        return ["no units found — check the paths, the language table, and whether "
                f"--min-lines {opts.min_lines} / --min-nodes {opts.min_nodes} excluded everything"], checks

    by_file = defaultdict(list)
    for u in units:
        by_file[u.file].append(u)

    def nodes_of(parser, blob: bytes, lang: str) -> list:
        r = parser.parse(blob).root_node
        kinds = UNITS[lang]
        stack, found = [r], []
        while stack:
            n = stack.pop()
            if n.type in kinds:
                found.append(n)
                continue
            stack.extend(reversed(n.named_children))
        found.sort(key=lambda n: (n.start_point[0], n.start_byte))
        return found

    # The first file, in path order, holding a unit with an operator in it. Both
    # mutations run against that one file, so the check costs one extra parse.
    # The first file, in path order, holding a flip that leaves the parse intact.
    # A flip that changes the node types proves nothing about the fingerprints, so
    # it is discarded rather than counted — the same rule the rename check follows.
    file, flipped_src = sorted(by_file)[0], None
    for candidate in sorted(by_file):
        cand_lang = by_file[candidate][0].lang
        cand_parser = get_parser(cand_lang)
        cand_src = Path(candidate).read_bytes()
        before = [shape(n) for n in nodes_of(cand_parser, cand_src, cand_lang)]
        for mutated in flip_candidates(cand_src, nodes_of(cand_parser, cand_src, cand_lang)):
            if [shape(n) for n in nodes_of(cand_parser, mutated, cand_lang)] == before:
                file, flipped_src = candidate, mutated
                break
        if flipped_src is not None:
            break
    if flipped_src is None:
        checks["operator"] = "unproven — no unit in this scope holds a flippable binary operator"
    lang = by_file[file][0].lang
    parser = get_parser(lang)
    src = Path(file).read_bytes()
    root = parser.parse(src).root_node

    def prints_of(nodes) -> list[tuple[set[int], list[str]]] | None:
        """None when something here is too deep to fingerprint.

        `scan` already caught that and left the unit out of the report, but this walks
        the file again from the source, so it meets the unit `scan` skipped. Letting the
        RecursionError out kills the whole run over a unit nothing was going to mention.
        """
        try:
            return [(fingerprint(n)[0], shape(n)) for n in nodes]
        except RecursionError:
            return None

    def units_of(blob: bytes) -> list[tuple[set[int], list[str]]] | None:
        return prints_of(nodes_of(parser, blob, lang))

    base = units_of(src)
    renamed_src = rename_identifiers(src, root)
    renamed = units_of(renamed_src) if base is not None else None
    # A mutation that changed no bytes proves nothing, and every score it compares is
    # 1.0 by construction. Reporting that as a pass is the exact false reassurance this
    # check exists to prevent, so it is recorded as unproven instead.
    if base is None or renamed is None:
        # The spelling loop below picks its own file, so it can still prove something.
        checks["rename"] = f"unproven — a unit in {file} is too deep to fingerprint"
    elif renamed_src == src:
        checks["rename"] = f"unproven — no identifier in {file} could be renamed"
    elif len(renamed) != len(base):
        problems.append(f"rename check: {len(base)} units before, {len(renamed)} after — the parser lost units")
    else:
        # A unit whose node types shifted under the rename was re-parsed differently:
        # grammars classify a few builtins by name, so `make(T)` stops reading as a
        # type once `make` is renamed. That is the grammar, not a leak, and it is the
        # one thing this check must not blame the fingerprints for. Names leaking in
        # would leave the node types identical and the score below 1.
        comparable = [(a, b) for (a, sa), (b, sb) in zip(base, renamed) if sa == sb]
        if not comparable:
            checks["rename"] = f"unproven — every unit in {file} re-parsed differently"
        else:
            worst = min(score(a, b) for a, b in comparable)
            if worst != 1.0:
                problems.append(f"rename check: renaming every identifier changed a score to {worst:.4f}, expected 1.0000 — names are leaking into the fingerprints")
            else:
                checks["rename"] = f"passed on {file} ({len(comparable)} units)"

    if flipped_src is not None and base is None:
        checks["operator"] = f"unproven — a unit in {file} is too deep to fingerprint"
    elif flipped_src is not None:
        flipped = units_of(flipped_src)
        if flipped is None:
            checks["operator"] = f"unproven — a unit in {file} is too deep to fingerprint"
        elif len(flipped) != len(base):
            problems.append("operator check: unit count changed")
        elif all(score(a, b) == 1.0 for (a, _), (b, _) in zip(base, flipped)):
            problems.append(f"operator check: flipping an operator in {file} changed nothing — operators are being normalised away")
        else:
            checks["operator"] = f"passed on {file}"

    for candidate in sorted(by_file):
        cand_lang = by_file[candidate][0].lang
        cand_parser = get_parser(cand_lang)
        cand_src = Path(candidate).read_bytes()
        cand_nodes = nodes_of(cand_parser, cand_src, cand_lang)
        before = prints_of(cand_nodes)
        if before is None:
            continue  # too deep to fingerprint; another file may still prove this
        for mutated in respell_candidates(cand_src, cand_nodes):
            mutated_nodes = nodes_of(cand_parser, mutated, cand_lang)
            after = prints_of(mutated_nodes)
            if after is None or len(after) != len(before):
                continue  # the edit broke the parse; try another string
            # Inside a raw string a `\n` is two ordinary characters and no node appears.
            # Nothing moved, but nothing was tested either — passing on that is the
            # false reassurance this whole block exists to prevent.
            if sum(raw_size(n) for n in mutated_nodes) == sum(raw_size(n) for n in cand_nodes):
                continue
            # Unlike the other two mutations, a changed shape here is the failure:
            # with spelling dropped, adding an escape must move nothing at all.
            if [s for _, s in after] != [s for _, s in before] or any(score(a, b) != 1.0 for (a, _), (b, _) in zip(before, after)):
                problems.append(f"spelling check: adding an escape inside a string in {candidate} changed the structure — literal spelling is leaking into the fingerprints")
            else:
                checks["spelling"] = f"passed on {candidate}"
            break
        if checks["spelling"] != "unproven" or problems:
            break
    else:
        checks["spelling"] = "unproven — no string literal inside a unit in this scope"

    return problems, checks


# --- output ----------------------------------------------------------------------

def format_text(report: dict) -> str:
    """The default format, and the only one a human reads without asking for JSON.

    It prints what was scanned and what the self-checks said before it prints findings.
    Without that, a run where every file failed to parse printed "No duplicate candidates
    found." and nothing else — the same sentence a clean repository gets. The evidence
    that the answer was worth nothing was in the JSON, which nobody had asked for.
    """
    run = report["run"]
    head = [f"scanned {run['units']} units in {len(run['by_language'])} language(s), "
            f"grammar pack {run['engine']['pack']}"]
    for name, verdict in sorted(run["checks"].items()):
        head.append(f"  {name}: {verdict}")
    for label, key in (("units with parse errors", "units_with_parse_errors"),
                       ("units too deep to fingerprint", "units_too_deep"),
                       ("files unreadable", "files_unreadable"),
                       ("paths that do not exist", "paths_not_found"),
                       ("files in no supported language", "files_unsupported")):
        if run[key]:
            head.append(f"  {label}: {run[key]}")

    blocks = ["\n".join(head)]
    for f in report["families"]:
        lines = [f"DUPLICATE score={f['max_score']:.2f} size={f['size']} co-changed={f['cochange']}"]
        lines += [f"  {m['file']}:{m['start_line']}-{m['end_line']}" for m in f["members"]]
        blocks.append("\n".join(lines))
    if not report["families"]:
        blocks.append("No duplicate candidates found.")
    return "\n\n".join(blocks) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Structural duplication finder (dry4go algorithm, tree-sitter grammars).")
    ap.add_argument("paths", nargs="*", default=["."])
    ap.add_argument("--threshold", type=float, default=THRESHOLD)
    ap.add_argument("--min-lines", type=int, default=MIN_LINES)
    ap.add_argument("--min-nodes", type=int, default=MIN_NODES)
    ap.add_argument("--since", default=SINCE, help="git window for the co-change count")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    ap.add_argument("--brute-force", action="store_true", help="skip the exact prefilters; same answer, more work")
    ap.add_argument("--no-self-check", action="store_true")
    ap.add_argument("--no-cochange", action="store_true")
    opts = ap.parse_args()
    paths = opts.paths or ["."]

    sys.setrecursionlimit(20000)
    try:
        import tree_sitter_language_pack  # noqa: F401
    except ImportError:
        print("needs tree-sitter-language-pack: pip install tree-sitter-language-pack", file=sys.stderr)
        return 2

    notes = {"parse_errors": [], "too_deep": [], "unreadable": [], "missing": []}
    # Extensions and counts, not paths. A repo with an asset tree has tens of thousands
    # of files this engine has no grammar for, and listing them would bury the report's
    # own JSON in noise that says nothing the count does not.
    unsupported: dict[str, int] = defaultdict(int)
    units: list[Unit] = []
    langs: dict[str, int] = defaultdict(int)
    for path in source_files(paths, notes):
        lang = language_of(path)
        if lang is None:
            unsupported[path.suffix.lower() or "(no extension)"] += 1
            continue
        found = scan(path, lang, opts, notes)
        langs[lang] += len(found)
        units.extend(found)

    checks = {"self_check": "skipped"}
    if not opts.no_self_check:
        problems, checks = self_check(units, opts)
        if problems:
            for p in problems:
                print("SELF-CHECK FAILED: " + p, file=sys.stderr)
            return 2

    # Units of different languages are never compared: each grammar has its own
    # node vocabulary, so the scores are not the same measurement.
    found = []
    for lang in sorted(langs):
        same = [u for u in units if u.lang == lang]
        found += (pairs_brute if opts.brute_force else pairs_indexed)(same, opts.threshold)
    found = sort_pairs(found)

    fams = families(found, units)
    verdicts = (["skipped"] * len(fams) if opts.no_cochange
                else cochange_all([f["files"] for f in fams], opts.since))
    for f, verdict in zip(fams, verdicts):
        f["cochange"] = verdict

    # The grammar decides the node vocabulary, so it decides the scores. Two reports
    # from different pack versions are not comparable, which is why this is recorded
    # rather than assumed. The cache path carries the version for the same reason.
    import tree_sitter_language_pack as pack

    report = {
        "run": {
            "engine": {
                "pack": getattr(pack, "__version__", "unknown"),
                "cache": str(pack.cache_dir()),
            },
            "threshold": opts.threshold,
            "min_lines": opts.min_lines,
            "min_nodes": opts.min_nodes,
            "since": opts.since,
            "prefilters": not opts.brute_force,
            "checks": checks,
            "units": len(units),
            "by_language": dict(sorted(langs.items())),
            "files_unsupported": sum(unsupported.values()),
            "unsupported_by_extension": dict(sorted(unsupported.items(), key=lambda kv: (-kv[1], kv[0]))),
            "units_with_parse_errors": len(notes["parse_errors"]),
            "units_too_deep": len(notes["too_deep"]),
            "files_unreadable": len(notes["unreadable"]),
            "paths_not_found": len(notes["missing"]),
        },
        "families": fams,
        "pairs": [{"score": s, "left": a.loc(), "right": b.loc(), "left_nodes": a.nodes, "right_nodes": b.nodes} for s, a, b in found],
        "notes": notes,
    }
    print(json.dumps(report, indent=2) if opts.format == "json" else format_text(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
