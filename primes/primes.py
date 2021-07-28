#!/usr/bin/python3
import numpy as np
import matplotlib.pyplot as plt

# Sieve code adapted from
# https://code.activestate.com/recipes/117119-sieve-of-eratosthenes/ which is
# licensed under the PSF license.
def sieve(up_to):
    composites = {}
    cur = 2
    primes = []
    while cur < up_to:
        if cur not in composites:
            primes.append(cur)
            composites[cur * cur] = [cur]  # Cur is the only factor of cur^2.
        else:
            for factor in composites[cur]:
                composites.setdefault(cur + factor, []).append(factor)
            del composites[cur]
        cur += 1
    return primes


def spiral_out(square_size):
    """This generates a list of coordinates spiraling outward, clockwise, from
    the center of a square.  It terminates when it's covered the whole square.

    In the pattern below, each character is one such coordinate pair, working
    outward from 'a'.
    The capitalization change represents the second loop level, and the letter
    increment represents the loop over edge_size.  Note that the traced shape is
    square only after the "lowercase" letter sequence, before incrementing to
    "uppercase"; that's why we return out of the innermost loop.

        dddd
        CbbB
        CAaB
        Cccc
    """

    center = square_size // 2
    coords = np.array([center, center])
    vector = np.array([0, -1])
    rotate = np.array([[0, 1], [-1, 0]])
    for edge_size in range(1, square_size + 1):
        for _ in ["lowercase", "uppercase"]:
            for _ in range(edge_size):
                print(coords)
                yield np.copy(coords)
                coords += vector
            if edge_size == square_size:
                return
            vector = rotate.dot(vector)


def map_primes(square_size):
    count = square_size * square_size
    display = np.zeros([square_size, square_size])
    primes = set(sieve(count + 2))
    generator = spiral_out(square_size)
    for i in range(2, count):
        coords = next(generator)
        if i in primes:
            display[tuple(coords)] = 1
    return display

def plot_primes(square_size):
    """ Adapted from https://matplotlib.org/stable/gallery/mplot3d/3d_bars.html;
    see https://github.com/matplotlib/matplotlib/blob/master/LICENSE/LICENSE.
    """
    fig = plt.figure(figsize=(6, 6))
    plot = fig.add_subplot(111, projection='3d')

    _x = np.arange(square_size)
    _y = np.arange(square_size)
    _xx, _yy = np.meshgrid(_x, _y)
    x, y = _xx.ravel(), _yy.ravel()

    primes = map_primes(square_size)
    top = primes.ravel()
    bottom = np.zeros_like(top)
    width = depth = 1

    plot.bar3d(x, y, bottom, width, depth, top, shade=True)
    plot.set_title('Prime spiral')

    plt.show()


def map_coords(square_size):
    """ This is test code to display the spiral path. """
    count = square_size * square_size
    display = np.zeros([square_size, square_size])
    generator = spiral_out(square_size)
    for i in range(count):
        coords = next(generator)
        display[tuple(coords)] = i
    return display

if __name__ == "__main__":
    print(map_coords(3))
