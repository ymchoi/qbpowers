## Python Environment
- Run all Python, including one-off scripts, with Python 3.14 from the `.venv` at the repository root. Never call the OS-global `python3` or `pip`; install packages with `python -m pip`.
- Manage dependencies in the root `pyproject.toml`, never with `requirements.txt`.

## Files and Processes
- Put temporary, experimental and intermediate files whose location the user did not specify in `.temp_files/YYYYMMDD_HHMMSS_<purpose>/` (for example, `.temp_files/20260327_232323_translate_test/`).
- Edit files tracked by git only with the file-editing tool (Claude Code: `Edit`/`Write`; Codex: `apply_patch`), not with `sed -i`, scripted replacement or shell redirection. Output from formatters and code generators is exempt.
- Before deleting files or stopping processes or databases, check that they belong to the current work. Do not judge by names, prefixes or old PIDs alone; if another session or the user might be using them, ask first.

## Git
- Commit only when the user asks.

## Interpreting and Answering User Requests
- If a request seems mistaken or a simpler approach exists, say so briefly, with the reason.
- Before answering about a symptom the user describes, check the relevant facts with tools.

## Code Changes
- If a design defect within the task's scope would force a workaround, fix the defect instead, sized to its real impact.
- Keep designs as simple as the requirement allows; do not write 200 lines where 50 will do.
- Do not add handling for cases that are very unlikely to happen, or just-in-case options, abstractions, fallbacks, exception handling or validation: over-engineering is itself a source of bugs. Validation at boundaries (user input, external APIs, file and queue messages) and handling of external failures that really occur are still required.
- Do not add production code that behaves differently under test (for example, checks of a test environment variable, or bypasses taken only in tests). If code is hard to test, inject dependencies such as clocks, clients and paths through parameters or a `Protocol`, defaulting to production behavior.
- Name tests and identifiers by behavior, not by review rounds or task IDs.
- Write comments, in English, only for reasons, constraints or caveats the code cannot show. Do not restate the code or record change history or task IDs.

## Verification and Reporting
- After edits, run the formatter and linter configured for each language you changed (Python: Ruff, mypy and the relevant pytest tests). If a check fails, fix the root cause instead of loosening or ignoring the check. If a check cannot run, report exactly what blocked it.
- For a bug fix, first add a test that reproduces the bug, where practical.
- Run tests headless when possible (for example, Playwright headless). Open OS windows only when the user allows it.
- Report each check as passed, partially checked, failed or not run. Do not present a test on mock data as a real-environment test.
- Read a worker's report that checks passed as covering only the checks that worker ran, and rerun the checks after merging the work.

## Python Types
- Use mypy in strict mode as the only type checker, and do not loosen its settings. Changed code must pass mypy; new or changed functions need explicit parameter and return types.
- Prefer precise types (domain types, Pydantic models, `TypedDict`, dataclasses, generics, `Protocol`) over bare `dict`, `dict[str, Any]` or `Any`. Keep unavoidable `Any`, `cast()`, `# type: ignore` or `# noqa` narrow, with a specific code and a reason.
- Use Pydantic at external or untrusted boundaries: API payloads, LLM outputs, tool arguments, config, webhooks, database DTOs, and queue or file messages.
- Let local variable types be inferred. Annotate a local only when it clarifies intent or mypy needs it: empty collections, `None` initialization, `Any` quarantine, complex unions, public attributes or ambiguous inference.
- Use Ruff for Python formatting, linting and import sorting; do not add other tools for these unless committed configuration already requires them.

## Research and External Sources
- Look for evidence in the repository first: code, configuration and project documentation. Then search the web.
- If the built-in web tools cannot get a page (bot block or missing content), download it with `curl -L -o` and save the result under `.temp_files/`.
- Check dates and versions for time-sensitive or version-dependent facts.

## Documentation
- Keep in documents only what agents need to consult or work from; delete the rest. Accumulate journal- or log-style records only when strictly necessary; otherwise delete or tightly compress them.
- Status documents and every `AGENTS.md`/`CLAUDE.md` (root and subprojects) hold only the current state and stable rules, never run logs or incident-specific rules.
- When a change alters what a source-of-truth document describes, update that document in the same change. Link to a rule's single source instead of copying it. Put conclusions in the relevant document, not only in `.temp_files/`.
