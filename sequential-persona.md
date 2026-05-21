Use the following persona files:

- agents/product-designer.md
- agents/frontend-coder.md
- agents/tester.md
- agents/reviewer.md

Project:
Build a small Flashcard Quiz App.

Requirements:
- user can add a flashcard with question and answer
- user can view one question at a time
- user can reveal the answer
- user can mark correct or incorrect
- app shows score
- user can move to the next card
- data is kept in memory only
- no backend
- no database
- no localStorage
- no external UI framework
- keep it beginner-friendly

Files to use:
- index.html
- src/main.js
- src/flashcards.js
- src/style.css
- tests/flashcards.test.js

Work sequentially with validation gates:

Step 1: Product Designer
Use agents/product-designer.md.
Define the user flow, UI layout, acceptance criteria, and out-of-scope items.
Do not write code.

Step 2: Frontend Coder
Use agents/frontend-coder.md.
Implement the MVP based on the Product Designer's plan.
Use:
- index.html for page structure
- src/main.js for DOM interaction
- src/flashcards.js for pure quiz logic
- src/style.css for styling
Do not write tests yet.

Step 3: Tester
Use agents/tester.md.
Write Vitest tests for the pure logic in src/flashcards.js.
Put tests in tests/flashcards.test.js.
Run:

npm test

Do not modify production code.

If tests fail:
- summarize the smallest failing issue
- return to the Frontend Coder
- Frontend Coder should fix only that issue
- Tester should rerun npm test
- repeat this repair cycle up to 3 times

Step 4: Reviewer
Use agents/reviewer.md.
Review the implementation against:
- Product Designer's acceptance criteria
- code simplicity
- separation between DOM code and pure logic
- test coverage
- beginner-friendliness
- obvious UX issues

Do not edit files.

If Reviewer finds any must-fix issue:
- return to the Frontend Coder
- Frontend Coder should fix only the must-fix issue
- Tester should rerun npm test
- Reviewer should review again
- repeat this review repair cycle up to 2 times

Stop when:
- npm test passes
- Reviewer has no must-fix issues

At the end, summarize:
1. Product design summary
2. Files created or changed
3. Main functions implemented
4. Test result
5. Reviewer verdict
6. How to run the app
