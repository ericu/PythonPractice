#!/usr/bin/env python3
import numpy as np  # type: ignore
import matplotlib.pyplot as plt  # type: ignore


def sieve(up_to: int):
    """Sieve code adapted from
    https://code.activestate.com/recipes/117119-sieve-of-eratosthenes/ which is
    available under the PSF license.
    """
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


def spiral_out(square_size: int):
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
                yield np.copy(coords)
                coords += vector
            if edge_size == square_size:
                return
            vector = rotate.dot(vector)


def map_primes(square_size: int):
    count = square_size * square_size
    display = np.zeros([square_size, square_size])
    primes = set(sieve(count + 2))
    generator = spiral_out(square_size)
    for i in range(2, count):
        coords = next(generator)
        if i in primes:
            display[tuple(coords)] = 1
    return display


def plot_primes(square_size: int):
    fig, ax = plt.subplots()

    primes = map_primes(square_size)
    ax.imshow(primes)
    ax.set_title("Primes are marked in yellow.")
    ax.axis("off")
    fig.canvas.set_window_title("Ulam Spiral")
    plt.show()


def map_coords(square_size: int):
    """This is test code to display the spiral path."""
    count = square_size * square_size
    display = np.zeros([square_size, square_size])
    generator = spiral_out(square_size)
    for i in range(count):
        coords = next(generator)
        display[tuple(coords)] = i
    return display


if __name__ == "__main__":
    plot_primes(100)
