Use these subagents:

- product-designer
- frontend-coder
- tester
- reviewer

Build a small Flashcard Quiz App using a hybrid workflow.

MVP requirements:
- add flashcards
- quiz one card at a time
- reveal answer
- mark correct / incorrect
- show score

Keep it beginner-friendly and small.

Main path:
1. product-designer defines the MVP.
2. frontend-coder implements the MVP.
3. tester checks the core behavior.
4. reviewer reviews the result.

Let frontend-coder choose a simple beginner-friendly file structure.

Repair path:
If a problem is found, route it to the responsible subagent:

- UX, requirement, or scope issue → product-designer
- bug, failed test, or implementation issue → frontend-coder
- test quality or missing test issue → tester
- code quality or maintainability issue → frontend-coder

After any design clarification:
- frontend-coder updates the implementation if needed
- tester checks again
- reviewer checks again

After any code change:
- tester checks again
- reviewer checks again

Stop when:
- the MVP is clear and stable
- tests pass
- reviewer has no must-fix issues

Limit repair cycles to 3 rounds.

Do not add new features unless product-designer explicitly decides they belong in the MVP.

At the end, summarize:
- final app behavior
- final file structure
- test result
- reviewer verdict
- repair cycles performed, if any
- how to run the app
