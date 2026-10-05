"use client";

import { BookOpen } from "lucide-react";

interface OpeningBadgeProps {
  opening: string | null;
}

export function OpeningBadge({ opening }: OpeningBadgeProps) {
  if (!opening) return null;

  return (
    <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-purple-500/10 border border-purple-500/30 text-purple-300 text-xs sm:text-sm font-medium backdrop-blur-md shadow-[0_0_15px_rgba(168,85,247,0.2)] animate-in fade-in zoom-in-95 duration-300">
      <BookOpen className="w-3.5 h-3.5 text-purple-400" />
      <span className="font-semibold tracking-wide">Opening:</span>
      <span className="text-white drop-shadow-sm">{opening}</span>
    </div>
  );
}
