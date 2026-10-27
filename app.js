"use strict";

const TILE_STATES = ["incorrect", "wrong-place", "correct"];
const TILE_LABELS = {
  incorrect: "gray, not in the word",
  "wrong-place": "yellow, in the word but in the wrong position",
  correct: "green, correct position",
};

const elements = {
  status: document.querySelector("#status"),
  history: document.querySelector("#history"),
  tiles: document.querySelector("#guess-tiles"),
  suggestions: document.querySelector("#suggestions"),
  remainingCount: document.querySelector("#remaining-count"),
  form: document.querySelector("#guess-form"),
  submit: document.querySelector("#submit-button"),
  customEntry: document.querySelector("#custom-entry"),
  customWord: document.querySelector("#custom-word"),
  toggleCustomEntry: document.querySelector("#toggle-custom-entry"),
  useWord: document.querySelector("#use-word-button"),
  reset: document.querySelector("#reset-button"),
};

const originalWords = [...new Set(WORDS)];
let remainingWords = [];
let currentGuess = "";
let tileStates = Array(5).fill("incorrect");
let history = [];
let gameDone = false;

function setStatus(message, isError = false) {
  elements.status.textContent = message;
  elements.status.classList.toggle("error", isError);
}

function makeTiles(container, word, states, interactive = false) {
  container.replaceChildren();
  for (let index = 0; index < 5; index += 1) {
    const letter = word[index] || "";
    const state = states[index] || "incorrect";
    const tile = document.createElement(interactive ? "button" : "span");
    tile.className = `tile ${state}`;
    tile.textContent = letter;
    if (interactive) {
      tile.type = "button";
      tile.setAttribute("aria-label", `Position ${index + 1}: ${letter || "blank"}, ${TILE_LABELS[state]}`);
      tile.addEventListener("click", () => {
        const nextState = (TILE_STATES.indexOf(tileStates[index]) + 1) % TILE_STATES.length;
        tileStates[index] = TILE_STATES[nextState];
        renderCurrentGuess();
      });
    } else {
      tile.setAttribute("aria-label", `Position ${index + 1}: ${letter}, ${TILE_LABELS[state]}`);
    }
    container.append(tile);
  }
}

function renderCurrentGuess() {
  makeTiles(elements.tiles, currentGuess, tileStates, true);
  elements.tiles.querySelectorAll("button").forEach((tile) => {
    tile.disabled = gameDone;
  });
  elements.toggleCustomEntry.disabled = gameDone;
  elements.submit.disabled = !/^[a-z]{5}$/i.test(currentGuess) || remainingWords.length === 0;
}

function renderHistory() {
  elements.history.replaceChildren();
  for (const entry of history) {
    const row = document.createElement("div");
    row.className = "tiles";
    row.setAttribute("aria-label", `Guess ${entry.word.toUpperCase()}`);
    makeTiles(row, entry.word, entry.states);
    elements.history.append(row);
  }
}

function getSuggestions() {
  const letterHeatmap = new Map();
  let letterTotal = 0;

  for (const word of remainingWords) {
    for (let index = 0; index < word.length; index += 1) {
      const letter = word[index];
      if (!letterHeatmap.has(letter)) {
        letterHeatmap.set(letter, Array(word.length).fill(0));
      }
      letterHeatmap.get(letter)[index] += 1;
      letterTotal += 1;
    }
  }

  if (letterTotal === 0) return [];

  for (const positions of letterHeatmap.values()) {
    for (let index = 0; index < positions.length; index += 1) {
      positions[index] /= letterTotal;
    }
  }

  const scores = remainingWords.map((word) => {
    const score = [...word].reduce((total, letter, index) => {
      return total + letterHeatmap.get(letter)[index] / [...word].filter((item) => item === letter).length;
    }, 0);
    return { word, score };
  });
  scores.sort((left, right) => right.score - left.score || left.word.localeCompare(right.word));

  const scoreTotal = scores.reduce((total, item) => total + item.score, 0);
  const percentages = scores.map(({ word, score }) => ({
    word,
    percentage: scoreTotal ? (score * 100) / scoreTotal : 0,
  }));
  if (percentages.length <= 9) return percentages;

  const others = percentages.slice(9).reduce((total, item) => total + item.percentage, 0);
  return [...percentages.slice(0, 9), { word: ".....", percentage: others, other: true }];
}

