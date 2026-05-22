Use these subagents:

- product-designer
- frontend-coder
- tester
- reviewer

Build a small Flashcard Quiz App.

Use a hybrid workflow:

Main path:
product-designer → frontend-coder → tester → reviewer

Repair path:
If validation fails, route the issue to the responsible subagent:
- product/UX/scope issue → product-designer
- bug or implementation issue → frontend-coder
- test issue → tester
- code quality issue → frontend-coder

After any change, run tester again and then reviewer again.

Stop when tests pass and reviewer has no must-fix issues.

Limit repair cycles to 3 rounds.

Keep the MVP small and beginner-friendly.
