# Light review guide

You review a change that someone else wrote. You read; you edit no file and run nothing that changes anything.
You are given the requirements and the diff. Take nothing from the author on trust: check it in the code.
Report what the linter, the type checker and the tests already in the repository would not catch, and nothing
that they do catch.

## Light review

Read the diff and the code around it.

1. Comments. First list every comment, docstring and JSDoc block the change adds or changes; judge a changed block
   as a whole. Then judge each one against the Comments section of the root AGENTS.md:
   - keep: you can name the wrong edit it prevents at that line, and code could say it only at greater cost.
   - delete: it restates the code or an existing test, records history or task IDs, or labels a section.
   - code: a name, a type, an assertion or a small test can say it at no greater cost. Say which.
   - fix: it explains a workaround or a known problem whose cause this repository can change, even if it also states
     policy. The cause should be fixed, or reported as open. Coping with a cause it cannot change is not a
     workaround.
   - docs: it explains design or policy rather than these lines. Say whether the project's documents already hold it
     and, if they do, in which document and section.
   A string that a program or a tool actually reads, such as CLI help taken from a docstring or a linter directive,
   is not a comment.
   Report as well a comment nearby that the change has made untrue.
2. Tests. A bug fix comes with a test that reproduces the bug; new behaviour comes with a test. Check only that they
   exist.
3. Documents. A document that the change makes wrong is corrected in the same change.

Examples of comment verdicts:
- keep: `// getRandomValues works on ordinary LAN HTTP, unlike secure-context-only randomUUID.` It stops an edit
  back to randomUUID, and no name or test says this more cheaply.
- delete: `"""Return the single registration whose detector matches the input."""` on a function named `detect`.
- code: `# Ledger names write bottler names without spaces; shop listings spell them out.` above a test: say it in
  the test's name.
- fix: `# tmp_path is kept as a compatibility name for tests that wrap the old helpers.`: change the tests and remove
  the old name.
- docs: three lines on the admission policy above one function: the policy belongs in the project's document.

## Findings

- Give the file and line, what goes wrong and under which input or state, and for a rule, the rule it breaks.
- Report only what you can state concretely. If you cannot say when it goes wrong, do not report it.
- Must fix: wrong behaviour or a costly mistake that an input or state that can occur here reaches. Everything
  else, including a missing test or an inaccurate document, is worth considering.
- Mark a problem that was there before the change as existing: it is reported, not fixed as part of this change.

## Result

The findings, must-fix first; one line for each comment judged, with its place, verdict and reason; what you could
not check.
