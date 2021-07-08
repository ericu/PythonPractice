#!/usr/bin/python3
import sys
from enum import Enum

def drawHLine(length):
  return (length * " ---") + '\n'

def drawDataLine(dataLine):
  return ''.join(map(lambda d: "| " + showPlayer(d) + " ", dataLine)) + "|\n"

def drawBoard(data):
  lineLen = len(data[0])
  return (
    drawHLine(lineLen) +
    ''.join(map(lambda dataLine: drawDataLine(dataLine) + drawHLine(lineLen), data)))

def printBoard(board):
  print(drawBoard(board))

NO_PLAYER = 0
def showPlayer(index):
  return " XO"[index]

def winningLine(line):
  if line[0] == line[1] and line[1] == line[2] and line[0] != NO_PLAYER:
    return line[0]
  return None

def horizontalWin(board):
  for i in range(0, 3):
    who = winningLine(board[i])
    if who != None:
      return who
  return None

def invert(board):
  return [[board[x][y] for x in range(3)] for y in range(3)]

def verticalWin(board):
  return horizontalWin(invert(board))

def diagonalWin(board):
  who = winningLine([board[i][i] for i in range(3)])
  if who != None:
    return who
  return winningLine([board[2 - i][i] for i in range(3)])

def currentWinner(board):
  for f in [horizontalWin, verticalWin, diagonalWin]:
    who = f(board)
    if who != None:
      return who
  return None

def copyBoard(board):
  return [row.copy() for row in board]

class Result(Enum):
  TIE = 0
  WIN = 1
  LOSS = 2

def bestResultAndMove(player, board):
  assert currentWinner(board) == None
  assert not boardFull(board)
  bestForPlayer = (-1, -1, Result.LOSS) # We'll never use these coords.
  for row in range(3):
    for col in range(3):
      if board[row][col] == NO_PLAYER: # it's a legal move
        newBoard = copyBoard(board)
        newBoard[row][col] = player
        winner = currentWinner(newBoard) 
        if winner != None:
          assert winner == player
          return (row, col, Result.WIN)
        if boardFull(newBoard):
          bestForPlayer = (row, col, Result.TIE)
        else:
          (_, _, bestForOpponent) = \
            bestResultAndMove(nextPlayer(player), newBoard)
          if bestForOpponent == Result.LOSS:
            return (row, col, Result.WIN)
          elif bestForOpponent == Result.TIE:
            bestForPlayer = (row, col, Result.TIE)
  return bestForPlayer

def boardFull(board):
  for row in board:
    for entry in row:
      if entry == NO_PLAYER:
        return False
  return True

board = [3 * [NO_PLAYER] for i in range(3)]

def nextPlayer(player):
  return 3 - player

def checkIfDone(board):
  winner = currentWinner(board)
  if winner != None:
    print("Player %s won." % showPlayer(winner))
    return True
  if (boardFull(board)):
    print("Game over, a tie.")
    return True
  return False

def playAndCheck(board, player, r, c):
  board[r][c] = player
  player = nextPlayer(player)
  printBoard(board)
  done = checkIfDone(board)
  return (player, board, done)

player = 1
print("Coordinates are 1-based, with [1,1] top left and [3, 1] top right.")
done = False
printBoard(board)
while not done:
  inString = input(
    "Enter move coords for player %s as x,y > " % showPlayer(player))
  try:
    [x, y] = map(lambda s: int(s.strip()), inString.split(','))
    cx = y-1
    cy = x-1
  except:
    print("Bad input; try again.")
    continue
  if cx < 0 or cx > 2 or cy < 0 or cy > 2:
    print("Illegal move--out of range.")
    continue
  if board[cx][cy]:
    print("Illegal move--square already occupied.")
    continue
  (player, board, done) = playAndCheck(board, player, cx, cy)
  if not done:
    (r, c, _) = bestResultAndMove(player, board)
    (player, board, done) = playAndCheck(board, player, r, c)
