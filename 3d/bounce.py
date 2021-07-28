#!/usr/bin/env python3

from itertools import chain
from collections import namedtuple
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
import queue
import random
import sys
import asyncio

import numpy as np
import mcubes  # Requires scipy as well
import pyglet
from pyglet import gl  # Requires PyOpenGL PyOpenGL_accelerate
import psutil

import shapes

EPSILON = 0.001
EXPECTED_FRAME_RATE = 1 / 65.0


def concat(lists):
    return chain.from_iterable(lists)


BallFieldInfo = namedtuple("BallFieldInfo", ("charge", "size", "coords"))
TimingRecord = namedtuple(
    "TimingRecord", ("max_workers", "samples", "duration")
)


def get_field_for_point(field_info, coords):
    strength = 0
    for shape in field_info:
        distance = np.linalg.norm(coords - shape.coords)
        if distance < shape.size + EPSILON:
            strength += shape.charge
        else:
            strength += shape.charge / ((1 + 4 * (distance - shape.size)) ** 3)
    return strength


def get_field_for_slice(field_info, samples, progress_queue, i):
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
    progress_queue.put(i)
    return output


# pylint: disable=abstract-method
class AppWindow(pyglet.window.Window):
    def __init__(self, executor):
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
        self.draw_surface = False
        self.surface_to_draw = None
        self.draw_voxels = False
        self.voxels_to_draw = None
        self.samples = 30
        self.executor = executor
        manager = multiprocessing.Manager()
        # Queue space is cheap, so give it space for all it'll ever hold.
        self.progress_queue = manager.Queue(self.samples)
        self.progress_count = 0
        self.job_in_progress = False
        pyglet.clock.schedule_interval(self.update, EXPECTED_FRAME_RATE)

    def on_key_press(self, symbol, modifiers):
        def get_field_for_handler(handler):
            def wrapped_hander(arg):
                self.job_in_progress = False
                self.progress_count = 0
                handler(arg)

            self.job_in_progress = True
            coroutine = self.field_over_matrix()
            task = asyncio.ensure_future(coroutine)
            task.add_done_callback(wrapped_hander)

        if symbol == pyglet.window.key.C and not self.job_in_progress:

            def handler(future):
                self.surface_to_draw = self.capture_surface(future.result())

            get_field_for_handler(handler)
        elif symbol == pyglet.window.key.V and not self.job_in_progress:

            def handler(future):
                self.voxels_to_draw = self.capture_voxels(future.result())

            get_field_for_handler(handler)
        elif symbol == pyglet.window.key.B and not self.job_in_progress:

            def handler(future):
                self.surface_to_draw = self.capture_surface(future.result())
                self.voxels_to_draw = self.capture_voxels(future.result())

            get_field_for_handler(handler)
        elif symbol == pyglet.window.key.D:
            self.draw_surface = not self.draw_surface
        elif symbol == pyglet.window.key.E:
            self.draw_voxels = not self.draw_voxels
        elif symbol == pyglet.window.key.Q:
            sys.exit()

    async def field_over_matrix(self):
        field_info = list(
            filter(None, [shape.field_info() for shape in self.shapes])
        )

        # Another approach to optimization would be to try to reduce the number
        # of points that need calculation.  We could start with anything within
        # some distance of a ball, and then look at all uncomputed neighbors of
        # points with values above the cutoff, repeating until there are none
        # left uncomputed.  However, that approach likely wouldn't parallelize
        # well, as we'd have to pass lots of incremental state back and forth.
        output = [None] * self.samples

        futures = [
            asyncio.get_event_loop().run_in_executor(
                self.executor,
                get_field_for_slice,
                field_info,
                self.samples,
                self.progress_queue,
                i,
            )
            for i in range(self.samples)
        ]
        await asyncio.wait(futures, return_when=asyncio.FIRST_EXCEPTION)
        for i, future in enumerate(futures):
            output[i] = future.result()

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
        surface_vertex_count = len(surface_vertexes) // 3
        # The indices appear to be ints, but when I pass them to add_indexed and
        # they have math done on them [adding to another int], they turn into
        # floats, which causes something expecting ints to blow up.  This
        # explicit cast fixes that.
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

    def draw_progress_bar(self):
        try:
            while True:
                self.progress_queue.get_nowait()
                # We can get these late; clear the queue anyway.
                if self.job_in_progress:
                    self.progress_count += 1
        except queue.Empty:
            pass
        if self.progress_count:
            progress_fraction = self.progress_count / self.samples
            gl.glMatrixMode(gl.GL_PROJECTION)
            gl.glLoadIdentity()
            gl.gluOrtho2D(0, 1, 0, 1)
            gl.glMatrixMode(gl.GL_MODELVIEW)
            gl.glLoadIdentity()
            # fmt: off
            progress_height = 0.04
            vertices = (
                0, 0,
                progress_fraction, 0,
                progress_fraction, progress_height,
                0, progress_height
            )
            indices = (
                0, 1, 2, 3
            )
            # fmt: on
            gl.glDisable(gl.GL_DEPTH_TEST)
            pyglet.graphics.draw_indexed(
                len(vertices) // 2,
                gl.GL_QUADS,
                indices,
                ("v2f", vertices),
                ("c3B", 4 * (255, 64, 64)),
            )

    def on_draw(self):

        self.clear()

        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.gluPerspective(85, self.width / self.height, 0.1, 100)

        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()
        gl.glTranslatef(0, 0, -2)

        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glEnable(gl.GL_BLEND)
        gl.glEnable(gl.GL_DEPTH_TEST)
        for shape in self.shapes:
            shape.draw()

        if self.draw_surface and self.surface_to_draw:
            self.surface_to_draw.draw()
        if self.draw_voxels and self.voxels_to_draw:
            self.voxels_to_draw.draw()
        self.draw_progress_bar()

    def on_resize(self, width, height):
        gl.glViewport(0, 0, width, height)
        return pyglet.event.EVENT_HANDLED

    def update(self, delta_t):
        for shape in self.shapes:
            shape.update(delta_t / EXPECTED_FRAME_RATE)


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

    def field_info(self):
        return BallFieldInfo(self.charge, self.size, self.coords)


async def main():
    # Leave 1 for the UI.  Hyperthreading isn't really good enough to
    # eliminate jank--I have to leave a whole physical CPU free.
    max_workers = max(psutil.cpu_count(logical=False) - 1, 1)
    # Note that using the context manager here may not be ideal style; we could
    # theoretically hold on to the executor reference in the AppWindow beyond
    # the life of the context.
    with ProcessPoolExecutor(max_workers=max_workers) as process_executor:
        window = AppWindow(process_executor)
        # We can't use pyglet's standard main loop here, as both it and asyncio
        # want to own the event loop.  This replaces the pyglet main loop with
        # one that does asyncio.sleep to yield to other asyncio threads, instead
        # of whatever pyglet would normally do, which doesn't yield to asyncio.
        while True:
            pyglet.clock.tick()
            for window in pyglet.app.windows:
                window.switch_to()
                window.dispatch_events()
                window.dispatch_event("on_draw")
                window.flip()
            await asyncio.sleep(0)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
