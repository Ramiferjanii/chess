"use client";

import { useCallback, useRef } from "react";

export function useChessAudio() {
  const moveAudioRef = useRef<HTMLAudioElement | null>(null);
  const captureAudioRef = useRef<HTMLAudioElement | null>(null);

  // Play audio safely (handling browser autoplay policies)
  const playSafe = useCallback((audio: HTMLAudioElement | null) => {
    if (!audio) return;
    audio.currentTime = 0;
    audio.play().catch(() => {
      // Browser blocked autoplay or user hasn't interacted yet
    });
  }, []);

  const playMove = useCallback(() => {
    if (typeof window === "undefined") return;
    if (!moveAudioRef.current) {
      moveAudioRef.current = new Audio("/sounds/move.wav");
    }
    playSafe(moveAudioRef.current);
  }, [playSafe]);

  const playCapture = useCallback(() => {
    if (typeof window === "undefined") return;
    if (!captureAudioRef.current) {
      captureAudioRef.current = new Audio("/sounds/capture.wav");
    }
    playSafe(captureAudioRef.current);
  }, [playSafe]);

  // Synthetic tone for Check alert using Web Audio API
  const playCheck = useCallback(() => {
    if (typeof window === "undefined") return;
    try {
      const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      const ctx = new AudioCtx();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = "sine";
      osc.frequency.setValueAtTime(440, ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.18);

      gain.gain.setValueAtTime(0.15, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.25);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start();
      osc.stop(ctx.currentTime + 0.25);
    } catch {
      // AudioContext unavailable
    }
  }, []);

  // Synthetic victory chime
  const playVictory = useCallback(() => {
    if (typeof window === "undefined") return;
    try {
      const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      const ctx = new AudioCtx();
      const notes = [523.25, 659.25, 783.99, 1046.5]; // C5, E5, G5, C6
      notes.forEach((freq, idx) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = "triangle";
        osc.frequency.value = freq;
        const start = ctx.currentTime + idx * 0.1;
        gain.gain.setValueAtTime(0.12, start);
        gain.gain.exponentialRampToValueAtTime(0.001, start + 0.4);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(start);
        osc.stop(start + 0.45);
      });
    } catch {
      // AudioContext unavailable
    }
  }, []);

  return { playMove, playCapture, playCheck, playVictory };
}
