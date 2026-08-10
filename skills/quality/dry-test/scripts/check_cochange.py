#!/usr/bin/env python3
"""Co-change tests for dry.py, against a throwaway git repository.

`cochange` is the only part of the engine that reads something other than the source
text, and it is the part with the most ways to be quietly wrong. Every failure here
returns a value the report prints as if it were a measurement: a run from the wrong
directory once scored every family at zero co-change, and nothing said so.

So each case below pins one answer, and the two that matter most are the ones that
must NOT come back as a number:

    same-file   a family living inside one file — there is nothing to correlate
    unknown     no repository, or a path outside it — say nothing rather than zero

Determinism is the point. Commit dates are fixed and `--since` is an absolute date,
so the counts do not move with the wall clock. Global and system git config are
pointed at a file that does not exist, so the machine's own settings cannot change
the answer either.

    python3 scripts/check_cochange.py

Needs git on PATH. Does not need the grammar pack.
"""

from __future__ import annotations

import contextlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import dry  # noqa: E402

# Captured before anything replaces it, so a fake git can still call the real one.
REAL_RUN = subprocess.run

# Absolute, not "12.months": a relative window plus fixed commit dates would stop
# matching one year after this file was written.
SINCE = "1970-01-01"
STAMP = "2020-01-01T00:00:00+0000"


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True,
                   env=os.environ | {"GIT_AUTHOR_DATE": STAMP, "GIT_COMMITTER_DATE": STAMP})


def commit(repo: Path, message: str, files: dict[str, str]) -> None:
    for name, body in files.items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body)
        git(repo, "add", name)
    git(repo, "commit", "-q", "-m", message)


def build(repo: Path) -> None:
    """A repo where pkg/a and pkg/b were edited together three times, and a alone once.

    The files live in a subdirectory on purpose: with everything at the root, a path
    typed relative to the working directory and the path git prints are the same
    string, and the bug this file exists to catch cannot happen.
    """
    git(repo, "init", "-q")
    for n in range(3):
        commit(repo, f"together {n}", {"pkg/a.py": f"a{n}\n", "pkg/b.py": f"b{n}\n"})
    commit(repo, "a alone", {"pkg/a.py": "a3\n"})
    commit(repo, "unrelated", {"pkg/c.py": "c\n"})
    # Names git does not print plainly: an accent, which git C-quotes by default, and a
    # bracket, which is a character class if the path is read as a pathspec pattern.
    for n in range(2):
        commit(repo, f"awkward {n}", {"pkg/café.py": f"c{n}\n", "pkg/a[1].py": f"d{n}\n"})


def build_renamed(repo: Path) -> None:
    """pkg/x and pkg/y edited together twice, and then y renamed to z.

    git filters history on the name a commit used, so a pathspec naming `z` cannot see
    what the file did as `y`. Counting anyway would report 0 for two files that were in
    fact always edited together.
    """
    git(repo, "init", "-q")
    for n in range(2):
        commit(repo, f"together {n}", {"pkg/x.py": f"x{n}\n", "pkg/y.py": f"y{n}\n"})
    git(repo, "mv", "pkg/y.py", "pkg/z.py")
    git(repo, "commit", "-q", "-m", "rename y to z")
    # A pair in the same repository that was never renamed, so the verdict below can be
    # shown to be about the family's own files rather than about the whole repository.
    for n in range(2):
        commit(repo, f"pair {n}", {"pkg/x.py": f"xx{n}\n", "pkg/w.py": f"w{n}\n"})


@contextlib.contextmanager
def fake_git(handler):
    """Run the block with dry.py's git replaced, and the root cache emptied either side.

    The three failures below cannot be staged with a real repository: a timeout needs a
    slow git, a `git log` that fails after `git rev-parse` succeeded needs git to break
    between two calls, and an empty root needs a git that answers wrongly. Each returns
    a value the report would otherwise print as though it were a measurement.
    """
    dry.repo_root.cache_clear()
    subprocess.run = handler
    try:
        yield
    finally:
        subprocess.run = REAL_RUN
        dry.repo_root.cache_clear()


def breaks_on(word: str, make_error):
    """Real git, except the call whose arguments contain `word`, which fails."""
    def run(cmd, *a, **kw):
        if word in cmd:
            raise make_error(cmd)
        return REAL_RUN(cmd, *a, **kw)
    return run


def empty_root(cmd, *a, **kw):
    """A `git rev-parse --show-toplevel` that succeeds and prints nothing."""
    if "rev-parse" in cmd:
        return subprocess.CompletedProcess(cmd, 0, stdout="\n", stderr="")
    return REAL_RUN(cmd, *a, **kw)


