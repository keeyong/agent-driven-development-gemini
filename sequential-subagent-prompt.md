Use these subagents:

- product-designer
- frontend-coder
- tester
- reviewer

Build a small Flashcard Quiz App.

MVP requirements:
- add flashcards
- quiz one card at a time
- reveal answer
- mark correct / incorrect
- show score

Keep it beginner-friendly and small.

Work sequentially:

1. product-designer defines the MVP.
2. frontend-coder implements it.
3. tester checks the core behavior.
4. reviewer reviews the result.

Let frontend-coder choose a simple file structure.

Validation:
- If tests fail, return to frontend-coder for a minimal fix.
- If reviewer finds must-fix issues, route the issue to the responsible subagent.
- UX or scope issues should go back to product-designer.
- Bugs or implementation issues should go back to frontend-coder.
- After any code change, tester should rerun tests.

Stop when:
- tests pass
- reviewer has no must-fix issues

Limit repair cycles to 3 rounds.

At the end, summarize:
- final app behavior
- final file structure
- test result
- reviewer verdict
- how to run it
