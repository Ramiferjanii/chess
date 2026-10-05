"use client";

import Image from "next/image";
import { User, ShieldAlert } from "lucide-react";
import { PieceColor } from "../hooks/useChessSocket";

interface PlayerCardProps {
  color: PieceColor;
  isCurrentTurn: boolean;
  isMe: boolean;
  isConnected: boolean;
  isInCheck: boolean;
  capturedPieces?: string[]; // array of piece names captured by this player
}

export function PlayerCard({
  color,
  isCurrentTurn,
  isMe,
  isConnected,
  isInCheck,
  capturedPieces = [],
}: PlayerCardProps) {
  const isWhite = color === "white";

  return (
    <div
      className={`relative px-4 py-3 rounded-xl transition-all duration-300 border ${
        isCurrentTurn
          ? "bg-purple-950/30 border-purple-500/40 shadow-[0_0_20px_rgba(139,92,246,0.15)] ring-1 ring-purple-500/30"
          : "bg-[#0f1322]/60 border-white/[0.06]"
      } backdrop-blur-md`}
    >
      <div className="flex items-center justify-between gap-3">
        {/* Left: Avatar & Name */}
        <div className="flex items-center gap-3">
          <div
            className={`w-10 h-10 rounded-lg flex items-center justify-center border shadow-inner ${
              isWhite
                ? "bg-gradient-to-br from-slate-200 to-slate-400 border-white text-slate-900"
                : "bg-gradient-to-br from-slate-800 to-slate-950 border-slate-700 text-slate-100"
            }`}
          >
            <User className="w-5 h-5" />
          </div>

          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-sm text-white">
                {isWhite ? "White Player" : "Black Player"}
              </span>
              {isMe && (
                <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30">
                  YOU
                </span>
              )}
            </div>

            {/* Connection status */}
            <div className="flex items-center gap-1.5 mt-0.5 text-xs text-slate-400">
              <span
                className={`w-2 h-2 rounded-full ${
                  isConnected
                    ? "bg-emerald-400 shadow-[0_0_6px_#10b981]"
                    : "bg-amber-400 animate-pulse shadow-[0_0_6px_#f59e0b]"
                }`}
              />
              <span>{isConnected ? "Connected" : "Waiting for player..."}</span>
            </div>
          </div>
        </div>

        {/* Right: Turn / Check Badge */}
        <div>
          {isInCheck ? (
            <span className="flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/40 animate-pulse">
              <ShieldAlert className="w-3.5 h-3.5" />
              CHECK
            </span>
          ) : isCurrentTurn ? (
            <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
              Turn
            </span>
          ) : null}
        </div>
      </div>

      {/* Captured pieces bar */}
      {capturedPieces.length > 0 && (
        <div className="mt-2 pt-2 border-t border-white/[0.05] flex flex-wrap gap-1 items-center">
          {capturedPieces.map((p, idx) => (
            <div key={idx} className="relative w-5 h-5 opacity-80 hover:opacity-100 transition-opacity">
              <Image
                src={`/pieces/${p}.png`}
                alt={p}
                fill
                sizes="20px"
                className="object-contain"
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
