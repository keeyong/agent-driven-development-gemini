Use these persona files:

@agents/product-designer.md
@agents/frontend-coder.md
@agents/tester.md
@agents/reviewer.md

We are building a small Flashcard Quiz App.

Work sequentially:

1. First act as Product Designer.
   Define the user flow, UI layout, and acceptance criteria.

2. Then act as Frontend Coder.
   Implement the app using:
   - index.html
   - src/main.js
   - src/flashcards.js
   - src/style.css

3. Then act as Tester.
   Write tests in tests/flashcards.test.js.
   Use Vitest.
   Focus on pure logic in src/flashcards.js.

4. Then act as Reviewer.
   Review the final code and test result.

Requirements:
- user can add a flashcard with question and answer
- user can view one question at a time
- user can reveal the answer
- user can mark correct or incorrect
- app shows score
- user can move to the next card
- keep data in memory only for this tutorial
- no backend
- no external UI framework
- keep the app beginner-friendly

After implementation, run:

npm test
