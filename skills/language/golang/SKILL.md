---
name: golang
description: >
  Go (Golang) development guide. Use for any Go coding, review, debugging, or
  setup task — writing code, style and naming, errors, concurrency, context,
  testing, benchmarks, performance, security, databases, gRPC, GraphQL, CLI
  tools, dependency injection, linting, CI, observability, refactoring, project
  layout, and the samber/*, uber-go/*, spf13/* and stretchr/testify libraries.
license: MIT
---

# Golang

Merged from [samber/cc-skills-golang](https://github.com/samber/cc-skills-golang).

## How to use this skill

This file is only an index. Read the topic files you need, and nothing more.

1. Match the task to one or more rows below.
2. Read that row's file with the Read tool. Paths are relative to this skill's
   folder, for example `references/testing/GUIDE.md`.
3. Each guide may point to deeper files in its own `references/` folder. Read
   those only when the guide tells you to.

Load two or three topics at most. If a task spans more, start with the closest
one and follow its links.

## Topics

### Writing everyday Go

| Read this | When |
|---|---|
| `references/code-style/GUIDE.md` | Line breaking, declarations, control flow, when a comment helps |
| `references/naming/GUIDE.md` | Naming packages, structs, interfaces, errors, receivers, tests |
| `references/documentation/GUIDE.md` | Godoc comments, README, CHANGELOG, example tests |
| `references/structs-interfaces/GUIDE.md` | Composition, embedding, type switches, field tags, receivers |
| `references/design-patterns/GUIDE.md` | Functional options, constructors, lifecycle, graceful shutdown |
| `references/data-structures/GUIDE.md` | Slices, maps, container/*, strings.Builder, pointer semantics |
| `references/error-handling/GUIDE.md` | Wrapping with %w, errors.Is/As, sentinel errors, panic/recover |
| `references/context/GUIDE.md` | Cancellation, deadlines, request values, context propagation |
| `references/concurrency/GUIDE.md` | Goroutines, channels, sync, errgroup, worker pools, races |
| `references/safety/GUIDE.md` | Nil panics, append aliasing, map races, zero-value design |
| `references/modernize/GUIDE.md` | Replacing old patterns with current Go features |
| `references/refactoring/GUIDE.md` | Safe large-scale restructuring with gopls, gofmt -r, gopatch |

### Testing and measuring

| Read this | When |
|---|---|
| `references/testing/GUIDE.md` | Table tests, parallel tests, fuzzing, fixtures, coverage, goleak |
| `references/stretchr-testify/GUIDE.md` | assert, require, mock, suite |
| `references/benchmark/GUIDE.md` | Benchmarks, pprof, benchstat, profile reading |
| `references/performance/GUIDE.md` | Fixing a known bottleneck: allocations, GC, pooling, hot paths |
| `references/troubleshooting/GUIDE.md` | Bugs, crashes, deadlocks, root-cause hunting |
| `references/gopls/GUIDE.md` | Code intelligence: definitions, references, rename, diagnostics |

### Building services and tools

| Read this | When |
|---|---|
| `references/project-layout/GUIDE.md` | New project, monorepo, workspaces, package boundaries |
| `references/cli/GUIDE.md` | CLI design: flags, exit codes, signals, completion |
| `references/spf13-cobra/GUIDE.md` | cobra command trees |
| `references/spf13-viper/GUIDE.md` | viper layered configuration |
| `references/database/GUIDE.md` | SQL access, transactions, pools, migrations, database/sql, sqlx, pgx |
| `references/grpc/GUIDE.md` | gRPC servers, clients, protobuf, interceptors |
| `references/graphql/GUIDE.md` | gqlgen or graphql-go servers, schemas, resolvers |
| `references/swagger/GUIDE.md` | OpenAPI docs with swaggo/swag annotations |
| `references/observability/GUIDE.md` | slog, Prometheus metrics, OpenTelemetry traces, alerting |
| `references/security/GUIDE.md` | Injection, crypto, secrets, file and network safety |

### Dependency injection

| Read this | When |
|---|---|
| `references/dependency-injection/GUIDE.md` | Choosing an approach, manual wiring, library comparison |
| `references/google-wire/GUIDE.md` | google/wire (compile time) |
| `references/uber-dig/GUIDE.md` | uber-go/dig |
| `references/uber-fx/GUIDE.md` | uber-go/fx |
| `references/samber-do/GUIDE.md` | samber/do |

### Toolchain and project upkeep

| Read this | When |
|---|---|
| `references/lint/GUIDE.md` | golangci-lint setup, .golangci.yml, nolint directives |
| `references/continuous-integration/GUIDE.md` | GitHub Actions, coverage, scanners, GoReleaser, Dependabot |
| `references/dependency-management/GUIDE.md` | go.mod, upgrades, vulnerability scans, version conflicts |
| `references/popular-libraries/GUIDE.md` | Picking a library or comparing alternatives |
| `references/pkg-go-dev/GUIDE.md` | Looking up package docs and versions with `godig` |
| `references/stay-updated/GUIDE.md` | Go news, releases, learning resources |

### samber libraries

| Read this | When |
|---|---|
| `references/samber-lo/GUIDE.md` | Generic helpers: Map, Filter, Reduce, GroupBy, Uniq |
| `references/samber-mo/GUIDE.md` | Monads: Option, Result, Either, Future, IO |
| `references/samber-oops/GUIDE.md` | Structured errors with stack traces and context |
| `references/samber-hot/GUIDE.md` | In-memory caching and eviction algorithms |
| `references/samber-ro/GUIDE.md` | Reactive streams and observables |
| `references/samber-slog/GUIDE.md` | slog handlers, pipelines, sampling, HTTP middleware |
