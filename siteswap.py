#!/usr/bin/python3
import unittest
import argparse
import sys

class InputError(Exception):
  def __init__(self, message):
    self.message = message

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
    for index, throw in enumerate(pattern):
      destination = (index + throw) % length
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
    self.hands = 2 # for now

  def __repr__(self):
    return f'SiteSwap({self.pattern!r})'

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
    print(SiteSwap.from_string('4,4, 1'))
