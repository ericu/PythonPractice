#!/usr/bin/env python3

import curses
import random
import time

MOVE_PERIOD_SECONDS = 1 / 10
SLEEP_TIME = MOVE_PERIOD_SECONDS / 4

FOOD_VALUE = 3
FOOD_CHAR = "$"
DOOR_CHAR = "#"


class DeathException(Exception):
    def __init__(self, message):
        super().__init__(self)
        self.message = message


class WinException(Exception):
    pass


class SnakeGame:
    def __init__(self, window, height, width):
        self.done = False
        curses.curs_set(0)  # hide cursor
        self.window = window
        self.window.nodelay(True)
        self.height = height
        self.width = width

        self.draw_borders()

        self.status_bar = curses.newwin(1, width - 2, 1, 1)

        self.game_width = width - 2  # space for borders
        self.game_height = height - 4  # space for borders and status
        self.game_area = curses.newwin(self.game_height, self.game_width, 3, 1)
        self.player_coords = [self.game_height // 2, self.game_width // 2]
        self.player_drawings = []
        self.player_add_length = 5
        self.player_v = [0, 1]
        self.draw_player(self.player_coords)
        self.place_food()
        self.place_door()
        self.game_area.refresh()

    def pick_clear_location(self):
        def pick_location():
            y = random.randint(0, self.game_height - 1)
            x = random.randint(0, self.game_width - 1)
            return [y, x]

        coords = pick_location()
        while (self.game_area.inch(coords[0], coords[1]) & 0xFF) != ord(" "):
            coords = pick_location()
        return coords

    def place_door(self):
        self.door_location = self.pick_clear_location()
        self.draw_char(self.door_location, DOOR_CHAR)

    def place_food(self):
        self.food_location = self.pick_clear_location()
        self.draw_char(self.food_location, FOOD_CHAR)

    def draw_char(self, coords, char):
        y, x = coords
        # Curses can't addch to the bottom-right corner without ERR.
        # https://stackoverflow.com/questions/36387625/curses-fails-when-calling-addch-on-the-bottom-right-corner
        if y == self.game_height - 1 and x == self.game_width - 1:
            self.game_area.insch(y, x, char)
        else:
            self.game_area.addch(y, x, char)

    def draw_player(self, coords):
        self.draw_char(self.player_coords, "s")
        self.player_coords = coords
        self.player_drawings.append(self.player_coords)
        self.draw_char(self.player_coords, "S")
        if self.player_add_length > 0:
            self.player_add_length -= 1
            self.set_status(f"Current length: {len(self.player_drawings)}")
        else:
            y, x = self.player_drawings[0]
            self.player_drawings = self.player_drawings[1:]
            self.game_area.addch(y, x, " ")

    def move_player(self):
        p_y, p_x = self.player_coords
        v_y, v_x = self.player_v
        p_y += v_y
        p_x += v_x
        if (
            p_x < 0
            or p_y < 0
            or p_x > self.game_width - 1
            or p_y > self.game_height - 1
        ):
            raise DeathException("You ran into a wall.  You have died.")

        need_more_food = False
        hit_char = self.game_area.inch(p_y, p_x) & 0xFF
        if hit_char == ord(" "):
            pass
        elif hit_char == ord(FOOD_CHAR):
            self.player_add_length += FOOD_VALUE
            need_more_food = True
        elif hit_char == ord(DOOR_CHAR):
            raise WinException()
        else:
            raise DeathException("You bit yourself.  You have died.")

        self.draw_player([p_y, p_x])
        if need_more_food:
            self.place_food()

    def die(self, cause_of_death):
        for coords in self.player_drawings:
            self.draw_char(coords, "x")
        self.draw_char(self.player_coords, "X")
        self.game_area.refresh()
        self.set_status(cause_of_death)
        self.done = True

    def win(self):
        self.set_status(
            f"You have gotten away with {len(self.player_drawings)} points."
        )
        self.game_area.clear()
        self.game_area.refresh()
        self.done = True

    def play(self):
        next_draw = time.time() + MOVE_PERIOD_SECONDS
        while True:
            time.sleep(SLEEP_TIME)
            c = self.window.getch()
            if c == ord("q"):
                break
            map_directions = {
                ord("h"): [0, -1],
                curses.KEY_LEFT: [0, -1],
                ord("l"): [0, 1],
                curses.KEY_RIGHT: [0, 1],
                ord("k"): [-1, 0],
                curses.KEY_UP: [-1, 0],
                ord("j"): [1, 0],
                curses.KEY_DOWN: [1, 0],
            }
            if c in map_directions:
                [d_y, d_x] = map_directions[c]
                if self.player_v != [-d_y, -d_x]:
                    self.player_v = [d_y, d_x]
            current_time = time.time()
            try:
                if not self.done and current_time >= next_draw:
                    next_draw = current_time + MOVE_PERIOD_SECONDS
                    self.move_player()
                    self.game_area.refresh()
            except DeathException as err:
                self.die(err.message)
            except WinException:
                self.win()

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
    (height, width) = window.getmaxyx()
    if width < 20 or height < 15:
        raise RuntimeError(
            f"Sorry, your screen of {width} by {height} is too small"
        )
    game = SnakeGame(window, height, width)
    game.play()


if __name__ == "__main__":
    curses.wrapper(main)
