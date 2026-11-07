# Wordle Solver
An intelligent Wordle solver powered by information theory

## Web app

The solver runs as a static web app using only HTML, CSS, and JavaScript. No build step or dependencies are required. On startup, it loads the five-letter Wordle guess list from [tabatkins/wordle-list](https://github.com/tabatkins/wordle-list). If the external list cannot be reached, it falls back to the bundled list in `words.js`. Loading the external list requires an internet connection.

Open `index.html` in a browser. Choose a suggested word or enter your own, click each tile to cycle through gray, yellow, and green feedback, and submit the row to filter the remaining possibilities. Use **Reset** to start over.

## Python

The solver has a legacy python version for offline use.