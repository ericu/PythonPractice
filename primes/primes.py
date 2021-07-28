#!/usr/bin/python3
import numpy as np
import matplotlib.pyplot as plt

# ..................................................
# ..................................................
# ..................................................
# ..................................................
# ..................................................
# ..................................................
# ..................................................
# ..................................................
# ..................................................
# .....................54444........................
# .....................53224........................
# .....................53124........................
# .....................53124........................
# .....................53334........................
# .....................55555........................
# ..................................................
# ..................................................
# ..............................544446..............
# ..............................532246..............
# ..............................531246..............
# ..............................531246..............
# ..............................533346..............
# ..............................555556..............
# ..................................................
# ..................................................
# ..................................................
# ..................................................

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
    """This generates a list of coordinates spiraling outward,
    counterclockwise, from the center of a square.  It terminates when it's
    covered the whole square."""
    halfway = (square_size + 1) // 2 - 1
    coords = np.array([halfway, halfway])
    vector = np.array([1, 0])
    rotate = np.array([[0, -1], [1, 0]])
    for edge_size in range(1, square_size + 1):
        for _ in [0, 1]:
            for _ in range(edge_size):
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
    # setup the figure and axes
    fig = plt.figure(figsize=(6, 6))
    ax1 = fig.add_subplot(111, projection='3d')

    # fake data
    _x = np.arange(square_size)
    _y = np.arange(square_size)
    _xx, _yy = np.meshgrid(_x, _y)
    x, y = _xx.ravel(), _yy.ravel()

    primes = map_primes(square_size)
    top = primes.ravel()
    bottom = np.zeros_like(top)
    width = depth = 1

    print('x', x)
    print('y', y)
    print('bottom', bottom)
    print('width', width)
    print('depth', depth)
    print('top', top)
    print('primes', primes)
    ax1.bar3d(x, y, bottom, width, depth, top, shade=True)
    ax1.set_title('Shaded')

    plt.show()


if __name__ == "__main__":
    plot_primes(40)
