# pokie

*awk-style record processing with Python syntax and library support.*

Pokie is at the design stage. The repository contains a Python scaffold; the
language interpreter and `pokie` command are planned, not implemented.

______________________________________________________________________

## Why pokie?

Text-processing scripts often combine regex extraction, conversion exceptions,
and accumulator updates. Pokie explores a compact notation that keeps those
decisions together:

- Ordered record rules for filtering and aggregation.
- Structural cases for positional and named regex captures.
- Explicit predicates and conversions, with rejection as case fall-through.
- Python statements and installed libraries for the rest of the job.

______________________________________________________________________

## Quick start

### Install the development scaffold

From a checkout, with [uv](https://docs.astral.sh/uv/) installed:

```bash
uv sync --group dev
```

The scaffold requires Python 3.14 or newer. This installs the development
package; it does not install a language interpreter.

### Run the current package

```bash
uv run python -c 'from pokie import hello; print(hello())'
```

Expected output: `hello from Python`.

### Preview the proposed language

This is proposed pokie syntax, not executable with the current scaffold:

```text
start:
    accepted = 0

when /user=(\w+) uid=(\S+)/:
    case name, int(uid) if uid >= 0:
        accepted += 1

end:
    print(accepted)
```

The regex extracts values. The case converts the identifier, the guard rejects
negative values, and the action counts accepted records.

______________________________________________________________________

## Planned features

- `start:`, ordered `when` rules, and `end:` for persistent stream state.
- `$0`, positional fields, `NF`, and `NR` for record access.
- Multiple capture cases, guards, optional captures, and named views.
- Predicate and coercion adapters with explicit match/no-match results.
- Pokie IR lowered to Python ASTs and executed by CPython.
- Diagnostics associated with original pokie source.

Parallel execution, a package manager, and Rust acceleration are deferred. The
[roadmap](docs/roadmap.md) records the evidence required for delivery.

______________________________________________________________________

## Learn more

- [Documentation contents](docs/contents.md) – the complete index.
- [Terms of reference](docs/terms-of-reference.md) – users, scope, and success.
- [Context](docs/context.md) – shared language and evidence distinctions.
- [Technical design](docs/pokie-design.md) – proposed semantics and
  architecture.
- [Users' guide](docs/users-guide.md) – current usage and validation commands.
- [Developers' guide](docs/developers-guide.md) – contributor workflow.
- [Roadmap](docs/roadmap.md) – GIST delivery steps and evidence gates.

______________________________________________________________________

## Licence

ISC – see [LICENSE](LICENSE).

______________________________________________________________________

## Contributing

Contributions are welcome. Start with the design's open questions and
[AGENTS.md](AGENTS.md), then follow the
[developers' guide](docs/developers-guide.md). Examples, counterexamples, and
real text-processing jobs help settle the language before implementation.
