# Adaptive Chess Engine with Context-Aware Natural Language Feedback

This project is a local chess analysis tool that combines a traditional chess engine
with adaptive, context-aware natural language commentary.

Rather than presenting raw numerical evaluations, the system explains what a move
leads to in plain language, adjusting tone and severity based on the position and
move quality.

---

## Features

* Stockfish-powered chess evaluation
* Move-by-move natural language feedback
* Commentary adapts to move quality (neutral, inaccuracy, mistake, blunder)
* Backend-authoritative game state to prevent desynchronization
* No cloud APIs or API keys required
* Clean, minimal frontend using Chessboard.js

---

## Architecture Overview

* The frontend sends the current board position and attempted move to the backend
* The backend:

  * Validates the move
  * Evaluates the position using Stockfish
  * Classifies move quality
  * Generates a concise, context-aware explanation
  * Plays the engine reply
* The frontend updates the board using the server’s response

The backend is the single source of truth for the game state.

---

## Requirements

### System Requirements

* Python 3.10+
* Stockfish (local executable)
* Ollama (optional, for natural language commentary)

### Python Dependencies

Install all required Python packages using:

```
pip install -r requirements.txt
```

---

## Stockfish Setup

Download Stockfish and place the executable in the project directory.

If necessary, update the path in `main.py`:

```
STOCKFISH_PATH = "stockfish-windows-x86-64.exe"
```

---

## Ollama Setup (Optional)

Natural language commentary is generated locally using Ollama.

1. Install Ollama from: [https://ollama.com](https://ollama.com)
2. Pull the model:

```
ollama pull llama3
```

3. Ollama runs in the background automatically once installed

If Ollama is not available, the application will still run, but commentary may fall
back to a simple placeholder message.

---

## Running the Project

1. Start the backend server:

```
python main.py
```

2. Open `index.html` in a web browser
3. Make a move on the board to receive analysis and feedback

---

## Notes

* This project is designed as a local demo and analysis tool
* Game state is stored in memory (single-session)
* No persistence, authentication, or multiplayer support is implemented
* The focus is on correctness, clarity, and explainability rather than scale

---

## Motivation

Most chess engines focus on numerical evaluation.
This project explores how engine insights can be translated into
human-readable, context-aware commentary without relying on cloud services.

---

## License

Provided for educational and demonstration purposes.

