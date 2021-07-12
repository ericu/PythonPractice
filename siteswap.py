#!/usr/bin/python3
import unittest
import argparse
import sys
import math
from collections import namedtuple
from more_itertools import take

class InputError(Exception):
  def __init__(self, message):
    self.message = message

Throw = namedtuple('Throw', ('index', 'height'))
Orbit = namedtuple('Orbit', ('ballIds', 'start_index', 'sequence', 'length'))
Analysis = namedtuple('Analysis', ('pattern', 'num_hands', 'orbits', 'max_cycle_length'))
# todo: this will gain more fields for throw+catch location.
Segment = namedtuple('Segment', ('index', 'height', 'throw_hand', 'catch_hand'))


#todo: Classes for these, possibly subclasses of some parent.
Arc = namedtuple('Arc', ('index', 'duration', 'throw_pos', 'catch_pos'))
HandMove = namedtuple('HandMove', ('index', 'duration', 'start_pos', 'end_pos'))

#todo: Classes for these, possibly subclasses of some parent?
CarryEnd = namedtuple('CarryEnd', ('index', 'position', 'ball'))
CarryStart = namedtuple('CarryStart', ('index', 'position', 'ball'))

# This is a hack to put in default throw/catch locations.
r = 10
def simple_throw_pos(hand, num_hands):
  if num_hands == 2:
    return ((hand - 0.5) * r, 0)
  else:
    angle = hand / num_hands * 2 * math.pi
    return (r * math.cos(angle), r * math.sin(angle))
  
def simple_catch_pos(hand, num_hands):
  if num_hands == 2:
    return ((hand - 0.5) * r * 2, 0)
  else:
    angle = (hand * 0.5) / num_hands * 2 * math.pi
    return (r * math.cos(angle), r * math.sin(angle))

class SiteSwap:
  """Class for representing asynchronous site-swap juggling patterns."""

  @staticmethod
  def validate_pattern(pattern):
    if not all(map(lambda i: isinstance(i, int), pattern)):
      raise InputError(f'Pattern {pattern} contains non-integer value(s).')
    if not all(map(lambda i: i >= 0, pattern)):
      raise InputError(f'Pattern {pattern} contains negative value(s).')
    length = len(pattern)
    num_balls = sum(pattern) / length
    if int(num_balls) != num_balls:
      raise InputError(f'Pattern {pattern} uses fractional balls {num_balls}.')
    destinations = [False] * length
    for index, height in enumerate(pattern):
      destination = (index + height) % length
      if destinations[destination]:
        raise InputError(f'Pattern {pattern} has a collision.')
      destinations[destination] = True
    assert(all(destinations))
    return int(num_balls)

  def from_string(str):
    """Produces a SiteSwap from a comma-separated list of natural numbers."""
    as_strings = [s.strip() for s in str.split(",")]
    pattern = [int(i) for i in as_strings if len(i)]
    return SiteSwap(pattern)

  def __init__(self, parsedPattern, num_hands=2):
    self.num_balls = SiteSwap.validate_pattern(parsedPattern)
    self.pattern = parsedPattern
    self.num_hands = num_hands

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
    if len(self.pattern) % self.num_hands:
      # This makes sure each ball gets back to its original hand, not just the
      # starting spot in the numerical pattern.  todo: if the overage and
      # num_hands aren't relatively prime, we can make it somewhat shorter.
      pattern = self.pattern * self.num_hands
    else:
      pattern = self.pattern
    balls_found = 0
    cycles_found = 0
    max_cycle_length = 0
    throws_seen = set([ind for (ind, height) in enumerate(pattern)
                       if not height]) # skip zeroes
    index = 0
    pattern_length = len(pattern)
    orbits = []
    while balls_found < self.num_balls:
      assert(index < pattern_length)
      length = 0
      sequence = []
      cur_index = index
      if cur_index not in throws_seen:
        hand = cur_index % self.num_hands
        while not length or cur_index != index:
          throws_seen.add(cur_index)
          height = pattern[cur_index]
          catch_hand = (hand + height) % self.num_hands
          sequence.append(Segment(cur_index, height, hand, catch_hand))
          assert(height)
          length = length + height
          hand = catch_hand
          cur_index = (cur_index + height) % pattern_length
      if length:
        cycles_found += 1
        max_cycle_length = max(max_cycle_length, length)
        balls_in_cycle = length / pattern_length
        assert(balls_in_cycle == int(balls_in_cycle))
        balls_in_cycle = int(balls_in_cycle)
        ballIds = list(range(balls_found, balls_found + balls_in_cycle))
        orbits.append(Orbit(ballIds, index, sequence, length))
        balls_found += balls_in_cycle
      index += 1
    return Analysis(self.pattern, self.num_hands, orbits, max_cycle_length)

