#!/usr/bin/python3

from itertools import chain
from collections import namedtuple
import concurrent.futures
import random
import sys
import time

import numpy as np
import mcubes  # Requires scipy as well
import pyglet
from pyglet import gl  # Requires PyOpenGL PyOpenGL_accelerate

import shapes

EPSILON = 0.001
EXPECTED_FRAME_RATE = 1 / 65.0


def concat(lists):
    return chain.from_iterable(lists)


BallFieldInfo = namedtuple("BallFieldInfo", ("charge", "size", "coords"))

def get_field_for_point(field_info, coords):
    strength = 0
    for shape in field_info:
        distance = np.linalg.norm(coords - shape.coords)
        if distance < shape.size + EPSILON:
            strength += shape.charge
        else:
            strength += shape.charge / ((1 + 4 * (distance - shape.size)) ** 3)
    return strength

def get_field_for_slice(field_info, samples, i):
    # start_time = time.time()
    samples_imaginary = samples * 1j
    x = i * 2 / (samples - 1) - 1
    y_values, z_values = np.mgrid[
        -1:1:samples_imaginary,
        -1:1:samples_imaginary,
    ]
    output = np.zeros([samples, samples])
    for j in range(samples):
        for k in range(samples):
            y = y_values[j][k]
            z = z_values[j][k]
            output[j][k] = get_field_for_point(field_info, np.array([x, y, z]))
    return output

# pylint: disable=abstract-method
class AppWindow(pyglet.window.Window):
    def __init__(self):
        display = pyglet.canvas.get_display()
        screen = display.get_default_screen()
        template = gl.Config(
            alpha_size=8,
            depth_size=24,
            sample_buffers=1,
            samples=4,
            stencil_size=0,
        )
        config = screen.get_best_config(template)
        super().__init__(config=config, resizable=True)
        self.balls = [Ball(0, 0, 0) for i in range(10)]
        self.shapes = [Box()] + self.balls
        pyglet.clock.schedule_interval(
            lambda delta_t: self.update(delta_t), EXPECTED_FRAME_RATE
        )
        self.draw_surface = False
        self.surface_to_draw = None
        self.draw_voxels = False
        self.voxels_to_draw = None
        self.samples = 30

    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.C:
            field = self.field_over_matrix()
            self.surface_to_draw = self.capture_surface(field)
        elif symbol == pyglet.window.key.V:
            field = self.field_over_matrix()
            self.voxels_to_draw = self.capture_voxels(field)
        elif symbol == pyglet.window.key.B:
            field = self.field_over_matrix()
            self.surface_to_draw = self.capture_surface(field)
            self.voxels_to_draw = self.capture_voxels(field)
        elif symbol == pyglet.window.key.D:
            self.draw_surface = not self.draw_surface
        elif symbol == pyglet.window.key.E:
            self.draw_voxels = not self.draw_voxels
        elif symbol == pyglet.window.key.Q:
            sys.exit()

    def field_over_matrix(self):
        start_time = time.time()
        field_info = list(filter(None,
                                 [shape.field_info() for shape in self.shapes]))
        
        # Another approach to optimization is to try to reduce the number of
        # points that need calculation.  We could start with anything within
        # some distance of a ball, and then look at all uncomputed neighbors of
        # points with values above the cutoff, repeating until there are none
        # left uncomputed.  That approach likely wouldn't parallelize well, as
        # we'd have to pass lots of incremental state back and forth.
        output = [None] * self.samples

        with concurrent.futures.ProcessPoolExecutor() as executor:
            futures = { executor.submit(get_field_for_slice, field_info,
                                        self.samples, i) : i
                        for i in range(self.samples) }
            for future in concurrent.futures.as_completed(futures):
                i = futures[future]
                output[i] = future.result()

        end_time = time.time()
        print('field', end_time - start_time)

        return np.array(output)

    def capture_voxels(self, field):
        self.draw_voxels = True

        values_in_set = field > 0.6

        samples_imaginary = self.samples * 1j
        x_values, y_values, z_values = np.mgrid[
            -1:1:samples_imaginary,
            -1:1:samples_imaginary,
            -1:1:samples_imaginary,
        ]
        coords_list = []
        for i in range(self.samples):
            for j in range(self.samples):
                for k in range(self.samples):
                    if values_in_set[i][j][k]:
                        x = x_values[i][j][k]
                        y = y_values[i][j][k]
                        z = z_values[i][j][k]
                        coords_list.append((x, y, z))

        # N samples means a range of [0...N-1], so a width of N-1 units.
        v = VoxelList(coords_list, 1 / (self.samples - 1))
        return v

    def capture_surface(self, field):
        self.draw_surface = True

        vertices, triangles = mcubes.marching_cubes(field, 0.6)
        surface_vertexes = tuple(
            v * 2 / (self.samples - 1) - 1 for v in concat(vertices)
        )
        # The indices appear to be ints, but when I pass them in and they have
        # math done on them [adding to another int], they turn into floats,
        # which causes something expecting ints to blow up.  This explicit cast
        # fixes that.
        surface_vertex_count = len(surface_vertexes) // 3
        surface_indices = tuple(map(int, concat(triangles)))
        surface_colors = tuple(surface_vertex_count * [64, 64, 192, 128])
        batch = pyglet.graphics.Batch()
        batch.add_indexed(
            surface_vertex_count,
            gl.GL_TRIANGLES,
            None,
            surface_indices,
            ("v3f", surface_vertexes),
            ("c4B", surface_colors),
        )
        return batch

    def on_draw(self):

        self.clear()

        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.gluPerspective(85, self.width / self.height, 0.1, 100)

        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()
        gl.glTranslatef(0, 0, -2)
        # Angle, axis
        #      gl.glRotatef(45, 0, 1, 0)

        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glEnable(gl.GL_BLEND)
        gl.glEnable(gl.GL_DEPTH_TEST)
        for shape in self.shapes:
            shape.draw()

        if self.draw_surface and self.surface_to_draw:
            self.surface_to_draw.draw()
        if self.draw_voxels and self.voxels_to_draw:
            self.voxels_to_draw.draw()

    def on_resize(self, width, height):
        gl.glViewport(0, 0, width, height)
        return pyglet.event.EVENT_HANDLED

    def update(self, delta_t):
        for shape in self.shapes:
            shape.update(delta_t / EXPECTED_FRAME_RATE)

    def field_strength(self, coords):
        strength = 0
        for ball in self.balls:
            strength += ball.field_strength(coords)
        return strength


