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
- keep: `# Sync the directory as well: without it a crash can undo the rename on Linux.` It stops an edit that drops
  the second sync as redundant, and only a crash test could say this in code.
- delete: `"""Return the user with the given id."""` on a function named `get_user_by_id`.
- code: `# An empty list must not raise.` above a test: say it in the test's name.
- fix: `# Sleep two seconds because the cache is sometimes not ready yet.`: wait for the cache's ready signal and
  remove the sleep.
- docs: `# Retry policy: three attempts with doubling waits, never after a 4xx answer.` above one function: the
  policy belongs in the project's document.

## Findings

- Give the file and line, what goes wrong and under which input or state, and for a rule, the rule it breaks.
- Report only what you can state concretely. If you cannot say when it goes wrong, do not report it.
- Must fix: wrong behaviour or a costly mistake that an input or state that can occur here reaches. Everything
  else, including a missing test or an inaccurate document, is worth considering.
- Mark a problem that was there before the change as existing, in addition to must fix or worth considering: it is reported, not fixed as part of this change.

## Result

The findings, must-fix first; one line for each comment judged, with its place, verdict and reason; what you could
not check.
