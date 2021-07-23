import numpy as np

# This tetrahedron is centered at the origin, and its points are on the unit
# sphere.
def make_tetrahedron_geometry():
  # Start with the point at the origin.
  # Go straight up to make point 0.
  # Go down to the right by 109.5* to make point 1.
  # Rotate around the Y axis by 120* to make point2, then again for point 3.
  point0 = np.array([0, 1.0, 0])
  theta = 109.5/360 * 2 * np.pi
  point1 = np.array([np.sin(theta), np.cos(theta), 0])
  phi = 120/360 * 2 * np.pi
  point2 = np.array([
    point1[0] * np.cos(phi),
    point1[1],
    point1[0] * np.sin(phi)])
  phi *= 2
  point3 = np.array([
    point1[0] * np.cos(phi),
    point1[1],
    point1[0] * np.sin(phi)])
  points = [point0, point1, point2, point3]
  faces = [
    0, 1, 3,
    0, 3, 2,
    0, 2, 1,
    1, 2, 3
  ]
  colors = [
    1, 0, 0, 1,
    0, 1, 0, 1,
    0, 0, 1, 1,
    1, 0, 1, 1
  ]
  return {'points':points, 'faces':faces, 'colors':colors}

def make_sphere_geometry(n):
  assert(n >= 0)
  midpoints = {}
  shape = make_tetrahedron_geometry()
  faces = shape['faces']
  points = shape['points']
  for i in range(n):
    newFaces = []
    # Split each face into 4.
    for f in range(0, len(faces), 3):
      pi0 = faces[f]
      pi1 = faces[f + 1]
      pi2 = faces[f + 2]
      pi01 = get_midpoint(pi0, pi1, points, midpoints)
      pi12 = get_midpoint(pi1, pi2, points, midpoints)
      pi02 = get_midpoint(pi0, pi2, points, midpoints)
      newFaces.append(pi0)
      newFaces.append(pi01)
      newFaces.append(pi02)
      newFaces.append(pi01)
      newFaces.append(pi1)
      newFaces.append(pi12)
      newFaces.append(pi12)
      newFaces.append(pi2)
      newFaces.append(pi02)
      newFaces.append(pi01)
      newFaces.append(pi12)
      newFaces.append(pi02)
    faces = newFaces
  return { 'points':points, 'normals':points,
           'faces':faces, 'colors':makeSimpleColors(points) }

def get_midpoint_string(a, b):
  c = a
  d = b
  if (a < b):
    c = b
    d = a
  return f'M{c}":"{d}'

# This is the great-circle midpoint of two points on the unit sphere.  It'll
# fail if they're diametrically opposed.
def get_midpoint(pi0, pi1, points, midpoints):
  s = get_midpoint_string(pi0, pi1)
  if s in midpoints:
    return midpoints[s]
  else:
    p0 = points[pi0]
    p1 = points[pi1]
    # This normalization projects the point to the surface of the unit sphere.
    temp = normalize(p0 + p1)
    index = len(points)
    points.append(temp)
    midpoints[s] = index
    return index

def normalize(v):
  norm = np.linalg.norm(v)
  if norm < 0.0001:
    return v
  return v / norm

def makeSimpleColors(points):
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