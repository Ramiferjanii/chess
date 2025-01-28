from const import *
from square import Square
from piece import *


class Board:
    def __init__(self):
        self.squares = [(0, 0, 0, 0, 0, 0, 0, 0) for col in range(cols)]
        self._create()
        self._add_pieces('white')
        self._add_pieces('black')

    # we pu '_' after name of  the function because i show to this methods is private methods
    def _create(self):
        for row in range(rows):
            for col in range(cols):
                self.squares[row][col] = Square(row, col)

    def _add_pieces(self, color):
        """    its the same value
        if color == 'white' :
                row_pawn , row_other = ( 6 , 7 )
            else :
                row_pawn , row_other = (1 , 0 )"""
        row_pawn, row_other = (6, 7) if color == 'white' else (1, 0)
        # this are all pawns
        for col in range(cols):
            self.squares[row_pawn][col] = Square(row_pawn, col, Pawn(color))
        # knight
        self.squares[row_other][1] = Square(row_other, 1, Knight(color))
        self.squares[row_other][6] = Square(row_other, 6, Knight(color))

        # bishops
        self.squares[row_other][2] = Square(row_other, 2, Bishop(color))
        self.squares[row_other][5] = Square(row_other, 5, Bishop(color))

        #rooks

        self.squares[row_other][0] = Square(row_other, 0, Rook(color))
        self.squares[row_other][7] = Square(row_other, 7, Rook(color))

        #queen
        self.squares[row_other][3] = Square(row_other, 3, Queen(color))

        # king
        self.squares[row_other][4] = Square(row_other, 4, King(color))
