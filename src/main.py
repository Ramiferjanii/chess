"""
main.py – Chess entry point

Startup modes
─────────────
  python main.py              → local two-player (same keyboard)
  python main.py server       → host an online game (port 5555)
  python main.py client <ip>  → join an online game
  python main.py client <ip> <port>

Online protocol
───────────────
  Server plays White, Client plays Black.
  The active side drags/drops; the result is sent over the network.
  The passive side receives the move and applies it automatically.
"""

import pygame
import sys
from const import *
from game import Game
from square import Square
from move import Move
from network import Network


class Main:

    def __init__(self, network: Network | None = None, online_color: str | None = None):
        pygame.init()
        self.screen       = pygame.display.set_mode((width, height))
        pygame.display.set_caption('Chess  ♟')
        self.game         = Game()
        self.network      = network        # None  → local play
        self.online_color = online_color   # 'white' | 'black' | None

    # ─────────────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _my_turn(self):
        """True when it is this instance's turn (local or networked)."""
        if self.online_color is None:
            return True            # local: always your turn
        return self.game.next_player == self.online_color

    def _apply_network_move(self, move_dict):
        """Apply an opponent move received over the network."""
        board   = self.game.board
        ir, ic  = move_dict['ir'], move_dict['ic']
        fr, fc  = move_dict['fr'], move_dict['fc']
        piece   = board.squares[ir][ic].piece
        if piece is None:
            return
        initial = Square(ir, ic)
        final   = Square(fr, fc)
        move    = Move(initial, final)
        board.calc_moves(piece, ir, ic, filter_checks=True)
        if board.valid_move(piece, move):
            captured = board.squares[fr][fc].has_piece()
            board.move(piece, move)
            self.game.record_move(move)
            self.game.play_sound(captured)
            self.game.next_turn()

    def _redraw_full(self, game, screen):
        game.show_bg(screen)
        game.show_last_move(screen)
        game.show_moves(screen)
        game.show_pieces(screen)
        game.show_hover(screen)
        game.show_check(screen)
        game.show_opening(screen)
        game.show_gameover(screen)

    # ─────────────────────────────────────────────────────────────────────────
    # Main loop
    # ─────────────────────────────────────────────────────────────────────────

    def mainloop(self):
        game    = self.game
        screen  = self.screen
        dragger = self.game.dragger
        board   = self.game.board

        while True:
            # ── Draw ────────────────────────────────────────────────────────
            game.show_bg(screen)
            game.show_last_move(screen)
            game.show_moves(screen)
            game.show_pieces(screen)
            game.show_hover(screen)
            game.show_check(screen)
            game.show_opening(screen)

            if dragger.dragging:
                dragger.update_blit(screen)

            game.show_gameover(screen)  # always on top

            # ── Poll network for opponent move ────────────────────────────
            if self.network and self.network.connected and not self._my_turn():
                move_dict = self.network.poll()
                if move_dict:
                    self._apply_network_move(move_dict)

            # ── Events ──────────────────────────────────────────────────────
            for event in pygame.event.get():

                # ── Mouse Down ──────────────────────────────────────────────
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if game.is_game_over():
                        continue          # block input after game ends

                    dragger.update_mouse(event.pos)
                    clicked_row = dragger.mousey // sqsize
                    clicked_col = dragger.mousex // sqsize

                    if board.squares[clicked_row][clicked_col].has_piece():
                        piece = board.squares[clicked_row][clicked_col].piece

                        if piece.color == game.next_player and self._my_turn():
                            board.calc_moves(piece, clicked_row, clicked_col, filter_checks=True)
                            dragger.save_initial(event.pos)
                            dragger.drag_piece(piece)
                            self._redraw_full(game, screen)

                # ── Mouse Motion ─────────────────────────────────────────────
                elif event.type == pygame.MOUSEMOTION:
                    motion_row = event.pos[1] // sqsize
                    motion_col = event.pos[0] // sqsize
                    game.set_hover(motion_row, motion_col)

                    if dragger.dragging:
                        dragger.update_mouse(event.pos)
                        self._redraw_full(game, screen)
                        dragger.update_blit(screen)

                # ── Mouse Up ─────────────────────────────────────────────────
                elif event.type == pygame.MOUSEBUTTONUP:
                    if dragger.dragging:
                        dragger.update_mouse(event.pos)
                        released_row = dragger.mousey // sqsize
                        released_col = dragger.mousex // sqsize

                        initial = Square(dragger.initial_row, dragger.initial_col)
                        final   = Square(released_row, released_col)
                        move    = Move(initial, final)

                        if board.valid_move(dragger.piece, move):
                            captured = board.squares[released_row][released_col].has_piece()
                            board.move(dragger.piece, move)
                            game.record_move(move)
                            game.play_sound(captured)
                            self._redraw_full(game, screen)
                            game.next_turn()

                            # Send move to opponent
                            if self.network and self.network.connected:
                                self.network.send(move)

                    dragger.undrag_piece()

                # ── Key Press ────────────────────────────────────────────────
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_t:
                        game.change_theme()
                    if event.key == pygame.K_r:
                        game.reset()
                        game    = self.game
                        dragger = self.game.dragger
                        board   = self.game.board

                # ── Quit ─────────────────────────────────────────────────────
                elif event.type == pygame.QUIT:
                    if self.network:
                        self.network.close()
                    pygame.quit()
                    sys.exit()

            pygame.display.update()


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    network      = None
    online_color = None

    if len(sys.argv) >= 2:
        mode = sys.argv[1].lower()

        if mode == 'server':
            port = int(sys.argv[2]) if len(sys.argv) >= 3 else Network.DEFAULT_PORT
            network = Network()
            network.start_server(port)
            online_color = 'white'
            print("[Main] Waiting for opponent to connect…")
            # Pygame caption update happens after init
        elif mode == 'client':
            if len(sys.argv) < 3:
                print("Usage: python main.py client <host> [port]")
                sys.exit(1)
            host = sys.argv[2]
            port = int(sys.argv[3]) if len(sys.argv) >= 4 else Network.DEFAULT_PORT
            network = Network()
            network.start_client(host, port)
            online_color = 'black'
        else:
            print(f"Unknown mode '{mode}'.  Valid: server | client <ip>")
            sys.exit(1)

    app = Main(network=network, online_color=online_color)

    if online_color:
        color_str = online_color.capitalize()
        pygame.display.set_caption(f'Chess  ♟  – Online ({color_str})')

    app.mainloop()


if __name__ == '__main__':
    main()
