Use these persona files:

- agents/product-designer.md
- agents/frontend-coder.md
- agents/tester.md
- agents/reviewer.md

Run a repair loop on the current Flashcard Quiz App.

Important:
- Do not rebuild the app from scratch.
- Start from the current implementation.
- Focus only on finding and fixing issues.
- Do not add new features unless Product Designer says the current MVP is unclear or incomplete.

Each round:
1. Tester checks the current behavior and test result.
2. Reviewer checks code quality and maintainability.
3. Product Designer is consulted only if the issue is about UX, scope, or unclear requirements.
4. Route the issue to the responsible persona:
   - UX, scope, or requirement issue → Product Designer
   - bug or implementation issue → Frontend Coder
   - test issue → Tester
   - code quality issue → Frontend Coder

After any code change:
- Tester checks again
- Reviewer checks again

Stop when:
- no blocking issue remains
- tests pass
- Reviewer has no must-fix issues

Limit the loop to 3 repair rounds.

At the end, summarize:
- issues found
- fixes made
- remaining risks, if any
- final test result
- reviewer verdict
