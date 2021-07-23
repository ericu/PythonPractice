#!/usr/bin/python3

import pyglet
from pyglet.gl import *
from itertools import chain

import shapes

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
    self.shapes = [
      Box(),
      Point(0.5, 0, 0),
      Point(-0.5, 0.3, 0.4)
    ]
#    self.cube2 = Box((-0.1, 0.1), (-0.1, 0.1), (-0.1, 0.1), (255, 128, 64))

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
#      self.cube2.draw()
#      self.cube.draw()


  def on_resize(self, arg, arg2):
    glViewport(0, 0, self.width, self.height)
    return pyglet.event.EVENT_HANDLED

class Shape():

  def draw():
    raise NotImplementedError()

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

class Point(Shape):
  def __init__(self, x, y, z):
    self.coords = (x, y, x)
    self.size = 0.1
    geometry = shapes.make_sphere_geometry(4)
    self.vertices = tuple([i for i in concat(geometry['points'])])
    self.indices = tuple(geometry['faces'])
    self.colors = geometry['colors']

  def draw(self):
    glPushMatrix()
    glTranslatef(*self.coords)
    glScalef(self.size, self.size, self.size)
    pyglet.graphics.draw_indexed(len(self.vertices) // 3,
                                 pyglet.gl.GL_TRIANGLES,
                                 self.indices,
                                 ('v3f', self.vertices),
                                 ('c4B', self.colors))
    glPopMatrix()

if __name__ == '__main__':
  window = AppWindow()
  pyglet.app.run()
