#!/usr/bin/python3
import sys


def drawHLine(length):
    return (length * " ---") + "\n"


def drawDataLine(dataLine):
    return "".join(map(lambda d: "| " + mark(d) + " ", dataLine)) + "|\n"


def drawBoard(data):
    lineLen = len(data[0])
    return drawHLine(lineLen) + "".join(
        map(lambda dataLine: drawDataLine(dataLine) + drawHLine(lineLen), data)
    )


def mark(index):
    return " XO"[index]


def lineAllSame(line):
    if line[0] == line[1] and line[1] == line[2] and line[0] != 0:
        return (True, line[0])
    return (False, None)


def horizontalMatch(board):
    for i in range(0, 3):
        (t, who) = lineAllSame(board[i])
        if t:
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


def match(board):
    for f in [horizontalMatch, verticalMatch, diagonalMatch]:
        (t, who) = f(board)
        if t:
            print("match returning winner", t, who, f)
            return (t, who)
    return (False, None)


def showBoard(board):
    print(drawBoard(board))


def boardFull(board):
    for row in board:
        for entry in row:
            if not entry:
                return False
    return True


board = [3 * [0] for i in range(3)]

# print('H?', horizontalMatch(sampleData))
# print('V?', verticalMatch(sampleData))
# print('D?', diagonalMatch(sampleData))
# print('M?', match(sampleData))


def nextPlayer(player):
    return 3 - player


player = 1
print("Coordinates are 1-based, with [1,1] top left and [3, 1] top right.")
while True:
    showBoard(board)
    inString = input(
        "Enter move coords for player %s as x,y > " % mark(player)
    )
    try:
        [x, y] = map(lambda s: int(s.strip()), inString.split(","))
        cx = y - 1
        cy = x - 1
    except:
        print("Bad input; try again.")
        continue
    if cx < 0 or cx > 2 or cy < 0 or cy > 2:
        print("Illegal move--out of range.")
        continue
    if board[cx][cy]:
        print("Illegal move--square already occupied.")
        continue
    board[y - 1][x - 1] = player
    (win, winner) = match(board)
    if win:
        showBoard(board)
        print("Player %s won." % mark(winner))
        break
    if boardFull(board):
        showBoard(board)
        print("Game over, a tie.")
        break
    player = nextPlayer(player)
