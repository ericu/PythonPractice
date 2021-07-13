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
 
animation = siteswap.SiteSwap([4,5,3]).animation()
num_balls = animation.num_balls()
num_hands = animation.num_hands()

BALL_RADIUS = 3
HAND_HALF_W = 6
HAND_H = 4
ANIMATION_BOTTOM = CANVAS_HEIGHT - HAND_H

CANVAS_CENTER_X = CANVAS_WIDTH / 2
CANVAS_CENTER_Y = CANVAS_HEIGHT / 2
FRAMES_PER_BEAT = 60
BEATS_PER_SECOND = 2

def create_canvas_objects(animation):
  balls = {}
  hands = {}
  for hand in range(animation.num_hands()):
    hands[hand] = canvas.create_rectangle(-BALL_RADIUS, -BALL_RADIUS,
                                          BALL_RADIUS, BALL_RADIUS,
                                          fill='yellow', outline='blue')
  for ball in range(animation.num_balls()):
    balls[ball] = canvas.create_rectangle(-HAND_HALF_W, 0, HAND_HALF_W, HAND_H,
                                          fill='red', outline='purple')
  return { 'hands': hands, 'balls': balls }
    

def draw(animation, time, objects):
  for hand in range(num_hands):
    (x, y) = animation.hand_location_at(hand, time)
    x += CANVAS_CENTER_X
    y = ANIMATION_BOTTOM - y
    x0 = x - HAND_HALF_W
    y0 = y
    x1 = x + HAND_HALF_W
    y1 = y + HAND_H
    canvas.coords(objects['hands'][hand], (x0, y0, x1, y1))
  for ball in range(num_balls):
    (x, y) = animation.ball_location_at(ball, time)
    x += CANVAS_CENTER_X
    y = ANIMATION_BOTTOM - y
    x0 = x - BALL_RADIUS
    y0 = y - BALL_RADIUS
    x1 = x + BALL_RADIUS
    y1 = y + BALL_RADIUS
    canvas.coords(objects['balls'][ball], (x0, y0, x1, y1))

start_time = time.time()
#start_time_ns = time.time_ns() # Not available until 3.7

canvas_objects = create_canvas_objects(animation)


def redraw():
  request_redraw()
  cur_time = time.time()
  dt = BEATS_PER_SECOND * (cur_time - start_time)
  draw(animation, dt, canvas_objects)

def request_redraw():
  # TODO: This could use a frame counter to figure out how long to wait, in case
  # we're drifting behind.
  root.after(int(1000 / BEATS_PER_SECOND / FRAMES_PER_BEAT), redraw)

request_redraw()
root.mainloop()
