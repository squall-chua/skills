---
name: security-compliance
description: >
  Scan the code, its dependencies, its history, and the running app for security
  flaws, rank each one by whether an attacker can actually reach it, map the set to
  OWASP, and report every finding with a fix.
disable-model-invocation: true
---

A scanner hands over hundreds of findings and no idea which one matters. The fact that sorts
them is **reach**: whether a path exists from something an attacker controls to the dangerous
line. A CVSS 9.8 in a build-time dependency reaches nobody. A 5.3 on an unauthenticated route
reaches everybody, and it is the one that gets used.

So every finding here carries a **path** — entry point, route through the code, sink — or an
argument for why no path exists. Without it a finding is a guess with a severity attached.

## What this skill writes

One report, and the scanner configs left in the repo so the next run and CI match this one.
Fixes are written as diffs for a person to apply: a dependency bump and a rewritten query are
changes their owner has to test.

## 1. Pin the scope and the standard

The paths the user named are the scope, exactly as given. Named none? Take the whole repository
and say so.

Expand the scope to its file list and count it, then name what the report maps findings to:

- **OWASP Top 10 (2021)** for the category on every finding, unless the user names another
  edition or standard.
- **CWE** for the flaw class, because it is what tools emit and what a fix is looked up by.
- **OWASP ASVS** where the team has a level they are held to, with the report saying which
  requirements this run examined and which it left.

Write down what stands outside the scope — an unread service, a vendored SDK, infrastructure
another team owns. An unstated gap reads as a clean bill of health for ground nobody looked at.

**Done when:** the scope is a counted file list, the standard is named, and everything left out
is written down.

## 2. Scan four ways

Each scan sees a different class of flaw, so a run missing one has a blind spot rather than a
clean result. Prefer the tool the project already has. Otherwise:

| Scan | What it finds | Tools |
| --- | --- | --- |
| **SAST** — the code | injection, unsafe deserialization, path traversal, weak crypto, hardcoded credentials | Semgrep, CodeQL, Bandit, gosec, Brakeman, SpotBugs with FindSecBugs, Psalm taint mode, `cargo clippy` security lints |
| **SCA** — the dependencies | known **CVE**s in what you import, direct and transitive | `osv-scanner`, Trivy, `npm audit`, `pip-audit`, `govulncheck`, `cargo audit`, `bundler-audit`, `dotnet list package --vulnerable`, OWASP Dependency-Check |
| **Secrets** — the history | live keys, tokens, and passwords committed at any point | `gitleaks`, `trufflehog` |
| **Config** — images and infrastructure | a base image with known CVEs, a public bucket, an open security group, a container running as root | Trivy, `hadolint`, `checkov`, `tfsec`, `kube-score` |

### Nothing installed?

Most of these tools are one-shot scanners, so `npx`, `uvx`, `pipx run`, or a container image
runs them without touching the manifest at all. Reach for that first — it is the only way to
run four scanners without leaving four dependencies behind.

Where a tool has no ephemeral runner, or the project should own it permanently, put the setup
to the user in one message: the tool, the exact install command, the config file with its
contents, and what it costs in download size and first-run time. Wait for the go-ahead, and
commit nothing.

Where the user declines a scan kind, the report marks it **not run** with what it would have
covered — the same as DAST without authorization. Four kinds of blind spot are worth naming
individually.

Two settings decide whether the output is usable: **SARIF or JSON**, since step 4 needs the rule
id and CWE and step 6 needs the file and line on every finding; and the **full history** for the
secret scan, since
a key deleted in the next commit is still in the pack and still live.

On Go, `govulncheck` reports whether the vulnerable symbol is actually called — step 6's question
answered by the tool.

Leave the config files in the repo.

**Done when:** each of the four ran with its version and output file recorded, or is marked not
applicable with a reason — no Dockerfile, no infrastructure code, no lockfile — or not run
because the user declined its setup.

## 3. DAST — with authorization, on a target you own

A DAST run sends attacks at a live service, so it needs permission in writing before anything
is sent:

- **Who authorized it**, by name, and when.
- **The target**, which is staging or a dedicated test environment. Production runs only on an
  explicit go-ahead from the person who owns it, and read-only checks until then.
- **The host list** in scope. A scanner follows links off-domain unless told otherwise, and a
  third-party host is somebody else's system.
