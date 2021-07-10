#!/usr/bin/python3
import unittest
import argparse
import sys
from collections import namedtuple
from more_itertools import take

class InputError(Exception):
  def __init__(self, message):
    self.message = message

Throw = namedtuple('Throw', ('index', 'height'))

class SiteSwap:
  """Class for representing site-swap juggling patterns."""

  @staticmethod
  def validate_pattern(pattern):
    if not all(map(lambda i: isinstance(i, int), pattern)):
      raise InputError(f'Pattern {pattern} contains non-integer value(s).')
    if not all(map(lambda i: i >= 0, pattern)):
      raise InputError(f'Pattern {pattern} contains negative value(s).')
    length = len(pattern)
    balls = sum(pattern) / length
    if int(balls) != balls:
      raise InputError(f'Pattern {pattern} uses fractional ball count {balls}.')
    destinations = [False] * length
    for index, height in enumerate(pattern):
      destination = (index + height) % length
      if destinations[destination]:
        raise InputError(f'Pattern {pattern} has a collision.')
      destinations[destination] = True
    assert(all(destinations))
    return balls

  def from_string(str):
    """Produces a SiteSwap from a comma-separated list of natural numbers."""
    as_strings = [s.strip() for s in str.split(",")]
    pattern = [int(i) for i in as_strings if len(i)]
    return SiteSwap(pattern)

  def __init__(self, parsedPattern):
    self.balls = SiteSwap.validate_pattern(parsedPattern)
    self.pattern = parsedPattern

  def __repr__(self):
    return f'SiteSwap({self.pattern!r})'

  class Iterator:
    """Class for running a pattern forever."""

    def __init__(self, pattern):
      self.pattern = pattern
      self.next_throw = 0

    def iterate(self):
      while True:
        index = self.next_throw
        height = self.pattern[index]
        self.next_throw = (self.next_throw + 1) % len(self.pattern)
        yield Throw(index, height)

  def iterator(self):
    return self.Iterator(self.pattern)

  def analyze(self):
    if len(self.pattern) % 2: # or num_hands, eventually
      # This makes sure each ball gets back to its original hand, not just the
      # starting spot in the numerical pattern.
      pattern = self.pattern + self.pattern
    else:
      pattern = self.pattern
    balls_found = 0
    cycles_found = 0
    max_cycle_length = 0
    # Skip zeroes.
    throws_seen = set([ind for (ind, height) in enumerate(pattern) if not height])
    index = 0
    pattern_length = len(pattern)
    while balls_found < self.balls:
      assert(index < pattern_length)
      length = 0
      cur_index = index
      if cur_index not in throws_seen:
        while not length or cur_index != index:
          throws_seen.add(cur_index)
          height = pattern[cur_index]
          assert(height)
          length = length + height
          cur_index = (cur_index + height) % pattern_length
      index += 1
      if length:
        cycles_found += 1
        max_cycle_length = max(max_cycle_length, length)
        balls_in_cycle = length / pattern_length
        balls_found += balls_in_cycle
    print(f'Found {cycles_found} cycles, max length {max_cycle_length}.')

class TestValidatePattern(unittest.TestCase):
  def test_simple_patterns(self):
    self.assertEqual(3, SiteSwap.validate_pattern([3]))
    self.assertEqual(3, SiteSwap.validate_pattern([2, 3, 4]))
    self.assertEqual(3, SiteSwap.validate_pattern([4, 4, 1]))

  def test_bad_input(self):
    with self.assertRaises(InputError):
      SiteSwap.validate_pattern([1.5, 2.5])

  def test_bad_ball_count(self):
    with self.assertRaises(InputError):
      SiteSwap.validate_pattern([3, 4])

  def test_collision(self):
    with self.assertRaises(InputError):
      SiteSwap.validate_pattern([4, 3, 2])

  def test_string_constructor(self):
    self.assertEqual(repr(SiteSwap([4, 4, 1])),
                     repr(SiteSwap.from_string("4, 4,1")))

  def test_iterator(self):
    iterator = SiteSwap([4, 4, 1]).iterator()
    throws1 = take(4, iterator.iterate())
    self.assertEqual(throws1[0].height, 4)
    self.assertEqual(throws1[0].index, 0)
    self.assertEqual(throws1[1].height, 4)
    self.assertEqual(throws1[1].index, 1)
    self.assertEqual(throws1[2].height, 1)
    self.assertEqual(throws1[2].index, 2)
    self.assertEqual(throws1[3].height, 4)
    self.assertEqual(throws1[3].index, 0)

def get_args():
  name = sys.argv[0]
  parser = argparse.ArgumentParser()
  parser.add_argument("-u", "--unittest", help="run unit tests", action="store_true")
  parser.add_argument("-t", "--test", help="run current test", action="store_true")
  args, argv = parser.parse_known_args()
  sys.argv[:] = [name] + argv
  return args

if __name__ == '__main__':
  args = get_args()
  if args.unittest:
    unittest.main()
  elif args.test:
    SiteSwap([2,8]).analyze()
    SiteSwap([4,4,1]).analyze()
    SiteSwap([5,6,1]).analyze()
    SiteSwap([3]).analyze()
    SiteSwap([8]).analyze()
