---
name: freeze
description: Forbid file changes outside .temp_files/ until /freeze end. Usage /freeze [end].
disable-model-invocation: true
---

Until the session ends, the latest `/freeze` decides whether files may change.

- `/freeze`: the freeze is on. Do not create, modify or delete any file outside `.temp_files/`, yourself or through a worker. Reading, analysis, research and changes under `.temp_files/` stay allowed. If a change outside `.temp_files/` is needed, say what you would change, and make it only after `/freeze end`.
- `/freeze end`: the freeze is off. File changes follow the project's normal rules again.

A worker cannot see this conversation: while the freeze is on, state the limit in the prompt of every worker you start.
