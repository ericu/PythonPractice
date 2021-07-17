#!/usr/bin/python3


def get_numbers(filename):
    with open(filename, "r") as input_file:
        return [int(line.strip()) for line in input_file]


primes = set(get_numbers("primenumbers.txt"))
print("primes", primes)
happies = set(get_numbers("happynumbers.txt"))
print("happies", happies)
print("intersection", primes.intersection(happies))
