"""
opening.py – Chess Opening Book
Recognises famous openings from the move history.
Moves are stored as (from_col, from_row, to_col, to_row) tuples matching
the Move objects used in the engine.
"""

# Each entry: ( sequence_of_moves_as_tuples , "Opening Name" )
# Moves are 0-indexed (row 0 = rank 8, col 0 = file a)
# Tuple format: (initial_col, initial_row, final_col, final_row)

OPENINGS = [
    # ── King's Pawn Openings ─────────────────────────────────────────────
    ([(4,6,4,4)],                                               "King's Pawn (e4)"),
    ([(4,6,4,4),(4,1,4,3)],                                     "Open Game (e4 e5)"),
    ([(4,6,4,4),(4,1,4,3),(6,7,5,5)],                           "King's Knight Opening"),
    ([(4,6,4,4),(4,1,4,3),(6,7,5,5),(1,0,2,2)],                 "Four Knights (partial)"),
    ([(4,6,4,4),(4,1,4,3),(6,7,5,5),(6,0,5,2)],                 "King's Knight – Nc6"),
    ([(4,6,4,4),(4,1,4,3),(6,7,5,5),(6,0,5,2),(5,7,2,4)],       "Italian Game"),
    ([(4,6,4,4),(4,1,4,3),(6,7,5,5),(6,0,5,2),(5,7,4,6)],       "Ruy López (Spanish)"),
    ([(4,6,4,4),(4,1,4,3),(6,7,5,5),(6,0,5,2),(5,7,4,6),(0,0,2,0)], "Ruy López – Morphy Defence"),
    ([(4,6,4,4),(4,1,4,3),(6,7,5,5),(6,0,5,2),(2,7,5,4)],       "Bishop's Opening"),
    ([(4,6,4,4),(4,1,4,3),(6,7,5,5),(6,0,5,2),(3,7,7,3)],       "Scotch Game"),
    ([(4,6,4,4),(4,1,4,3),(6,7,5,5),(3,6,3,4)],                 "King's Gambit"),
    ([(4,6,4,4),(4,1,4,3),(6,7,5,5),(5,7,2,4)],                 "King's Bishop's Game"),
    # ── Sicilian Defence ────────────────────────────────────────────────
    ([(4,6,4,4),(2,1,2,3)],                                     "Sicilian Defence"),
    ([(4,6,4,4),(2,1,2,3),(6,7,5,5)],                           "Sicilian – Open (Nf3)"),
    ([(4,6,4,4),(2,1,2,3),(6,7,5,5),(3,1,3,2)],                 "Sicilian – Kan"),
    ([(4,6,4,4),(2,1,2,3),(6,7,5,5),(3,1,3,3)],                 "Sicilian – Najdorf"),
    ([(4,6,4,4),(2,1,2,3),(6,7,5,5),(6,0,5,2)],                 "Sicilian – Classical"),
    ([(4,6,4,4),(2,1,2,3),(3,6,3,4)],                           "Sicilian – Alapin (c3)"),
    ([(4,6,4,4),(2,1,2,3),(2,6,2,4)],                           "Sicilian – Closed"),
    # ── French Defence ──────────────────────────────────────────────────
    ([(4,6,4,4),(4,1,4,2)],                                     "French Defence"),
    ([(4,6,4,4),(4,1,4,2),(3,6,3,4),(3,1,3,3)],                 "French – Advance Variation"),
    ([(4,6,4,4),(4,1,4,2),(6,7,5,5),(3,1,3,3)],                 "French – Knight Variation"),
    # ── Caro-Kann ───────────────────────────────────────────────────────
    ([(4,6,4,4),(2,1,2,2)],                                     "Caro-Kann Defence"),
    ([(4,6,4,4),(2,1,2,2),(3,6,3,4),(3,1,3,3)],                 "Caro-Kann – Advance"),
    # ── Queen's Pawn Openings ────────────────────────────────────────────
    ([(3,6,3,4)],                                               "Queen's Pawn (d4)"),
    ([(3,6,3,4),(3,1,3,3)],                                     "Queen's Gambit (partial)"),
    ([(3,6,3,4),(3,1,3,3),(2,6,2,4)],                           "Queen's Gambit"),
    ([(3,6,3,4),(3,1,3,3),(2,6,2,4),(2,1,2,3)],                 "Queen's Gambit Declined"),
    ([(3,6,3,4),(3,1,3,3),(2,6,2,4),(3,1,2,4)],                 "Queen's Gambit Accepted"),
    ([(3,6,3,4),(6,0,5,2)],                                     "Indian Defence"),
    ([(3,6,3,4),(6,0,5,2),(2,6,2,4),(6,1,6,2)],                 "King's Indian Defence"),
    ([(3,6,3,4),(6,0,5,2),(2,6,2,4),(5,1,5,2)],                 "Nimzo-Indian (partial)"),
    ([(3,6,3,4),(3,1,3,3),(2,6,2,4),(6,0,5,2)],                 "Grünfeld Defence"),
    # ── English / Réti ──────────────────────────────────────────────────
    ([(2,6,2,4)],                                               "English Opening"),
    ([(2,6,2,4),(4,1,4,3)],                                     "English – Symmetrical"),
    ([(6,7,5,5)],                                               "Réti Opening"),
    ([(6,7,5,5),(3,1,3,3)],                                     "Réti – d5 Response"),
    # ── Dutch Defence ───────────────────────────────────────────────────
    ([(3,6,3,4),(5,1,5,3)],                                     "Dutch Defence"),
    # ── Scandinavian ────────────────────────────────────────────────────
    ([(4,6,4,4),(3,1,3,2)],                                     "Scandinavian Defence"),
]


def _move_key(move):
    """Convert a Move object to a comparable tuple."""
    return (move.initial.col, move.initial.row, move.final.col, move.final.row)


def identify_opening(move_history):
    """
    Given a list of Move objects, return the best matching opening name
    or None if no known opening is recognised.
    Best match = longest matching sequence.
    """
    history_keys = [_move_key(m) for m in move_history]
    best_name = None
    best_len  = 0

    for sequence, name in OPENINGS:
        n = len(sequence)
        if n > len(history_keys):
            continue
        if history_keys[:n] == list(sequence):
            if n > best_len:
                best_len  = n
                best_name = name

    return best_name
