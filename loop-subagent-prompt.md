Use these subagents:

- product-designer
- frontend-coder
- tester
- reviewer

Run a bounded validation loop for the current Flashcard Quiz App.

Each round:

1. product-designer checks product fit, UX clarity, and scope.
2. tester checks behavior and tests.
3. reviewer checks code quality and maintainability.
4. Route fixes based on the issue type:
   - UX, requirement, or scope issue → product-designer
   - bug, failed test, or implementation issue → frontend-coder
   - test quality issue → tester
   - code quality issue → frontend-coder

After product-designer changes the intended behavior:
- frontend-coder updates the implementation if needed
- tester reruns tests
- reviewer checks again

After frontend-coder changes code:
- tester reruns tests
- reviewer checks again

Stop when:
- product fit is acceptable
- tests pass
- reviewer has no must-fix issues

Limit the loop to 3 repair rounds.

Do not add new features unless product-designer explicitly decides they belong in the MVP.
