#!/usr/bin/python3
import sys

val = input("input board size > ")
# TODO: Catch conversion error.
size = int(val)
if size <= 0:
  print('Board size must be an integer greater than zero')
  sys.exit(-1)
print("Got size: %d" % size)

def horizontalLine(length):
  return (length * " ---") + '\n'

def boardLine(dataLine):
  return ''.join(map(lambda d: "| " + d + " ", dataLine)) + "|\n"

def fakeDataLine(size):
  return "." * size

def fakeData(size):
  return [fakeDataLine(size) for a in range(size)]

def board(data):
  lineLen = len(data[0])
  return (
    horizontalLine(lineLen) +
    ''.join(map(lambda dataLine: boardLine(dataLine) + horizontalLine(lineLen), data)))

print(board(fakeData(size)))
