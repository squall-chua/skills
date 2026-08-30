# Report shape

The shape step 7 of [`crap-test`](SKILL.md) writes. A TypeScript after-report — the tables and
columns are what transfers. Each is shown with a row or two; a real report lists them all.

````markdown
# CRAP Report

| | |
| --- | --- |
| **Run** | <YYYY-MM-DD HH:MM:SS> |
| **Formula** | `comp² × (1 − cov)³ + comp`, threshold 30 |
| **Complexity** | `eslint --rule '{"complexity":["warn",0]}' -f json` → `complexity.json` |
| **Coverage** | `vitest --coverage.reporter=json` → `coverage-final.json` — generated here; no fresh `/code-coverage` file in `.reports/` |
| **Script** | [`crap-2026-08-09-142233.py`](./crap-2026-08-09-142233.py) — 12/12 vectors passed |
| **Data** | [`crap-2026-08-09-142233.csv`](./crap-2026-08-09-142233.csv) |
| **Commit** | `a1b2c3d` (dirty working tree) |
| **Scope** | `src/**` — 84 files, 6 excluded |
| **Suite** | 412 passed, 0 failed, 3 skipped |
| **Before** | [`crap-report-2026-08-09-091412.md`](./crap-report-2026-08-09-091412.md) |

Where step 2 reused a coverage file `/code-coverage` had already written, the **Coverage** row
says so instead, and links it where it lies under its own earlier timestamp:

| **Coverage** | reused [`coverage-2026-08-09-141005.json`](./coverage-2026-08-09-141005.json), same commit — not re-run |

## What moved

| Metric | Before | After | Change |
| --- | --- | --- | --- |
| **Functions over 30** | 14 | **6** | **−8** |
| **Worst CRAP** | 930.0 | **39.9** | **−890.1** |
| **Functions scored** | 702 | 711 | +9 (splits) |

| Function | Before | After | How |
| --- | --- | --- | --- |
| `orders/reconcile.ts:112 reconcileOrder` | 73.2 | 5.6 | split into 4, max complexity 5 |
| `pricing/discount.ts:88 applyDiscount` | 53.4 | 14.5 | covered 34.0% → 74.0% |

**Rose:** none.

## Totals

| Band | Count | Share |
| --- | --- | --- |
| 🔴 Split — complexity ≥ 31 | 2 | 0.3% |
| 🟠 Test — CRAP > 30 | 4 | 0.6% |
| 🟡 Watch — CRAP 20–30 | 23 | 3.2% |
| 🟢 Pass | 682 | 95.9% |
| **Scored** | **711** | |
| ⚪ Unmeasured — file not in the coverage report | 9 | |

| Module | Functions | Worst CRAP (max, not mean) | Over 30 |
| --- | --- | --- | --- |
| `src/http` | 38 | 39.9 | 1 |

## Reconciliation

| | Count |
| --- | --- |
| Functions in the complexity file | 720 |
| Matched to coverage | 711 (98.8%) |
| Unmeasured — file absent from coverage | 9 |
| Unmatched — file measured, line not found | 0 |
| In coverage with no complexity row | 4 (generated `*.gen.ts`) |

---

## 🔴 Split — no test can pass these

### `src/domain/orders/reconcile.ts:112` — `reconcileOrder`

| | |
| --- | --- |
| **Complexity · coverage · CRAP** | 38 · 71.0% · **73.2** |
| **Why it cannot pass** | complexity 38 scores 38 at *full* coverage |
| **Decides** | which ledger rows are written when a payment and an order disagree |
| **Split target** | parts at complexity ≤ 5; the groups are the three payment states and the two currency paths |
| **Outcome** | 🟢 split into 4, max complexity 5, suite green |

## 🟠 Test — the gap to 30

| Function | Comp | Now | Needs | Gap | CRAP | Decides | Outcome |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `pricing/discount.ts:88 applyDiscount` | 12 | 34.0% | **50.0%** | +16.0 | 53.4 | how much money comes off an order | 🟢 74.0%, CRAP 14.5 |
| `http/errorMapper.ts:40 mapError` | 15 | 52.0% | **59.5%** | +7.5 | 39.9 | which status a domain error becomes | 🔴 open |

## 🟡 Watch — passing, no headroom

| Function | Comp | Coverage | CRAP |
| --- | --- | --- | --- |
| `src/auth/session.ts:22 renew` | 8 | 35.0% | 25.6 |

23 functions between 20 and 30. One added branch puts any of them over.

## ⚪ Unmeasured

A zero here would be invented rather than measured.

| File | Functions | Why |
| --- | --- | --- |
| `src/cli/repl.ts` | 9 | excluded from the coverage config as program wiring |

---

## Findings for the code

| Function | Finding | Suggested action |
| --- | --- | --- |
| `src/legacy/oldRefund.ts:44` | complexity 22, 3 branches unreachable — every caller sets `mode` to `standard` or `partial` | delete them; complexity falls to 12 and it passes at 50% |

## Excluded from the scope

| Path | Reason |
| --- | --- |
| `src/**/*.gen.ts` | generated from the OpenAPI schema |
| **Without these** | 4 fewer functions scored, worst CRAP unchanged |

## The gate

| Setting | Value | File | State |
| --- | --- | --- | --- |
| Functions over 30 | ceiling 6 | `.github/workflows/ci.yml` | applied |
| Changed-function CRAP | fail above 30 on the diff | `.github/workflows/ci.yml` | applied |

The ceiling is the count measured, so it can only fall.
````

Drop any empty section and lead the body with 🔴. The before report is the same shape,
shorter: no "Before" row, no "What moved", no "Outcome" columns, both gate rows "not applied".
