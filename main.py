import os
import requests
import chess
import chess.engine

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict

# -------------------- CONFIG --------------------

STOCKFISH_PATH = "stockfish-windows-x86-64.exe"
OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3"

PIECE_NAMES = {
    "P": "pawn",
    "N": "knight",
    "B": "bishop",
    "R": "rook",
    "Q": "queen",
    "K": "king"
}

# -------------------- APP --------------------

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- STATE --------------------
# In-memory history (single-session demo)
move_log: List[Dict] = []

# -------------------- MODELS --------------------

class GameState(BaseModel):
    fen: str
    user_move: str

# -------------------- CHESS HELPERS --------------------

def game_phase(board: chess.Board) -> str:
    piece_count = sum(
        len(board.pieces(p, chess.WHITE)) + len(board.pieces(p, chess.BLACK))
        for p in (chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT)
    )

    if piece_count > 10:
        return "opening"
    if piece_count > 4:
        return "middlegame"
    return "endgame"


def move_quality(eval_change: int) -> str:
    if eval_change <= -300:
        return "blunder"
    if eval_change <= -100:
        return "mistake"
    if eval_change <= -30:
        return "inaccuracy"
    if eval_change >= 80:
        return "strong"
    return "neutral"

def explain_move(
    san: str,
    piece: str,
    eval_change: int,
    phase: str,
    quality: str
) -> str:
    
    prompt = (
        "You generate one-line chess commentary.\n"
        "This is not a conversation.\n"
        "No acknowledgements, no questions, no setup text.\n\n"

        f"Move: {san}\n"
        f"Piece: {piece}\n"
        f"Phase: {phase}\n"
        f"Quality: {quality}\n"
        f"Eval delta: {eval_change}\n\n"

        "Write exactly ONE short sentence describing the resulting position or momentum.\n"
        "If the move is a mistake or blunder, describe loss, weakness, or advantage for the opponent.\n"
        "If the move is a mistake or blunder, NEVER describe it as an attack, initiative, or sacrifice.\n"
        "Tone: confident, calm, professional, lightly witty.\n\n"

        "Strict rules:\n"
        "- Never address the player\n"
        "- Never ask questions\n"
        "- Never mention inputs or parameters\n"
        "- Never describe the move itself\n"
        "- Never mention squares, locations, directions, or piece actions\n"
        "- Never mention numbers, evaluations, or centipawns\n"
        "- Never use 'you', 'your', or 'you're'\n"
        "- No quotes, labels, or explanations\n"
        "- Maximum 15 words\n"
        "- Output ONE sentence only\n"
    )

    try:
        r = requests.post(
            OLLAMA_ENDPOINT,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=30
        )
        return r.json().get("response", "").strip() or "Move noted."
    except Exception:
        return "No explanation available."

# -------------------- API --------------------

@app.post("/analyze_and_move")
async def analyze_and_move(state: GameState):
    board = chess.Board(state.fen)

    move = chess.Move.from_uci(state.user_move)

    # Validate move
    if move not in board.legal_moves:
        return {"error": "Illegal move."}

    # Generate SAN BEFORE applying move
    san = board.san(move)

    piece = board.piece_at(move.from_square)
    piece_name = PIECE_NAMES.get(piece.symbol().upper(), "piece") if piece else "piece"

    # Apply user move
    board.push(move)

    # Start Stockfish
    _, engine = await chess.engine.popen_uci(STOCKFISH_PATH)

    # Analyze after user's move
    info = await engine.analyse(board, chess.engine.Limit(time=0.1))

    evaluation = 0
    score_info = info.get("score")
    if score_info and score_info.relative:
        evaluation = score_info.relative.score(mate_score=10000) or 0

    # Normalize to user's perspective
    if board.turn == chess.BLACK:
        evaluation = -evaluation

    phase = game_phase(board)
    quality = move_quality(evaluation)

    explanation = explain_move(
        san=san,
        piece=piece_name,
        eval_change=evaluation,
        phase=phase,
        quality=quality
    )

    move_log.append({
        "move": san,
        "piece": piece_name,
        "phase": phase,
        "quality": quality,
        "explanation": explanation
    })

    # Engine reply
    result = await engine.play(board, chess.engine.Limit(time=0.5))
    ai_move = ""

    if result.move:
        board.push(result.move)
        ai_move = result.move.uci()

    await engine.quit()

    return {
        "fen": board.fen(),
        "ai_move": ai_move,
        "explanation": explanation,
        "history": move_log
    }


# -------------------- ENTRY --------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
