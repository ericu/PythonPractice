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
# TODO: This will gain more fields for throw+catch location.
Segment = namedtuple('Segment', ('index', 'height', 'throw_hand', 'catch_hand'))


#TODO: Classes for these, possibly subclasses of some parent.
Arc = namedtuple('Arc', ('index', 'duration', 'throw_pos', 'catch_pos'))
HandMove = namedtuple('HandMove', ('index', 'duration', 'start_pos', 'end_pos'))

#TODO: Classes for these, possibly subclasses of some parent?
CarryEnd = namedtuple('CarryEnd', ('index', 'position'))
CarryStart = namedtuple('CarryStart', ('index', 'position'))

# TODO: This is a hack to put in default throw/catch locations.  Do better.
r = 10
def simple_throw_pos(hand, num_hands):
  angle = hand / num_hands * 2 * math.pi
  return (r * math.cos(angle), r * math.sin(angle))
  
def simple_catch_pos(hand, num_hands):
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
    # TODO: Return a new object.  The point of this object is to be able to
    # answer the question, "Where is ball N at time T?"  Possibly we'll move
    # this all to the constructor, and SiteSwap will be that object, but maybe
    # not.  It's trivial to pick the Orbit for the ball; we need to find the
    # right Segment and where in it the ball is.  Perhaps Orbit should be a
    # class with some smarts.
    # If an orbit of K balls and length L starts at time T0, and we want ball B
    # of that orbit [e.g. 2 if it's the third ball in the orbit] at time T1...
    #   First we need to rotate the orbit by B * L / K, *backwards*, since that
    #   ball is thrown B * L / K *later* than the starting index.  That's the
    #   same as adding (L - B * L / K) to the current time.  Then we need
    #   to move forward by T1 - T0.  Then we need to mod to get back within the
    #   sequence length by % L.
    # Simplify:
    #   * All subtractions are done by adding L - ${value}.
    #   * Start by subtracting off the start_index of the orbit from T.
    #   * Then subtract off B * L / K.
    #   * Then % by L.  Now you just need to find the right segment in the
    #     orbit: while t > height[i]: t -= height[i++].
    # NOTE: This assumes throw-carry is part of the throw record.  We may
    # wish to make separate carry records in between the throw records, so
    # throw records will generally have N-1 beats and carry records will have 1.
    # For 1s we'll have to do something special; I'm leaning toward simplifying
    # by saying that a 1 spends 0.5 beats in the air and then 0.5 beats in the
    # hand; that lets it not mess with the previous carry, so it can just affect
    # the usual throw+carry records.  For a true handacross, you'd need to
    # adjust the carry before the non-throw and the carry before the catch to
    # include the hand across and special prep for next throw, and you wouldn't
    # have a throw record at all; you'd still need a special post-throw carry
    # record, too.
    # NOTE: We'll also need to answer where a given hand is.  Hands will
    # generally be controlled by multiple orbits.  We'll have to compute hand
    # orbits by walking through ball orbits and spitting out hand records; each
    # time we hit a carry, emit one carry record per ball in the orbit, noting
    # the offset for that event.
    return Analysis(self.pattern, self.num_hands, orbits, max_cycle_length)

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
        _, height, throw_hand, catch_hand = segment
        #TODO: We're ignoring index in Sequence, since they're based on the
        # orbit's start_index and are redundant; take them out?
        # TODO: Deal with 1s.
        duration = height - 1
        throw_time = index % length
        catch_time = (index + duration) % length
        throw_pos = simple_throw_pos(throw_hand, num_hands)
        catch_pos = simple_catch_pos(catch_hand, num_hands)
        ball_path.append(Arc(throw_time, duration, throw_pos, catch_pos))
        # todo: Add velocity info for splined throws instead of just position.
        hands[throw_hand].append(CarryEnd(throw_time, throw_pos))
        hands[catch_hand].append(CarryStart(catch_time, catch_pos))
        index += height
      ball_path.sort(key=lambda arc: arc.index)
      ball_paths[ball] = ball_path
      start_index += offset_increment
  hand_paths = {}
  for hand, carry_parts in hands.items():
    path = []
    assert(not len(carry_parts) % 2)
    carry_parts.sort(key=lambda p: p.index)
    for i in range(len(carry_parts)):
      start = carry_parts[i]
      end = carry_parts[(i + 1) % len(carry_parts)]
      # carry_parts should alternate between begin and end.
      assert(type(start) != type(end))
      duration = (end.index - start.index + max_cycle_length) % max_cycle_length
      path.append(HandMove(start.index, duration, start.position, end.position))
    hand_paths[hand] = path
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
#    print(SiteSwap([4,4,1]).analyze())
#    print(SiteSwap([5,6,1]).analyze())
#    print(SiteSwap([5,6,1], num_hands=3).analyze())
#    print(SiteSwap([3]).analyze())
#    print(SiteSwap([8], num_hands=3).analyze())
#    print(SiteSwap([8]).analyze())
