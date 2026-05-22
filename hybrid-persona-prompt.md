Use these persona files:

- agents/product-designer.md
- agents/frontend-coder.md
- agents/tester.md
- agents/reviewer.md

Build a small Flashcard Quiz App using a hybrid workflow.

MVP requirements:
- add flashcards
- quiz one card at a time
- reveal answer
- mark correct / incorrect
- show score

Keep it small and beginner-friendly.

Main path:
1. Product Designer defines the MVP.
2. Frontend Coder implements the MVP.
3. Tester checks the core behavior.
4. Reviewer reviews the result.

Repair path:
If validation fails, route the issue to the responsible persona:
- product, UX, or scope issue → Product Designer
- bug or implementation issue → Frontend Coder
- test issue → Tester
- code quality issue → Frontend Coder

After any repair:
- Tester checks again
- Reviewer checks again

Stop when:
- tests pass
- Reviewer has no must-fix issues

Limit repair cycles to 3 rounds.

At the end, summarize:
- final app behavior
- final file structure
- test result
- reviewer verdict
- repair cycles performed, if any
