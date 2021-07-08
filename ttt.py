#!/usr/bin/python3
import sys
from enum import Enum

#To win a game:
#
#Assuming the game isn't over, for each legal open move m:
#  1) Did m win me the game immediately?  [assume only I can win on my move]
#  2) If not, it's your move on the modified board.  Did-you-win-recursive?
#    [Could be win/lose/tie.]
#    If you lose, I pick m and exit reporting it and my victory.
#    If you tie, I store this as a possible best answer and continue.
#    If you win, I do nothing.
#
#If I found a tie, I return that move and report the tie.
#If I found no win/tie, I report the loss.

def drawHLine(length):
  return (length * " ---") + '\n'

def drawDataLine(dataLine):
  return ''.join(map(lambda d: "| " + mark(d) + " ", dataLine)) + "|\n"

def drawBoard(data):
  lineLen = len(data[0])
  return (
    drawHLine(lineLen) +
    ''.join(map(lambda dataLine: drawDataLine(dataLine) + drawHLine(lineLen), data)))

NO_PLAYER = 0
def mark(index):
  return " XO"[index]

def lineAllSame(line):
  if line[0] == line[1] and line[1] == line[2] and line[0] != NO_PLAYER:
    return line[0]
  return None

def horizontalMatch(board):
  for i in range(0, 3):
    who = lineAllSame(board[i])
    if who != None:
      return who
  return None

def invert(board):
  return [[board[x][y] for x in range(3)] for y in range(3)]

def verticalMatch(board):
  return horizontalMatch(invert(board))

def diagonalMatch(board):
  who = lineAllSame([board[i][i] for i in range(3)])
  if who != None:
    return who
  return lineAllSame([board[2 - i][i] for i in range(3)])

def currentWinner(board):
  for f in [horizontalMatch, verticalMatch, diagonalMatch]:
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

def showBoard(board):
  print(drawBoard(board))

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
    showBoard(board)
    print("Player %s won." % mark(winner))
    return True
  if (boardFull(board)):
    showBoard(board)
    print("Game over, a tie.")
    return True
  return False

player = 1
print("Coordinates are 1-based, with [1,1] top left and [3, 1] top right.")
done = False
while not done:
  showBoard(board)
  inString = input("Enter move coords for player %s as x,y > " % mark(player))
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
  board[y-1][x-1] = player
  done = checkIfDone(board)
  if not done:
    computerPlayer = nextPlayer(player)
    (r, c, _) = bestResultAndMove(computerPlayer, board)
    board[r][c] = computerPlayer
    done = checkIfDone(board)
