#!/usr/bin/python3

from tkinter import *
from tkinter import ttk
import sys
import time

from siteswap import SiteSwap, InputError

root = Tk()
root.title("Test Window")

frame = ttk.Frame(root, width=200)
frame.grid(column=0, row=0)
 
label = ttk.Label(frame, text = "SiteSwap Animator")
label.grid(column=0, row=0, columnspan=2)
 
CANVAS_WIDTH = 300
CANVAS_HEIGHT = 300
canvas = Canvas(frame, bg="black", height=CANVAS_HEIGHT, width=CANVAS_WIDTH)
canvas.grid(column=0, row=1, columnspan=2)

list_frame = ttk.Frame(frame)
list_frame.grid(column=1, row=2, sticky=(N,S,E,W))

list_label = ttk.Label(frame, text="Choose pattern")
list_label.grid(column=0, row=2)

pattern_set = set(["4, 4, 1",
                   "3",
                   "6",
                   "9",
                   "5, 6, 1",
                   "7, 5, 7, 1",
                   "10, 8, 9, 5, 3, 1"])
list_choices = list(pattern_set)
list_choices.sort()
list_choices_var = StringVar(value=list_choices)
listbox = Listbox(list_frame, height=4, listvariable=list_choices_var)
listbox.grid(column=0, row=0, sticky=(N,S,E,W))
def on_select_pattern(_):
  indices = listbox.curselection()
  if indices:
    (index,) = indices
    text = listbox.get(index)
    run_pattern(text)
listbox.bind("<<ListboxSelect>>", on_select_pattern)

scrollbar = ttk.Scrollbar(list_frame, orient=VERTICAL, command=listbox.yview)
scrollbar.grid(column=1, row=0, sticky=(N,S))
listbox['yscrollcommand'] = scrollbar.set

canvas.grid(column=0, row=1, columnspan=2)

input_label = ttk.Label(frame, text="Or input pattern")
input_label.grid(column=0, row=3)
input_text = StringVar()
input_entry = ttk.Entry(frame, width=10, textvariable=input_text)
input_entry.grid(column=1, row=3)
input_entry.focus()

def run_pattern(text):
  try:
    ss = SiteSwap.from_string(text)
    pattern_set.add(ss.pattern_string())
    list_choices = list(pattern_set)
    list_choices.sort()
    list_choices_var.set(list_choices)
    cur_index = list_choices.index(ss.pattern_string())
    listbox.see(cur_index)
    listbox.selection_clear(0, 'end')
    listbox.selection_set(cur_index)
    start_animation(ss)
    error_text.set('')
  except InputError as error:
    error_text.set(error.message)

def run_input_pattern():
  return run_pattern(input_text.get())

root.bind("<Return>", lambda x: run_input_pattern())

current_pattern_label = ttk.Label(frame, text="Current pattern")
current_pattern_label.grid(column=0, row=4)
current_pattern_text = StringVar()
current_pattern_display = ttk.Label(frame, textvariable=current_pattern_text)
current_pattern_display.grid(column=1, row=4)

speed_slider_label = ttk.Label(frame, text="Animation speed")
speed_slider_label.grid(column=0, row=5)
beats_per_second_var = DoubleVar(value=3)
speed_slider = ttk.Scale(frame, orient=HORIZONTAL, length=100, from_=0.5, to=5,
                         variable=beats_per_second_var)
speed_slider.grid(column=1, row=5, columnspan=2)

# TODO: Error text will stretch the window out oddly if it's long; adjust
# centering.
error_text = StringVar()
error_display = ttk.Label(frame, textvariable=error_text)
error_display.grid(column=0, row=6, columnspan=3)

exit_button = ttk.Button(frame, text = "Exit", command = sys.exit)
exit_button.grid(column=0, row=7, columnspan=3)
exit_button.bind('<Enter>', lambda e: exit_button.configure(text='Click me!'))
exit_button.bind('<Leave>', lambda e: exit_button.configure(text='Exit'))
 
BALL_RADIUS = 3
HAND_HALF_W = 6
HAND_H = 4
ANIMATION_Y_MIN = CANVAS_HEIGHT - HAND_H
ANIMATION_Y_MAX = BALL_RADIUS
ANIMATION_X_MIN = BALL_RADIUS
ANIMATION_X_MAX = CANVAS_WIDTH - BALL_RADIUS
ANIMATION_WIDTH = ANIMATION_X_MAX - ANIMATION_X_MIN
ANIMATION_HEIGHT = ANIMATION_Y_MAX - ANIMATION_Y_MIN

FRAMES_PER_SECOND = 60

def create_canvas_objects(animation):
  canvas.delete("all")
  balls = {}
  hands = {}
  for hand in range(animation.num_hands()):
    hands[hand] = canvas.create_rectangle(-BALL_RADIUS, -BALL_RADIUS,
                                          BALL_RADIUS, BALL_RADIUS,
                                          fill='green', outline='blue')
  for ball in range(animation.num_balls()):
    balls[ball] = canvas.create_rectangle(-HAND_HALF_W, 0, HAND_HALF_W, HAND_H,
                                          fill='red', outline='purple')
  return { 'hands': hands, 'balls': balls }
    


def start_animation(ss):
  current_pattern_text.set(ss.pattern_string())
  start_time = time.time() # Supposedly lacks resolution on some systems.
  #start_time_ns = time.time_ns() # Not available until 3.7
  animation = ss.animation()
  canvas_objects = create_canvas_objects(animation)
  (x_min, y_min, x_max, y_max) = animation.bounding_box()
  print(x_min, y_min, x_max, y_max)
  x_scale = ANIMATION_WIDTH / (x_max - x_min)
  y_scale = ANIMATION_HEIGHT / (y_min - y_max) # invert
  def coord_to_canvas(anim_value, anim_min, scale, canvas_min):
    print('coord_to_canvas', anim_value, anim_min, scale, canvas_min)
    print('output', (anim_value - anim_min) * scale + canvas_min)
    return (anim_value - anim_min) * scale + canvas_min
  def coords_to_canvas(coords):
    (x, y) = coords
    return (coord_to_canvas(x, x_min, x_scale, ANIMATION_X_MIN),
            coord_to_canvas(y, y_min, y_scale, ANIMATION_Y_MAX))

  def redraw():
    request_redraw()
    cur_time = time.time()
    dt = beats_per_second_var.get() * (cur_time - start_time)
    draw(animation, dt, canvas_objects)

  def request_redraw():
    # todo: This could use a frame counter to figure out how long to wait, in
    # case we're drifting behind.
    root.after(int(1000 / FRAMES_PER_SECOND), redraw)

  def draw(animation, time, objects):
    for hand in range(animation.num_hands()):
      (cx, cy) = animation.hand_location_at(hand, time)
      (x, y) = coords_to_canvas(animation.hand_location_at(hand, time))
      print(cx, cy, ' became ', x, y)
      #sys.exit()
      x0 = x - HAND_HALF_W
      y0 = y
      x1 = x + HAND_HALF_W
      y1 = y + HAND_H
      canvas.coords(objects['hands'][hand], (x0, y0, x1, y1))
    for ball in range(animation.num_balls()):
      (x, y) = coords_to_canvas(animation.ball_location_at(ball, time))
      x0 = x - BALL_RADIUS
      y0 = y - BALL_RADIUS
      x1 = x + BALL_RADIUS
      y1 = y + BALL_RADIUS
      canvas.coords(objects['balls'][ball], (x0, y0, x1, y1))

  request_redraw()


# TODO: Choose from pattern set.
start_animation(SiteSwap([4,4,1]))
root.mainloop()
