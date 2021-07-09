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
  def validatePatternGetBallCount(pattern):
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

  def __init__(self, parsedPattern):
    self.balls = SiteSwap.validatePatternGetBallCount(parsedPattern)
    self.pattern = parsedPattern

class TestValidatePattern(unittest.TestCase):
  def test_simple_patterns(self):
    self.assertEqual(3, SiteSwap.validatePatternGetBallCount([3]))
    self.assertEqual(3, SiteSwap.validatePatternGetBallCount([2, 3, 4]))
    self.assertEqual(3, SiteSwap.validatePatternGetBallCount([4, 4, 1]))

  def test_bad_input(self):
    with self.assertRaises(InputError):
      SiteSwap.validatePatternGetBallCount([1.5, 2.5])

  def test_bad_ball_count(self):
    with self.assertRaises(InputError):
      SiteSwap.validatePatternGetBallCount([3, 4])

  def test_collision(self):
    with self.assertRaises(InputError):
      SiteSwap.validatePatternGetBallCount([4, 3, 2])

def getArgs():
  name = sys.argv[0]
  parser = argparse.ArgumentParser()
  parser.add_argument("-u", "--unittest", help="run unit tests", action="store_true")
  args, argv = parser.parse_known_args()
  sys.argv[:] = [name] + argv
  return args

if __name__ == '__main__':
  args = getArgs()
  if args.unittest:
    unittest.main()
