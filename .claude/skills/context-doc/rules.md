## Document rules

Keep these documents current without being asked. Where another rule about keeping documents differs from this block, the block decides for this project's documents.

- This file is the entry: what the project is, the rules that always apply, and a table with a row for each topic document.
- `docs/status.md` holds work in progress only. Overwrite it: finished work and seldom-changing facts leave it. While it exists, a line near the top of this file links to it and says to read it first on entry and after a context compaction.
- Other files in `docs/` are topic documents. Rewrite them in place, one owner document per fact; others link to it.
- Write in the same turn when: the user decides something (a rule with its reason, in its owner document); a unit of work (a merge, a measurement, a verification) ends (remove it from status, move what lasts to topic documents); next steps, waits or running work change (update status); a code change makes a document wrong (fix it in the same change).
- Write only what the code cannot tell and what saves an agent trial and error, work or repeated analysis. No history, logs or decision log.
- A rule is one directive and its reason, on one line, kept while the reason holds and the code does not hold it. A reason that is the user's preference says so, in the rule or in the failure that replaces it; only the user changes such a rule.
- Before writing a rule, and when an agent breaks one, check whether the code can hold it instead, so that breaking it fails a check or cannot be written; if it can, change the code, let the failure explain why, and keep no rule for it.
- Write a guess as a guess, with the way to check it. Build no rule on a guess.
- If a document says the code does one thing and the code does another, follow the code, and fix the document in the same change. If the code breaks a rule, keep the rule and tell the user.
- Write every document in English. Keep Korean only where English would be wrong or ambiguous, not merely less familiar. Such places are rare; when unsure, write English. This rule is for documents only: talk to the user in the user's language.
- Only the main session edits these documents, except a worker running a procedure of the skill below. Other workers report what the documents need.
- Evidence goes under `.temp_files/`; only status may point there. Material that cannot be made again goes in `ref/`, and a document says why it is there.
- Limits: 5,000 tokens per document; 100,000 in total, or this file's `Document budget:` line. After each unit of work, run `python .claude/skills/context-doc/scripts/check_docs.py <project directory>` with a Python that has `tiktoken`, and fix what it reports.
- Procedures: `.claude/skills/context-doc/SKILL.md`. Paths in this block are from the repository root.
