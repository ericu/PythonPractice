#!/usr/bin/python3

import pyglet

class AppWindow(pyglet.window.Window):
  def __init__(self):
    display = pyglet.canvas.get_display()
    screen = display.get_default_screen()
    template = pyglet.gl.Config(alpha_size=8, depth_size=24, sample_buffers=1,
                                samples=4, stencil_size=0)
    config = screen.get_best_config(template)
    super().__init__(config=config)

  # Maps coords in -1,-1 to 1,1 to the window
  def map_coords_to_window(self, x, y):
    return ((x + 1) * self.width / 2, (y + 1) * self.height / 2)

  def on_draw(self):
      self.clear()
      # First arg is number of vertices, not triangles; it figures out triangle
      # count from the array of indices.
      w = self.width / 2
      h = self.height / 2
      c0 = self.map_coords_to_window(-0.5, -0.5)
      c1 = self.map_coords_to_window(-0.5,  0.5)
      c2 = self.map_coords_to_window( 0.5,  0.5)
      c3 = self.map_coords_to_window( 0.5, -0.5)
      coords = c0 + c1 + c2 + c3
      pyglet.graphics.draw_indexed(4, pyglet.gl.GL_TRIANGLES,
                                   [0, 1, 2, 0, 2, 3],
                                   ('v2f', coords),
                                   ('c3B', (0, 0, 255,
                                            0, 255, 0,
                                            255, 0, 0,
                                            0, 255, 255)))

if __name__ == '__main__':
  window = AppWindow()
  print(f'dimensions ({window.width},{window.height})')
  context = window.context
  config = context.config
#  print(config)
  pyglet.app.run()
