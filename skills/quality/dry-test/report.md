# Report shape

The shape step 6 of [`dry-test`](SKILL.md) writes. A Python after-report — the tables and
buckets are what transfers. Each is shown with a row or two; a real report lists them all.

````markdown
# DRY Report

| | |
| --- | --- |
| **Run** | <YYYY-MM-DD HH:MM:SS> |
| **Engine** | `scripts/dry.py` · tree-sitter-language-pack 1.14.3 |
| **Metric** | Jaccard over subtree fingerprints, threshold 0.76 · floors 4 lines, 20 nodes |
| **Checks** | units ✅ · rename ✅ · operator ✅ · spelling ✅ |
| **Commit** | `a1b2c3d` (dirty working tree) |
| **Scope** | `src/`, `tests/` — 486 units, python |
| **Data** | [`dry-2026-08-09-142233.json`](./dry-2026-08-09-142233.json) |
| **Before** | [`dry-report-2026-08-09-091412.md`](./dry-report-2026-08-09-091412.md) |

## What moved

| | Before | After | Change |
| --- | --- | --- | --- |
| **Families** | 23 | **21** | **−2** |
| **Units in a family** | 61 | 52 | −9 |
| **Verbatim (1.00)** | 14 | 12 | −2 |

**Score rose:** none.

## Totals

| Bucket | Families | Units |
| --- | --- | --- |
| 🔴 Verbatim / duplication | 12 | 31 |
| 🟠 Unsettled | 6 | 14 |
| 🟡 Incidental | 3 | 7 |
| **Scored** | **21** | **52** |

| Coverage of the scan | Count |
| --- | --- |
| Units scanned | 486 |
| Files with no grammar | 26 — `.rst` 14, `.cfg` 8, `.toml` 4 |
| Files unreadable | 0 |
| Units dropped, parse errors | 0 |
| Units below 4 lines or 20 nodes | not counted — the floors are silent |

---

## 🔴 Duplication — one knowledge, several homes

### 1. `src/requests/api.py:74,137,154` — the verb wrappers

| | |
| --- | --- |
| **Score · size · co-changed** | 1.00 (verbatim) · 3 · `same-file` |
| **Knowledge** | how to open a session, send one request for a verb, return the response |
| **Same sentence for every member?** | yes |
| **Proposal** | keep them. The shared part is already `request()`; the remaining lines are the signature, and collapsing them would hide the verb from the reader |
| **Outcome** | ⏸️ deferred, reason recorded |

### 2. `adapters.py:555` / `sessions.py:883` — `close()`

| | |
| --- | --- |
| **Score · size · co-changed** | 0.77 · 2 · **4 commits** in 5 years |
| **Knowledge** | *adapters:* release the pooled connections this adapter owns. *sessions:* close every adapter this session owns |
| **Same sentence for every member?** | **no** — "loop over what I own and close each" is a shape, not a fact |
| **Proposal** | leave them. The table put this in 🔴 on co-change; the code says otherwise, and the code wins |
| **Outcome** | ⏸️ deferred, reason recorded |

### 3. `tests/test_requests.py:277,292,306` — the redirect cases

| | |
| --- | --- |
| **Score · size · co-changed** | 1.00 (verbatim) · 3 · `same-file` |
| **Knowledge** | one redirect case per status code |
| **Same sentence for every member?** | yes — only the status code differs |
| **Proposal** | parametrise the test |
| **Outcome** | 🔴 open |

## 🟠 Unsettled — the code decides

| Family | Score | Size | Co-changed | Knowledge | Proposal | Outcome |
| --- | --- | --- | --- | --- | --- | --- |
| `models.py:412` / `sessions.py:104` | 0.81 | 2 | **2 commits** | header merge order | read both — likely one rule | ⏸️ deferred |
| `_async.py:88` / `api.py:74` | 0.79 | 2 | `untracked` | new async wrappers, not committed yet | re-run once they are in git | ⏸️ deferred |

The second is not a low score, it is no score: git has never seen those files, so co-change has
nothing to say and `0` would have been a lie. It stays 🟠 until the branch is committed.

## 🟡 Incidental — same shape, different reasons

| Family | Score | Size | Co-changed |
| --- | --- | --- | --- |
| `encodings/*.py` codec stubs | 1.00 | 97 | 0 |

97 files, one shape, never edited together. Each holds a different fact — which codec is
registered — and merging them would put 97 unrelated changes behind one edit.

---

## What this run could not see

| | |
| --- | --- |
| Not scanned | 26 files the engine has no grammar for |
| Not measured | duplication in SQL, templates, and CI config |
| Not found by shape | two different implementations of one rule |

## The gate

| Setting | Value | File | State |
| --- | --- | --- | --- |
| New family above 0.76 on changed files | fail | `.github/workflows/ci.yml` | applied |
| Pinned engine | `tree-sitter-language-pack==1.14.3` | `requirements-dev.txt` | applied |
````

Drop any empty section and lead the body with 🔴. The before report is the same shape,
shorter: no "Before" row, no "What moved", no "Outcome" rows, both gate rows "not applied".
