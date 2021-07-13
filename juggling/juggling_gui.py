#!/usr/bin/python3

from tkinter import *
from tkinter import ttk

import sys
import siteswap
import time

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

def copy():
  outputText.set(inputText.get())

root.bind("<Return>", lambda x: copy())

outputText = StringVar()
outputDisplay = ttk.Label(frame, textvariable=outputText, width=10)
outputDisplay.grid(column=3, row=2)

copyButton = ttk.Button(frame, text = "Copy", command = copy)
copyButton.grid(column=2, row=2)
 
exitButton = ttk.Button(frame, text = "Exit", command = sys.exit)
exitButton.grid(column=1, row=3)
exitButton.bind('<Enter>', lambda e: exitButton.configure(text='Click me!'))
exitButton.bind('<Leave>', lambda e: exitButton.configure(text='Exit'))
 
animation = siteswap.SiteSwap([3]).animation()
num_balls = animation.num_balls()
num_hands = animation.num_hands()

BALL_RADIUS = 3
HAND_HALF_W = 6
HAND_H = 4

CANVAS_CENTER_X = CANVAS_WIDTH / 2
CANVAS_CENTER_Y = CANVAS_HEIGHT / 2
FRAMES_PER_BEAT = 60
BEATS_PER_SECOND = 2

def draw(animation, time):
  for hand in range(num_hands):
    (x, y) = animation.hand_location_at(hand, time)
    x += CANVAS_CENTER_X
    y = CANVAS_CENTER_Y - y
    canvas.create_rectangle(x - HAND_HALF_W, y, x + HAND_HALF_W, y + HAND_H,
                            fill='yellow', outline='blue')
  for ball in range(num_balls):
    (x, y) = animation.ball_location_at(ball, time)
    x += CANVAS_CENTER_X
    y = CANVAS_CENTER_Y - y
    canvas.create_oval(x - BALL_RADIUS, y - BALL_RADIUS,
                       x + BALL_RADIUS, y + BALL_RADIUS,
                       fill='red', outline='purple')

start_time = time.time()
#start_time_ns = time.time_ns() # Not available until 3.7

def redraw():
  request_redraw()
  cur_time = time.time()
  dt = BEATS_PER_SECOND * (cur_time - start_time)
  draw(animation, dt)

def request_redraw():
  # TODO: This could use a frame counter to figure out how long to wait, in case
  # we're drifting behind.
  root.after(int(1000 / BEATS_PER_SECOND / FRAMES_PER_BEAT), redraw)

request_redraw()
root.mainloop()
