"use client";

import { use } from "react";
import Link from "next/link";
import { ArrowLeft, Wifi, AlertTriangle } from "lucide-react";
import { useChessSocket } from "@/hooks/useChessSocket";
import { ChessBoard } from "@/components/ChessBoard";
import { PlayerCard } from "@/components/PlayerCard";
import { OpeningBadge } from "@/components/OpeningBadge";
import { ShareModal } from "@/components/Modals/ShareModal";
import { GameOverModal } from "@/components/Modals/GameOverModal";

export default function GamePage({
  params,
}: {
  params: Promise<{ roomId: string }>;
}) {
  const resolvedParams = use(params);
  const roomId = resolvedParams.roomId;

  const {
    board,
    myColor,
    nextPlayer,
    gameState,
    selectedSquare,
    validMoves,
    validCaptures,
    lastMove,
    kingInCheck,
    opening,
    moveHistoryCount,
    opponentDisconnected,
    handleSquareClick,
  } = useChessSocket(roomId);

  const opponentColor = myColor === "white" ? "black" : "white";
  const isMyTurn = myColor !== null && nextPlayer === myColor;

  return (
    <div className="min-h-screen flex flex-col justify-between p-3 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full relative">
      {/* Top Navbar */}
      <header className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-white/[0.08] z-20">
        <div className="flex items-center gap-3">
          <Link
            href="/"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-xs sm:text-sm text-slate-300 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="hidden sm:inline">Lobby</span>
          </Link>

          <div className="flex items-center gap-2">
            <span className="text-xs uppercase font-mono tracking-wider px-2 py-1 rounded-md bg-purple-500/20 text-purple-300 border border-purple-500/30">
              Room #{roomId}
            </span>
            <OpeningBadge opening={opening} />
          </div>
        </div>

        {/* Global Connection / Status Pill */}
        <div className="flex items-center gap-2">
          {opponentDisconnected && (
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-rose-500/15 border border-rose-500/30 text-rose-300 text-xs animate-pulse">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>Opponent Disconnected</span>
            </div>
          )}

          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-xs text-slate-300">
            <Wifi className="w-3.5 h-3.5 text-emerald-400" />
            <span className="font-medium capitalize">{gameState}</span>
          </div>
        </div>
      </header>

      {/* Main Arena Layout */}
      <main className="flex-1 flex flex-col lg:flex-row items-center justify-center gap-6 lg:gap-10 py-6 z-10">
        {/* Left / Center: Board Column */}
        <div className="flex flex-col items-center w-full max-w-[560px]">
          {/* Top Player (Opponent) */}
          <div className="w-full mb-3">
            <PlayerCard
              color={opponentColor}
              isCurrentTurn={nextPlayer === opponentColor}
              isMe={false}
              isConnected={gameState === "playing" || gameState === "check"}
              isInCheck={kingInCheck !== null && nextPlayer === opponentColor}
            />
          </div>

          {/* 3D Chessboard */}
          <ChessBoard
            board={board}
            myColor={myColor}
            selectedSquare={selectedSquare}
            validMoves={validMoves}
            validCaptures={validCaptures}
            lastMove={lastMove}
            kingInCheck={kingInCheck}
            onSquareClick={handleSquareClick}
            disabled={gameState !== "playing" && gameState !== "check"}
          />

          {/* Bottom Player (You) */}
          <div className="w-full mt-3">
            <PlayerCard
              color={myColor || "white"}
              isCurrentTurn={isMyTurn}
              isMe={true}
              isConnected={true}
              isInCheck={kingInCheck !== null && nextPlayer === myColor}
            />
          </div>
        </div>

        {/* Right Column: Game HUD & Sidebar */}
        <aside className="w-full max-w-[420px] flex flex-col gap-4">
          {/* Share Modal (Shown especially while waiting for 2nd player) */}
          {gameState === "waiting" && <ShareModal roomId={roomId} />}

          {/* Match HUD Card */}
          <div className="rounded-2xl border border-white/10 bg-[#0f1322]/80 p-5 backdrop-blur-xl shadow-xl">
            <h3 className="font-semibold text-sm text-white mb-3">Match Details</h3>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 rounded-xl bg-black/40 border border-white/5">
                <span className="text-slate-400 block mb-1">Your Color</span>
                <span className="font-bold text-sm text-white capitalize">
                  {myColor ? `${myColor} ♟` : "Assigning..."}
                </span>
              </div>

              <div className="p-3 rounded-xl bg-black/40 border border-white/5">
                <span className="text-slate-400 block mb-1">Move Count</span>
                <span className="font-bold text-sm text-white font-mono">
                  {moveHistoryCount}
                </span>
              </div>
            </div>

            {/* Turn Banner */}
            <div className="mt-4 pt-3 border-t border-white/[0.08]">
              {gameState === "waiting" ? (
                <div className="text-center p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs">
                  Waiting for an opponent to join via link...
                </div>
              ) : isMyTurn ? (
                <div className="text-center p-3 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-xs font-semibold shadow-[0_0_15px_rgba(16,185,129,0.15)] animate-pulse">
                  ✅ Your Turn – Click a piece to view moves
                </div>
              ) : (
                <div className="text-center p-3 rounded-xl bg-white/5 border border-white/10 text-slate-400 text-xs">
                  ⏳ Opponent is thinking...
                </div>
              )}
            </div>
          </div>
        </aside>
      </main>

      {/* Game Over Modal */}
      <GameOverModal
        gameState={gameState}
        myColor={myColor}
        nextPlayer={nextPlayer}
      />
    </div>
  );
}
