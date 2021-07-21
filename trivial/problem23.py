#!/usr/bin/python3


def get_numbers(filename):
    with open(filename, "r") as input_file:
        return [int(line.strip()) for line in input_file]


numbers0 = set(get_numbers("numbers0.txt"))
print("first file", numbers0)
numbers1 = set(get_numbers("numbers1.txt"))
print("second file", numbers1)
print("intersection", numbers0.intersection(numbers1))
