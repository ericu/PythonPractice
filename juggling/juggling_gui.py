#!/usr/bin/python3

import tkinter
from tkinter import ttk, N, S, E, W, HORIZONTAL, VERTICAL
import sys
import time

from siteswap import SiteSwap, InputError

root = tkinter.Tk()
root.title("Juggling SiteSwap Animator")

frame = ttk.Frame(root, width=200)
frame.grid(column=0, row=0)

label = ttk.Label(frame, text="This program animates vanilla siteswaps.")
label.grid(column=0, row=0, columnspan=2)

CANVAS_WIDTH = 300
CANVAS_HEIGHT = 300
canvas = tkinter.Canvas(
    frame, bg="black", height=CANVAS_HEIGHT, width=CANVAS_WIDTH
)
canvas.grid(column=0, row=1, columnspan=2)

list_frame = ttk.Frame(frame)
list_frame.grid(column=1, row=2, sticky=(N, S, E, W))

list_label = ttk.Label(frame, text="Choose pattern")
list_label.grid(column=0, row=2)

pattern_set = set(
    [
        "4, 4, 1",
        "1, 9, 1, 5",
        "3",
        "6",
        "9",
        "5, 6, 1",
        "7, 5, 7, 1",
        "10, 8, 9, 5, 3, 1",
        "13",
        "9,7,5",
    ]
)
list_choices = list(pattern_set)
list_choices.sort()
list_choices_var = tkinter.StringVar(value=list_choices)
listbox = tkinter.Listbox(list_frame, height=4, listvariable=list_choices_var)
listbox.grid(column=0, row=0, sticky=(N, S, E, W))


scrollbar = ttk.Scrollbar(list_frame, orient=VERTICAL, command=listbox.yview)
scrollbar.grid(column=1, row=0, sticky=(N, S))
listbox["yscrollcommand"] = scrollbar.set

canvas.grid(column=0, row=1, columnspan=2)

input_label = ttk.Label(frame, text="Or type a pattern")
input_label.grid(column=0, row=3)
input_pattern_var = tkinter.StringVar()
input_pattern_entry = ttk.Entry(
    frame, width=10, textvariable=input_pattern_var
)
input_pattern_entry.grid(column=1, row=3)
input_pattern_entry.focus()

# Until Python 3.7, ttk lacks Spinbox; I'm running 3.6.9.
# Spinbox class polyfill from https://stackoverflow.com/questions/52440314/ttk-spinbox-missing-in-tkinter-ttk/52440947
# Licensed under https://creativecommons.org/licenses/by-sa/4.0/
class Spinbox(ttk.Entry):
    def __init__(self, master=None, **kw):

        ttk.Entry.__init__(self, master, "ttk::spinbox", **kw)

    def set(self, value):
        self.tk.call(self._w, "set", value)


num_hands_label = ttk.Label(frame, text="Number of hands")
num_hands_label.grid(column=0, row=4)
num_hands_var = tkinter.StringVar(value=2)
num_hands_selector = Spinbox(frame, from_=1, to=7, textvariable=num_hands_var,
                             width=2)
num_hands_selector.grid(column=1, row=4)


running_animation = None


def run_pattern(canvas, text):
    global running_animation
    try:
        num_hands = int(num_hands_var.get())
        ss = SiteSwap.from_string(text, num_hands)
        pattern_set.add(ss.pattern_string())
        pattern_list = list(pattern_set)
        pattern_list.sort()
        list_choices_var.set(pattern_list)
        cur_index = pattern_list.index(ss.pattern_string())
        listbox.see(cur_index)
        listbox.selection_clear(0, "end")
        listbox.selection_set(cur_index)
        running_animation = RunningAnimation(
            root, canvas, ss, beats_per_second_var.get()
        )
        current_pattern_text.set(running_animation.pattern_string)
        error_text.set("")
    except InputError as error:
        error_text.set(error)


def on_select_pattern(_):
    indices = listbox.curselection()
    if indices:
        (index,) = indices
        text = listbox.get(index)
        run_pattern(canvas, text)


listbox.bind("<<ListboxSelect>>", on_select_pattern)


def on_select_num_hands(_):
    # This delay lets the value in current_pattern_text update.
    root.after(1, lambda: run_pattern(canvas, current_pattern_text.get()))


num_hands_selector.bind("<<Increment>>", on_select_num_hands)
num_hands_selector.bind("<<Decrement>>", on_select_num_hands)

input_pattern_entry.bind(
    "<Return>", lambda x: run_pattern(canvas, input_pattern_var.get())
)

current_pattern_label = ttk.Label(frame, text="Current pattern")
current_pattern_label.grid(column=0, row=5)
current_pattern_text = tkinter.StringVar()
current_pattern_display = ttk.Label(frame, textvariable=current_pattern_text)
current_pattern_display.grid(column=1, row=5)

