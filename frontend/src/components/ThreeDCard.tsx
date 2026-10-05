"use client";

import React, { useRef, useState } from "react";

interface ThreeDCardProps {
  children: React.ReactNode;
  className?: string;
  glowColor?: string;
}

export function ThreeDCard({
  children,
  className = "",
  glowColor = "rgba(139, 92, 246, 0.25)",
}: ThreeDCardProps) {
  const cardRef = useRef<HTMLDivElement>(null);
  const [rotate, setRotate] = useState({ x: 0, y: 0 });
  const [sheen, setSheen] = useState({ x: 50, y: 50, opacity: 0 });

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    const rotateX = ((y - centerY) / centerY) * -10;
    const rotateY = ((x - centerX) / centerX) * 10;

    setRotate({ x: rotateX, y: rotateY });
    setSheen({
      x: (x / rect.width) * 100,
      y: (y / rect.height) * 100,
      opacity: 1,
    });
  };

  const handleMouseLeave = () => {
    setRotate({ x: 0, y: 0 });
    setSheen((prev) => ({ ...prev, opacity: 0 }));
  };

  return (
    <div
      className="perspective-1000"
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      <div
        ref={cardRef}
        className={`relative transition-transform duration-200 ease-out preserve-3d rounded-2xl border border-white/10 bg-[#0f1322]/80 backdrop-blur-xl shadow-2xl overflow-hidden ${className}`}
        style={{
          transform: `rotateX(${rotate.x}deg) rotateY(${rotate.y}deg)`,
          boxShadow: sheen.opacity
            ? `0 20px 40px -15px ${glowColor}, 0 0 25px -5px ${glowColor}`
            : undefined,
        }}
      >
        {/* Dynamic Sheen highlight */}
        <div
          className="pointer-events-none absolute -inset-px transition-opacity duration-300"
          style={{
            opacity: sheen.opacity,
            background: `radial-gradient(400px circle at ${sheen.x}% ${sheen.y}%, rgba(255, 255, 255, 0.12), transparent 70%)`,
          }}
        />
        <div className="relative z-10">{children}</div>
      </div>
    </div>
  );
}