- **The window**, recorded start to stop, so the owner can match your traffic to their alerts.
- **A rate limit** the environment can take.

With that recorded, run passive first — ZAP baseline, `nuclei` with its default templates — then
active scanning across the agreed hosts only. Point it at the contract or the route list so it
tests real endpoints rather than guessing paths.

| Kind | Tools |
| --- | --- |
| Passive and active web scan | OWASP ZAP, Burp Suite |
| Template-based checks | `nuclei` |
| API fuzzing | Schemathesis with its checks on, `restler` |
| TLS and headers | `testssl.sh`, `securityheaders` rules in ZAP |

Without authorization the run stops at the other three scans and the report marks DAST **not
run**, with what it would have covered. That is an honest gap; a scan without permission is an
incident with your name on it.

**Done when:** the authorization, target, host list, window, and rate limit are recorded and the
scan ran — or DAST is marked not run, with the reason and what it would have covered.

## 4. Dedupe and map to the standard

Three tools find the same SQL injection and report it three ways. Merge on file, line, and flaw
class into one finding carrying every tool that saw it: agreement between tools is worth keeping,
and three rows for one bug inflates the total into noise.

Give every finding a **CWE** and an **OWASP Top 10 category**, then build the coverage table the
other way round — for each of the ten categories, what checked it and how.

That is where the blind spots show. Scanners are strong on injection, crypto, and known CVEs, and
weak to useless on **A01 Broken Access Control**, business logic, and anything needing to know
who is allowed to do what. A category with no tool against it is a gap step 5 fills by hand, not
a category that passed.

**Done when:** every finding is one row with its CWE, its OWASP category, and the tools that
reported it; and every OWASP category carries either the check that covered it or a note that
step 5 must.

## 5. Read for what scanners miss

Work these by hand, over the scope from step 1. Each ends with a verdict and the `file:line` you
examined:

| Check | The question |
| --- | --- |
| **Object ownership** | does every handler that takes an id confirm the object belongs to the caller, or does it trust the id? |
| **Route authorization** | does every route have an authorization check, and is any new route missing what its neighbours have? |
| **Tenant isolation** | is the tenant taken from the session, or from a parameter the caller sends? |
| **Mass assignment** | can a request body set fields the caller should never set — `role`, `isAdmin`, `balance`? |
| **SSRF** | does any user-supplied URL reach a server-side fetch, and what can it reach inside the network? |
| **Business logic** | negative quantities, zero prices, a refund larger than the payment, a coupon applied twice |
| **Auth flows** | reset-token entropy and expiry, session fixation on login, timing on credential comparison, account lockout |
| **Crypto use** | a password hashed with a fast digest, a static IV, ECB mode, a key in the same store as the data |
| **Errors and logs** | stack traces to the caller, tokens or PII written to logs |
| **Upload and render** | file type checked by content rather than extension, and user content escaped where it renders |

**Done when:** every check has a verdict, the `file:line` behind it, and — where it failed — a
finding raised with the same CWE and category as any other.

## 6. Trace the path and rank by reach

For every finding from steps 2 to 5, trace the path from an entry point an attacker controls to
the sink, and give it one state:

- **Reachable** — the path exists. Write it out: the route or handler, the parameter, the
  functions between, the sink line.
- **Guarded** — the path exists and a control stands in it: authentication, an allow-list, a
  network policy, a role check. Name the control, the line it lives on, and what the finding
  becomes if that control is removed or bypassed.
- **Unreachable** — no path. A development-only dependency, a function nothing calls, a branch
  behind a flag that is off, a CVE in a symbol the code never invokes. Needs a written argument,
  because it is the state that removes work.

Then bucket, on reach first and the tool's severity second:

- **P1** — reachable, and it yields remote code execution, data theft, authentication bypass, or
  a live credential. Anything in the secret scan that has not been rotated starts here.
- **P2** — guarded, or reachable with limited impact.
- **P3** — unreachable, defence in depth, or informational.

CVSS describes the flaw in the abstract; the bucket describes it in *this* repository. Where the
two disagree the bucket wins, the report shows both, and one sentence explains the gap — a 9.8 in
a test-only dependency is P3, a 5.3 reachable from an unauthenticated route is P1.