# The point of this object is to be able to answer the question, "Where is
# ball/hand N at time T?"  Possibly we'll move this all to the SiteSwap
# constructor, but maybe not.
# TODO: This is completely untested.
def analysis_to_animation(analysis):
  _, num_hands, orbits, max_cycle_length = analysis
  hands = dict([(hand, []) for hand in range(num_hands)])
  ball_paths = {}
  for orbit in orbits:
    ballIds, start_index, sequence, length = orbit
    balls_in_orbit = len(ballIds)
    assert(int(length / balls_in_orbit) == length / balls_in_orbit)
    offset_increment = int(length / balls_in_orbit)
    for ball in ballIds:
      ball_path = []
      index = start_index
      for segment in sequence:
        #todo: We're ignoring index in Sequence, since they're based on the
        # orbit's start_index and are redundant; take them out?
        _, height, throw_hand, catch_hand = segment
        # We hack 1s here; instead of a true hand-across, which is messy, we
        # have it spend half a beat in the air, followed by a half-beat carry.
        if height == 1:
          duration = 0.5
        else:
          duration = height - 1
        throw_time = index % length
        catch_time = (index + duration) % length
        throw_pos = simple_throw_pos(throw_hand, num_hands)
        catch_pos = simple_catch_pos(catch_hand, num_hands)
        ball_path.append(Arc(throw_time, duration, throw_pos, catch_pos))
        # todo: Add velocity info for splined throws instead of just position.
        hands[throw_hand].append(CarryEnd(throw_time, throw_pos, ball))
        hands[catch_hand].append(CarryStart(catch_time, catch_pos, ball))
        index += height
      ball_paths[ball] = ball_path
      start_index += offset_increment
  hand_paths = {}
  for hand, carry_parts in hands.items():
    #TODO: We don't have the ball being carried by the hand.  Add to the ball
    #paths as we produce the carry paths.
    path = []
    assert(not len(carry_parts) % 2)
    carry_parts.sort(key=lambda p: p.index)
    for i in range(len(carry_parts)):
      start = carry_parts[i]
      end = carry_parts[(i + 1) % len(carry_parts)]
      # carry_parts should alternate between begin and end.
      assert(type(start) != type(end))
      duration = (end.index - start.index + max_cycle_length) % max_cycle_length
      move = HandMove(start.index, duration, start.position, end.position)
      path.append(move)
      if type(start) == CarryStart:
        assert(start.ball == end.ball)
        ball_paths[start.ball].append(move)
    hand_paths[hand] = path
  for ball_path in ball_paths.values():
    ball_path.sort(key=lambda arc: arc.index)
  return (ball_paths, hand_paths)

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
  parser.add_argument("-u", "--unittest", help="run unit tests",
                      action="store_true")
  parser.add_argument("-t", "--test", help="run current test",
                      action="store_true")
  args, argv = parser.parse_known_args()
  sys.argv[:] = [name] + argv
  return args

if __name__ == '__main__':
  args = get_args()
  if args.unittest:
    unittest.main()
  elif args.test:
    analysis = SiteSwap([2,8]).analyze()
    print('analysis', analysis)
    print('paths', analysis_to_animation(analysis))
    analysis = SiteSwap([4,4,1]).analyze()
    print('analysis', analysis)
    print('paths', analysis_to_animation(analysis))
    analysis = SiteSwap([5,6,1]).analyze()
    print('analysis', analysis)
    print('paths', analysis_to_animation(analysis))
    analysis = SiteSwap([5,6,1], num_hands=3).analyze()
    print('analysis', analysis)
    print('paths', analysis_to_animation(analysis))
    analysis = SiteSwap([3]).analyze()
    print('analysis', analysis)
    print('paths', analysis_to_animation(analysis))
    analysis = SiteSwap([8], num_hands=3).analyze()
    print('analysis', analysis)
    print('paths', analysis_to_animation(analysis))
    analysis = SiteSwap([8]).analyze()
    print('analysis', analysis)
    print('paths', analysis_to_animation(analysis))
