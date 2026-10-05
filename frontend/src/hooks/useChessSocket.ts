"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useChessAudio } from "./useChessAudio";

export type PieceColor = "white" | "black";
export type SquarePiece = string | null; // e.g. "white_pawn", "black_knight", null
export type BoardState = SquarePiece[][];

export interface LastMove {
  fr: number;
  fc: number;
  tr: number;
  tc: number;
}

export type GameState =
  | "connecting"
  | "waiting"
  | "playing"
  | "check"
  | "checkmate"
  | "stalemate"
  | "finished"
  | "full"
  | "disconnected";

export function useChessSocket(roomId: string) {
  const [board, setBoard] = useState<BoardState>(() =>
    Array.from({ length: 8 }, () => Array(8).fill(null))
  );
  const [myColor, setMyColor] = useState<PieceColor | null>(null);
  const [nextPlayer, setNextPlayer] = useState<PieceColor>("white");
  const [gameState, setGameState] = useState<GameState>("connecting");
  const [selectedSquare, setSelectedSquare] = useState<{ row: number; col: number } | null>(null);
  const [validMoves, setValidMoves] = useState<[number, number][]>([]);
  const [validCaptures, setValidCaptures] = useState<[number, number][]>([]);
  const [lastMove, setLastMove] = useState<LastMove | null>(null);
  const [kingInCheck, setKingInCheck] = useState<[number, number] | null>(null);
  const [opening, setOpening] = useState<string | null>(null);
  const [moveHistoryCount, setMoveHistoryCount] = useState<number>(0);
  const [opponentDisconnected, setOpponentDisconnected] = useState<boolean>(false);

  const wsRef = useRef<WebSocket | null>(null);
  const { playMove, playCapture, playCheck, playVictory } = useChessAudio();

  // Determine WebSocket endpoint
  const getWsUrl = useCallback(() => {
    const configuredWs = process.env.NEXT_PUBLIC_WS_URL;
    if (configuredWs) {
      return `${configuredWs.replace(/\/$/, "")}/ws/${roomId}`;
    }
    if (typeof window !== "undefined") {
      const isHttps = window.location.protocol === "https:";
      const host = window.location.hostname;
      // If running on localhost or any IP address (e.g. 192.168.x.x, 10.x.x.x, 127.0.0.1), use port 8000
      const isLocalOrIp =
        host === "localhost" ||
        host === "127.0.0.1" ||
        /^(\d{1,3}\.){3}\d{1,3}$/.test(host);
      const port = isLocalOrIp ? ":8000" : "";
      return `${isHttps ? "wss" : "ws"}://${host}${port}/ws/${roomId}`;
    }
    return `ws://localhost:8000/ws/${roomId}`;
  }, [roomId]);

  useEffect(() => {
    if (!roomId) return;

    let isMounted = true;
    const url = getWsUrl();
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      if (!isMounted) return;
      setGameState("connecting");
      setOpponentDisconnected(false);
    };

    ws.onmessage = (event) => {
      if (!isMounted) return;
      try {
        const msg = JSON.parse(event.data);

        switch (msg.type) {
          case "assigned":
            setMyColor(msg.color);
            break;

          case "waiting":
            setGameState("waiting");
            break;

          case "start":
            setGameState("playing");
            setBoard(msg.board);
            setNextPlayer(msg.next_player);
            setOpponentDisconnected(false);
            break;

          case "moves":
            setSelectedSquare({ row: msg.row, col: msg.col });
            setValidMoves(msg.moves || []);
            setValidCaptures(msg.captures || []);
            break;

          case "update":
            setBoard(msg.board);
            setNextPlayer(msg.next_player);
            setGameState(msg.state);
            setKingInCheck(msg.king_pos || null);
            setLastMove(msg.last_move || null);
            setSelectedSquare(null);
            setValidMoves([]);
            setValidCaptures([]);
            setMoveHistoryCount((prev) => prev + 1);

            if (msg.opening) {
              setOpening(msg.opening);
            }

            // Audio cues
            if (msg.captured) {
              playCapture();
            } else {
              playMove();
            }

            if (msg.state === "check") {
              playCheck();
            } else if (msg.state === "checkmate") {
              playVictory();
            }
            break;

          case "invalid":
            setSelectedSquare(null);
            setValidMoves([]);
            setValidCaptures([]);
            break;

          case "full":
            setGameState("full");
            break;

          case "disconnect":
            setOpponentDisconnected(true);
            break;

          default:
            break;
        }
      } catch (err) {
        console.error("Error parsing message from websocket:", err);
      }
    };

    ws.onclose = () => {
      if (isMounted) {
        setGameState("disconnected");
      }
    };

    return () => {
      isMounted = false;
      ws.close();
    };
  }, [roomId, getWsUrl, playCapture, playCheck, playMove, playVictory]);

  // Request valid moves for selected square
  const getMoves = useCallback((row: number, col: number) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: "get_moves",
          row,
          col,
        })
      );
    }
  }, []);

  // Send a move
  const sendMove = useCallback((fromRow: number, fromCol: number, toRow: number, toCol: number) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: "move",
          from_row: fromRow,
          from_col: fromCol,
          to_row: toRow,
          to_col: toCol,
        })
      );
    }
  }, []);

  // Handle board square interaction (click or drag-drop destination)
  const handleSquareClick = useCallback(
    (row: number, col: number) => {
      if (!["playing", "check"].includes(gameState)) return;
      if (nextPlayer !== myColor) return;

      const piece = board[row]?.[col];
      const isDestinationValid =
        validMoves.some(([r, c]) => r === row && c === col) ||
        validCaptures.some(([r, c]) => r === row && c === col);

      // 1. If clicking a valid destination after selecting a piece -> Make Move
      if (selectedSquare && isDestinationValid) {
        sendMove(selectedSquare.row, selectedSquare.col, row, col);
        setSelectedSquare(null);
        setValidMoves([]);
        setValidCaptures([]);
        return;
      }

      // 2. If clicking own piece -> Request moves
      if (piece && myColor && piece.startsWith(myColor)) {
        getMoves(row, col);
        return;
      }

      // 3. Otherwise deselect
      setSelectedSquare(null);
      setValidMoves([]);
      setValidCaptures([]);
    },
    [board, gameState, myColor, nextPlayer, selectedSquare, validCaptures, validMoves, sendMove, getMoves]
  );

  return {
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
    sendMove,
  };
}