**Done when:** every finding carries a state, a written path or a written argument, a bucket,
and both scores where they differ.

## 7. Write the fix

Every P1 and P2 gets a fix a person can apply:

| Finding | The fix |
| --- | --- |
| SAST flaw | the diff — parameterized query, encoded output, the safe API in place of the unsafe one |
| CVE | the fixed version, whether it is a major bump, and what else it drags with it. No fixed version yet? the mitigation that holds until there is |
| Secret | **rotate first**, then remove it from the code. The key is live until it is rotated, and the history keeps the old value whatever the next commit does |
| Access control | the check, and where it belongs — a middleware or policy layer rather than one more `if` in one more handler |
| Config | the setting, in the file that declares it, so the next deploy keeps it |

Where the real fix is a design change, say so and give the mitigation that holds in the meantime
— the route disabled, a rule at the edge, a network policy. A design change presented as a
one-line patch gets applied badly and closed.

The code stays as it is: these are proposals for their owner.

**Done when:** every P1 and P2 finding carries a fix — a diff, a version, or a named design
change with its interim mitigation — and every secret carries its rotation as the first step.

## 8. Work out the gates

Four, and the second is the one people miss:

| Gate | Runs | Judged on |
| --- | --- | --- |
| SAST | every pull request, changed files | no new finding above P2 |
| SCA | **on a schedule**, daily or nightly | no new reachable CVE |
| Secrets | a pre-commit hook, plus history on a schedule | nothing new |
| DAST | nightly against staging | no new P1 |

The scheduled SCA run matters because dependency risk moves when the code does not: a repository
clean on Friday is vulnerable on Monday because a CVE was published, and a gate that only fires
on a pull request never notices.

Nothing is applied here, so every gate is reported as recommended.

**Done when:** all four are written down with the workflow file each would live in, and no CI
file has been edited.

## 9. Write the report

Header: the timestamp from `date '+%Y-%m-%d-%H%M%S'`, the commit from `git rev-parse --short
HEAD`, and a note if the working tree is dirty.

Write to `<module>/.reports/security-report-<timestamp>.md`. `<module>` is the nearest directory
at or above the scope holding the project's manifest (`package.json`, `go.mod`,
`pyproject.toml`, `pom.xml`, `Cargo.toml`, `composer.json`, `Gemfile`, `*.csproj`); a run
spanning several writes to the repository root. Create the folder if missing, add `.reports/` to
the root `.gitignore` if nothing there covers it, one file per run, never overwrite an older one.

A security report names live weaknesses in a system somebody runs. Keep secret values, session
tokens, and captured PII out of it — a path, a `file:line`, and the first four characters of a key
identify a finding without republishing it. Point the user at the file rather than pasting its P1
section into a chat log.

Use the shape below and put the data in tables. The prose left over is the path on each P1, the
argument on each unreachable finding, and one sentence per fix needing a design change.

Then give the user the file path, the P1 count, and the single finding to take first — leading
with the rotation where a secret was found.

**Done when:** the report sits in the module's `.reports` folder, `.reports/` is git-ignored, no
older report was overwritten, every finding from steps 2 to 5 appears in exactly one bucket with
its path or argument, every OWASP category carries how it was checked, and no secret value or
captured personal data is written into the file.

---

# Report shape

A TypeScript service. The tables, states, and buckets are what transfers — swap in your own
tools, paths, and standard. Every table is shown with one or two data rows; a real report lists
them all.

````markdown
# Security & Compliance Report

| | |
| --- | --- |
| **Run** | <YYYY-MM-DD HH:MM:SS> |
| **Commit** | `<short sha>` (dirty working tree) |
| **Scope** | `src/**`, `Dockerfile`, `infra/**` — 96 files |
| **Standard** | OWASP Top 10 (2021), CWE on every finding, ASVS L2 |
| **Scans** | SAST `semgrep 1.86.0` · SCA `osv-scanner 1.9.1` · secrets `gitleaks 8.21.2` · config `trivy 0.58.1` · DAST `zap 2.15.0` |
| **DAST** | staging, authorized by <name> 2026-07-31, 14:02–14:41 UTC |
| **Previous** | [`security-report-2026-07-24-101500.md`](./security-report-2026-07-24-101500.md) |

## Where it stands

