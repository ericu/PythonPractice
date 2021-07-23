#!/usr/bin/python3

import pyglet
from pyglet.gl import *
from itertools import chain

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
    self.cube = Cube((-0.5, 0.5), (-0.5, 0.5), (-0.5, 0.5))

  def on_draw(self):

      self.clear()

      glMatrixMode(GL_PROJECTION)
      glLoadIdentity()
      gluPerspective(90, 1, 0.1, 100)

      glMatrixMode(GL_MODELVIEW)
      glLoadIdentity()
      glTranslatef(0, 0, -1)
      # Angle, axis
      glRotatef(45, 0, 1, 0)

      glEnable(GL_DEPTH_TEST)
      c0 = (-0.5, -0.5)
      c1 = (-0.5,  0.5)
      c2 = ( 0.5,  0.5)
      c3 = ( 0.5, -0.5)
      coords = c0 + c1 + c2 + c3
      pyglet.graphics.draw_indexed(4, pyglet.gl.GL_TRIANGLES,
                                   [0, 1, 2, 0, 2, 3],
                                   ('v2f', coords),
                                   ('c3B', (0, 0, 255,
                                            0, 255, 0,
                                            255, 0, 0,
                                            0, 255, 255)))
      self.cube.draw()

  def on_resize(self, arg, arg2):
    glViewport(0, 0, self.width, self.height)
    return pyglet.event.EVENT_HANDLED


class Cube():
  def __init__(self, x_dims, y_dims, z_dims):
    self.x_dims = x_dims
    self.y_dims = y_dims
    self.z_dims = z_dims

  def draw(self):
    coords = tuple(concat([(x, y, z) for x in self.x_dims
                                     for y in self.y_dims
                                     for z in self.z_dims]))
    print(coords)
    indices = [
      0, 1, 3, 2,
      4, 5, 8, 6, # quads are double-sided, so we can be lazy
    ]
    vertex_count = len(coords) // 3
    print('vertex_count', vertex_count)
    colors = tuple([80, 80, 80] * vertex_count)
    pyglet.graphics.draw_indexed(vertex_count, pyglet.gl.GL_QUADS,
                                 indices,
                                 ('v3f', coords),
                                 ('c3B', colors))


if __name__ == '__main__':
  window = AppWindow()
  print(f'dimensions ({window.width},{window.height})')
  context = window.context
  config = context.config
#  print(config)
  pyglet.app.run()
