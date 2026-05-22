Use these persona files:

- agents/product-designer.md
- agents/frontend-coder.md
- agents/tester.md
- agents/reviewer.md

Build a small Flashcard Quiz App.

Use a hybrid workflow.

Main path:
Product Designer → Frontend Coder → Tester → Reviewer

MVP requirements:
- add flashcards
- quiz one card at a time
- reveal answer
- mark correct / incorrect
- show score

Keep it small and beginner-friendly.

If validation fails, route the issue to the responsible persona:
- product, UX, or scope issue → Product Designer
- bug or implementation issue → Frontend Coder
- test issue → Tester
- code quality issue → Frontend Coder

After any fix, run Tester again and then Reviewer again.

Stop when tests pass and Reviewer has no must-fix issues.

Limit repair cycles to 3 rounds.
