#!/usr/bin/python3
import sys

def horizontalLine(length):
  return (length * " ---") + '\n'

def boardLine(dataLine):
  return ''.join(map(lambda d: "| " + str(d) + " ", dataLine)) + "|\n"

def board(data):
  lineLen = len(data[0])
  return (
    horizontalLine(lineLen) +
    ''.join(map(lambda dataLine: boardLine(dataLine) + horizontalLine(lineLen), data)))

sampleData = [
  [ 1, 2, 2 ],
  [ 0, 0, 2 ],
  [ 1, 2, 1 ]
]

def lineAllSame(line):
  if line[0] == line[1] and line[1] == line[2]:
    return (True, line[0])
  return (False, None)

def horizontalMatch(board):
  for i in range(0, 3):
    (t, who) = lineAllSame(board[i])
    if t and who != 0:
      return (t, who)
  return (False, None)

def invert(board):
  return [[board[x][y] for x in range(3)] for y in range(3)]

def verticalMatch(board):
  return horizontalMatch(invert(board))

def diagonalMatch(board):
  (t, who) = lineAllSame([board[i][i] for i in range(3)])
  if t:
    return (t, who)
  return lineAllSame([board[2 - i][i] for i in range(3)])

print((sampleData))

def match(board):
  for f in [horizontalMatch, verticalMatch, diagonalMatch]:
    (t, who) = f(board)
    if t:
      return (t, who)
  return (False, None)

print('H?', horizontalMatch(sampleData))
print('V?', verticalMatch(sampleData))
print('D?', diagonalMatch(sampleData))
print('M?', match(sampleData))

