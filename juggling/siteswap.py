#!/usr/bin/python3
from collections import namedtuple
from functools import reduce
import argparse
import math
import sys
import unittest

from more_itertools import take
import numpy as np


class InputError(Exception):
    pass


Throw = namedtuple("Throw", ("index", "height"))

Segment = namedtuple("Segment", ("height", "throw_hand", "catch_hand"))
# Sequence is a list of Segments.
Orbit = namedtuple("Orbit", ("ball_ids", "start_index", "sequence", "length"))
Analysis = namedtuple(
    "Analysis", ("pattern", "num_hands", "orbits", "cycle_length")
)


def lcm(numbers):
    return reduce(lambda a, b: a * b // math.gcd(a, b), numbers)


class Motion:
    def __init__(self, time, duration, start_pos, end_pos):
        self.time = time
        self.duration = duration
        self.end_time = time + duration
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.delta = self.end_pos - self.start_pos

    def __repr__(self):
        type_name = type(self).__name__
        return (
            f"{type_name}({self.time!r},{self.duration!r},"
            + f"{self.start_pos!r},{self.end_pos!r})"
        )

    def covers(self, time, cycle_length):
        time %= cycle_length
        time_to_check = time if time >= self.time else time + cycle_length
        return self.time <= time_to_check < self.end_time

    def location_at(self, time, cycle_length):
        raise NotImplementedError("Unimplemented")

    def bounding_box(self):
        raise NotImplementedError("Unimplemented")


class Arc(Motion):
    G = -25

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Here we need the equation for the parabola.
        # s = v_i t + 0.5 a t^2
        # s is dy; t is duration; choose G as convenient.
        delta_y = self.delta[1]
        self.v_i = (
            delta_y - 0.5 * self.G * self.duration * self.duration
        ) / self.duration

    def location_at(self, time, cycle_length):
        time %= cycle_length
        time = time if time >= self.time else time + cycle_length
        assert self.time <= time < self.end_time
        d_t = time - self.time
        fraction = d_t / self.duration
        delta_x = fraction * self.delta[0]
        delta_y = self.v_i * d_t + 0.5 * self.G * d_t * d_t
        return self.start_pos + np.array([delta_x, delta_y])

    def bounding_box(self):
        # vf^2 = v_i^2 + 2 a s; peak is at vf = 0.
        # - 2 a s = v_i^2
        # s = v_i^2 / (-2 a)
        dy_max = self.v_i * self.v_i / (-2 * self.G)
        minima = np.minimum(self.start_pos, self.end_pos)
        maxima = np.maximum(self.start_pos, self.end_pos)
        maxima[1] = self.start_pos[1] + dy_max
        return (minima, maxima)


class HandMove(Motion):
    def location_at(self, time, cycle_length):
        time %= cycle_length
        time = time if time >= self.time else time + cycle_length
        assert self.time <= time < self.end_time
        fraction = (time - self.time) / self.duration
        return self.start_pos + fraction * self.delta

    def bounding_box(self):
        minima = np.minimum(self.start_pos, self.end_pos)
        maxima = np.maximum(self.start_pos, self.end_pos)
        return (minima, maxima)


class HandStationary(Motion):
    def __init__(self, pos):
        super().__init__(0, 0, pos, pos)

    def location_at(self, time, cycle_length):
        return self.start_pos

    def covers(self, *_):
        return True

    def bounding_box(self):
        return (self.start_pos, self.start_pos)


# This is a hack to put in default throw/catch locations.
R = 75


def _simple_throw_pos(hand, num_hands):
    if num_hands == 2:
        return np.array([(hand - 0.5) * R, 0])
    angle = hand / num_hands * 2 * math.pi
    return np.array([R * math.cos(angle), R * math.sin(angle)])


def _simple_catch_pos(hand, num_hands):
    if num_hands == 2:
        return np.array([(hand - 0.5) * R * 2, R * 0.1])
    angle = hand / num_hands * 2 * math.pi
    outer_r = R * 1.1
    return np.array([outer_r * math.cos(angle), outer_r * math.sin(angle)])


def _simple_handoff_pos(from_hand, to_hand, num_hands):
    return 0.5 * (
        _simple_throw_pos(from_hand, num_hands)
        + _simple_throw_pos(to_hand, num_hands)
    )


class Animation:
    """The point of this object is to be able to answer the question, "Where is
    ball/hand N at time T?"  Possibly we'll move this all to the SiteSwap
    constructor, but maybe not."""

    def __init__(self, ball_paths, hand_paths, cycle_length):
        self.ball_paths = ball_paths
        self.hand_paths = hand_paths
        self.cycle_length = cycle_length

    def num_balls(self):
        return len(self.ball_paths.keys())

    def num_hands(self):
        return len(self.hand_paths.keys())

    def __repr__(self):
        return (
            f"Animation({self.ball_paths!r},{self.hand_paths!r},"
            + f"{self.cycle_length!r})"
        )

    def hand_location_at(self, hand, time):
        for move in self.hand_paths[hand]:
            if move.covers(time, self.cycle_length):
                return move.location_at(time, self.cycle_length)
        assert False, "Any time should have a hand location."
        return np.zeroes(2)

    def ball_location_at(self, ball, time):
        for move in self.ball_paths[ball]:
            if move.covers(time, self.cycle_length):
                return move.location_at(time, self.cycle_length)
        assert False, "Any time should have a ball location."
        return np.zeroes(2)

    def bounding_box(self):
        def merge_boxes(b_0, b_1):
            min_0, max_0 = b_0
            min_1, max_1 = b_1
            return (np.minimum(min_0, min_1), np.maximum(max_0, max_1))

        path_list = list(self.ball_paths.values()) + list(
            self.hand_paths.values()
        )
        motion_list = [motion for path in path_list for motion in path]
        bbox_list = map(lambda m: m.bounding_box(), motion_list)
        return reduce(merge_boxes, bbox_list)


class SiteSwap:
    """Class for representing vanilla site-swap juggling patterns."""

    @staticmethod
    def validate_pattern(pattern):
        if not pattern:
            raise InputError("Pattern has no throws.")
        if not all(map(lambda i: isinstance(i, int), pattern)):
            raise InputError(
                f"Pattern {pattern} contains non-integer value(s)."
            )
        if not all(map(lambda i: i >= 0, pattern)):
            raise InputError(f"Pattern {pattern} contains negative value(s).")
        length = len(pattern)
        num_balls = sum(pattern) / length
        if int(num_balls) != num_balls:
            raise InputError(
                f"Pattern {pattern} uses fractional balls {num_balls}."
            )
        destinations = [False] * length
        for index, height in enumerate(pattern):
            destination = (index + height) % length
            if destinations[destination]:
                raise InputError(f"Pattern {pattern} has a collision.")
            destinations[destination] = True
        assert all(destinations)
        return int(num_balls)

    @staticmethod
    def from_string(string_pattern, num_hands=2):
        """Produces a SiteSwap from a comma-separated list of natural numbers."""
        # todo: Would be nice to split on comma *or* whitespace.
        as_strings = [s.strip() for s in string_pattern.split(",")]
        try:
            pattern = [int(i) for i in as_strings if len(i)]
        except ValueError as error:
            raise InputError("Invalid pattern string") from error
        return SiteSwap(pattern, num_hands)

    def pattern_string(self):
        return ", ".join(map(str, self.pattern))

    def __init__(self, parsedPattern, num_hands=2):
        self.num_balls = SiteSwap.validate_pattern(parsedPattern)
        self.pattern = parsedPattern
        self.num_hands = num_hands

    def __repr__(self):
        return f"SiteSwap({self.pattern!r})"

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
        """Computes the orbits for each ball in the pattern and other basic
        properties."""
        if len(self.pattern) % self.num_hands:
            # This makes sure each ball gets back to its original hand, not just
            # the starting spot in the numerical pattern.
            pattern = self.pattern * self.num_hands
        else:
            pattern = self.pattern
        if self.num_hands == 1:
            # To give the hand time to get back to throwing position, double all
            # the throw heights and put a 0 in between, as if it's a 2-handed
            # pattern.
            def fake_second_hand(pat, throw):
                pat.append(2 * throw)
                pat.append(0)
                return pat

            pattern = reduce(fake_second_hand, pattern, [])
        balls_found = 0
        cycles_found = 0
        cycle_lengths = []
        throws_seen = {
            ind for (ind, height) in enumerate(pattern) if not height
        }  # skip zeroes
        index = 0
        pattern_length = len(pattern)
        orbits = []
        while balls_found < self.num_balls:
            assert index < pattern_length
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
                    assert height
                    length = length + height
                    hand = catch_hand
                    cur_index = (cur_index + height) % pattern_length
            if length:
                cycles_found += 1
                cycle_lengths.append(length)
                balls_in_cycle = length / pattern_length
                assert balls_in_cycle == int(balls_in_cycle)
                balls_in_cycle = int(balls_in_cycle)
                ball_ids = list(
                    range(balls_found, balls_found + balls_in_cycle)
                )
                orbits.append(Orbit(ball_ids, index, sequence, length))
                balls_found += balls_in_cycle
            index += 1
        return Analysis(
            self.pattern, self.num_hands, orbits, lcm(cycle_lengths)
        )

    def animation(self):
        return analysis_to_animation(self.analyze())


def analysis_to_animation(analysis):
    CarryEnd = namedtuple("CarryEnd", ("time", "position", "ball"))
    CarryStart = namedtuple("CarryStart", ("time", "position", "ball"))

    _, num_hands, orbits, cycle_length = analysis
    hands = {hand: [] for hand in range(num_hands)}
    ball_paths = {}
    for orbit in orbits:
        ball_ids, start_index, sequence, length = orbit
        balls_in_orbit = len(ball_ids)
        assert int(length / balls_in_orbit) == length / balls_in_orbit
        offset_increment = int(length / balls_in_orbit)
        for ball in ball_ids:
            ball_path = []
            index = start_index
            for segment in sequence:
                height, throw_hand, catch_hand = segment
                duration = height - 1
                if duration:
                    throw_pos = _simple_throw_pos(throw_hand, num_hands)
                    catch_pos = _simple_catch_pos(catch_hand, num_hands)
                else:  # It's a 1.
                    throw_pos = _simple_handoff_pos(
                        throw_hand, catch_hand, num_hands
                    )
                    catch_pos = throw_pos
                (repeats, remainder) = divmod(cycle_length, length)
                assert remainder == 0
                # clone each segment to fill cycle_length
                for i in range(repeats):
                    clone_offset = i * length
                    throw_time = (index + clone_offset) % cycle_length
                    catch_time = (
                        index + duration + clone_offset
                    ) % cycle_length
                    if duration:
                        ball_arc = Arc(
                            throw_time, duration, throw_pos, catch_pos
                        )
                        ball_path.append(ball_arc)
                    # todo: Add velocity info for splined throws.
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
        assert not len(carry_parts) % 2
        carry_parts.sort(key=lambda p: p.time)
        for (i, start) in enumerate(carry_parts):
            end = carry_parts[(i + 1) % len(carry_parts)]
            # carry_parts should alternate between begin and end.
            assert type(start) != type(end)
            duration = (end.time - start.time + cycle_length) % cycle_length
            move = HandMove(start.time, duration, start.position, end.position)
            path.append(move)
            if isinstance(start, CarryStart):
                assert start.ball == end.ball
                ball_paths[start.ball].append(move)
        hand_paths[hand] = path
    for ball_path in ball_paths.values():
        ball_path.sort(key=lambda arc: arc.time)
    for hand in range(num_hands):
        if not hand_paths[hand]:
            print("Hit one!")
            hand_paths[hand] = [
                HandStationary(_simple_throw_pos(hand, num_hands))
            ]

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
        self.assertEqual(
            repr(SiteSwap([4, 4, 1])), repr(SiteSwap.from_string("4, 4,1"))
        )

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

    def test_animation(self):
        # Animations are quite complex to verify, so this just checks that we
        # don't throw while computing them.
        SiteSwap([2, 8]).animation()
        SiteSwap([4, 4, 1]).animation()
        SiteSwap([5, 6, 1]).animation()
        SiteSwap([5, 6, 1], num_hands=3).animation()
        SiteSwap([3]).animation()
        SiteSwap([8], num_hands=5).animation()
        SiteSwap([8]).animation()


def _get_args():
    name = sys.argv[0]
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-u", "--unittest", help="run unit tests", action="store_true"
    )
    parser.add_argument(
        "-t", "--test", help="run current test", action="store_true"
    )
    args, argv = parser.parse_known_args()
    sys.argv[:] = [name] + argv
    return args


def main():
    args = _get_args()
    if args.unittest:
        unittest.main()
    elif args.test:
        analysis = SiteSwap([5, 0, 1]).analyze()
        print("analysis", analysis)
        print("paths", analysis_to_animation(analysis))
        analysis = SiteSwap([5, 0, 1], num_hands=3).analyze()
        print("analysis", analysis)
        print("paths", analysis_to_animation(analysis))


if __name__ == "__main__":
    main()