class Shape:
    def draw(self):
        raise NotImplementedError()

    def update(self, frame_scaling):
        pass

    def field_info(self):
        return None

class Box(Shape):
    def __init__(self):
        # fmt: off
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
            0, 1, 3, 2,  # Left wall
            4, 5, 7, 6,  # Right wall
            2, 3, 7, 6,  # Ceiling
            0, 1, 5, 4,  # Floor
        ]
        # fmt: on
        floor_color = (64, 64, 64)
        ceiling_color = (192, 192, 192)
        self.wall_colors = tuple((2 * floor_color + 2 * ceiling_color) * 2)
        self.wall_vertex_count = len(self.wall_coords) // 3
        self.back_indices = [0, 2, 6, 4]
        self.back_colors = tuple(8 * [32, 32, 64])

    def draw(self):
        pyglet.graphics.draw_indexed(
            self.wall_vertex_count,
            gl.GL_QUADS,
            self.wall_indices,
            ("v3f", self.wall_coords),
            ("c3B", self.wall_colors),
        )
        pyglet.graphics.draw_indexed(
            self.wall_vertex_count,
            gl.GL_QUADS,
            self.back_indices,
            ("v3f", self.wall_coords),
            ("c3B", self.back_colors),
        )


class VoxelList(Shape):
    def __init__(self, coords_list, size):
        self.coords_list = coords_list
        self.size = size
        # fmt: off
        wall_coords_template = np.array([
            [-1, -1, -1],
            [-1, -1,  1],
            [-1,  1, -1],
            [-1,  1,  1],
            [ 1, -1, -1],
            [ 1, -1,  1],
            [ 1,  1, -1],
            [ 1,  1,  1],
        ]) * size
        wall_indices_template = np.array([
            0, 1, 3, 2,  # Left wall
            4, 5, 7, 6,  # Right wall
            2, 3, 7, 6,  # Ceiling
            0, 1, 5, 4,  # Floor
            1, 3, 7, 5,  # Front
        ])
        wall_coords = []
        wall_indices = []
        num_vertices_in_template = len(wall_coords_template)
        for (index, coords) in enumerate(coords_list):
            wall_coords.append(concat(wall_coords_template + coords))
            wall_indices.append(wall_indices_template +
                                index * num_vertices_in_template)
        self.wall_coords = tuple(concat(wall_coords))
        self.wall_indices = tuple(concat(wall_indices))

        # fmt: on
        self.wall_vertex_count = len(self.wall_coords) // 3
        self.wall_colors = self.wall_vertex_count * (64, 192, 64, 128)

    def draw(self):
        pyglet.graphics.draw_indexed(
            self.wall_vertex_count,
            gl.GL_QUADS,
            self.wall_indices,
            ("v3f", self.wall_coords),
            ("c4B", self.wall_colors),
        )


class Ball(Shape):
    def __init__(self, x, y, z):
        self.coords = np.array([float(x), float(y), float(z)])
        self.size = 0.1
        geometry = shapes.make_sphere_geometry(4)
        self.vertices = tuple(i for i in concat(geometry["points"]))
        self.indices = tuple(geometry["faces"])
        self.colors = geometry["colors"]
        # Not uniform over the sphere, but fine for this application.
        speed = 0.5 * EXPECTED_FRAME_RATE

        self.velocity = np.array(
            [
                random.random() * speed,
                random.random() * speed,
                random.random() * speed,
            ]
        )
        self.charge = 1.0

    def draw(self):
        gl.glPushMatrix()
        gl.glTranslatef(self.coords[0], self.coords[1], self.coords[2])
        gl.glScalef(self.size, self.size, self.size)
        pyglet.graphics.draw_indexed(
            len(self.vertices) // 3,
            gl.GL_TRIANGLES,
            self.indices,
            ("v3f", self.vertices),
            ("c4B", self.colors),
        )
        gl.glPopMatrix()

    def update(self, frame_scaling):
        self.coords += self.velocity * frame_scaling
        wall_buffer = 0.15
        for (index, component) in enumerate(self.coords):
            upper_bound = 1 - wall_buffer
            lower_bound = -1 + wall_buffer
            if component > upper_bound:
                self.coords[index] += 2 * (upper_bound - component)
                self.velocity[index] = -self.velocity[index]
            elif component < lower_bound:
                self.coords[index] += 2 * (lower_bound - component)
                self.velocity[index] = -self.velocity[index]

    def field_strength(self, coords):
        distance = np.linalg.norm(coords - self.coords)
        if distance < self.size + EPSILON:
            return self.charge
        return self.charge / ((1 + 4 * (distance - self.size)) ** 3)

    def field_info(self):
      return BallFieldInfo(self.charge, self.size, self.coords)

if __name__ == "__main__":
    window = AppWindow()
    pyglet.app.run()