function renderSuggestions() {
  elements.suggestions.replaceChildren();
  elements.remainingCount.textContent = `${remainingWords.length} remaining`;
  if (remainingWords.length === 0) {
    const message = document.createElement("li");
    message.className = "empty-state";
    message.textContent = "No words match those colors. Check the feedback or start again.";
    elements.suggestions.append(message);
    return;
  }

  for (const suggestion of getSuggestions()) {
    const item = document.createElement("li");
    const button = document.createElement("button");
    const word = document.createElement("span");
    const score = document.createElement("span");
    button.type = "button";
    button.className = "suggestion";
    word.className = "suggestion-word";
    score.className = "suggestion-score";
    word.textContent = suggestion.other ? "OTHER…" : suggestion.word.toUpperCase();
    score.textContent = `${suggestion.percentage.toFixed(4)}%`;
    button.append(word, score);
    button.addEventListener("click", () => {
      if (suggestion.other) {
        if (elements.customEntry.hidden) elements.toggleCustomEntry.click();
        else elements.customWord.focus();
        return;
      }
      setCurrentGuess(suggestion.word);
    });
    item.append(button);
    elements.suggestions.append(item);
  }
}

function setCurrentGuess(word) {
  currentGuess = word.toLowerCase();
  tileStates = Array(5).fill("incorrect");
  elements.customWord.value = "";
  elements.customEntry.hidden = true;
  elements.toggleCustomEntry.setAttribute("aria-expanded", "false");
  renderCurrentGuess();
}

function wordFeedback(solution, guess) {
  const result = Array(5).fill("incorrect");
  const unmatched = [...solution];

  for (let index = 0; index < 5; index += 1) {
    if (guess[index] === solution[index]) {
      result[index] = "correct";
      unmatched[index] = null;
    }
  }

  for (let index = 0; index < 5; index += 1) {
    if (result[index] === "correct") continue;
    const matchIndex = unmatched.indexOf(guess[index]);
    if (matchIndex !== -1) {
      result[index] = "wrong-place";
      unmatched[matchIndex] = null;
    }
  }
  return result;
}

function submitGuess(event) {
  event.preventDefault();
  if (gameDone || !/^[a-z]{5}$/i.test(currentGuess) || remainingWords.length === 0) return;

  history.push({ word: currentGuess, states: [...tileStates] });
  remainingWords = remainingWords.filter((word) => {
    const feedback = wordFeedback(word, currentGuess);
    return feedback.every((state, index) => state === tileStates[index]);
  });
  renderHistory();
  renderSuggestions();
  if (tileStates.every((state) => state === "correct")) {
    gameDone = true;
    elements.reset.textContent = "Again";
    currentGuess = "";
    renderCurrentGuess();
    setStatus(`Solved in ${history.length} ${history.length === 1 ? "guess" : "guesses"}!`);
  } else if (remainingWords.length > 0) {
    setCurrentGuess(getSuggestions()[0].word);
    setStatus(`${remainingWords.length} possible ${remainingWords.length === 1 ? "word" : "words"} remain.`);
  } else {
    gameDone = true;
    elements.reset.textContent = "Again";
    currentGuess = "";
    renderCurrentGuess();
    setStatus("No words match that feedback. Review the tile colors.", true);
  }
}

function resetGame() {
  gameDone = false;
  elements.reset.textContent = "Reset";
  remainingWords = [...originalWords];
  history = [];
  renderHistory();
  renderSuggestions();
  const firstSuggestion = getSuggestions()[0];
  setCurrentGuess(firstSuggestion ? firstSuggestion.word : "");
  setStatus(`${remainingWords.length} words loaded. Click a suggested word or enter your own.`);
}

function useCustomWord(event) {
  event.preventDefault();
  const word = elements.customWord.value.trim().toLowerCase();
  if (!/^[a-z]{5}$/.test(word)) {
    setStatus("Enter a word containing exactly five letters.", true);
    elements.customWord.focus();
    return;
  }
  setCurrentGuess(word);
  setStatus("Click each tile to enter the feedback from your game.");
}

elements.form.addEventListener("submit", submitGuess);
elements.toggleCustomEntry.addEventListener("click", () => {
  const isExpanded = elements.toggleCustomEntry.getAttribute("aria-expanded") === "true";
  elements.toggleCustomEntry.setAttribute("aria-expanded", String(!isExpanded));
  elements.customEntry.hidden = isExpanded;
  if (!isExpanded) elements.customWord.focus();
});
elements.useWord.addEventListener("click", useCustomWord);
elements.customWord.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    useCustomWord();
  }
});
elements.reset.addEventListener("click", resetGame);
resetGame();
