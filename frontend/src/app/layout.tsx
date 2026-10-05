import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Chess Online | Modern 3D Multiplayer",
  description: "Play real-time chess with anyone worldwide. 3D board, dynamic opening recognition, instantaneous link-sharing, no signup required.",
  keywords: ["chess", "chess online", "3d chess", "multiplayer chess", "fastapi chess"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark h-full">
      <body className={`${inter.className} min-h-screen bg-[#07090e] text-slate-100 selection:bg-purple-500/30 selection:text-purple-200 antialiased relative overflow-x-hidden`}>
        {/* Ambient atmospheric gradients */}
        <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
          <div className="absolute -top-[30%] left-1/2 -translate-x-1/2 w-[900px] h-[600px] bg-purple-600/10 rounded-full blur-[140px]" />
          <div className="absolute top-1/2 -left-[10%] w-[500px] h-[500px] bg-blue-600/5 rounded-full blur-[120px]" />
          <div className="absolute -bottom-[20%] right-[-5%] w-[600px] h-[600px] bg-emerald-600/5 rounded-full blur-[140px]" />
        </div>

        <div className="relative z-10 flex flex-col min-h-screen">
          {children}
        </div>
      </body>
    </html>
  );
}
