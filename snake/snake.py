#!/usr/bin/env python3

from typing import List, Dict, Optional
import curses
import random
import time

MOVE_PERIOD_SECONDS = 1 / 10
SLEEP_TIME = MOVE_PERIOD_SECONDS / 4
FOOD_VALUE = 3
FOOD_CHAR = "$"
DOOR_CHAR = "#"
POISON_CHAR = "\u2620"


class DeathException(Exception):
    def __init__(self, message):
        super().__init__(self)
        self.message = message


class WinException(Exception):
    pass


class Player:
    def __init__(self, coords: List[int], length: int):
        self.coords = coords
        self.drawings: List[List[int]]
        self.drawings = []
        self.add_length = length
        self.v = [0, 1]

    def set_coords(self, coords: List[int]) -> Optional[List[int]]:
        self.drawings.append(coords)
        self.coords = coords
        if self.add_length > 0:
            self.add_length -= 1
            return None
        coords = self.drawings[0]
        self.drawings = self.drawings[1:]
        return coords

    def eat_food(self, how_much: int) -> None:
        self.add_length += how_much


class SnakeGame:
    def __init__(self, window, height: int, width: int):
        self.done = False
        self.window = window
        self.window.nodelay(True)
        self.width = width

        self.draw_borders()

        self.status_bar = curses.newwin(1, width - 2, 1, 1)
        self.set_status('Avoid poison \u2620, eat food $, go out door # to win. Steer with hjkl/arrows.')

        self.poison_locations: Dict[str, bool]
        self.poison_locations = {}
        game_width = width - 2  # space for borders
        game_height = height - 4  # space for borders and status
        self.game_area = curses.newwin(game_height, game_width, 3, 1)
        self.player = Player([game_height // 2, game_width // 2], 5)
        self.draw_player(self.player.coords)
        self.place_food()
        self.place_door()
        self.place_poison()
        self.game_area.refresh()

    def pick_clear_location(self) -> List[int]:
        (height, width) = self.game_area.getmaxyx()

        def pick_location():
            y = random.randint(0, height - 1)
            x = random.randint(0, width - 1)
            return [y, x]

        coords = pick_location()
        while (str(coords) in self.poison_locations) or (
            self.game_area.inch(coords[0], coords[1]) & 0xFF  # type: ignore
        ) != ord(" "):
            coords = pick_location()
        return coords

    def place_door(self) -> None:
        door_location = self.pick_clear_location()
        self.draw_char(door_location, DOOR_CHAR)

    def place_food(self) -> None:
        food_location = self.pick_clear_location()
        self.draw_char(food_location, FOOD_CHAR)

    def place_poison(self) -> None:
        location = self.pick_clear_location()
        self.poison_locations[str(location)] = True
        self.draw_char(location, POISON_CHAR)

    def draw_char(self, coords: List[int], char: str) -> None:
        (height, width) = self.game_area.getmaxyx()
        y, x = coords
        # Curses can't addch to the bottom right corner without ERR.
        # https://stackoverflow.com/questions/36387625/curses-fails-when-calling-addch-on-the-bottom-right-corner
        if y == height - 1 and x == width - 1:
            self.game_area.insch(y, x, char)
        else:
            self.game_area.addch(y, x, char)

    def draw_player(self, coords: List[int]) -> None:
        self.draw_char(self.player.coords, "s")
        to_erase = self.player.set_coords(coords)
        self.draw_char(self.player.coords, "S")
        if to_erase:
            y, x = to_erase
            self.game_area.addch(y, x, " ")

    def move_player(self) -> None:
        (height, width) = self.game_area.getmaxyx()
        p_y, p_x = self.player.coords
        v_y, v_x = self.player.v
        p_y += v_y
        p_x += v_x
        if p_x < 0 or p_y < 0 or p_x > width - 1 or p_y > height - 1:
            raise DeathException("You ran into a wall.")

        if str([p_y, p_x]) in self.poison_locations:
            raise DeathException("You ate the poison.")

        need_more_food = False
        hit_char = self.game_area.inch(p_y, p_x) & 0xFF  # type: ignore
        if hit_char == ord(" "):
            pass
        elif hit_char == ord(FOOD_CHAR):
            self.player.eat_food(FOOD_VALUE)
            need_more_food = True
        elif hit_char == ord(DOOR_CHAR):
            raise WinException()
        else:
            raise DeathException("You bit yourself.")

        self.draw_player([p_y, p_x])
        if need_more_food:
            self.place_food()
            self.place_poison()

    def die(self, cause_of_death: str) -> None:
        for coords in self.player.drawings:
            self.draw_char(coords, "x")
        self.draw_char(self.player.coords, "X")
        self.game_area.refresh()
        self.set_status(cause_of_death + "  You have died.  Press 'q' to quit.")
        self.done = True

    def win(self) -> None:
        self.set_status(
            f"You have gotten away with {len(self.player.drawings)} points.  Press 'q' to quit."
        )
        self.done = True

    def play(self) -> None:
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
                if self.player.v != [-d_y, -d_x]:
                    self.player.v = [d_y, d_x]
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

    def draw_borders(self) -> None:
        self.window.clear()
        self.window.border()
        self.window.hline(2, 1, curses.ACS_HLINE, self.width - 2)
        self.window.addch(2, 0, curses.ACS_LTEE)
        self.window.addch(2, self.width - 1, curses.ACS_RTEE)
        self.window.refresh()

    def set_status(self, status: str) -> None:
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
    curses.curs_set(0)  # hide cursor
    game = SnakeGame(window, height, width)
    game.play()


if __name__ == "__main__":
    curses.wrapper(main)
