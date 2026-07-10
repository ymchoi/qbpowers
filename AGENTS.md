## Python Execution Rules
- Use Python 3.14.
- Do not call the OS-global `python3` / `pip` directly. Run everything with the `python` from the relevant `.venv` (or with `python -m pip`).

## File Modification Permissions and Temporary Files
- Non-modifying actions such as reading/analyzing local files, web browsing/search, and discussion are always automatically allowed.
- Every user prompt starts in a `file modification prohibited` state by default.
- Only begin file addition, modification, or deletion work when the prompt contains the exact phrase `<GATE_MARKER>`.
- The following work is allowed without `<GATE_MARKER>`:
  - Adding, modifying, or deleting files under `.temp_files/`.
- Experiment files, temporary files, and intermediate files that are safe to delete and whose paths are not explicitly specified must be stored under `{project root}/.temp_files/`. Create a subdirectory named with `YYYYMMDD_HHMMSS` plus a description of the purpose, and save the files there. Example: `.temp_files/20260327_232323_translate_test/test_data.json`

## Subagents
- Unless the user explicitly specifies a subagent's `model`/`effort`: in codex, create subagents with `gpt-5.6-sol`+`ultra`. In claude code, default to `opus`+`max`, but since `effort` cannot be set through the plain `Agent` tool, specify `max` only on paths that support `effort` (such as the `Workflow` `agent()` options); on other paths, specify only the `opus` model and let `effort` inherit the session value.
- Inject the temporary-folder (.temp_files) rule into every subagent every time.
- If more than three direct `mcp__context7__` calls are needed in one turn, delegate to new subagents in batches of three calls so context7 can be used without a call-count limit.
- Even without explicit instruction from the user, make full and active use of parallel subagents for any work where subagents can help. Even when parallelism isn't needed, the technique of using just one subagent to save the main agent's context size is also very useful.

## Research Evidence and External Documentation
- Look for evidence in local files first. Prioritize repository-internal code, configuration, and project documentation.
- If you cannot find evidence in local files, obtain the necessary factual evidence through `mcp__context7__` or sufficient web search, as appropriate.
- If web access is blocked by a site's bot protection, try `curl -L -o`; if curl is blocked too, use `utils/fetch_web/fetch_site.py`. Even without bot blocking, use `fetch_site.py` for pages where the built-in web tools or `curl` cannot collect the information properly. `fetch_site.py` cannot run in parallel and must be used strictly serially; when processing multiple pages, serialize by running a single dedicated subagent that alone makes the `fetch_site.py` calls. Save the outputs of `curl` and `fetch_site.py` under `.temp_files`.
- Check the date and version for time-sensitive or version-dependent information.

## Prompt Interpretation and User Confirmation
- Do not read only the surface wording of the user's message. Analyze the context in which the prompt was sent, its position in the conversation flow, and what the user ultimately wants to know. If the interpretation of the user's prompt is uncertain, ask a specific question.
- When you receive a prompt, first classify the parts you may decide freely and the parts that require the user's confirmation.
- If uncertainty remains after verification, explicitly state `unverified` or `speculation`. If there is no evidence, answer `I don't know` or `needs verification`.
- For symptoms described by the user, answer only after directly checking the related facts with tools.

## Tasks, Planning, and Verification
- Transform tasks into verifiable goals:
  - `Add validation` → `Write tests for invalid inputs, then make them pass`
  - `Fix the bug` → `Write a test that reproduces it, then make it pass`
  - `Refactor X` → `Ensure tests pass before and after`
- If the same or a similar attempt fails multiple times, do not keep trying in the same direction.
- For features that can be tested headlessly (e.g., with Playwright), run tests in headless mode without opening physical OS popup windows. Playwright headless testing is especially useful.

## Code Change Principles
- Before modifying or deleting code, check the import relationships, configuration, tests, and related documentation that may affect the result. Do not judge by the beginning of a file only; read list-like information to the end. If you cannot check everything, state the checked and unchecked ranges.
- If a senior engineer would call it `over-engineered`, simplify it. For example, if something written in 200 lines could be done in 50, rewrite it (the numbers are illustrative).
- State assumptions explicitly. If uncertain or if multiple interpretations are possible, do not silently choose one; ask a question or present choices. If there is a simpler approach, say so. When justified, push back on the user's decision.
- When modifying or adding code, also clean up unnecessary complexity found in the same file or directly related code.
- Write code comments in this project in English.

## Python Type, Lint, and Verification Rules
- Use mypy as the repository's authoritative Python type checker. Do not add another type checker unless the project explicitly adopts it.
- Use mypy strict mode and do not weaken type settings.
- All new or modified functions and methods must have explicit parameter and return types, and changed Python code must pass the configured mypy check without weakening type settings.
- Prefer precise domain types, Pydantic models, `TypedDict`, dataclasses, generics, and `Protocol` over bare `dict`, `dict[str, Any]`, or broad `Any`.
- Use Pydantic at external or untrusted boundaries: API payloads, LLM outputs, tool arguments, config, webhooks, database DTOs, and queued/file messages.
- Prefer inference for obvious local variables. Annotate locals only when it clarifies intent or helps mypy: empty collections, `None` initialization, `Any` quarantine, complex unions, public attributes, or ambiguous inference.
- Avoid unnecessary `Any`, `cast()`, `# type: ignore`, and `# noqa`. If unavoidable, keep the escape hatch local, use a specific code, and explain why.
- Ruff owns formatting, linting, and import sorting. Do not introduce other Python formatters, linters, or import sorters unless existing committed configuration requires them.
- After Python edits, run Ruff, mypy, and relevant pytest tests. Fix root causes instead of weakening checks; report exact blockers when verification cannot be run.
