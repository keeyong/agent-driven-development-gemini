Use these persona files:

- agents/product-designer.md
- agents/frontend-coder.md
- agents/tester.md
- agents/reviewer.md

Run a bounded validation loop for the Flashcard Quiz App.

Start from the current implementation.

Loop:

1. Product Designer checks whether the current app still matches the intended MVP and user flow.

2. Tester checks the app behavior and test result.

3. Reviewer checks code quality, simplicity, and maintainability.

4. Route the next step based on the issue type:

- If the issue is about unclear requirements, UX flow, or scope:
  return to Product Designer.

- If the issue is about a bug, failed test, or implementation detail:
  return to Frontend Coder.

- If the issue is about code quality or maintainability:
  return to Frontend Coder.

5. After Product Designer updates the design, Frontend Coder makes the smallest required change.

6. After Frontend Coder changes the code, Tester reruns tests.

7. Reviewer reviews again.

Stop when:
- the app matches the intended MVP
- tests pass
- Reviewer has no must-fix issues

Limit the loop to 3 repair rounds.

Do not add new features unless Product Designer explicitly decides they are part of the MVP.
