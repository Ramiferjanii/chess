import copy
from const import *
from square import Square
from piece import *
from move import *


class Board:
    def __init__(self):
        self.squares = [[None for _ in range(cols)] for _ in range(rows)]
        self._create()
        self.last_move = None
        self._add_pieces('white')
        self._add_pieces('black')

    # ─────────────────────────────────────────────────────────────────────────
    # Basic move execution
    # ─────────────────────────────────────────────────────────────────────────

    def move(self, piece, move, testing=False):
        initial = move.initial
        final   = move.final

        self.squares[initial.row][initial.col].piece = None
        self.squares[final.row][final.col].piece = piece

        # Pawn promotion (auto-queen unless in testing mode)
        if isinstance(piece, Pawn):
            self.check_promotion(piece, final)

        # Castling – move the rook
        if isinstance(piece, King):
            if self.castling(initial, final):
                diff = final.col - initial.col
                rook = piece.left_rook if (diff < 0) else piece.right_rook
                self.move(rook, rook.moves[-1])

        piece.moved = True
        piece.clear_moves()

        if not testing:
            self.last_move = move

    def valid_move(self, piece, move):
        return move in piece.moves

    def check_promotion(self, piece, final):
        if final.row == 0 or final.row == 7:
            self.squares[final.row][final.col].piece = Queen(piece.color)

    def castling(self, initial, final):
        return abs(initial.col - final.col) == 2

    # ─────────────────────────────────────────────────────────────────────────
    # Check / Checkmate / Stalemate detection
    # ─────────────────────────────────────────────────────────────────────────

    def in_check(self, color):
        """
        Returns True if the king of *color* is currently under attack.
        """
        king_row, king_col = self._find_king(color)
        return self._is_attacked(king_row, king_col, color)

    def _find_king(self, color):
        for row in range(rows):
            for col in range(cols):
                sq = self.squares[row][col]
                if sq.has_piece() and isinstance(sq.piece, King) and sq.piece.color == color:
                    return row, col
        raise ValueError(f"King of {color} not found on board!")

    def _is_attacked(self, row, col, color):
        """
        Returns True if square (row, col) is attacked by any opponent piece.
        Uses a temporary opponent-color dummy to reuse calc_moves logic.
        """
        opponent = 'black' if color == 'white' else 'white'
        for r in range(rows):
            for c in range(cols):
                sq = self.squares[r][c]
                if sq.has_piece() and sq.piece.color == opponent:
                    # Compute raw moves WITHOUT check-filtering to avoid recursion
                    self._calc_moves_raw(sq.piece, r, c)
                    for m in sq.piece.moves:
                        if m.final.row == row and m.final.col == col:
                            sq.piece.clear_moves()
                            return True
                    sq.piece.clear_moves()
        return False

    def filter_moves_leaving_check(self, piece, row, col):
        """
        Remove any moves from piece.moves that would leave the piece's own
        king in check.  Must be called after calc_moves.
        """
        safe_moves = []
        for move in piece.moves:
            # Deep-copy the board, execute the move on the copy, test for check
            temp = copy.deepcopy(self)
            temp_piece = temp.squares[row][col].piece
            temp.move(temp_piece, move, testing=True)
            if not temp.in_check(piece.color):
                safe_moves.append(move)
        piece.moves = safe_moves

    def has_any_legal_moves(self, color):
        """Return True if *color* has at least one legal move available."""
        for row in range(rows):
            for col in range(cols):
                sq = self.squares[row][col]
                if sq.has_piece() and sq.piece.color == color:
                    self.calc_moves(sq.piece, row, col, filter_checks=True)
                    if sq.piece.moves:
                        sq.piece.clear_moves()
                        return True
                    sq.piece.clear_moves()
        return False

    def is_checkmate(self, color):
        return self.in_check(color) and not self.has_any_legal_moves(color)

    def is_stalemate(self, color):
        return not self.in_check(color) and not self.has_any_legal_moves(color)

    # ─────────────────────────────────────────────────────────────────────────
    # Move calculation  (public + raw internal)
    # ─────────────────────────────────────────────────────────────────────────

    def calc_moves(self, piece, row, col, filter_checks=True):
        """
        Calculate all pseudo-legal moves for *piece* at (row, col).
        If filter_checks=True, remove moves that leave own king in check.
        """
        self._calc_moves_raw(piece, row, col)
        if filter_checks:
            self.filter_moves_leaving_check(piece, row, col)

    def _calc_moves_raw(self, piece, row, col):
        """Pseudo-legal moves only (no check-filter)."""

        def pawn_moves():
            steps = 1 if piece.moved else 2
            start = row + piece.dir
            end   = row + (piece.dir * (steps + 1))
            step_size = piece.dir

            for possible_move_row in range(start, end, step_size):
                if Square.in_range(possible_move_row):
                    if self.squares[possible_move_row][col].isempty():
                        initial = Square(row, col)
                        final   = Square(possible_move_row, col)
                        piece.add_move(Move(initial, final))
                    else:
                        break
                else:
                    break

            # Diagonal captures
            possible_move_row = row + piece.dir
            for possible_move_col in [col - 1, col + 1]:
                if Square.in_range(possible_move_row, possible_move_col):
                    if self.squares[possible_move_row][possible_move_col].has_enemy_piece(piece.color):
                        initial = Square(row, col)
                        final   = Square(possible_move_row, possible_move_col)
                        piece.add_move(Move(initial, final))

        def king_moves():
            adjs = [
                (row-1, col),   (row-1, col+1),
                (row,   col+1), (row+1, col+1),
                (row+1, col),   (row+1, col-1),
                (row,   col-1), (row-1, col-1),
            ]
            for (mr, mc) in adjs:
                if Square.in_range(mr, mc):
                    sq = self.squares[mr][mc]
                    if sq.isempty() or sq.has_enemy_piece(piece.color):
                        piece.add_move(Move(Square(row, col), Square(mr, mc)))

            # Castling
            if not piece.moved:
                # Queen-side
                left_rook = self.squares[row][0].piece
                if isinstance(left_rook, Rook) and not left_rook.moved:
                    clear = all(self.squares[row][c].isempty() for c in range(1, 4))
                    if clear:
                        piece.left_rook = left_rook
                        left_rook.add_move(Move(Square(row, 0), Square(row, 3)))
                        piece.add_move(Move(Square(row, col), Square(row, 2)))

                # King-side
                right_rook = self.squares[row][7].piece
                if isinstance(right_rook, Rook) and not right_rook.moved:
                    clear = all(self.squares[row][c].isempty() for c in range(5, 7))
                    if clear:
                        piece.right_rook = right_rook
                        right_rook.add_move(Move(Square(row, 7), Square(row, 5)))
                        piece.add_move(Move(Square(row, col), Square(row, 6)))

        def straightline_moves(incrs):
            for (row_incr, col_incr) in incrs:
                mr, mc = row + row_incr, col + col_incr
                while True:
                    if not Square.in_range(mr, mc):
                        break
                    initial = Square(row, col)
                    final   = Square(mr, mc)
                    move    = Move(initial, final)
                    sq      = self.squares[mr][mc]
                    if sq.isempty():
                        piece.add_move(move)
                    elif sq.has_enemy_piece(piece.color):
                        piece.add_move(move)
                        break
                    else:
                        break
                    mr += row_incr
                    mc += col_incr

        def knight_moves():
            possible = [
                (row-2, col+1), (row-1, col+2),
                (row+1, col+2), (row+2, col+1),
                (row+2, col-1), (row+1, col-2),
                (row-1, col-2), (row-2, col-1),
            ]
            for (mr, mc) in possible:
                if Square.in_range(mr, mc):
                    if self.squares[mr][mc].isempty_or_enemy(piece.color):
                        piece.add_move(Move(Square(row, col), Square(mr, mc)))

        # Dispatch
        if isinstance(piece, Pawn):
            pawn_moves()
        elif isinstance(piece, Knight):
            knight_moves()
        elif isinstance(piece, Bishop):
            straightline_moves([(-1,1),(-1,-1),(1,1),(1,-1)])
        elif isinstance(piece, Rook):
            straightline_moves([(-1,0),(0,1),(1,0),(0,-1)])
        elif isinstance(piece, Queen):
            straightline_moves([(-1,1),(-1,-1),(1,1),(1,-1),(-1,0),(0,1),(1,0),(0,-1)])
        elif isinstance(piece, King):
            king_moves()

    # ─────────────────────────────────────────────────────────────────────────
    # Board setup
    # ─────────────────────────────────────────────────────────────────────────

    def _create(self):
        for row in range(rows):
            for col in range(cols):
                self.squares[row][col] = Square(row, col)

    def _add_pieces(self, color):
        row_pawn, row_other = (6, 7) if color == 'white' else (1, 0)

        for col in range(cols):
            self.squares[row_pawn][col] = Square(row_pawn, col, Pawn(color))

        self.squares[row_other][1] = Square(row_other, 1, Knight(color))
        self.squares[row_other][6] = Square(row_other, 6, Knight(color))
        self.squares[row_other][2] = Square(row_other, 2, Bishop(color))
        self.squares[row_other][5] = Square(row_other, 5, Bishop(color))
        self.squares[row_other][0] = Square(row_other, 0, Rook(color))
        self.squares[row_other][7] = Square(row_other, 7, Rook(color))
        self.squares[row_other][3] = Square(row_other, 3, Queen(color))
        self.squares[row_other][4] = Square(row_other, 4, King(color))
