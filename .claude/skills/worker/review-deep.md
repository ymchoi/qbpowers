# Deep review guide

First do everything `review-light.md` in this folder asks, under its rules for findings and the result. Then look for defects: read the callers of what changed, and the tests.

4. Behaviour. Does the change do what the requirements ask? Where does it go wrong: empty or missing input, a
   failure path, concurrent runs, a caller that relied on the old behaviour?
5. Costly mistakes. Deleting or overwriting files or data the code does not own; a secret reaching a log, an error
   message or output; spending money without a limit; a test writing to a real resource; and mistakes of that kind.
   Report one even when it was there before the change.
6. Tests that prove it. Would the test of a bug fix fail without the fix? Do the tests assert the changed
   behaviour, or would they pass whatever the code did? Tests of a refactoring may pass before it; that is not a finding.
7. Recurrence. When the change fixes a mistake that could recur, can the same mistake still be made again, here or
   elsewhere, without failing a check? Report it where the code could be changed, at a cost that fits the risk, so
   that making it again fails a check or cannot be written.
