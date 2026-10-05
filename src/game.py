import pygame
from const import *
from board import Board
from config import Config
from dragger import Dragger
from square import Square
from opening import identify_opening

# ── Game state constants ───────────────────────────────────────────────────────
STATE_PLAYING    = 'playing'
STATE_CHECK      = 'check'
STATE_CHECKMATE  = 'checkmate'
STATE_STALEMATE  = 'stalemate'


class Game:
    def __init__(self):
        self.next_player  = 'white'
        self.hovered_sqr  = None
        self.board        = Board()
        self.dragger      = Dragger()
        self.config       = Config()
        self.move_history = []           # list of Move objects (full game)
        self.state        = STATE_PLAYING
        self.opening_name = None         # recognised opening name or None

        # Overlay fonts
        self._font_big   = pygame.font.SysFont('segoeui', 56, bold=True)
        self._font_med   = pygame.font.SysFont('segoeui', 28, bold=True)
        self._font_small = pygame.font.SysFont('monospace', 16, bold=True)

    # ─────────────────────────────────────────────────────────────────────────
    # Show methods
    # ─────────────────────────────────────────────────────────────────────────

    def show_bg(self, surface):
        theme = self.config.theme
        for row in range(rows):
            for col in range(cols):
                color = theme.bg.light if (row + col) % 2 == 0 else theme.bg.dark
                rect  = (col * sqsize, row * sqsize, sqsize, sqsize)
                pygame.draw.rect(surface, color, rect)

                # Row numbers
                if col == 0:
                    clr = theme.bg.dark if row % 2 == 0 else theme.bg.light
                    lbl = self.config.font.render(str(rows - row), 1, clr)
                    surface.blit(lbl, (5, 5 + row * sqsize))

                # Column letters
                if row == 7:
                    clr = theme.bg.dark if (row + col) % 2 == 0 else theme.bg.light
                    lbl = self.config.font.render(Square.get_alpacol(col), 1, clr)
                    surface.blit(lbl, (col * sqsize + sqsize - 20, height - 20))

    def show_pieces(self, surface):
        for row in range(rows):
            for col in range(cols):
                if self.board.squares[row][col].has_piece():
                    piece = self.board.squares[row][col].piece
                    if piece is not self.dragger.piece:
                        piece.set_texture(size=80)
                        img = pygame.image.load(piece.texture)
                        img_center = col * sqsize + sqsize // 2, row * sqsize + sqsize // 2
                        piece.texture_rect = img.get_rect(center=img_center)
                        surface.blit(img, piece.texture_rect)

    def show_moves(self, surface):
        theme = self.config.theme
        if self.dragger.dragging:
            piece = self.dragger.piece
            for move in piece.moves:
                color = theme.moves.light if (move.final.row + move.final.col) % 2 == 0 \
                        else theme.moves.dark
                rect = (move.final.col * sqsize, move.final.row * sqsize, sqsize, sqsize)
                pygame.draw.rect(surface, color, rect)

    def show_last_move(self, surface):
        theme = self.config.theme
        if self.board.last_move:
            initial = self.board.last_move.initial
            final   = self.board.last_move.final
            for pos in [initial, final]:
                color = theme.trace.light if (pos.row + pos.col) % 2 == 0 else theme.trace.dark
                rect  = (pos.col * sqsize, pos.row * sqsize, sqsize, sqsize)
                pygame.draw.rect(surface, color, rect)

    def show_hover(self, surface):
        if self.hovered_sqr:
            color = (180, 180, 180)
            rect  = (self.hovered_sqr.col * sqsize, self.hovered_sqr.row * sqsize, sqsize, sqsize)
            pygame.draw.rect(surface, color, rect, width=3)

    def show_check(self, surface):
        """Highlight the king square in red when in check."""
        if self.state in (STATE_CHECK, STATE_CHECKMATE):
            try:
                king_row, king_col = self.board._find_king(self.next_player)
                # Pulsing red overlay
                overlay = pygame.Surface((sqsize, sqsize), pygame.SRCALPHA)
                overlay.fill((220, 30, 30, 160))
                surface.blit(overlay, (king_col * sqsize, king_row * sqsize))
            except ValueError:
                pass

    def show_opening(self, surface):
        """Display recognised opening name at top of board."""
        if self.opening_name:
            lbl = self._font_small.render(f"♟ {self.opening_name}", True, (255, 255, 255))
            bg  = pygame.Surface((lbl.get_width() + 16, lbl.get_height() + 8), pygame.SRCALPHA)
            bg.fill((20, 20, 20, 180))
            surface.blit(bg,  (8, 4))
            surface.blit(lbl, (16, 8))

    def show_gameover(self, surface):
        """Full-screen overlay for checkmate / stalemate."""
        if self.state not in (STATE_CHECKMATE, STATE_STALEMATE):
            return

        # Semi-transparent dark backdrop
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((10, 10, 20, 200))
        surface.blit(overlay, (0, 0))

        if self.state == STATE_CHECKMATE:
            winner = 'White' if self.next_player == 'black' else 'Black'
            title  = f"Checkmate!"
            sub    = f"{winner} wins  🏆"
        else:
            title = "Stalemate!"
            sub   = "It's a draw  🤝"

        # Title
        t_surf = self._font_big.render(title, True, (255, 230, 80))
        t_rect = t_surf.get_rect(center=(width // 2, height // 2 - 50))
        surface.blit(t_surf, t_rect)

        # Subtitle
        s_surf = self._font_med.render(sub, True, (220, 220, 220))
        s_rect = s_surf.get_rect(center=(width // 2, height // 2 + 20))
        surface.blit(s_surf, s_rect)

        # Hint
        h_surf = self._font_small.render("Press  R  to play again", True, (160, 160, 160))
        h_rect = h_surf.get_rect(center=(width // 2, height // 2 + 80))
        surface.blit(h_surf, h_rect)

    # ─────────────────────────────────────────────────────────────────────────
    # Game logic helpers
    # ─────────────────────────────────────────────────────────────────────────

    def next_turn(self):
        self.next_player = 'white' if self.next_player == 'black' else 'black'
        self._update_state()

    def _update_state(self):
        """Recalculate check / checkmate / stalemate after each turn."""
        if self.board.is_checkmate(self.next_player):
            self.state = STATE_CHECKMATE
        elif self.board.is_stalemate(self.next_player):
            self.state = STATE_STALEMATE
        elif self.board.in_check(self.next_player):
            self.state = STATE_CHECK
        else:
            self.state = STATE_PLAYING

    def record_move(self, move):
        """Append move to history and refresh opening recognition."""
        self.move_history.append(move)
        self.opening_name = identify_opening(self.move_history)

    def is_game_over(self):
        return self.state in (STATE_CHECKMATE, STATE_STALEMATE)

    def set_hover(self, row, col):
        self.hovered_sqr = self.board.squares[row][col]

    def change_theme(self):
        self.config.change_theme()

    def play_sound(self, captured=False):
        if captured:
            self.config.capture_sound.play()
        else:
            self.config.move_sound.play()

    def reset(self):
        self.__init__()
