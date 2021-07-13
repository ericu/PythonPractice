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
 
label = ttk.Label(frame, text = "Testing GUI")
label.grid(column=2, row=0)
 
CANVAS_WIDTH = 100
CANVAS_HEIGHT = 100
canvas = Canvas(frame, bg="black", height=CANVAS_HEIGHT, width=CANVAS_WIDTH)
canvas.grid(column=2, row=1)

inputText = StringVar()
inputEntry = ttk.Entry(frame, width=10, textvariable=inputText)
inputEntry.grid(column=1, row=2)
inputEntry.focus()

def run_input_pattern():
  try:
    ss = SiteSwap.from_string(inputText.get())
    start_animation(ss)
    errorText.set('')
  except InputError as error:
    errorText.set(error.message)

root.bind("<Return>", lambda x: run_input_pattern())

outputText = StringVar()
outputDisplay = ttk.Label(frame, textvariable=outputText, width=10)
outputDisplay.grid(column=3, row=2)
errorText = StringVar()
errorDisplay = ttk.Label(frame, textvariable=errorText)
errorDisplay.grid(column=1, row=3, columnspan=3)

copyButton = ttk.Button(frame, text = "Run", command = run_input_pattern)
copyButton.grid(column=2, row=2)
 
exitButton = ttk.Button(frame, text = "Exit", command = sys.exit)
exitButton.grid(column=2, row=4)
exitButton.bind('<Enter>', lambda e: exitButton.configure(text='Click me!'))
exitButton.bind('<Leave>', lambda e: exitButton.configure(text='Exit'))
 
BALL_RADIUS = 3
HAND_HALF_W = 6
HAND_H = 4
ANIMATION_BOTTOM = CANVAS_HEIGHT - HAND_H

CANVAS_CENTER_X = CANVAS_WIDTH / 2
CANVAS_CENTER_Y = CANVAS_HEIGHT / 2
FRAMES_PER_BEAT = 30
BEATS_PER_SECOND = 2

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
  outputText.set(','.join(map(str, ss.pattern)))
  start_time = time.time() # Supposedly lacks resolution on some systems.
  #start_time_ns = time.time_ns() # Not available until 3.7
  animation = ss.animation()
  canvas_objects = create_canvas_objects(animation)

  def redraw():
    request_redraw()
    cur_time = time.time()
    dt = BEATS_PER_SECOND * (cur_time - start_time)
    draw(animation, dt, canvas_objects)

  def request_redraw():
    # todo: This could use a frame counter to figure out how long to wait, in
    # case we're drifting behind.
    root.after(int(1000 / BEATS_PER_SECOND / FRAMES_PER_BEAT), redraw)

  def draw(animation, time, objects):
    for hand in range(animation.num_hands()):
      (x, y) = animation.hand_location_at(hand, time)
      x += CANVAS_CENTER_X
      y = ANIMATION_BOTTOM - y
      x0 = x - HAND_HALF_W
      y0 = y
      x1 = x + HAND_HALF_W
      y1 = y + HAND_H
      canvas.coords(objects['hands'][hand], (x0, y0, x1, y1))
    for ball in range(animation.num_balls()):
      (x, y) = animation.ball_location_at(ball, time)
      x += CANVAS_CENTER_X
      y = ANIMATION_BOTTOM - y
      x0 = x - BALL_RADIUS
      y0 = y - BALL_RADIUS
      x1 = x + BALL_RADIUS
      y1 = y + BALL_RADIUS
      canvas.coords(objects['balls'][ball], (x0, y0, x1, y1))

  request_redraw()


start_animation(SiteSwap([7,5,7,1]))
root.mainloop()
