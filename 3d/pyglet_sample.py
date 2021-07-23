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
#    self.cube = Cube((-0.5, 0.5), (-0.5, 0.5), (-0.5, 0.5))
    self.point = Point((0, 0, 0), (255, 128, 64))
#    self.cube2 = Cube((-0.1, 0.1), (-0.1, 0.1), (-0.1, 0.1), (255, 128, 64))

  def on_draw(self):

      self.clear()

      glMatrixMode(GL_PROJECTION)
      glLoadIdentity()
      gluPerspective(95, 1, 0.1, 100)

      glMatrixMode(GL_MODELVIEW)
      glLoadIdentity()
      glTranslatef(0, 0, -1)
      # Angle, axis
#      glRotatef(45, 0, 1, 0)

      glEnable(GL_DEPTH_TEST)
      self.point.draw()
#      self.cube2.draw()
#      self.cube.draw()


  def on_resize(self, arg, arg2):
    glViewport(0, 0, self.width, self.height)
    return pyglet.event.EVENT_HANDLED


class Cube():
  def __init__(self, x_dims, y_dims, z_dims, color=None):
    self.coords = tuple(concat([(x, y, z) for x in x_dims
                                          for y in y_dims
                                          for z in z_dims]))
    self.indices = [
      0, 1, 3, 2, # Left wall
      4, 5, 7, 6, # Right wall
      2, 3, 7, 6, # Ceiling
      0, 1, 5, 4, # Floor
      0, 2, 6, 4 # Back wall
    ]
    if color:
      floor_color = color
      ceiling_color = color
    else:
      floor_color = (64, 64, 64)
      ceiling_color = (192, 192, 192)
    self.colors = tuple((2 * floor_color + 2 * ceiling_color) * 2)
    self.vertex_count = len(self.coords) // 3

  def draw(self):
    pyglet.graphics.draw_indexed(self.vertex_count, pyglet.gl.GL_QUADS,
                                 self.indices,
                                 ('v3f', self.coords),
                                 ('c3B', self.colors))

class Point():
  def __init__(self, coords, color):
    self.coords = coords
    self.color = color
    geometry = shapes.make_sphere_geometry(1)
    self.vertices = tuple([i for i in concat(geometry['points'])])
    self.indices = tuple(geometry['faces'])
    self.colors = tuple([round(f * 255) for f in geometry['colors']])

  def draw(self):
    print('draw point')
    pyglet.graphics.draw_indexed(len(self.vertices) // 3,
                                 pyglet.gl.GL_TRIANGLES,
                                 self.indices,
                                 ('v3f', self.vertices),
                                 ('c4B', self.colors))
    

if __name__ == '__main__':
  window = AppWindow()
  context = window.context
  config = context.config
#  print(config)
  pyglet.app.run()
