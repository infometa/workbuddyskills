---
name: tdd
description: Test-driven development with red-green-refactor loop. Use when user wants to build features or fix bugs using TDD, mentions "red-green-refactor", wants integration tests, or asks for test-first development.
description_zh: "测试驱动开发：红→绿→重构，以行为测试驱动实现"
description_en: "Test-driven development with red-green-refactor loop and behavior-first testing"
version: 1.0.0
homepage: https://github.com/mattpocock/skills
allowed-tools: Read,Write,Bash,Grep
---

# Test-Driven Development

## Philosophy

**Core principle**: Tests should verify behavior through public interfaces, not implementation details. Code can change entirely; tests shouldn't.

**Good tests** are integration-style: they exercise real code paths through public APIs. They describe _what_ the system does, not _how_ it does it. A good test reads like a specification - "user can checkout with valid cart" tells you exactly what capability exists. These tests survive refactors because they don't care about internal structure.

**Bad tests** are coupled to implementation. They mock internal collaborators, test private methods, or verify through external means (like querying a database directly instead of using the interface). The warning sign: your test breaks when you refactor, but behavior hasn't changed. If you rename an internal function and tests fail, those tests were testing implementation, not behavior.

### Mocking guidelines

- Mock at system boundaries only (network, filesystem, external services)
- Never mock internal collaborators or private implementation details
- Prefer real implementations over mocks when the cost of running them is acceptable
- If you need to mock something internal, that's a signal the code needs better seam design

## How to run tests

Before starting, detect the project's test runner by reading `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, or similar config files. Use `Bash` to run tests:

- **JavaScript/TypeScript**: `npm test`, `npx jest`, `npx vitest run`, or `npx mocha`
- **Python**: `pytest`, `python -m pytest`
- **Go**: `go test ./...`
- **Rust**: `cargo test`
- **Java/Kotlin**: `./gradlew test` or `mvn test`
- **Ruby**: `bundle exec rspec`

If uncertain, check `package.json` scripts or the project README. **Always confirm a test command works before starting the RED-GREEN loop.**

RED = run test, see it fail with the expected failure (not a compile error or wrong failure).
GREEN = run test, see it pass.

## Anti-Pattern: Horizontal Slices

**DO NOT write all tests first, then all implementation.** This is "horizontal slicing" - treating RED as "write all tests" and GREEN as "write all code."

This produces **crap tests**:

- Tests written in bulk test _imagined_ behavior, not _actual_ behavior
- You end up testing the _shape_ of things (data structures, function signatures) rather than user-facing behavior
- Tests become insensitive to real changes - they pass when behavior breaks, fail when behavior is fine
- You outrun your headlights, committing to test structure before understanding the implementation

**Correct approach**: Vertical slices via tracer bullets. One test → one implementation → repeat. Each test responds to what you learned from the previous cycle. Because you just wrote the code, you know exactly what behavior matters and how to verify it.

```
WRONG (horizontal):
  RED:   test1, test2, test3, test4, test5
  GREEN: impl1, impl2, impl3, impl4, impl5

RIGHT (vertical):
  RED→GREEN: test1→impl1
  RED→GREEN: test2→impl2
  RED→GREEN: test3→impl3
  ...
```

## Workflow

### 1. Planning

When exploring the codebase, use the project's domain glossary so that test names and interface vocabulary match the project's language, and respect ADRs in the area you're touching.

Before writing any code:

- [ ] Detect the test runner and confirm `run tests` command works
- [ ] Confirm with user what interface changes are needed
- [ ] Confirm with user which behaviors to test (prioritize)
- [ ] Identify opportunities for deep modules (small interface, deep implementation)
- [ ] Design interfaces for testability
- [ ] **Produce a numbered behavior list** — this becomes the loop queue for Steps 2-3

Ask: "What should the public interface look like? Which behaviors are most important to test?"

**You can't test everything.** Confirm with the user exactly which behaviors matter most. Focus testing effort on critical paths and complex logic, not every possible edge case.

The behavior list produced here drives Steps 2 and 3. Each item is checked off as it reaches GREEN.

### 2. Tracer Bullet

Take behavior #1 from the planning list. Write ONE test that confirms it:

```
RED:   Write test → run tests → confirm failure message matches expected behavior
GREEN: Write minimal code → run tests → confirm pass
```

This is your tracer bullet - proves the path works end-to-end.

### 3. Incremental Loop

For each remaining behavior in the planning list (in order):

```
RED:   Write test → run tests → confirm RED
GREEN: Minimal code to pass → run tests → confirm GREEN
Check off this behavior from the list
```

Rules:

- One test at a time
- Only enough code to pass current test
- Don't anticipate future tests
- Keep tests focused on observable behavior

**Loop ends** when all behaviors from the planning list are checked off and GREEN.

### 4. Refactor

After all behaviors pass, look for refactor candidates:

- [ ] Extract duplication
- [ ] Deepen modules (move complexity behind simple interfaces)
- [ ] Apply SOLID principles where natural
- [ ] Consider what new code reveals about existing code
- [ ] Run tests after each refactor step — all must stay GREEN

**Never refactor while RED.** Get to GREEN first.

**Done when**: all planned behaviors are GREEN and tests still pass after refactor.

## Checklist Per Cycle

```
[ ] Test describes behavior, not implementation
[ ] Test uses public interface only
[ ] Test would survive internal refactor
[ ] RED confirmed by actually running the test (not assumed)
[ ] Code is minimal for this test
[ ] GREEN confirmed by actually running the test
[ ] No speculative features added
```
