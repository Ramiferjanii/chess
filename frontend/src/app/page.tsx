"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { Swords, LogIn, Sparkles, BookOpen, ShieldCheck, Zap } from "lucide-react";
import { ThreeDCard } from "@/components/ThreeDCard";

export default function Home() {
  const router = useRouter();
  const [joinCode, setJoinCode] = useState("");
  const [isCreating, setIsCreating] = useState(false);

  const handleCreateRoom = async () => {
    setIsCreating(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/api/rooms`, {
        method: "POST",
      });

      if (res.ok) {
        const data = await res.json();
        router.push(`/game/${data.room_id}`);
      } else {
        // Fallback: generate local 8-char code
        const fallbackId = Math.random().toString(36).substring(2, 10);
        router.push(`/game/${fallbackId}`);
      }
    } catch {
      const fallbackId = Math.random().toString(36).substring(2, 10);
      router.push(`/game/${fallbackId}`);
    } finally {
      setIsCreating(false);
    }
  };

  const handleJoinRoom = (e: React.FormEvent) => {
    e.preventDefault();
    const clean = joinCode.trim();
    if (!clean) return;
    router.push(`/game/${clean}`);
  };

  return (
    <main className="min-h-screen flex flex-col justify-between p-4 sm:p-8 lg:p-12 relative overflow-hidden">
      {/* Header */}
      <header className="flex items-center justify-between max-w-6xl mx-auto w-full z-10 py-2">
        <div className="flex items-center gap-3">
          <div className="relative w-9 h-9 rounded-xl bg-purple-600/20 border border-purple-500/30 flex items-center justify-center shadow-[0_0_15px_rgba(139,92,246,0.3)]">
            <Image
              src="/pieces/white_knight.png"
              alt="Chess Logo"
              width={26}
              height={26}
              className="drop-shadow"
            />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-1.5">
              CHESS<span className="text-purple-400">ONLINE</span>
            </h1>
            <p className="text-[11px] text-slate-400 font-mono tracking-wider">3D REAL-TIME MULTIPLAYER</p>
          </div>
        </div>

        <div className="hidden sm:flex items-center gap-2 text-xs text-slate-400 bg-white/5 border border-white/10 px-3.5 py-1.5 rounded-full backdrop-blur-md">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_#10b981]" />
          <span>WebSocket Engine Active</span>
        </div>
      </header>

      {/* Hero Section */}
      <div className="max-w-4xl mx-auto w-full text-center mt-8 sm:mt-14 mb-10 z-10">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-300 text-xs sm:text-sm font-medium mb-6 shadow-[0_0_20px_rgba(139,92,246,0.15)]">
          <Sparkles className="w-3.5 h-3.5 text-purple-400" />
          <span>Zero Sign-up • Instant 1-Click Game Links • 100+ Openings</span>
        </div>

        <h2 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-white drop-shadow-sm leading-[1.1]">
          Master The Board. <br />
          <span className="bg-gradient-to-r from-purple-400 via-indigo-300 to-cyan-400 bg-clip-text text-transparent">
            Play Anywhere in 3D.
          </span>
        </h2>

        <p className="mt-5 text-sm sm:text-lg text-slate-400 max-w-2xl mx-auto leading-relaxed">
          Challenge friends instantly. Share a unique link, watch your board adapt with real-time perspective flipping, and analyze openings as you play.
        </p>
      </div>

      {/* 3D Action Cards */}
      <div className="max-w-5xl mx-auto w-full grid grid-cols-1 md:grid-cols-2 gap-6 z-10 mb-12">
        {/* Create Match Card */}
        <ThreeDCard glowColor="rgba(139, 92, 246, 0.4)">
          <div className="p-6 sm:p-8 flex flex-col justify-between h-full">
            <div>
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-purple-600/20 text-purple-400 border border-purple-500/30 mb-5 shadow-[0_0_20px_rgba(139,92,246,0.3)]">
                <Swords className="h-6 w-6" />
              </div>

              <h3 className="text-xl sm:text-2xl font-bold text-white tracking-wide">
                Create New Match
              </h3>
              <p className="mt-2 text-sm text-slate-400 leading-relaxed">
                Launch a fresh room, copy the invitation link, and send it to your opponent. The game begins the second they join.
              </p>
            </div>

            <button
              onClick={handleCreateRoom}
              disabled={isCreating}
              className="mt-6 flex items-center justify-center gap-2.5 w-full py-3.5 px-6 rounded-xl bg-gradient-to-r from-purple-600 via-purple-500 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-semibold shadow-lg shadow-purple-600/30 transition-all duration-200 active:scale-[0.98] disabled:opacity-60 cursor-pointer"
            >
              <Swords className="w-4 h-4" />
              <span>{isCreating ? "Creating Room..." : "Create Game Room"}</span>
            </button>
          </div>
        </ThreeDCard>

        {/* Join Match Card */}
        <ThreeDCard glowColor="rgba(6, 182, 212, 0.3)">
          <div className="p-6 sm:p-8 flex flex-col justify-between h-full">
            <div>
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-cyan-600/20 text-cyan-400 border border-cyan-500/30 mb-5 shadow-[0_0_20px_rgba(6,182,212,0.3)]">
                <LogIn className="h-6 w-6" />
              </div>

              <h3 className="text-xl sm:text-2xl font-bold text-white tracking-wide">
                Join with Code
              </h3>
              <p className="mt-2 text-sm text-slate-400 leading-relaxed">
                Got a room code or link from a friend? Enter the code below to connect to the match instantly.
              </p>
            </div>

            <form onSubmit={handleJoinRoom} className="mt-6 flex flex-col sm:flex-row gap-2.5">
              <input
                type="text"
                value={joinCode}
                onChange={(e) => setJoinCode(e.target.value)}
                placeholder="e.g. 8d3a1f9c"
                className="flex-1 bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 font-mono transition-colors"
              />

              <button
                type="submit"
                disabled={!joinCode.trim()}
                className="flex items-center justify-center gap-2 py-3 px-6 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-semibold shadow-lg shadow-cyan-600/25 transition-all duration-200 active:scale-[0.98] disabled:opacity-50 cursor-pointer"
              >
                <LogIn className="w-4 h-4" />
                <span>Join</span>
              </button>
            </form>
          </div>
        </ThreeDCard>
      </div>

      {/* Feature Highlights Grid */}
      <div className="max-w-5xl mx-auto w-full grid grid-cols-1 sm:grid-cols-3 gap-4 z-10 mb-8">
        <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.06] backdrop-blur-sm flex items-start gap-3">
          <Zap className="w-5 h-5 text-purple-400 shrink-0 mt-0.5" />
          <div>
            <h4 className="font-semibold text-sm text-slate-200">Sub-millisecond Sync</h4>
            <p className="text-xs text-slate-400 mt-1">High-throughput WebSockets for zero move lag.</p>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.06] backdrop-blur-sm flex items-start gap-3">
          <BookOpen className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />
          <div>
            <h4 className="font-semibold text-sm text-slate-200">Live Opening Engine</h4>
            <p className="text-xs text-slate-400 mt-1">Identifies Ruy Lopez, Sicilian, French, and 100+ openings.</p>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.06] backdrop-blur-sm flex items-start gap-3">
          <ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
          <div>
            <h4 className="font-semibold text-sm text-slate-200">Server-Side Validation</h4>
            <p className="text-xs text-slate-400 mt-1">Pure Python rule engine enforces legal moves and castling.</p>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="text-center text-xs text-slate-500 z-10 py-4 border-t border-white/[0.04] max-w-5xl mx-auto w-full">
        <p>Built with Next.js 15, Tailwind CSS & FastAPI WebSocket Engine.</p>
      </footer>
    </main>
  );
}
