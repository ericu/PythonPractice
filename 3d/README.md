This is me playing with OpenGL, Pyglet, Numpy, and asyncio/concurrent.
You'll likely need to 'pip3 install' or otherwise grab:

* PyOpenGL
* PyOpenGL_accelerate
* pyglet
* PyMCubes
* scipy
* psutil

It bounces a bunch of balls around a box and computes the field around the balls
as if they were [non-interacting] charged particles.

Keys it understands:
* c: Generate a marching-cubes outline of the field.
* v: Generate a voxel-based outline of the field.
* b: Generate both kinds of outlines simultaneously.
* d: Toggle display of the last marching-cubes outline on or off.
* e: Toggle display of the last voxel outline on or off.
* q: Quit

Computing the field is done in a background process, so there will be a small
pause while it's generated, but the animation shouldn't be interrupted.

![screen capture of the running program](bounce.gif)
