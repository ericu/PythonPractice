#!/usr/bin/env python3


def draw_h_line(length):
    return (length * " ---") + "\n"


def draw_data_line(data_line):
    return "".join(map(lambda d: "| " + mark(d) + " ", data_line)) + "|\n"


def draw_board(data):
    line_len = len(data[0])
    return draw_h_line(line_len) + "".join(
        map(
            lambda data_line: draw_data_line(data_line)
            + draw_h_line(line_len),
            data,
        )
    )


def mark(index):
    return " XO"[index]


def line_all_same(line):
    if line[0] == line[1] and line[1] == line[2] and line[0] != 0:
        return (True, line[0])
    return (False, None)


def horizontal_match(board):
    for i in range(0, 3):
        (found, who) = line_all_same(board[i])
        if found:
            return (found, who)
    return (False, None)


def invert(board):
    return [[board[x][y] for x in range(3)] for y in range(3)]


def vertical_match(board):
    return horizontal_match(invert(board))


def diagonal_match(board):
    (found, who) = line_all_same([board[i][i] for i in range(3)])
    if found:
        return (found, who)
    return line_all_same([board[2 - i][i] for i in range(3)])


def match(board):
    for func in [horizontal_match, vertical_match, diagonal_match]:
        (found, who) = func(board)
        if found:
            print("match returning winner", found, who, func)
            return (found, who)
    return (False, None)


def show_board(board):
    print(draw_board(board))


def board_full(board):
    for row in board:
        for entry in row:
            if not entry:
                return False
    return True


def next_player(player):
    return 3 - player


def main():
    board = [3 * [0] for i in range(3)]
    player = 1
    print("Coordinates are 1-based, with [1,1] top left and [3, 1] top right.")
    while True:
        show_board(board)
        in_string = input(
            "Enter move coords for player %s as x,y > " % mark(player)
        )
        try:
            [x, y] = map(lambda s: int(s.strip()), in_string.split(","))
            c_x = y - 1
            c_y = x - 1
        except ValueError:
            print("Bad input; try again.")
            continue
        if c_x < 0 or c_x > 2 or c_y < 0 or c_y > 2:
            print("Illegal move--out of range.")
            continue
        if board[c_x][c_y]:
            print("Illegal move--square already occupied.")
            continue
        board[y - 1][x - 1] = player
        (win, winner) = match(board)
        if win:
            show_board(board)
            print("Player %s won." % mark(winner))
            break
        if board_full(board):
            show_board(board)
            print("Game over, a tie.")
            break
        player = next_player(player)


if __name__ == "__main__":
    main()
