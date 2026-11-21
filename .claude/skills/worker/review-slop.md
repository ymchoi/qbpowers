# Slop review guide

You review a change that someone else wrote, for code that should not be there. You read; you edit no file and run
nothing that changes anything. You are given the requirements and the diff.

Judge the change against the Code Changes section of the root AGENTS.md. Go through the change unit by unit,
leaving none out.

1. List every function, method, class and test, and every other block of code, that the change adds or changes,
   and everything it removes or replaces.
2. For each unit it adds or changes, ask of each case it handles and each option it offers: who or what produces
   that case in this repository, and did the requirements ask for it? It should not be there when the change did
   not need it: handling for a case that cannot happen or is very unlikely here, a just-in-case option,
   abstraction, fallback, exception handler or validation, a test whose only job is to pin such code, behaviour
   that differs under test, a workaround where the cause could be fixed here, a pattern copied from existing code
   that one would not write that way now, and code of that kind.
3. For each thing it removes or replaces, look for what was there only for it and remains: the old code itself,
   and the parameters, options, helpers, tests and names that nothing else uses now.

Checking input that comes from outside the program where it enters (a user, an external API or model reply, a file
or queue message), handling an external failure that really occurs, and what the requirements ask for are
required: they are not findings.

Style, naming, comments and defects of any other kind are not findings here.

## Findings

- For what should not be there, give the file and lines, its kind, the case the code handles, who or what produces
  that case in this repository and how often, why that is very unlikely, impossible or beyond the requirements, and
  what deleting or replacing it takes: the code, and the tests that pin it. When you cannot say who or what
  produces the case, say so: that is part of the finding.

## Result

One line for each unit you listed, with its place and what should not be there, or `nothing`. Then what you could
not decide.