def main() -> int:
    # dry.py runs git itself, with the environment it is handed. Point the config at a
    # path that does not exist — git reads a missing config file as an empty one — so
    # this machine's settings cannot reach the answers below.
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp).resolve()
        # Stop git's upward search at the scratch directory. Without this the "not a
        # repository" case below is a fact about the machine, not about the code: a
        # developer whose TMPDIR happens to sit inside a checkout would see git find
        # that outer repository, the answer come back 0 instead of "unknown", and a
        # correct engine fail the suite.
        os.environ["GIT_CEILING_DIRECTORIES"] = str(tmp)
        os.environ["GIT_CONFIG_GLOBAL"] = str(tmp / "no-such-config")
        os.environ["GIT_CONFIG_SYSTEM"] = str(tmp / "no-such-config")
        os.environ["GIT_AUTHOR_NAME"] = os.environ["GIT_COMMITTER_NAME"] = "dry test"
        os.environ["GIT_AUTHOR_EMAIL"] = os.environ["GIT_COMMITTER_EMAIL"] = "dry@example.invalid"

        repo, outside = tmp / "repo", tmp / "outside"
        repo.mkdir()
        outside.mkdir()
        (outside / "d.py").write_text("d\n")
        build(repo)

        a, b, c = repo / "pkg/a.py", repo / "pkg/b.py", repo / "pkg/c.py"

        got = dry.cochange([str(a), str(b)], SINCE)
        assert got == 3, f"two files edited together in 3 commits scored {got!r}, expected 3"

        got = dry.cochange([str(a), str(c)], SINCE)
        assert got == 0, f"two files never edited together scored {got!r}, expected 0"

        got = dry.cochange([str(a)], SINCE)
        assert got == "same-file", f"a family inside one file scored {got!r}, expected 'same-file'"

        # git C-quotes a non-ASCII path unless told not to, and reads a pathspec as a
        # pattern unless told not to. Either one makes the file git prints a different
        # string from the file that was asked about, and the count silently falls to 0.
        got = dry.cochange([str(repo / "pkg/café.py"), str(repo / "pkg/a[1].py")], SINCE)
        assert got == 2, f"two awkwardly named files edited together twice scored {got!r}, expected 2"

        got = dry.cochange([str(outside / "d.py"), str(outside / "d.py")], SINCE)
        assert got == "unknown", f"a directory that is not a repository scored {got!r}, expected 'unknown'"

        # Never 0. A file git has never heard of has no co-change history, and reporting
        # that as "changed together zero times" is a claim the repository cannot support.
        got = dry.cochange([str(a), str(outside / "d.py")], SINCE)
        assert got == "unknown", f"a path outside the repository scored {got!r}, expected 'unknown'"

        # The regression. git prints paths from the repository root; these arrive however
        # the user typed them. Run from pkg/ with bare filenames and the two only match
        # if dry.py maps one onto the other.
        here = Path.cwd()
        try:
            os.chdir(repo / "pkg")
            got = dry.cochange(["a.py", "b.py"], SINCE)
            assert got == 3, f"the same scan from a subdirectory scored {got!r}, expected 3"
        finally:
            os.chdir(here)

        # git missing entirely — the branch that turns a crash into an honest "unknown".
        # The cache is emptied first, or the root found by an earlier case is simply
        # handed back and the branch under test is never reached.
        path = os.environ.get("PATH", "")
        try:
            dry.repo_root.cache_clear()
            os.environ["PATH"] = str(tmp / "no-such-bin")
            got = dry.cochange([str(a), str(b)], SINCE)
            assert got == "unknown", f"with no git on PATH the answer was {got!r}, expected 'unknown'"
        finally:
            os.environ["PATH"] = path
            dry.repo_root.cache_clear()

        # A renamed file. Never a number: git cannot see what the file did under its old
        # name, so any count would be an undercount presented as a measurement.
        moved = tmp / "moved"
        moved.mkdir()
        build_renamed(moved)
        dry.repo_root.cache_clear()
        got = dry.cochange([str(moved / "pkg/x.py"), str(moved / "pkg/z.py")], SINCE)
        assert got == "renamed", f"a renamed file scored {got!r}, expected 'renamed'"

        # A family in the same repository whose own files never moved still gets a
        # number. "renamed" is a statement about these files, not about the repository.
        got = dry.cochange([str(moved / "pkg/x.py"), str(moved / "pkg/w.py")], SINCE)
        assert got == 2, f"an unmoved pair in a repo that has a rename scored {got!r}, expected 2"

        # An untracked file. Never 0: git has no history for it, and reporting "changed
        # together zero times" would send the most ordinary case there is — a clone added
        # on a branch and not yet committed — straight into 🟡 "leave it alone".
        untracked = repo / "pkg/fresh.py"
        untracked.write_text("fresh\n")
        got = dry.cochange([str(a), str(untracked)], SINCE)
        assert got == "untracked", f"a file git does not track scored {got!r}, expected 'untracked'"

        # A tracked file that simply did not move in the window is a different thing, and
        # 0 is the honest answer there — otherwise "untracked" would swallow real zeroes.
        got = dry.cochange([str(a), str(c)], SINCE)
        assert got == 0, f"two tracked files never edited together scored {got!r}, expected 0"

        # The three branches a real repository cannot reach.
        with fake_git(breaks_on("log", lambda cmd: subprocess.TimeoutExpired(cmd, 120))):
            got = dry.cochange([str(a), str(b)], SINCE)
            assert got == "unknown", f"a `git log` that timed out scored {got!r}, expected 'unknown'"

        with fake_git(breaks_on("log", lambda cmd: subprocess.CalledProcessError(128, cmd))):
            got = dry.cochange([str(a), str(b)], SINCE)
            assert got == "unknown", (f"a `git log` that failed after `git rev-parse` succeeded "
                                      f"scored {got!r}, expected 'unknown'")

        with fake_git(empty_root):
            # Asserted on `repo_root` itself. Going only through `cochange` proves
            # nothing here: an empty root makes `Path("").resolve()` the working
            # directory, the files land outside it, and the answer is "unknown" by a
            # different route entirely — the test passed with this branch deleted.
            got = dry.repo_root(str(repo / "pkg"))
            assert got is None, f"an empty `git rev-parse` answer was read as the root {got!r}"
            got = dry.cochange([str(a), str(b)], SINCE)
            assert got == "unknown", (f"a `git rev-parse` that printed no root scored {got!r}, "
                                      f"expected 'unknown'")

    print("co-change: 15 cases pass")
    print("nothing git cannot answer comes back as a number: a missing repo, a path outside it,")
    print("  a timeout, a failed log and an empty root are all 'unknown'; one file is 'same-file';")
    print("  a file git does not track is 'untracked';")
    print("  and a file renamed inside the window is 'renamed'")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
