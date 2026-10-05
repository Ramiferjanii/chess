"use client";

import { useEffect } from "react";
import confetti from "canvas-confetti";
import { Trophy, RotateCcw, Home } from "lucide-react";
import Link from "next/link";
import { GameState, PieceColor } from "../../hooks/useChessSocket";

interface GameOverModalProps {
  gameState: GameState;
  myColor: PieceColor | null;
  nextPlayer: PieceColor;
  onRematch?: () => void;
}

export function GameOverModal({ gameState, myColor, nextPlayer, onRematch }: GameOverModalProps) {
  const isCheckmate = gameState === "checkmate";
  const isStalemate = gameState === "stalemate";

  const winner: PieceColor | "Draw" = isCheckmate
    ? nextPlayer === "white"
      ? "black"
      : "white"
    : "Draw";

  const iWon = myColor !== null && winner === myColor;

  useEffect(() => {
    if (isCheckmate && iWon) {
      try {
        confetti({
          particleCount: 80,
          spread: 70,
          origin: { y: 0.6 },
        });
      } catch {
        // Confetti unsupported or blocked
      }
    }
  }, [isCheckmate, iWon]);

  if (!isCheckmate && !isStalemate) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md animate-in fade-in duration-300">
      <div className="relative w-full max-w-sm rounded-2xl border border-white/10 bg-[#0f1322] p-6 text-center shadow-[0_20px_60px_rgba(0,0,0,0.8)] preserve-3d">
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-tr from-purple-600 to-indigo-500 shadow-[0_0_25px_rgba(139,92,246,0.5)]">
          <Trophy className="h-8 w-8 text-white" />
        </div>

        <h2 className="text-2xl font-bold text-white tracking-wide">
          {isCheckmate ? (iWon ? "Victory!" : "Checkmate!") : "Stalemate!"}
        </h2>

        <p className="mt-2 text-sm text-slate-300">
          {isCheckmate
            ? `${winner.charAt(0).toUpperCase() + winner.slice(1)} wins the match`
            : "The game ended in a draw"}
        </p>

        <div className="mt-6 flex flex-col gap-2.5">
          {onRematch && (
            <button
              onClick={onRematch}
              className="flex items-center justify-center gap-2 w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-medium shadow-lg shadow-purple-600/25 transition-all duration-200"
            >
              <RotateCcw className="w-4 h-4" />
              Play Again
            </button>
          )}

          <Link
            href="/"
            className="flex items-center justify-center gap-2 w-full py-2.5 px-4 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 font-medium transition-colors"
          >
            <Home className="w-4 h-4" />
            Back to Home
          </Link>
        </div>
      </div>
    </div>
  );
}
