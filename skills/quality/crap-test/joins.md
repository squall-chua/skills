# The join

CRAP needs two numbers about the same function: its cyclomatic complexity and its coverage.
Almost no toolchain gives both, so the work is joining two files. This page holds the exact
command, the field to read, and the join key, per language.

The join is where a CRAP run goes wrong, and it goes wrong silently — a bad key produces a
short table, not an error. Step 5 of the skill reconciles the counts for exactly this reason.

## Read the tool's own output first

Field names and message wording drift between versions. Run the command once on one file,
look at what came out, and write the parser against that — never against the shape written
here from memory. The commands below are a starting point, not a contract.

## The universal path — lizard + lcov

Reach for this when the language has no better pair below, or when one script must cover a
repo in several languages.

**Complexity** — `lizard` handles C, C++, Java, C#, JavaScript, TypeScript, Python, Ruby,
PHP, Swift, Scala, Go, Kotlin, Rust, and more, in one output format:

```sh
lizard --csv <path> > complexity.csv
```

Each row carries the cyclomatic number (`CCN`), the file, the function's long name, and its
start and end lines. Start and end are what make the join possible.

**Coverage** — nearly every coverage tool emits lcov. The `DA:<line>,<hits>` records give one
line and its hit count:

```
SF:src/pricing.ts
DA:88,4
DA:89,0
```

**Join** — a function owns the `DA` lines inside `[start, end]`, minus the ranges of any
function nested inside it. Coverage is hit lines over total lines in that set.

**Gotcha** — lcov `DA` records only cover *instrumented* lines, so blank lines, comments, and
declarations are simply absent. That is correct: they are not statements. Do not treat an
absent line as uncovered.

---

## One file holds both — Java and Kotlin

JaCoCo's XML report carries per-method counters, so there is no join at all:

```xml
<method name="reconcile" desc="(...)V" line="112">
  <counter type="COMPLEXITY" missed="14" covered="24"/>
  <counter type="LINE" missed="9" covered="31"/>
</method>
```

Complexity is `COMPLEXITY` missed + covered. Coverage is `LINE` covered ÷ (missed + covered).
Generate with `mvn jacoco:report` or the Gradle `jacocoTestReport` task, and read
`jacoco.xml`, not the HTML.

**Gotcha** — `<method>` sits under `<class>` under `<package>`; the source file name is on the
`<class>` element's `sourcefilename`, not on the method. Constructors appear as `<init>` and
static initialisers as `<clinit>`.

## Already computed — PHP

PHPUnit computes CRAP itself. With Xdebug or PCOV installed:

```sh
phpunit --coverage-clover clover.xml
```

Each `<method>` carries `complexity`, `coverage`, and `crap`. Read the published value; do not
recompute it. Any other Clover-format producer does the same.

## Go

```sh
gocyclo <path> > complexity.txt
go test -coverprofile=coverage.out -coverpkg=./... ./...
go tool cover -func=coverage.out > coverage.txt
```

`gocyclo` prints `<complexity> <package> <func> <file>:<line>:<col>`. `go tool cover -func`
prints `<file>:<line>:\t<func>\t<percent>%`. Both line numbers point at the `func` keyword, so
**file + line is an exact key** and the percentage is per function already — no line-range
arithmetic.

**Gotchas** — drop the final `total:` row from the coverage output. Methods print as the bare
method name in one tool and may carry the receiver in the other, so join on file and line, not
on the name. Without `-coverpkg=./...`, a package tested only from elsewhere reads as 0%.

## Python

```sh
radon cc -j -s <path> > complexity.json
coverage json -o coverage.json
```

`radon` gives `name`, `lineno`, `endline`, `complexity`, and `type` per block. `coverage json`
gives `files[<path>].executed_lines` and `missing_lines`.

**Join** — a function's statements are `(executed ∪ missing) ∩ [lineno, endline]`; coverage is
`executed ∩` that set, over its size.

**Gotchas** — drop rows with `type: "class"`, or every method is counted twice, once on its own
and once inside its class's range. Subtract nested function ranges from the enclosing function.
Decorator lines fall inside the range and belong to the function.

## JavaScript and TypeScript

```sh
npx eslint --no-config-lookup --rule '{"complexity":["warn",0]}' -f json <path> > complexity.json
```

Setting the maximum to 0 makes every function report. Each message carries `line`, `column`,
and a text like `Function 'x' has a complexity of 7. Maximum allowed is 0.` — take the number
after `complexity of`, and check the wording against the installed version before trusting the
pattern.

`--no-config-lookup` is what stops ESLint hunting for a project config, so the number is the
rule's and not the repo's. On ESLint 8 and older that flag was `--no-eslintrc`; it was removed
with flat config in v9, and passing it to a current ESLint fails outright rather than falling
back.

Coverage comes from Istanbul's JSON, which every common runner can emit — `vitest
--coverage.reporter=json`, `jest --coverage --coverageReporters=json`, or `nyc report -r json`.
In `coverage-final.json`, `fnMap` gives each function a `decl` (the signature) and a `loc` (the
body range); `statementMap` plus the `s` counts give per-statement hits.

**Join** — ESLint's `line` against `fnMap[i].decl.start.line`; then count the `statementMap`
entries inside `fnMap[i].loc`.

**Gotchas** — arrow functions and callbacks are functions here and nest constantly, so the
nested-range subtraction matters more than in most languages. For TypeScript, confirm the paths
in `coverage-final.json` point at the `.ts` sources and not at compiled output. Anonymous
functions arrive with an empty `name` — key them by file and line, and label them by their
enclosing function in the report.

## C#

```sh
dotnet test /p:CollectCoverage=true /p:CoverletOutputFormat=cobertura
```

Coverlet's Cobertura output has `<method>` elements carrying `line-rate` and a `complexity`
attribute.

**Check the attribute before relying on it.** If `complexity` reads 0 across every method, it
is absent rather than measured — fall back to `lizard` for complexity and join on file and the
method's first line.

## Ruby

Use `lizard` for complexity: RuboCop's `Metrics/CyclomaticComplexity` reports a number but only
a start location, and the end line is needed for the join.

```sh
lizard --csv <path> > complexity.csv
```

SimpleCov writes `coverage/.resultset.json`, holding one array per file with a hit count per
line — `null` for lines that are not statements. Join by line range, treating `null` as absent.

## Rust

```sh
cargo llvm-cov --json --output-path coverage.json
rust-code-analysis-cli -m -O json -p <path> -o complexity/
```

`llvm-cov`'s JSON has a `functions` array with names, filenames, and regions.
`rust-code-analysis-cli` reports cyclomatic per code space with start and end lines.

**Join** — file plus the function's start line.

**Gotcha** — llvm-cov's per-function figure is *region* coverage, which is closer to branch
coverage than to line coverage, and reads lower for the same tests. It is a legitimate input to
CRAP — the cube just bites sooner. Say in the report which one the score used, or a later run
against line coverage looks like an improvement that never happened.
