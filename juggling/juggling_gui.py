#!/usr/bin/env python3

from tkinter import ttk, N, S, E, W, HORIZONTAL, VERTICAL
import sys
import time
import tkinter as tk

import numpy as np

from siteswap import SiteSwap, InputError

BALL_RADIUS = 5
HAND_HALF_W = 10
HAND_H = 8
EDGE_BUFFER = 20

INITIAL_CANVAS_WIDTH = 300
INITIAL_CANVAS_HEIGHT = 300

FRAMES_PER_SECOND = 60


def create_gui():
    running_animation = None

    root = tk.Tk()
    root.title("Juggling SiteSwap Animator")
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(0, weight=1)

    frame = ttk.Frame(root, width=200, borderwidth=3)
    frame.grid(column=0, row=0, sticky=N + S + E + W)
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_columnconfigure(1, weight=1)
    frame.grid_rowconfigure(1, weight=1)

    label = ttk.Label(frame, text="This program animates vanilla siteswaps.")
    label.grid(column=0, row=0, columnspan=2)

    canvas = tk.Canvas(
        frame,
        bg="black",
        height=INITIAL_CANVAS_HEIGHT,
        width=INITIAL_CANVAS_WIDTH,
    )
    canvas.grid(column=0, row=1, columnspan=2, sticky=N + S + E + W)

    list_frame = ttk.Frame(frame)
    list_frame.grid(column=1, row=2)

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
            "9, 7, 5",
        ]
    )
    list_choices = list(pattern_set)
    list_choices.sort()
    list_choices_var = tk.StringVar(value=list_choices)
    listbox = tk.Listbox(list_frame, height=4, listvariable=list_choices_var)
    listbox.grid(column=0, row=0)

    scrollbar = ttk.Scrollbar(
        list_frame, orient=VERTICAL, command=listbox.yview
    )
    scrollbar.grid(column=1, row=0, sticky=N + S)
    listbox["yscrollcommand"] = scrollbar.set

    canvas.grid(column=0, row=1, columnspan=2)

    input_label = ttk.Label(frame, text="Or type a pattern")
    input_label.grid(column=0, row=3)
    input_pattern_var = tk.StringVar()
    input_pattern_entry = ttk.Entry(
        frame, width=10, textvariable=input_pattern_var
    )
    input_pattern_entry.grid(column=1, row=3)
    input_pattern_entry.focus()

    # Until Python 3.7, ttk lacks Spinbox; I'm running 3.6.9.
    # Spinbox class polyfill from
    # https://stackoverflow.com/questions/52440314/ttk-spinbox-missing-in-tkinter-ttk/52440947
    # Licensed under https://creativecommons.org/licenses/by-sa/4.0/
    class Spinbox(ttk.Entry):
        def __init__(self, master=None, **kw):

            ttk.Entry.__init__(self, master, "ttk::spinbox", **kw)

        def set(self, value):
            self.tk.call(self._w, "set", value)

    num_hands_label = ttk.Label(frame, text="Number of hands")
    num_hands_label.grid(column=0, row=4)
    num_hands_var = tk.StringVar(value=2)
    num_hands_selector = Spinbox(
        frame, from_=1, to=7, textvariable=num_hands_var, width=2
    )
    num_hands_selector.grid(column=1, row=4)

    def run_pattern(canvas, text):
        nonlocal running_animation
        try:
            num_hands = int(num_hands_var.get())
            siteswap = SiteSwap.from_string(text, num_hands)
            if siteswap.num_balls > 640:
                raise InputError('"640 balls out to be enough for anybody."')
            pattern_set.add(siteswap.pattern_string())
            pattern_list = list(pattern_set)
            pattern_list.sort()
            list_choices_var.set(pattern_list)
            cur_index = pattern_list.index(siteswap.pattern_string())
            listbox.see(cur_index)
            listbox.selection_clear(0, "end")
            listbox.selection_set(cur_index)
            new_animation = RunningAnimation(
                root,
                canvas,
                siteswap,
                beats_per_second_var.get(),
                (canvas.winfo_width(), canvas.winfo_height()),
            )
            if running_animation:
                running_animation.stop()
            running_animation = new_animation
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

    current_num_hands = num_hands_var.get()

    def on_select_num_hands(_):
        def helper():
            nonlocal current_num_hands
            if num_hands_var.get() != current_num_hands:
                current_num_hands = num_hands_var.get()
                run_pattern(canvas, current_pattern_text.get())

        # This delay lets the value in num_hands_var update.
        root.after(1, helper)

    num_hands_selector.bind("<<Increment>>", on_select_num_hands)
    num_hands_selector.bind("<<Decrement>>", on_select_num_hands)

    def run_input_pattern():
        pattern = input_pattern_var.get()
        input_pattern_entry.delete(0, "end")
        run_pattern(canvas, pattern)

    input_pattern_entry.bind("<Return>", lambda _: run_input_pattern())

    current_pattern_label = ttk.Label(frame, text="Current pattern")
    current_pattern_label.grid(column=0, row=5)
    current_pattern_text = tk.StringVar()
    current_pattern_display = ttk.Label(
        frame, textvariable=current_pattern_text
    )
    current_pattern_display.grid(column=1, row=5)

    speed_slider_label = ttk.Label(frame, text="Animation speed")
    speed_slider_label.grid(column=0, row=6)
    beats_per_second_var = tk.DoubleVar(value=3)
    speed_slider = ttk.Scale(
        frame,
        orient=HORIZONTAL,
        length=100,
        from_=0.5,
        to=10,
        variable=beats_per_second_var,
        command=lambda _: running_animation.set_speed(
            beats_per_second_var.get()
        ),
    )
    speed_slider.grid(column=1, row=6, columnspan=2)

    error_text = tk.StringVar()
    error_display = ttk.Label(frame, textvariable=error_text)
    error_display.grid(column=0, row=7, columnspan=3)

    exit_button = ttk.Button(frame, text="Exit", command=sys.exit)
    exit_button.grid(column=0, row=8, columnspan=3)

    canvas.bind(
        "<Configure>", lambda e: running_animation.resize([e.width, e.height])
    )
    return (root, canvas, run_pattern)


