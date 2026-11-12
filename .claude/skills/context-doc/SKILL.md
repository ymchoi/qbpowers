---
name: context-doc
description: Keep a project's documents small and current so that an agent can go on with its work after any number of context compactions. Usage /context-doc [project path] [review].
disable-model-invocation: true
---

# Context documents

- `/context-doc <project path>`: for the rest of the session, keep that project's documents by the rules below. Then:
  - No documents yet: [set up](#set-up).
  - Documents exist but no `AGENTS.md` with a `## Document rules` section: [restructure](#restructure).
  - The rule block is present: read `AGENTS.md` and `docs/status.md` if it exists, and [run the check](#check-script).
- `/context-doc <project path> review`: run the [whole-set review](#whole-set-review).
- Without a path, use the project an earlier `/context-doc` in this session named. If there is none, or more than one, ask the user which project.

Nothing turns the skill off; it ends with the session. `rules.md` next to this file is the core of the rules below, copied without change into each project's `AGENTS.md` for sessions that never invoke the skill.

Keep the project's documents current without being asked. Where another rule about keeping documents differs from the rules here, these decide for the project's documents.

## The documents

A project is the directory given to the skill. Its documents are `AGENTS.md` at its top and the Markdown files directly in `docs/`, in three kinds divided by how often they change, each with its own writing rule. Markdown that the program reads (prompts, templates, test data) is code, not a document.

`AGENTS.md`, the entry. Changes rarely.
- Holds: what the project is, in one or two sentences; while status exists, a link line to read it first on entry and after a context compaction; the rules that always apply, each with its reason on the same line (a reason that is the user's preference says so); the document table under `## Documents`; the rule block under `## Document rules`; a `Document budget:` line outside the block when the budget is not the default.
- A rule that needs more than its line links to the topic document that holds the detail. Neither repeats the other.
- Document table: one row per topic document, columns "When you", "Read", "You find". "When you" begins with the words a task would contain.
- Does not hold: what reading the code shows (layout, file lists, dependencies), procedures and long explanations (topic documents), progress (status). There is no separate index file.

`docs/status.md`, the state. Overwrite it.
- Holds work in progress only, in the sections of the [skeleton](#set-up), each present only while it has content: Goal, Next, Running and waiting, Do not, Decided, not yet in a topic document.
- Finished work leaves the file. It keeps no list of finished work and no facts that seldom change. It may point into `.temp_files/` for material of the work in progress.
- Create it when work first spans more than one sitting. With no work in progress there is no status file.
- Work too large for it gets a temporary plan document in `docs/`, with a row in the table. Its first line is `Delete this file when <condition>.` Like status, it may point into `.temp_files/`.

`docs/<topic>.md`, the knowledge. Rewrite it in place.
- Holds everything else the code cannot tell: specifications, working methods and their pitfalls, operating facts, external references.
- One owner document per fact; others link to it.
- The set is not fixed: merge, split and create documents whenever that serves the reader, and update the document table in the same turn. Their number has no limit. `docs/` has no subdirectories. A file name says what the file holds and carries no number.

Outside the documents:
- Evidence (worker reports, raw measurements, logs, screenshots) goes under `.temp_files/` and is disposable. `AGENTS.md` and topic documents do not point there.
- `ref/` holds material that cannot be made again at a reasonable cost. A document says why each file, group or folder is there. It is tracked by version control, kept as it is (not rewritten, not compressed) and not counted in the budgets; its size does not matter.
- Scripts and inputs that will be used again go into the project's code.

## What to write

- Write only what the code cannot tell and what saves an agent trial and error, work or repeated analysis: reasons, constraints, decisions, working methods, pitfalls, operating facts, the state of the work. This is the test for high value.
- Do not write what reading the code shows. Keep no history, logs or journals of what was done.
- A rule is one directive and its reason: split a line that holds several directives. Do not delete a rule whose reason still holds. A rule whose reason is the user's preference changes only when the user says so. Do not mark who decided a rule or when.
- A date appears only as part of a value: the date a measurement or an external fact was true.
- Write a guess as a guess, with the way to check it. Build no rule on a guess. Never turn a guess into a fact while tidying.
- Write into the document the numbers and commands the reader needs in order to act (a limit to stay under, a threshold that explains a result, a command to run): a bare pointer costs a file read each time. A value the reader would meet only while reading the code stays in the code.
- No decision log, no decision numbers: a decision becomes a rule with its reason in the document that owns it. Refer to a rule by a link to its section; when the section holds several rules, name the rule in a few words.
- If a document says the code does one thing and the code does another, follow the code, and fix the document in the same change. If the code breaks a rule, keep the rule and tell the user.
- Write every document in English. Keep Korean only where English would be wrong or ambiguous, not merely less familiar. Such places are rare; when unsure, write English. This rule is for documents only: talk to the user in the user's language.

## When to write

In normal work only the main session edits the documents. When you start a worker, ask it to end its report with what the documents need, and apply that yourself. Workers that compress, split, restructure or review under this skill are the exception.

Write in the same turn when:
1. The user decides something: write it as a rule with its reason in the document that owns it (`AGENTS.md` if it always applies). If no document owns it yet, create one. While a unit of work is running, you may note it in status instead and move it when the unit ends.
2. A unit of work ends (a merge, a measurement, a verification): remove it from status, and move what must be kept (rules, pitfalls, operating facts) to topic documents.
3. The next steps, the waits or the running work change: update status.
4. A code change makes a document wrong: fix that document in the same change.

There is no check at the end of every turn.

## Size

Sizes are `tiktoken` tokens, encoding `o200k_base`. The limits are ceilings, not targets: content that does not belong goes even from a small document.
- Each document: at most 5,000. Bring a document over the limit under 4,000.
- The total (`AGENTS.md` plus `docs/*.md`): at most 100,000, or the `Document budget:` value. Bring a total over the limit under 80% of the limit.
- Do not compress in the middle of a unit of work. When a limit is passed, finish the unit, then [compress](#compress-split-or-hand-over) before the next unit starts. Do not put it off further.

## Checks

- Run the [check script](#check-script) at the end of every unit of work, even when no document changed (a code change can break a path a document names), and after setting up, restructuring, compressing or splitting.
- A worker that did not write the text reviews what the script cannot judge, only at these times: a document is compressed or split (against its earlier version); the [whole set](#whole-set-review), on restructuring, when the total limit forces compression, and on `review`. Ordinary document changes get only the script.

## Set up

1. Create `AGENTS.md` from the skeleton below: the project line, the rules already known, a document table with no rows, and the rule block.
2. Create status and topic documents only when there is something to write: a small project is one `AGENTS.md`.
3. Run the check script.

When status is created later, add its link line to `AGENTS.md`; when it is deleted, remove the line. Status has no row in the table: the link line is its entry.

`AGENTS.md` skeleton (the status line only while status exists, the budget line only when the budget is not the default, the rule block last so that nothing else falls into its section):

```
# <Project name>

<What the project is, in one or two sentences.>

On entry and after a context compaction, read [docs/status.md](docs/status.md) first.

Document budget: <N> tokens

## Rules

- <Directive>: <reason>.
- <Directive>: the user's preference.

## Documents

| When you | Read | You find |
|---|---|---|
| <words a task would contain> | [docs/<topic>.md](docs/<topic>.md) | <what it holds> |

<the contents of rules.md, from its heading `## Document rules` to its end>
```

`docs/status.md` skeleton (leave out empty sections):

```
# Status

## Goal

<What the work must achieve.> Done when <what shows it>.

## Next

1. <One action that can be run now.>
2. <The step after it, and so on in order.>

## Running and waiting

- <What runs outside the conversation>. Check: `<command>`. Resume: `<command>`.
- <What is waited for>. Ends when <who or what ends the wait>.

## Do not

- <What was tried and failed, and how it failed>. Lifted when <condition>.

## Decided, not yet in a topic document

- <Directive>: <reason>.
```

## Restructure

For a project whose documents exist but whose `AGENTS.md` has no rule block.

1. Do not ask the user first. Carry it to the end, then report.
2. Whoever writes reads every document of the project to the end, and does not choose what to keep by searching or sampling. Take in documentation that serves the same purpose from outside `AGENTS.md` and `docs/`, such as a `README.md` at the project's top or files in subfolders of `docs/`.
3. Decide from evidence where evidence decides: where a document says the code does one thing and the code does another, the document follows the code; history and logs go; duplicated content goes to one owner document; a decision log dissolves into rules with reasons in the documents that own them; what the code shows goes. The project's own rules on what the rule block covers (an index file, a decision log, when to update or check documents) go too: the block replaces them.
4. Where evidence cannot decide (a rule whose reason is unknown, a rule the code breaks, two statements that conflict and the code does not settle), keep the statement as it is and list it for the user. Write a reason only where the repository states it (code, tests, history, another document). Otherwise the rule stays without a reason until the user gives it: never invent one.
5. Translate into English under the language rule.
6. Build `AGENTS.md` as in [The documents](#the-documents), keep every document under its limit, and delete each old file once its content is at its new place. Fix links into the project from the rest of the repository, and search the repository for the names of the old files: the script finds broken links, not prose that names a file. A statement elsewhere about how this project keeps its documents (a parent's index convention) gives way to the project's `AGENTS.md`: remove it or point it there.
7. Before writing, keep the documents as they were for the reviewer: a version-control revision if they are committed unchanged, otherwise a copy under `.temp_files/`. Writing may go to a worker, whose report lists what it removed, what it changed because the code disagreed, what it added from the code, and what it left for the user. Then the main session starts a worker that did not write the result. It compares the result with the documents as they were, restores high-value content that was lost, checks the writer's changes and additions against the code, and does the whole-set review. If the documents as they were are more than one worker can read to the end with care, split them by document among several such workers.
8. Run the check script.
9. Report: each rule removed and why, where content moved, and the list for the user to decide.

Commit only when the user asks.

## Compress, split or hand over

What goes first: history, what the code shows, duplicates (keep the owner, link to it), rules whose reason no longer holds. Then wording, without losing a condition or an exception.

- `AGENTS.md` or status over 5,000: compress it under 4,000. If only high-value content remains and compression would cost some of it, hand content over to topic documents.
- A topic document over 5,000: compress it under 4,000. If that would cost high-value content, split it into two or more documents.
- The total over its limit: compress topic documents until the total is under 80% of the limit. If that cannot be done without losing high-value content, do not cut: report it, and the user decides.

Who does it:
- Before the work starts, keep the earlier version for the reviewer: a version-control revision if the document is committed unchanged, otherwise a copy under `.temp_files/`.
- A worker compresses, splits or hands over, and a different worker reviews. For status the main session compresses, because only it knows what is finished, and a worker reviews.
- The reviewer compares the result with the earlier version, restores high-value content that was lost, and repairs sentences that compression made unclear.

Move before you delete: write the content at its new place, read it there, then remove the old copy. Update the document table and the links in the same turn, and run the check script.

When the total limit forced the compression, a worker then does the whole-set review.

The report to the user lists each rule that was removed and why.

## Whole-set review

Start a worker that did not write the text. It reads every document of the project to the end and looks for:
1. the same fact in two documents;
2. documents that disagree with each other or with the code;
3. a rule without a reason, or with a reason that no longer holds;
4. content that reading the code shows, and history or logs;
5. a guess written as a fact;
6. finished work or seldom-changing facts in status;
7. Korean that English could carry, and sentences that are unclear;
8. rows of the document table whose "When you" does not match how the document is used;
9. material in `ref/` for which no document gives a reason. Report it; do not delete it: it cannot be made again, so the user decides.

If the documents are more than one worker can read to the end with care, split them by document among several workers; each reads its share to the end and checks it against the rest of the set.

The reviewer fixes what evidence decides, as in [Restructure](#restructure), lists the rest in its report, and runs the check script. Pass the list to the user.

## Check script

```
python .claude/skills/context-doc/scripts/check_docs.py <project directory>
```

Run it with a Python that has `tiktoken`, giving the script's path from the repository root. Its result does not depend on the working directory. It exits 1 when a check fails and 0 otherwise.

It checks:
1. Size: each document at most 5,000 tokens, the total at most the budget, and a `Document budget:` line in the form `Document budget: <N> tokens`.
2. Document table: every Markdown file directly in `docs/` is linked from `AGENTS.md`, every relative link in `AGENTS.md` resolves, and `docs/` has no Markdown file in a subfolder.
3. Links: every relative Markdown link in the documents resolves to a file and, with a fragment into Markdown, to a heading. Links into the project's documents from Markdown files elsewhere in the repository are checked the same way.
4. Paths: a path named in backticks or in a shell code block exists (text with a slash whose first segment exists at the repository root or in the project; placeholders, patterns and URLs are skipped; the rule block is not checked).
5. Temporary paths: `AGENTS.md` and topic documents do not refer to anything under `.temp_files/`. Status and a temporary plan document may.
6. Rule block: the `## Document rules` section of `AGENTS.md` equals `rules.md`.

It does not check external URLs, the contents of `ref/`, or prose quality. Its output is a table of token counts per document and the total against the budget, then the problems grouped by check, with file and line. Without a `.git` above the project it skips the inbound links and says so.

Fix what it reports. A size failure follows the timing in [Size](#size). When the rule block differs, copy `rules.md` over the section again: the block is never edited inside a project. Write a path that exists only at run time with a placeholder (`<work_dir>/pages/`), which the path check skips.
