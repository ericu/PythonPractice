#!/usr/bin/env python3

import curses
import time

MOVE_PERIOD_SECONDS = 1 / 20
SLEEP_TIME = MOVE_PERIOD_SECONDS / 4

class SnakeGame():
    def __init__(self, window, height, width):
        curses.curs_set(0) # hide cursor
        self.window = window
        self.window.nodelay(True)
        self.height = height
        self.width = width

        self.draw_borders()

        self.status_bar = curses.newwin(1, width - 2, 1, 1)

        self.game_width = width - 2 # space for borders
        self.game_height = height - 4 # space for borders and status
        self.game_area = curses.newwin(self.game_height, self.game_width, 3, 1)
        self.player_coords = [self.game_height // 2, self.game_width // 2]
        self.player_drawings = []
        self.player_add_length = 5
        self.player_v = [0, 1]

        self.set_status(f'coords {height} by {width} game {self.game_height} by {self.game_width}')

    def draw_player_char(self, coords, char):
        y, x = coords
        # Curses can't addch to the bottom-right corner without ERR.
        # https://stackoverflow.com/questions/36387625/curses-fails-when-calling-addch-on-the-bottom-right-corner
        if y == self.game_height - 1 and x == self.game_width - 1:
          self.game_area.insch(y, x, char)
        else:
          self.game_area.addch(y, x, char)

    def draw_player(self, coords):
        self.draw_player_char(self.player_coords, 's')
        self.player_coords = coords
        self.player_drawings.append(self.player_coords)
        self.draw_player_char(self.player_coords, 'S')
        if self.player_add_length > 0:
            self.player_add_length -= 1
        else:
            y, x = self.player_drawings[0]
            self.player_drawings = self.player_drawings[1:]
            self.game_area.addch(y, x, ' ')

    def move_player(self):
        p_y, p_x = self.player_coords
        v_y, v_x = self.player_v
        p_y += v_y
        p_x += v_x
        if (p_x < 0 or p_y < 0 or
            p_x > self.game_width - 1 or p_y > self.game_height - 1):
            raise RuntimeError('Implement border death.')

        hit_char = self.game_area.inch(p_y, p_x) & 0xff
        if hit_char != ord(' '):
            raise RuntimeError(f'Hit something({hit_char}); implement death.')

        self.draw_player([p_y, p_x])
        self.set_status(f'drawing player at {self.player_coords}')

    def play(self):
        self.draw_player(self.player_coords)
        self.game_area.refresh()
        next_draw = time.time() + MOVE_PERIOD_SECONDS
        while True:
            time.sleep(SLEEP_TIME)
            c = self.window.getch()
            if c == ord('h') or c == curses.KEY_LEFT:
                self.player_v = [0, -1]
            elif c == ord('l') or c == curses.KEY_RIGHT:
                self.player_v = [0, 1]
            elif c == ord('k') or c == curses.KEY_UP:
                self.player_v = [-1, 0]
            elif c == ord('j') or c == curses.KEY_DOWN:
                self.player_v = [1, 0]
            elif c == ord('q'):
                break
            current_time = time.time()
            if current_time >= next_draw:
                next_draw = current_time + MOVE_PERIOD_SECONDS
                self.move_player()
                self.game_area.refresh()

    def draw_borders(self):
        self.window.clear()
        self.window.border()
        self.window.hline(2, 1, curses.ACS_HLINE, self.width - 2)
        self.window.addch(2, 0, curses.ACS_LTEE)
        self.window.addch(2, self.width - 1, curses.ACS_RTEE)
        self.window.refresh()

    def set_status(self, status):
        self.status_bar.clear()
        # Leave 1 space at each end, both for style and due to the curses
        # last-char-in-window wrapping exception.
        self.status_bar.addnstr(0, 1, status, self.width - 4, curses.A_REVERSE)
        self.status_bar.refresh()

def main(window):
    (y_min, x_min) = window.getbegyx()
    (height, width) = window.getmaxyx()
    if width < 20 or height < 15:
        raise RuntimeError(f'Sorry, your screen of {width} by {height} is too small')
    game = SnakeGame(window, height, width)
    game.play()


if __name__ == "__main__":
    curses.wrapper(main)

