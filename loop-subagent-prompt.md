Use these subagents:

- product-designer
- frontend-coder
- tester
- reviewer

Run a validation loop for the current Flashcard Quiz App.

Each round:
- product-designer checks product fit and UX
- tester checks behavior and tests
- reviewer checks code quality

Route fixes:
- UX or scope issue → product-designer
- bug or failed test → frontend-coder
- test issue → tester
- code quality issue → frontend-coder

After any code change, rerun tests and review again.

Stop when:
- product fit is acceptable
- tests pass
- no must-fix issues remain

Limit to 3 rounds.
Keep the MVP small.
