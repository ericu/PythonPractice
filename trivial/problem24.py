#!/usr/bin/env python3
import sys


def horizontal_line(length):
    return (length * " ---") + "\n"


def board_line(data_line):
    return "".join(map(lambda d: "| " + d + " ", data_line)) + "|\n"


def fake_data_line(size):
    return "." * size


def fake_data(size):
    return [fake_data_line(size) for a in range(size)]


def board(data):
    line_len = len(data[0])
    return horizontal_line(line_len) + "".join(
        map(
            lambda data_line: board_line(data_line) + horizontal_line(line_len),
            data,
        )
    )


def main():
    val = input("input board size > ")
    # NOTE: conversion errors not handled.
    size = int(val)
    if size <= 0:
        print("Board size must be an integer greater than zero")
        sys.exit(-1)
    print("Got size: %d" % size)

    print(board(fake_data(size)))


if __name__ == "__main__":
    main()