class RunningAnimation:
    def __init__(
        self, root, canvas, siteswap, beats_per_second, canvas_dimensions
    ):
        self.stopped = False
        self.canvas = canvas
        self.root = root
        self.beats_per_second = beats_per_second
        self.pattern_string = siteswap.pattern_string()
        self.canvas_dimensions = None

        self.start_time = time.time()  # Lacks resolution on some systems.
        # start_time_ns = time.time_ns() # Not available until 3.7
        self.animation = siteswap.animation()
        self.canvas_objects = self.create_canvas_objects()

        self.resize(canvas_dimensions)
        self.request_redraw()

    def resize(self, canvas_dimensions):
        if (self.canvas_dimensions is None) or (
            self.canvas_dimensions != canvas_dimensions
        ).any():

            (
                self.animation_minima,
                animation_maxima,
            ) = self.animation.bounding_box()
            self.canvas_dimensions = np.array(canvas_dimensions)
            edge_buffer = np.array([EDGE_BUFFER, EDGE_BUFFER])
            self.drawing_minima = edge_buffer
            self.drawing_maxima = self.canvas_dimensions - edge_buffer
            drawing_size = self.drawing_maxima - self.drawing_minima
            self.scale = drawing_size / (
                animation_maxima - self.animation_minima
            )

    ball_colors = [
        "sky blue",
        "medium orchid",
        "salmon",
        "LemonChiffon2",
        "thistle",
        "pink",
        "PeachPuff2",
        "honeydew3",
        "gold",
        "lawn green",
        "olive drab",
        "coral",
        "light goldenrod",
        "red",
        "turquoise",
    ]

    def stop(self):
        self.stopped = True

    def create_canvas_objects(self):
        self.canvas.delete("all")
        balls = {}
        hands = {}
        for hand in range(self.animation.num_hands()):
            hands[hand] = self.canvas.create_rectangle(
                -HAND_HALF_W,
                0,
                HAND_HALF_W,
                HAND_H,
                fill="green",
                outline="blue",
            )
        for ball in range(self.animation.num_balls()):
            balls[ball] = self.canvas.create_oval(
                -BALL_RADIUS,
                -BALL_RADIUS,
                BALL_RADIUS,
                BALL_RADIUS,
                fill=self.ball_colors[ball % len(self.ball_colors)],
            )
        return {"hands": hands, "balls": balls}

    def coords_to_canvas(self, coords):
        delta_x, delta_y = (coords - self.animation_minima) * self.scale
        return (
            delta_x + self.drawing_minima[0],
            self.drawing_maxima[1] - delta_y,
        )

    def redraw(self):
        if not self.stopped:
            self.request_redraw()
            cur_time = time.time()
            d_t = self.beats_per_second * (cur_time - self.start_time)
            self.draw(d_t)

    def request_redraw(self):
        self.root.after(int(1000 / FRAMES_PER_SECOND), self.redraw)

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


def main():
    (root, canvas, run_pattern_from_string) = create_gui()
    # todo: Choose from pattern set instead of using a string?
    run_pattern_from_string(canvas, "9, 7, 5")
    root.mainloop()


if __name__ == "__main__":
    main()
