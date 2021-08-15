#!/usr/bin/env python3

import curses
import time

MOVE_PERIOD_SECONDS = 1 / 20
SLEEP_TIME = MOVE_PERIOD_SECONDS / 4

class SnakeGame():
    def __init__(self, stdscr, height, width):
        curses.curs_set(0) # hide cursor
        self.stdscr = stdscr
        self.stdscr.nodelay(True)
        self.height = height
        self.width = width

        self.draw_borders()

        self.status_bar = curses.newwin(1, width - 2, 1, 1)

        self.game_width = width - 2 # space for borders
        self.game_height = height - 4 # space for borders and status
        self.game_area = curses.newwin(self.game_height, self.game_width, 3, 1)
        self.player_coords = [self.game_height // 2, self.game_width // 2]
        self.player_v = [0, 1]

        self.set_status(f'coords {height} by {width} game {self.game_height} by {self.game_width}')

    def draw_player(self):
        y, x = self.player_coords
        # Curses can't addch to the bottom-right corner without ERR.
        # https://stackoverflow.com/questions/36387625/curses-fails-when-calling-addch-on-the-bottom-right-corner
        if y == self.game_height - 1 and x == self.game_width - 1:
          self.game_area.insch(y, x, 'I')
        else:
          self.game_area.addch(y, x, 'I')

    def erase_player(self):
        y, x = self.player_coords
        self.game_area.delch(y, x)

    def play(self):
        self.draw_player()
        self.game_area.refresh()
        next_draw = time.time() + MOVE_PERIOD_SECONDS
        while True:
            time.sleep(SLEEP_TIME)
            c = self.stdscr.getch()
            if c == ord('h'):
                self.player_v = [0, -1]
            elif c == ord('l'):
                self.player_v = [0, 1]
            elif c == ord('k'):
                self.player_v = [-1, 0]
            elif c == ord('j'):
                self.player_v = [1, 0]
            elif c == ord('q'):
                break
            current_time = time.time()
            if current_time >= next_draw:
                next_draw = current_time + MOVE_PERIOD_SECONDS
                self.erase_player()
                p_y, p_x = self.player_coords
                v_y, v_x = self.player_v
                p_y += v_y
                p_x += v_x
                p_x = max(0, min(p_x, self.game_width - 1))
                p_y = max(0, min(p_y, self.game_height - 1))
                self.player_coords = [p_y, p_x]
                self.set_status(f'drawing player at {self.player_coords}')
                self.draw_player()
                self.game_area.refresh()

    def draw_borders(self):
        self.stdscr.clear()
        self.stdscr.border()
        self.stdscr.hline(2, 1, curses.ACS_HLINE, self.width - 2)
        self.stdscr.addch(2, 0, curses.ACS_LTEE)
        self.stdscr.addch(2, self.width - 1, curses.ACS_RTEE)
        self.stdscr.refresh()

    def set_status(self, status):
        self.status_bar.clear()
        # Leave 1 space at each end, both for style and due to the curses
        # last-char-in-window wrapping exception.
        self.status_bar.addnstr(0, 1, status, self.width - 4, curses.A_REVERSE)
        self.status_bar.refresh()

def main(stdscr):
    (y_min, x_min) = stdscr.getbegyx()
    (height, width) = stdscr.getmaxyx()
    if width < 20 or height < 15:
        raise RuntimeError(f'Sorry, your screen of {width} by {height} is too small')
    game = SnakeGame(stdscr, height, width)
    game.play()


if __name__ == "__main__":
    curses.wrapper(main)

