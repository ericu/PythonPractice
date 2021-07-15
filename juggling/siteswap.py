#!/usr/bin/python3
import unittest
import argparse
from functools import reduce
import math
import sys
from collections import namedtuple
from more_itertools import take

class InputError(Exception):
  def __init__(self, message):
    self.message = message

Throw = namedtuple('Throw', ('index', 'height'))
Orbit = namedtuple('Orbit', ('ballIds', 'start_index', 'sequence', 'length'))
Analysis = namedtuple('Analysis', ('pattern', 'num_hands', 'orbits', 'cycle_length'))
# todo: this will gain more fields for throw+catch location.
Segment = namedtuple('Segment', ('height', 'throw_hand', 'catch_hand'))

def lcm(numbers):
  return reduce(lambda a, b: a * b // math.gcd(a, b), numbers)

class Motion:
  #TODO: Rename index to time?
  def __init__(self, index, duration, start_pos, end_pos):
    self.index = index
    self.duration = duration
    self.end_time = index + duration
    self.start_pos = start_pos
    self.end_pos = end_pos

  def covers(self, time, cycle_length):
    time %= cycle_length
    time_to_check = time if time >= self.index else time + cycle_length
    return time_to_check >= self.index and time_to_check < self.end_time

  def location_at(self, time, cycle_length):
    raise NotImplementedError('Unimplemented')

  def bounding_box(self):
    raise NotImplementedError('Unimplemented')

class Arc(Motion):
  G = -25

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    sx, sy = self.start_pos
    ex, ey = self.end_pos
    self.dx = ex - sx
    self.dy = ey - sy
    # Here we need the equation for the parabola.
    # s = vi t + 0.5 a t^2
    # s is dy; t is duration; choose G as convenient.
    self.vi = ((self.dy - 0.5 * self.G * self.duration * self.duration) /
               self.duration)

  def location_at(self, time, cycle_length):
    time %= cycle_length
    time = time if time >= self.index else time + cycle_length
    assert time >= self.index and time < self.end_time
    # TODO: Use a vector object for positions.
    sx, sy = self.start_pos
    dt = time - self.index
    fraction = dt / self.duration
    x = sx + fraction * self.dx
    y = sy + self.vi * dt + 0.5 * self.G * dt * dt
    return (x, y)

  def bounding_box(self):
    # vf^2 = vi^2 + 2 a s; peak is at vf = 0.
    # - 2 a s = vi^2
    # s = vi^2 / (-2 a)
    dy_max = self.vi * self.vi / (- 2 * self.G)
    sx, sy = self.start_pos
    ex, ey = self.end_pos
    x_min = min(sx, ex)
    y_min = min(sy, ey)
    x_max = max(sx, ex)
    y_max = sy + dy_max
    return (x_min, y_min, x_max, y_max)

class HandMove(Motion):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

  def location_at(self, time, cycle_length):
    time %= cycle_length
    time = time if time >= self.index else time + cycle_length
    assert time >= self.index and time < self.end_time
    # TODO: Use a vector object for positions.
    sx, sy = self.start_pos
    ex, ey = self.end_pos
    fraction = (time - self.index) / self.duration
    dx = ex - sx
    dy = ey - sy
    x = sx + fraction * dx
    y = sy + fraction * dy
    return (x, y)

  def bounding_box(self):
    sx, sy = self.start_pos
    ex, ey = self.end_pos
    x_min = min(sx, ex)
    y_min = min(sy, ey)
    x_max = max(sx, ex)
    y_max = max(sy, ey)
    return (x_min, y_min, x_max, y_max)

#todo: Classes for these, possibly subclasses of some parent?
CarryEnd = namedtuple('CarryEnd', ('index', 'position', 'ball'))
CarryStart = namedtuple('CarryStart', ('index', 'position', 'ball'))

# This is a hack to put in default throw/catch locations.
r = 75
def _simple_throw_pos(hand, num_hands):
  if num_hands == 2:
    return ((hand - 0.5) * r, 0)
  else:
    angle = hand / num_hands * 2 * math.pi
    return (r * math.cos(angle), r * math.sin(angle))

def _simple_catch_pos(hand, num_hands):
  if num_hands == 2:
    return ((hand - 0.5) * r * 2, r * 0.1)
  else:
    angle = (hand * 0.5) / num_hands * 2 * math.pi
    return (r * math.cos(angle), r * math.sin(angle))

def _simple_handoff_pos(from_hand, to_hand, num_hands):
  (x0, y0) = _simple_throw_pos(from_hand, num_hands)
  (x1, y1) = _simple_throw_pos(to_hand, num_hands)
  return ((x0 + x1) / 2, (y0 + y1) / 2)

# TODO: Scale animation to just fit within a unit box, based on throw height and
# hand positions.
class Animation:
  def __init__(self, ball_paths, hand_paths, cycle_length):
    self.ball_paths = ball_paths
    self.hand_paths = hand_paths
    self.cycle_length = cycle_length
    self.g = -25

  def num_balls(self):
    return len(self.ball_paths.keys())

  def num_hands(self):
    return len(self.hand_paths.keys())

  def __repr__(self):
    return (
      f'Animation({self.ball_paths!r},{self.hand_paths!r},' +
      f'{self.cycle_length!r})')

  def hand_location_at(self, hand, time):
    for move in self.hand_paths[hand]:
      if move.covers(time, self.cycle_length):
        return move.location_at(time, self.cycle_length)
    assert False, 'Any time should have a hand location.'
    return (0, 0)

  def ball_location_at(self, ball, time):
    for move in self.ball_paths[ball]:
      if move.covers(time, self.cycle_length):
        return move.location_at(time, self.cycle_length)
    assert False, 'Any time should have a ball location.'
    return (0, 0)

  def bounding_box(self):
    def merge_boxes(b0, b1):
      x_min_0, y_min_0, x_max_0, y_max_0 = b0
      x_min_1, y_min_1, x_max_1, y_max_1 = b1
      x_min = min(x_min_0, x_min_1)
      y_min = min(y_min_0, y_min_1)
      x_max = max(x_max_0, x_max_1)
      y_max = max(y_max_0, y_max_1)
      return (x_min, y_min, x_max, y_max)

    path_list = list(self.ball_paths.values()) + list(self.hand_paths.values())
    motion_list = [motion for path in path_list for motion in path]
    bbox_list = map(lambda m: m.bounding_box(), motion_list)
    return reduce(merge_boxes, bbox_list)

class SiteSwap:
  """Class for representing asynchronous site-swap juggling patterns."""

  @staticmethod
  def validate_pattern(pattern):
    if not len(pattern):
      raise InputError(f'Pattern has no throws.')
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

  @staticmethod
  def from_string(string_pattern):
    """Produces a SiteSwap from a comma-separated list of natural numbers."""
    # todo: Would be nice to split on comma *or* whitespace.
    as_strings = [s.strip() for s in string_pattern.split(",")]
    try:
      pattern = [int(i) for i in as_strings if len(i)]
    except ValueError as error:
      raise InputError(error)
    return SiteSwap(pattern)

  def pattern_string(self):
    return ', '.join(map(str, self.pattern))

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
    cycle_lengths = []
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
          sequence.append(Segment(height, hand, catch_hand))
          assert(height)
          length = length + height
          hand = catch_hand
          cur_index = (cur_index + height) % pattern_length
      if length:
        cycles_found += 1
        cycle_lengths.append(length)
        balls_in_cycle = length / pattern_length
        assert(balls_in_cycle == int(balls_in_cycle))
        balls_in_cycle = int(balls_in_cycle)
        ballIds = list(range(balls_found, balls_found + balls_in_cycle))
        orbits.append(Orbit(ballIds, index, sequence, length))
        balls_found += balls_in_cycle
      index += 1
    return Analysis(self.pattern, self.num_hands, orbits, lcm(cycle_lengths))

  def animation(self):
    return analysis_to_animation(self.analyze())

# The point of this object is to be able to answer the question, "Where is
# ball/hand N at time T?"  Possibly we'll move this all to the SiteSwap
# constructor, but maybe not.
def analysis_to_animation(analysis):
  _, num_hands, orbits, cycle_length = analysis
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
        height, throw_hand, catch_hand = segment
        duration = height - 1
        if duration:
          throw_pos = _simple_throw_pos(throw_hand, num_hands)
          catch_pos = _simple_catch_pos(catch_hand, num_hands)
        else: # It's a 1.
          throw_pos = _simple_handoff_pos(throw_hand, catch_hand, num_hands)
          catch_pos = throw_pos
        (repeats, remainder) = divmod(cycle_length, length)
        assert(remainder == 0)
        for i in range(repeats): # clone each segment to fill cycle_length
          clone_offset = i * length
          throw_time = (index + clone_offset) % cycle_length
          catch_time = (index + duration + clone_offset) % cycle_length
          if duration:
            ball_arc = Arc(throw_time, duration, throw_pos, catch_pos)
            ball_path.append(ball_arc)
          # todo: Add velocity info for splined throws instead of just position.
          carry_end = CarryEnd(throw_time, throw_pos, ball)
          carry_start = CarryStart(catch_time, catch_pos, ball)
          hands[throw_hand].append(carry_end)
          hands[catch_hand].append(carry_start)
        index += height
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
      duration = (end.index - start.index + cycle_length) % cycle_length
      move = HandMove(start.index, duration, start.position, end.position)
      path.append(move)
      if type(start) == CarryStart:
        assert(start.ball == end.ball)
        ball_paths[start.ball].append(move)
    hand_paths[hand] = path
  for ball_path in ball_paths.values():
    ball_path.sort(key=lambda arc: arc.index)
  return Animation(ball_paths, hand_paths, cycle_length)

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

def _get_args():
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
  args = _get_args()
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
    # 3 is the only one I've hand-verified; others will wait for animation.
    analysis = SiteSwap([3]).analyze()
    print('analysis', analysis)
    print('paths', analysis_to_animation(analysis))
    analysis = SiteSwap([8], num_hands=3).analyze()
    print('analysis', analysis)
    print('paths', analysis_to_animation(analysis))
    analysis = SiteSwap([8]).analyze()
    print('analysis', analysis)
    print('paths', analysis_to_animation(analysis))
