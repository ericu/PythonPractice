#!/usr/bin/env python3


def horizontal_line(length):
    return (length * " ---") + "\n"


def board_line(data_line):
    return "".join(map(lambda d: "| " + str(d) + " ", data_line)) + "|\n"


def line_all_same(line):
    if line[0] == line[1] and line[1] == line[2]:
        return (True, line[0])
    return (False, None)


def horizontal_match(board):
    for i in range(0, 3):
        (found, who) = line_all_same(board[i])
        if found and who != 0:
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
            return (found, who)
    return (False, None)


def main():
    sample_data = [[1, 2, 2], [0, 0, 2], [1, 2, 1]]
    print((sample_data))
    print("H?", horizontal_match(sample_data))
    print("V?", vertical_match(sample_data))
    print("D?", diagonal_match(sample_data))
    print("M?", match(sample_data))


if __name__ == "__main__":
    main()
