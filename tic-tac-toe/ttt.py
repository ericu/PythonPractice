#!/usr/bin/env python3
from enum import Enum

NO_PLAYER = 0


def draw_h_line(length):
    return (length * " ---") + "\n"


def draw_data_line(data_line):
    return (
        "".join(map(lambda d: "| " + show_player(d) + " ", data_line)) + "|\n"
    )


def draw_board(data):
    line_len = len(data[0])
    return draw_h_line(line_len) + "".join(
        map(
            lambda data_line: draw_data_line(data_line) + draw_h_line(line_len),
            data,
        )
    )


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
        if who is not None:
            return who
    return None


def invert(board):
    return [[board[x][y] for x in range(3)] for y in range(3)]


def vertical_win(board):
    return horizontal_win(invert(board))


def diagonal_win(board):
    who = winning_line([board[i][i] for i in range(3)])
    if who is not None:
        return who
    return winning_line([board[2 - i][i] for i in range(3)])


def current_winner(board):
    for func in [horizontal_win, vertical_win, diagonal_win]:
        who = func(board)
        if who is not None:
            return who
    return None


def copy_board(board):
    return [row.copy() for row in board]


class Result(Enum):
    TIE = 0
    WIN = 1
    LOSS = 2


def best_result_and_move(player, board):
    assert current_winner(board) is None
    assert not board_full(board)
    best_for_player = (-1, -1, Result.LOSS)  # We'll never use these coords.
    for row in range(3):
        for col in range(3):
            if board[row][col] == NO_PLAYER:  # it's a legal move
                new_board = copy_board(board)
                new_board[row][col] = player
                winner = current_winner(new_board)
                if winner is not None:
                    assert winner == player
                    return (row, col, Result.WIN)
                if board_full(new_board):
                    best_for_player = (row, col, Result.TIE)
                else:
                    (_, _, best_for_opponent) = best_result_and_move(
                        next_player(player), new_board
                    )
                    if best_for_opponent == Result.LOSS:
                        return (row, col, Result.WIN)
                    if best_for_opponent == Result.TIE:
                        best_for_player = (row, col, Result.TIE)
    return best_for_player


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
    if winner is not None:
        print("Player %s won." % show_player(winner))
        return True
    if board_full(board):
        print("Game over, a tie.")
        return True
    return False


def play_and_check(board, player, row, col):
    board[row][col] = player
    player = next_player(player)
    print_board(board)
    done = check_if_done(board)
    return (player, board, done)


def main():
    print("Let's play a game of tic-tac-toe.")
    print("Coordinates are 1-based, with [1,1] top left and [3, 1] top right.")
    print("You go first.")

    game_board = [3 * [NO_PLAYER] for i in range(3)]
    player = 1
    done = False
    print_board(game_board)

    while not done:
        in_string = input(
            "Enter move coords for player %s as x,y > " % show_player(player)
        )
        try:
            [x, y] = map(lambda s: int(s.strip()), in_string.split(","))
            c_x = y - 1
            c_y = x - 1
        except:
            print("Bad input; try again.")
            continue
        if c_x < 0 or c_x > 2 or c_y < 0 or c_y > 2:
            print("Illegal move--out of range.")
            continue
        if game_board[c_x][c_y]:
            print("Illegal move--square already occupied.")
            continue
        (player, game_board, done) = play_and_check(game_board, player,
                                                    c_x, c_y)
        if not done:
            (row, col, _) = best_result_and_move(player, game_board)
            (player, game_board, done) = play_and_check(
                game_board, player, row, col
            )

if __name__ == "__main__":
    main()
