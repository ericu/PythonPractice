#!/usr/bin/env python3
import numpy as np

# Note that this file is a very-direct port of some old WebGL code of mine; it
# may still look a little JavaScripty.


def make_tetrahedron_geometry():
    """This tetrahedron is centered at the origin, and its points are on the
    unit sphere."""

    # Start with the point at the origin.
    # Go straight up to make point 0.
    # Go down to the right by 109.5* to make point 1.
    # Rotate around the Y axis by 120* to make point2, then again for point 3.

    point0 = np.array([0, 1.0, 0])
    theta = 109.5 / 360 * 2 * np.pi
    point1 = np.array([np.sin(theta), np.cos(theta), 0])
    phi = 120 / 360 * 2 * np.pi
    point2 = np.array(
        [point1[0] * np.cos(phi), point1[1], point1[0] * np.sin(phi)]
    )
    phi *= 2
    point3 = np.array(
        [point1[0] * np.cos(phi), point1[1], point1[0] * np.sin(phi)]
    )
    points = [point0, point1, point2, point3]
    faces = [0, 1, 3, 0, 3, 2, 0, 2, 1, 1, 2, 3]
    colors = [1, 0, 0, 1, 0, 1, 0, 1, 0, 0, 1, 1, 1, 0, 1, 1]
    return {"points": points, "faces": faces, "colors": colors}


def make_sphere_geometry(n):
    """
    Starting with a tetrahedron, repeat n times:
    * Split each face into 4 triangles.
    * Push the new points out to the unit sphere.
    """
    assert n >= 0
    midpoints = {}
    shape = make_tetrahedron_geometry()
    faces = shape["faces"]
    points = shape["points"]
    for _ in range(n):
        new_faces = []
        # Split each face into 4.
        for face in range(0, len(faces), 3):
            pi0 = faces[face]
            pi1 = faces[face + 1]
            pi2 = faces[face + 2]
            pi01 = get_midpoint(pi0, pi1, points, midpoints)
            pi12 = get_midpoint(pi1, pi2, points, midpoints)
            pi02 = get_midpoint(pi0, pi2, points, midpoints)
            # fmt: off
            new_faces.extend([
                pi0, pi01, pi02,
                pi01, pi1, pi12,
                pi12, pi2, pi02,
                pi01, pi12, pi02
            ])
            # fmt: on
        faces = new_faces
    return {
        "points": points,
        "normals": points,
        "faces": faces,
        "colors": make_simple_colors(points),
    }


def get_midpoint(pi0, pi1, points, midpoints):
    """This is the great-circle midpoint of two points on the unit sphere.
    It'll fail if they're diametrically opposed."""

    def get_midpoint_key(a, b):
        c = a
        d = b
        if a < b:
            c = b
            d = a
        return (c, d)

    def normalize(v):
        norm = np.linalg.norm(v)
        if norm < 0.0001:
            return v
        return v / norm

    s = get_midpoint_key(pi0, pi1)
    if s in midpoints:
        return midpoints[s]
    p_0 = points[pi0]
    p_1 = points[pi1]
    # Normalization projects the point to the surface of the unit sphere.
    temp = normalize(p_0 + p_1)
    index = len(points)
    points.append(temp)
    midpoints[s] = index
    return index


def make_simple_colors(points):
    colors = []
    for point in points:
        red = round(255 * abs(point[0]))
        green = round(255 * abs(point[1]))
        blue = round(255 * abs(point[2]))
        colors.append(red)
        colors.append(green)
        colors.append(blue)
        colors.append(255)
    return colors
