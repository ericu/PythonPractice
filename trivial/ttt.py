#!/usr/bin/python3
import sys
from enum import Enum

NO_PLAYER = 0

def draw_h_line(length):
  return (length * " ---") + '\n'

def draw_data_line(dataLine):
  return ''.join(map(lambda d: "| " + show_player(d) + " ", dataLine)) + "|\n"

def draw_board(data):
  lineLen = len(data[0])
  return (
    draw_h_line(lineLen) +
    ''.join(map(lambda dataLine: draw_data_line(dataLine) +
                                 draw_h_line(lineLen),
                data)))

def print_board(board):
  print(draw_board(board))

def show_player(index):
  return " XO"[index]

def winning_line(line):
  if line[0] == line[1] and line[1] == line[2] and line[0] != NO_PLAYER:
    return line[0]
  return None

def horizontal_win(board):
  for i in range(0, 3):
    who = winning_line(board[i])
    if who != None:
      return who
  return None

def invert(board):
  return [[board[x][y] for x in range(3)] for y in range(3)]

def vertical_win(board):
  return horizontal_win(invert(board))

def diagonal_win(board):
  who = winning_line([board[i][i] for i in range(3)])
  if who != None:
    return who
  return winning_line([board[2 - i][i] for i in range(3)])

def current_winner(board):
  for f in [horizontal_win, vertical_win, diagonal_win]:
    who = f(board)
    if who != None:
      return who
  return None

def copy_board(board):
  return [row.copy() for row in board]

class Result(Enum):
  TIE = 0
  WIN = 1
  LOSS = 2

def best_result_and_move(player, board):
  assert current_winner(board) == None
  assert not board_full(board)
  bestForPlayer = (-1, -1, Result.LOSS) # We'll never use these coords.
  for row in range(3):
    for col in range(3):
      if board[row][col] == NO_PLAYER: # it's a legal move
        newBoard = copy_board(board)
        newBoard[row][col] = player
        winner = current_winner(newBoard) 
        if winner != None:
          assert winner == player
          return (row, col, Result.WIN)
        if board_full(newBoard):
          bestForPlayer = (row, col, Result.TIE)
        else:
          (_, _, bestForOpponent) = \
            best_result_and_move(next_player(player), newBoard)
          if bestForOpponent == Result.LOSS:
            return (row, col, Result.WIN)
          elif bestForOpponent == Result.TIE:
            bestForPlayer = (row, col, Result.TIE)
  return bestForPlayer

def board_full(board):
  for row in board:
    for entry in row:
      if entry == NO_PLAYER:
        return False
  return True

def next_player(player):
  return 3 - player

def check_if_done(board):
  winner = current_winner(board)
  if winner != None:
    print("Player %s won." % show_player(winner))
    return True
  if (board_full(board)):
    print("Game over, a tie.")
    return True
  return False

def play_and_check(board, player, r, c):
  board[r][c] = player
  player = next_player(player)
  print_board(board)
  done = check_if_done(board)
  return (player, board, done)

if __name__ == '__main__':
  print("Coordinates are 1-based, with [1,1] top left and [3, 1] top right.")

  game_board = [3 * [NO_PLAYER] for i in range(3)]
  player = 1
  done = False
  print_board(game_board)

  while not done:
    inString = input("Enter move coords for player %s as x,y > " %
                     show_player(player))
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
    if game_board[cx][cy]:
      print("Illegal move--square already occupied.")
      continue
    (player, game_board, done) = play_and_check(game_board, player, cx, cy)
    if not done:
      (r, c, _) = best_result_and_move(player, game_board)
      (player, game_board, done) = play_and_check(game_board, player, r, c)
