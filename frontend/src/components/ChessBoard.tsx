"use client";

import React from "react";
import Image from "next/image";
import { BoardState, PieceColor, LastMove } from "../hooks/useChessSocket";

interface ChessBoardProps {
  board: BoardState;
  myColor: PieceColor | null;
  selectedSquare: { row: number; col: number } | null;
  validMoves: [number, number][];
  validCaptures: [number, number][];
  lastMove: LastMove | null;
  kingInCheck: [number, number] | null;
  onSquareClick: (row: number, col: number) => void;
  disabled?: boolean;
}

const FILES = ["a", "b", "c", "d", "e", "f", "g", "h"];
const RANKS = ["8", "7", "6", "5", "4", "3", "2", "1"];

export function ChessBoard({
  board,
  myColor,
  selectedSquare,
  validMoves,
  validCaptures,
  lastMove,
  kingInCheck,
  onSquareClick,
  disabled = false,
}: ChessBoardProps) {
  const isFlipped = myColor === "black";

  // Rows 0..7 or 7..0 depending on perspective
  const rowIndices = isFlipped ? [7, 6, 5, 4, 3, 2, 1, 0] : [0, 1, 2, 3, 4, 5, 6, 7];
  const colIndices = isFlipped ? [7, 6, 5, 4, 3, 2, 1, 0] : [0, 1, 2, 3, 4, 5, 6, 7];

  return (
    <div className="perspective-1200 flex justify-center items-center select-none py-2">
      {/* 3D Board Frame with multi-layer shadow and bevel */}
      <div className="relative p-2.5 sm:p-4 rounded-2xl bg-gradient-to-br from-[#1e2338] via-[#121626] to-[#0c0e18] shadow-[0_25px_60px_-15px_rgba(0,0,0,0.8),0_0_30px_rgba(139,92,246,0.15)] border border-purple-500/20 preserve-3d">
        {/* Inner board border */}
        <div className="relative rounded-lg overflow-hidden border-2 border-[#2d3553] shadow-inner">
          <div className="grid grid-cols-8 grid-rows-8 w-[min(88vw,420px)] h-[min(88vw,420px)] sm:w-[480px] sm:h-[480px] md:w-[540px] md:h-[540px]">
            {rowIndices.map((r, displayRowIndex) =>
              colIndices.map((c, displayColIndex) => {
                const isLight = (r + c) % 2 === 0;
                const piece = board[r]?.[c];
                const isSelected = selectedSquare?.row === r && selectedSquare?.col === c;
                const isValidMove = validMoves.some(([vr, vc]) => vr === r && vc === c);
                const isValidCapture = validCaptures.some(([cr, cc]) => cr === r && cc === c);
                const isLastFrom = lastMove && lastMove.fr === r && lastMove.fc === c;
                const isLastTo = lastMove && lastMove.tr === r && lastMove.tc === c;
                const isKingCheck = kingInCheck && kingInCheck[0] === r && kingInCheck[1] === c;

                // Rank / file labels (bottom rank and left file)
                const showFileLabel = displayRowIndex === 7;
                const showRankLabel = displayColIndex === 0;

                return (
                  <div
                    key={`${r}-${c}`}
                    onClick={() => !disabled && onSquareClick(r, c)}
                    className={`relative flex items-center justify-center cursor-pointer transition-colors duration-150 ${
                      isLight ? "bg-[#d1d5db]" : "bg-[#4b5563]"
                    } ${
                      isSelected
                        ? "!bg-purple-600/70 shadow-[inset_0_0_12px_rgba(139,92,246,0.8)]"
                        : isLastFrom || isLastTo
                        ? "!bg-amber-400/40 shadow-[inset_0_0_10px_rgba(251,191,36,0.5)]"
                        : ""
                    } ${isKingCheck ? "animate-check !bg-rose-600/70" : ""}`}
                  >
                    {/* Rank label */}
                    {showRankLabel && (
                      <span
                        className={`absolute top-0.5 left-1 text-[10px] font-bold pointer-events-none ${
                          isLight ? "text-slate-600" : "text-slate-300"
                        }`}
                      >
                        {RANKS[r]}
                      </span>
                    )}

                    {/* File label */}
                    {showFileLabel && (
                      <span
                        className={`absolute bottom-0.5 right-1 text-[10px] font-bold pointer-events-none ${
                          isLight ? "text-slate-600" : "text-slate-300"
                        }`}
                      >
                        {FILES[c]}
                      </span>
                    )}

                    {/* Legal move indicator (Empty square dot) */}
                    {isValidMove && !piece && (
                      <div className="w-3.5 h-3.5 sm:w-4 sm:h-4 rounded-full bg-emerald-400/80 shadow-[0_0_10px_#10b981] animate-legal pointer-events-none" />
                    )}

                    {/* Capture target indicator */}
                    {isValidCapture && (
                      <div className="absolute inset-1 rounded-full border-2 sm:border-3 border-rose-500/90 shadow-[0_0_12px_rgba(244,63,94,0.7)] pointer-events-none" />
                    )}

                    {/* Chess Piece Image */}
                    {piece && (
                      <div
                        className={`relative w-[82%] h-[82%] transition-all duration-200 ${
                          isSelected
                            ? "scale-110 -translate-y-1.5 drop-shadow-[0_12px_12px_rgba(0,0,0,0.6)]"
                            : "hover:scale-105 hover:-translate-y-0.5 drop-shadow-[0_4px_6px_rgba(0,0,0,0.4)]"
                        }`}
                      >
                        <Image
                          src={`/pieces/${piece}.png`}
                          alt={piece}
                          fill
                          sizes="(max-width: 640px) 45px, 65px"
                          className="object-contain pointer-events-none"
                          priority
                        />
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
