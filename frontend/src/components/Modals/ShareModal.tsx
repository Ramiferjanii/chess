"use client";

import { useState } from "react";
import { Copy, Check, Users, Share2 } from "lucide-react";

interface ShareModalProps {
  roomId: string;
}

export function ShareModal({ roomId }: ShareModalProps) {
  const [copied, setCopied] = useState(false);

  const getShareUrl = () => {
    if (typeof window !== "undefined") {
      return `${window.location.origin}/game/${roomId}`;
    }
    return `/game/${roomId}`;
  };

  const handleCopy = () => {
    const url = getShareUrl();
    navigator.clipboard.writeText(url).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2200);
    });
  };

  return (
    <div className="rounded-2xl border border-purple-500/20 bg-[#0f1322]/80 p-5 backdrop-blur-xl shadow-xl">
      <div className="flex items-center gap-3 mb-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
          <Share2 className="h-4 w-4" />
        </div>
        <div>
          <h3 className="font-semibold text-sm text-white">Invite Opponent</h3>
          <p className="text-xs text-slate-400">Share this link to start playing</p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <div className="relative flex-1 overflow-hidden rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-xs font-mono text-slate-300">
          <span className="truncate block">{typeof window !== "undefined" ? getShareUrl() : roomId}</span>
        </div>

        <button
          onClick={handleCopy}
          className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-medium transition-all duration-200 border ${
            copied
              ? "bg-emerald-500/20 border-emerald-500/40 text-emerald-300"
              : "bg-purple-600 hover:bg-purple-500 border-purple-500 text-white shadow-md shadow-purple-600/20"
          }`}
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5" />
              <span>Copied!</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>

      <div className="mt-3 flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-white/[0.06]">
        <span className="flex items-center gap-1">
          <Users className="w-3 h-3 text-purple-400" />
          Room Code: <strong className="text-slate-200 tracking-wider font-mono">{roomId}</strong>
        </span>
        <span className="flex items-center gap-1 text-amber-400">
          <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-ping" />
          Waiting for 2nd player...
        </span>
      </div>
    </div>
  );
}