speed_slider_label = ttk.Label(frame, text="Animation speed")
speed_slider_label.grid(column=0, row=6)
beats_per_second_var = tkinter.DoubleVar(value=3)
speed_slider = ttk.Scale(
    frame,
    orient=HORIZONTAL,
    length=100,
    from_=0.5,
    to=10,
    variable=beats_per_second_var,
    command=lambda _: running_animation.set_speed(beats_per_second_var.get()),
)
speed_slider.grid(column=1, row=6, columnspan=2)

# TODO: Error text will stretch the window out oddly if it's long; adjust
# centering.
error_text = tkinter.StringVar()
error_display = ttk.Label(frame, textvariable=error_text)
error_display.grid(column=0, row=7, columnspan=3)

exit_button = ttk.Button(frame, text="Exit", command=sys.exit)
exit_button.grid(column=0, row=8, columnspan=3)

BALL_RADIUS = 3
HAND_HALF_W = 6
HAND_H = 4
EDGE_BUFFER = 15
ANIMATION_Y_MIN = EDGE_BUFFER
ANIMATION_Y_MAX = CANVAS_HEIGHT - EDGE_BUFFER
ANIMATION_X_MIN = EDGE_BUFFER
ANIMATION_X_MAX = CANVAS_WIDTH - EDGE_BUFFER
ANIMATION_WIDTH = ANIMATION_X_MAX - ANIMATION_X_MIN
ANIMATION_HEIGHT = ANIMATION_Y_MAX - ANIMATION_Y_MIN

FRAMES_PER_SECOND = 60


class RunningAnimation:
    def __init__(self, root, canvas, ss, beats_per_second):
        self.canvas = canvas
        self.root = root
        self.beats_per_second = beats_per_second
        self.pattern_string = ss.pattern_string()

        self.start_time = time.time()  # Lacks resolution on some systems.
        # start_time_ns = time.time_ns() # Not available until 3.7
        self.animation = ss.animation()
        self.canvas_objects = self.create_canvas_objects()
        (self.x_min, self.y_min, x_max, y_max) = self.animation.bounding_box()
        self.x_scale = ANIMATION_WIDTH / (x_max - self.x_min)
        self.y_scale = ANIMATION_HEIGHT / (y_max - self.y_min)
        self.request_redraw()

    def create_canvas_objects(self):
        self.canvas.delete("all")
        balls = {}
        hands = {}
        # TODO: Unique colors per ball and hand.
        for hand in range(self.animation.num_hands()):
            hands[hand] = self.canvas.create_rectangle(
                -BALL_RADIUS,
                -BALL_RADIUS,
                BALL_RADIUS,
                BALL_RADIUS,
                fill="green",
                outline="blue",
            )
        for ball in range(self.animation.num_balls()):
            balls[ball] = self.canvas.create_rectangle(
                -HAND_HALF_W,
                0,
                HAND_HALF_W,
                HAND_H,
                fill="red",
                outline="purple",
            )
        return {"hands": hands, "balls": balls}

    def coords_to_canvas(self, coords):
        (x, y) = coords
        return (
            (x - self.x_min) * self.x_scale + ANIMATION_X_MIN,
            ANIMATION_Y_MAX - (y - self.y_min) * self.y_scale,
        )

    def redraw(self):
        self.request_redraw()
        cur_time = time.time()
        dt = self.beats_per_second * (cur_time - self.start_time)
        self.draw(dt)

    def request_redraw(self):
        self.root.after(int(1000 / FRAMES_PER_SECOND), lambda: self.redraw())

    def draw(self, at_time):
        for hand in range(self.animation.num_hands()):
            (x, y) = self.coords_to_canvas(
                self.animation.hand_location_at(hand, at_time)
            )
            x_0 = x - HAND_HALF_W
            y_0 = y
            x_1 = x + HAND_HALF_W
            y_1 = y + HAND_H
            self.canvas.coords(
                self.canvas_objects["hands"][hand], (x_0, y_0, x_1, y_1)
            )
        for ball in range(self.animation.num_balls()):
            (x, y) = self.coords_to_canvas(
                self.animation.ball_location_at(ball, at_time)
            )
            x_0 = x - BALL_RADIUS
            y_0 = y - BALL_RADIUS
            x_1 = x + BALL_RADIUS
            y_1 = y + BALL_RADIUS
            self.canvas.coords(
                self.canvas_objects["balls"][ball], (x_0, y_0, x_1, y_1)
            )

    def set_speed(self, beats_per_second):
        """Because rendering is based on a fixed start time, in order to smooth
        out timing variations in draw calls, if we just change the speed, we'll
        change where we are in the cycle.  That leads to lots of flickering as
        the slider moves.  To fix this, we change the start time so as to
        maintain where we are in the cycle."""
        if beats_per_second != self.beats_per_second:
            now = time.time()
            cycle_time = now - self.start_time
            cycle_beats = cycle_time * self.beats_per_second
            new_cycle_time = cycle_beats / beats_per_second
            self.start_time = now - new_cycle_time
            self.beats_per_second = beats_per_second


# todo: Choose from pattern set instead of using a string?
run_pattern(canvas, "9,7,5")
root.mainloop()
