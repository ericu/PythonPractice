#!/usr/bin/python3

import tkinter
from tkinter import ttk, N, S, E, W, HORIZONTAL, VERTICAL
import sys
import time

from siteswap import SiteSwap, InputError

root = tkinter.Tk()
root.title("Test Window")

frame = ttk.Frame(root, width=200)
frame.grid(column=0, row=0)

label = ttk.Label(frame, text="SiteSwap Animator")
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
        "1,9,1,5",
        "3",
        "6",
        "9",
        "5, 6, 1",
        "7, 5, 7, 1",
        "10, 8, 9, 5, 3, 1",
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

input_label = ttk.Label(frame, text="Or input pattern")
input_label.grid(column=0, row=3)
input_pattern_var = tkinter.StringVar()
input_pattern_entry = ttk.Entry(
    frame, width=10, textvariable=input_pattern_var
)
input_pattern_entry.grid(column=1, row=3)
input_pattern_entry.focus()

# Until Python 3.7, ttk lacks Spinbox.
class Spinbox(ttk.Entry):
    def __init__(self, master=None, **kw):

        ttk.Entry.__init__(self, master, "ttk::spinbox", **kw)

    def set(self, value):
        self.tk.call(self._w, "set", value)


num_hands_label = ttk.Label(frame, text="Number of hands")
num_hands_label.grid(column=0, row=4)
num_hands_var = tkinter.StringVar(value=2)
num_hands_selector = Spinbox(frame, from_=1, to=7, textvariable=num_hands_var)
num_hands_selector.grid(column=1, row=4)


def run_pattern(text):
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
        start_animation(ss)
        error_text.set("")
    except InputError as error:
        error_text.set(error)


def on_select_pattern(_):
    indices = listbox.curselection()
    if indices:
        (index,) = indices
        text = listbox.get(index)
        run_pattern(text)


listbox.bind("<<ListboxSelect>>", on_select_pattern)


def on_select_num_hands(_):
    # This delay lets the value in current_pattern_text update.
    root.after(1, lambda: run_pattern(current_pattern_text.get()))


num_hands_selector.bind("<<Increment>>", on_select_num_hands)
num_hands_selector.bind("<<Decrement>>", on_select_num_hands)


def run_input_pattern():
    return run_pattern(input_pattern_var.get())


input_pattern_entry.bind("<Return>", lambda x: run_input_pattern())

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
    to=5,
    variable=beats_per_second_var,
)
speed_slider.grid(column=1, row=6, columnspan=2)

# TODO: Error text will stretch the window out oddly if it's long; adjust
# centering.
error_text = tkinter.StringVar()
error_display = ttk.Label(frame, textvariable=error_text)
error_display.grid(column=0, row=7, columnspan=3)

exit_button = ttk.Button(frame, text="Exit", command=sys.exit)
exit_button.grid(column=0, row=8, columnspan=3)
exit_button.bind("<Enter>", lambda e: exit_button.configure(text="Click me!"))
exit_button.bind("<Leave>", lambda e: exit_button.configure(text="Exit"))

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


def create_canvas_objects(animation):
    canvas.delete("all")
    balls = {}
    hands = {}
    # TODO: Unique colors per ball and hand.
    for hand in range(animation.num_hands()):
        hands[hand] = canvas.create_rectangle(
            -BALL_RADIUS,
            -BALL_RADIUS,
            BALL_RADIUS,
            BALL_RADIUS,
            fill="green",
            outline="blue",
        )
    for ball in range(animation.num_balls()):
        balls[ball] = canvas.create_rectangle(
            -HAND_HALF_W, 0, HAND_HALF_W, HAND_H, fill="red", outline="purple"
        )
    return {"hands": hands, "balls": balls}


def start_animation(ss):
    current_pattern_text.set(ss.pattern_string())
    start_time = time.time()  # Supposedly lacks resolution on some systems.
    # start_time_ns = time.time_ns() # Not available until 3.7
    animation = ss.animation()
    canvas_objects = create_canvas_objects(animation)
    (x_min, y_min, x_max, y_max) = animation.bounding_box()
    x_scale = ANIMATION_WIDTH / (x_max - x_min)
    y_scale = ANIMATION_HEIGHT / (y_max - y_min)

    def coords_to_canvas(coords):
        (x, y) = coords
        return (
            (x - x_min) * x_scale + ANIMATION_X_MIN,
            ANIMATION_Y_MAX - (y - y_min) * y_scale,
        )

    def redraw():
        request_redraw()
        cur_time = time.time()
        dt = beats_per_second_var.get() * (cur_time - start_time)
        draw(animation, dt, canvas_objects)

    def request_redraw():
        # todo: This could use a frame counter to figure out how long to wait,
        # in case we're drifting behind.
        root.after(int(1000 / FRAMES_PER_SECOND), redraw)

    def draw(animation, at_time, objects):
        for hand in range(animation.num_hands()):
            (x, y) = coords_to_canvas(
                animation.hand_location_at(hand, at_time)
            )
            x_0 = x - HAND_HALF_W
            y_0 = y
            x_1 = x + HAND_HALF_W
            y_1 = y + HAND_H
            canvas.coords(objects["hands"][hand], (x_0, y_0, x_1, y_1))
        for ball in range(animation.num_balls()):
            (x, y) = coords_to_canvas(
                animation.ball_location_at(ball, at_time)
            )
            x_0 = x - BALL_RADIUS
            y_0 = y - BALL_RADIUS
            x_1 = x + BALL_RADIUS
            y_1 = y + BALL_RADIUS
            canvas.coords(objects["balls"][ball], (x_0, y_0, x_1, y_1))

    request_redraw()


# todo: Choose from pattern set instead of using a string?
run_pattern("4,4,1")
root.mainloop()