| Bucket | Count | Previous | Change |
| --- | --- | --- | --- |
| 🔴 **P1** — reachable, high impact | 4 | 2 | +2 |
| 🟠 **P2** — guarded, or limited impact | 11 | 14 | −3 |
| ⚪ **P3** — unreachable or informational | 63 | 58 | +5 |

209 raw findings from five tools became 78 after merging duplicates. One secret is live and
unrotated — the first item below.

## OWASP Top 10 coverage

| Category | Checked by | Findings |
| --- | --- | --- |
| A01 Broken Access Control | step 5, by hand — no tool covers it | 2 (1 P1) |
| A10 SSRF | Semgrep, step 5 | 0 — checked, none found |

A01 and the business-logic checks came from the step 5 read, because no scanner here covers
them.

---

## 🔴 P1 — take these first

### 1. Live AWS key in the git history — CWE-798

| | |
| --- | --- |
| **Found by** | gitleaks, over the full history |
| **Where** | `src/config/aws.ts:14`, added in `9f2c1ab` (2026-03-02), removed in `4d81be0` — still in the pack |
| **Key** | `AKIA3F…` — the value stays out of this report |
| **State** | reachable — anyone with clone access has it, and the repository has 40 collaborators |
| **Fix** | **rotate the key now**, then move it to the secret store. Rewriting history is optional; rotation is not, because the old value is already distributed |
| **OWASP** | A07 |

### 2. `GET /api/orders/{id}` returns any order — CWE-639

| | |
| --- | --- |
| **Found by** | step 5, object-ownership check |
| **Path** | `routes/orders.ts:41` → `orderService.get(id)` → `orderRepo.findById` — the session is authenticated, and the order id is never checked against the caller |
| **State** | reachable by any logged-in user, with any order id |
| **Impact** | every customer's order, address, and line items |
| **Fix** | scope the query to the caller — `findById(id, session.customerId)` — and put the check in the policy layer so the next handler inherits it |
| **OWASP** | A01 |

```ts
// routes/orders.ts:41
const order = await orderService.get(req.params.id)   // ← no ownership check
```

---

## 🟠 P2 — guarded, or limited impact

| # | Finding | CWE | State | The control standing in the way | Fix |
| --- | --- | --- | --- | --- | --- |
| 1 | `child_process.exec` with a filename from an upload, `src/jobs/convert.ts:88` | CWE-78 | guarded | the queue is internal, and only the upload handler writes to it — an SSRF or a queue write turns this into a P1 | `execFile` with an argument array, and validate the extension by content type |

---

## ⚪ P3 — unreachable or informational

| Finding | State | The argument |
| --- | --- | --- |
| `minimist 1.2.0` — CVE-2021-44906, CVSS 9.8 | unreachable | a `devDependency` of the build script, never shipped in the image and never run against untrusted input. Scored 9.8 by CVSS, P3 here |

62 more, listed by tool in `security/osv.json` and `security/semgrep.sarif`.

---

## DAST

| | |
| --- | --- |
| **Target** | `https://staging.example.com` — authorized by <name>, 2026-07-31 |
| **Window** | 14:02–14:41 UTC, 5 requests per second |
| **Hosts in scope** | `staging.example.com` only |
| **Alerts** | 1 high, 4 medium, 12 low, after merging with the SAST findings |

| Alert | Endpoint | Merged with | Bucket |
| --- | --- | --- | --- |
| Reflected XSS in the search parameter | `GET /search?q=` | Semgrep `react/dangerously-set-inner-html` | 🔴 P1 |
| Missing `Content-Security-Policy` | every response | — | 🟠 P2 |

---

## The gates

| Gate | Runs | Judged on | Where | State |
| --- | --- | --- | --- | --- |
| SAST | every pull request, changed files | no new finding above P2 | `.github/workflows/ci.yml` | recommended |
| SCA | nightly | no new reachable CVE | `.github/workflows/security-nightly.yml` | recommended |
| Secrets | pre-commit, plus history nightly | nothing new | `.pre-commit-config.yaml` | recommended |
| DAST | nightly against staging | no new P1 | `.github/workflows/security-nightly.yml` | recommended |

````

Every finding appears in exactly one bucket. Drop any empty section, and lead the body with P1.
Where no older report sits beside this one, drop the "Previous" row and the "Previous" and
"Change" columns.
