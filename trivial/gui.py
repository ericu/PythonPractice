#!/usr/bin/env python3

from tkinter import *
from tkinter import ttk

import sys

root = Tk()
root.title("Test Window")

frame = ttk.Frame(root)
frame.pack()

label = ttk.Label(frame, text="Testing GUI")
label.pack()

canvas = Canvas(frame, bg="black", height=100, width=100)
canvas.pack()

inputText = StringVar()
inputEntry = ttk.Entry(frame, width=10, textvariable=inputText)
inputEntry.pack()
inputEntry.focus()


def copy():
    outputText.set(inputText.get())


root.bind("<Return>", lambda x: copy())

outputText = StringVar()
outputDisplay = ttk.Label(frame, textvariable=outputText)
outputDisplay.pack()

copyButton = ttk.Button(frame, text="Copy", command=copy)
copyButton.pack(padx=3, pady=3)

exitButton = ttk.Button(frame, text="Exit", command=sys.exit)
exitButton.pack(padx=3, pady=3)
exitButton.bind("<Enter>", lambda e: exitButton.configure(text="Click me!"))
exitButton.bind("<Leave>", lambda e: exitButton.configure(text="Exit"))

root.mainloop()
