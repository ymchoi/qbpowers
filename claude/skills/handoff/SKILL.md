---
name: handoff
description: Generate a comprehensive handover document for the current session so a new, context-blind agent can continue the work.
disable-model-invocation: true
---

# Handoff

Generate a single Markdown handover document under `.temp_files/` that captures the current session with enough fidelity for a new, context-blind agent to continue without seeing this conversation.

## Argument

The user may include optional free-form text after `/handoff`:

```
/handoff [<text>]
```

- If `<text>` is empty, follow the default behavior described below.
- If `<text>` is present, treat it as **high-priority instructions** that may override the defaults (length, language, format, content focus, output destination of the report message, and so on). The only invariants that cannot be overridden are:
  - The handover file is written under `.temp_files/`.
  - The handover output is a single Markdown file.

## Steps

Run the following phases in a single invocation, automatically.

### Phase 1 — Write

1. Choose a destination folder under `.temp_files/`:
   - Format: `.temp_files/<YYYYMMDD_HHMMSS>_handoff_<purpose>/`
   - `<YYYYMMDD_HHMMSS>` is the current local time.
   - `<purpose>` is a short snake_case slug derived from the main subject of the current session. If no clear subject can be derived, omit the suffix and use `.temp_files/<YYYYMMDD_HHMMSS>_handoff/` instead.
   - The slug never reflects `<text>`; `<text>` is for content instructions only.
2. Inside that folder, create a single file named `handoff.md`.
3. Write the handover document into `handoff.md` so that it captures **as much high-value information from this session as possible**. Maximize information density. Do not summarize substance away. Do not omit details that could matter to a recipient who has nothing else to go on. Treat `handoff.md` as the recipient's only source of context for continuing the work. There is no fixed list of section titles. Decide what to include based on the actual content of this session, while respecting any high-priority instructions provided in `<text>`.
4. Do not print the document body in the chat reply.

### Phase 2 — Self-check

Once the file is written, evaluate it strictly from the position of a fresh agent who has **zero visibility** into this conversation and can rely **only** on what is written in `handoff.md`. Ask honestly: does that agent have **enough information to continue the work without being blocked**? Surface every gap that would weaken that answer, even small ones; do not gloss over uncertainty. The dimensions of evaluation are determined per session; do not assume a fixed checklist.

### Phase 3 — Augment (only if gaps were found)

If Phase 2 found gaps, append additional sections to the same `handoff.md` to address them. The structure and titles of the appended sections are decided per session, based on the gaps found. If Phase 2 found no gaps, skip this phase.

### Phase 4 — Report

Send a short message to the user (one or two lines) containing:

- The absolute path of the saved `handoff.md`.
- A brief self-check result such as `self-check passed` or `self-check found N gap(s); augmented`.

Do not include the document body or any specific content from it in this report.

## Constraints

- Write to `.temp_files/` only. Do not modify files elsewhere unless `<text>` explicitly authorizes it and the surrounding project rules permit it.
- The document body must not appear in the chat reply unless `<text>` explicitly requests it.
- Do not introduce a fixed template of section titles into this skill. The structure of `handoff.md` is determined per session by Phase 1 and Phase 2.
