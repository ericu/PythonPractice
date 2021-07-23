#!/usr/bin/python3

import pyglet
from pyglet.gl import * # Requires PyOpenGL PyOpenGL_accelerate
from itertools import chain
import numpy as np
import random
import mcubes # Requires scipy as well
import sys

import shapes

EPSILON = 0.001

def concat(lists):
  return chain.from_iterable(lists)

class AppWindow(pyglet.window.Window):
  def __init__(self):
    display = pyglet.canvas.get_display()
    screen = display.get_default_screen()
    template = pyglet.gl.Config(alpha_size=8, depth_size=24, sample_buffers=1,
                                samples=4, stencil_size=0)
    config = screen.get_best_config(template)
    super().__init__(config=config, resizable=True)
    self.balls = [Ball(0, 0, 0) for i in range(3)]
    self.shapes = [Box()] + self.balls
    # This appears to draw more smoothly at 65fps rather than 60fps; I'm
    # guessing it's syncing to the screen refresh, and so this is giving me a
    # true 60fps, whereas asking for 60fps may miss a frame here and there.
    # todo: A frame-rate counter would tell me whether that's the case.
    self.expected_frame_rate = 1 / 65.0
    pyglet.clock.schedule_interval(lambda dt: self.update(dt),
                                   self.expected_frame_rate)

  def on_draw(self):

      self.clear()

      glMatrixMode(GL_PROJECTION)
      glLoadIdentity()
      gluPerspective(85, self.width / self.height, 0.1, 100)

      glMatrixMode(GL_MODELVIEW)
      glLoadIdentity()
      glTranslatef(0, 0, -2)
      # Angle, axis
#      glRotatef(45, 0, 1, 0)

      glEnable(GL_DEPTH_TEST)
      for shape in self.shapes:
          shape.draw()

      # TODO: This is supposed to be slower than pre-rendering to an array.
      f = lambda x, y, z: self.field_strength(np.array([x, y, z]))
      vertices, triangles = mcubes.marching_cubes_func((-1, -1, -1), # min
                                                       (1, 1, 1), # max
                                                       25, 25, 25, # samples
                                                       f, 0.85)
      surface_vertexes = tuple(concat(vertices))
      surface_indexes = tuple(concat(triangles))
      pyglet.graphics.draw_indexed(len(surface_vertexes) // 3,
                                   pyglet.gl.GL_TRIANGLES,
                                   surface_indexes,
                                   ('v3f', surface_vertexes))
      print(vertices, triangles)


  def on_resize(self, arg, arg2):
      glViewport(0, 0, self.width, self.height)
      return pyglet.event.EVENT_HANDLED


  def update(self, dt):
      for shape in self.shapes:
          shape.update(dt / self.expected_frame_rate)

  def field_strength(self, coords):
    strength = 0
    for ball in self.balls:
      strength += ball.field_strength(coords)
    return strength


class Shape():

  def draw(self):
    raise NotImplementedError()

  def update(self, frame_scaling):
    pass

class Box(Shape):
  def __init__(self):
    self.wall_coords = [
      -1, -1, -1,
      -1, -1,  1,
      -1,  1, -1,
      -1,  1,  1,
       1, -1, -1,
       1, -1,  1,
       1,  1, -1,
       1,  1,  1,
    ]
    self.wall_indices = [
      0, 1, 3, 2, # Left wall
      4, 5, 7, 6, # Right wall
      2, 3, 7, 6, # Ceiling
      0, 1, 5, 4, # Floor
    ]
    floor_color = (64, 64, 64)
    ceiling_color = (192, 192, 192)
    self.wall_colors = tuple((2 * floor_color + 2 * ceiling_color) * 2)
    self.wall_vertex_count = len(self.wall_coords) // 3
    self.back_indices = [0, 2, 6, 4]
    self.back_colors = tuple(8 * [32, 32, 64])

  def draw(self):
    pyglet.graphics.draw_indexed(self.wall_vertex_count, pyglet.gl.GL_QUADS,
                                 self.wall_indices,
                                 ('v3f', self.wall_coords),
                                 ('c3B', self.wall_colors))
    pyglet.graphics.draw_indexed(self.wall_vertex_count, pyglet.gl.GL_QUADS,
                                 self.back_indices,
                                 ('v3f', self.wall_coords),
                                 ('c3B', self.back_colors))

class Ball(Shape):
  def __init__(self, x, y, z):
    self.coords = np.array([float(x), float(y), float(z)])
    self.size = 0.1
    geometry = shapes.make_sphere_geometry(4)
    self.vertices = tuple([i for i in concat(geometry['points'])])
    self.indices = tuple(geometry['faces'])
    self.colors = geometry['colors']
    # Not uniform over the sphere, but fine for this application.
    speed = 0.03
    self.velocity = np.array([
      random.random() * speed,
      random.random() * speed,
      random.random() * speed
    ])
    self.charge = 1.0

  def draw(self):
    glPushMatrix()
    glTranslatef(self.coords[0], self.coords[1], self.coords[2])
    glScalef(self.size, self.size, self.size)
    pyglet.graphics.draw_indexed(len(self.vertices) // 3,
                                 pyglet.gl.GL_TRIANGLES,
                                 self.indices,
                                 ('v3f', self.vertices),
                                 ('c4B', self.colors))
    glPopMatrix()

  def update(self, frame_scaling):
    self.coords += self.velocity * frame_scaling
    for (index, component) in enumerate(self.coords):
      upper_bound = 1 - self.size
      lower_bound = -1 + self.size
      if component > upper_bound:
        self.coords[index] += 2 * (upper_bound - component)
        self.velocity[index] = -self.velocity[index]
      elif component < lower_bound:
        self.coords[index] += 2 * (lower_bound - component)
        self.velocity[index] = -self.velocity[index]
    
  def field_strength(self, coords):
      distance = np.linalg.norm(coords - self.coords)
      if (distance < self.size + EPSILON):
        return self.charge
      return self.charge / ((1 + distance - self.size) ** 3)

if __name__ == '__main__':
  window = AppWindow()
  pyglet.app.run()
