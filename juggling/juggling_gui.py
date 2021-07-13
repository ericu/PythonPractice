#!/usr/bin/python3

from tkinter import *
from tkinter import ttk

import sys
import siteswap

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
for hand in range(num_hands):
  (x, y) = animation.hand_location_at(hand, 0)
  x += CANVAS_CENTER_X
  y = CANVAS_CENTER_Y - y
  canvas.create_rectangle(x - HAND_HALF_W, y, x + HAND_HALF_W, y + HAND_H,
                          fill='yellow', outline='blue')
for ball in range(num_balls):
  (x, y) = animation.ball_location_at(ball, 0)
  x += CANVAS_CENTER_X
  y = CANVAS_CENTER_Y - y
  canvas.create_oval(x - BALL_RADIUS, y - BALL_RADIUS,
                     x + BALL_RADIUS, y + BALL_RADIUS,
                     fill='red', outline='purple')

root.mainloop()
