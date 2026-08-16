---
name: grill-me
description: Interview the user relentlessly about what the user wants to do until reaching shared understanding, resolving each branch of the decision tree.
disable-model-invocation: true
---

Interview the user relentlessly about every relevant aspect of what they want to do until you reach a shared understanding. Work through each relevant branch of the decision tree and resolve dependencies between decisions. For each question, provide a recommended answer and briefly explain the recommendation based on the user's stated goals and known constraints. If no recommendation is defensible, say so explicitly rather than inventing one.

Ask one question at a time. Ask each question as a plain-text message in the regular chat; do not use the `AskUserQuestion` tool or any other structured question UI.

Before asking a question that may be answerable from evidence, investigate it first. Check the codebase first. If local evidence is insufficient, consult Context7 for relevant library documentation or search the web for current or external information, as appropriate and when available. Ask the user only when the answer depends on their preferences, priorities, constraints, or information that cannot be established from those sources. Do not use research to infer the user's preferences or make product decisions on the user's behalf.
