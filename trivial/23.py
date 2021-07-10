#!/usr/bin/python3

def getNumbers(filename):
  f = open(filename, 'r')
  return [int(line.strip()) for line in f]

primes = set(getNumbers('primenumbers.txt'))
print('primes', primes)
happies = set(getNumbers('happynumbers.txt'))
print('happies', happies)
print('intersection', primes.intersection(happies))
