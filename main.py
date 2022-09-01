import asyncio
import curses
import os
import random
import time
from itertools import cycle

from fire_animation import fire
from curses_tools import draw_frame, read_controls, get_frame_size
from space_garbage import fly_garbage


TIC_TIMEOUT = 0.1
STAR_SYMBOLS = '+*.:'
STARTS_NUM = 160


async def sleep(tics=1):

    for _ in range(tics):
        await asyncio.sleep(0)


async def blink(canvas, row, column, timeout, symbol='*'):
    star_stages = [
        (curses.A_DIM, 20),
        (curses.A_NORMAL, 3),
        (curses.A_BOLD, 2),
        (curses.A_NORMAL, 3),
    ]
    await sleep(timeout)
    while True:
        for appearance, tics_num in star_stages:
            for _ in range(tics_num):
                canvas.addch(row, column, symbol, appearance)
                await sleep()


async def animate_spaceship(canvas, frames):
    canvas_height, canvas_width = canvas.getmaxyx()
    frame_rows, frame_cols = get_frame_size(frames[0])

    current_row = canvas_height // 2
    current_column = canvas_width // 2 - frame_cols // 2

    for frame in cycle(frames):
        for _ in range(2):
            row_dir, col_dir, space_pressed = read_controls(canvas)
            current_row += row_dir
            current_column += col_dir

            if current_column < 1:
                current_column = 1
            elif current_column > (canvas_width - frame_cols - 1):
                current_column = canvas_width - frame_cols - 1
            if current_row < 1:
                current_row = 1
            elif current_row > (canvas_height - frame_rows - 1):
                current_row = canvas_height - frame_rows - 1

            draw_frame(canvas, current_row, current_column, frame)
            await sleep()
            draw_frame(canvas, current_row, current_column, frame,
                       negative=True)


async def fill_orbit_with_garbage(canvas, canvas_width, frames):

    while True:
        current_frame = random.choice(frames)
        frame_height, frame_width = get_frame_size(current_frame)

        coroutines.append(fly_garbage(canvas,
                                      random.randint(1,
                                                     canvas_width - frame_width - 1),
                                      current_frame))
        await sleep(random.randint(5, 20))


def draw(canvas):
    global coroutines
    frame_files = os.listdir('rocket_frames')
    frames = []
    for file_name in frame_files:
        with open(os.path.join('rocket_frames', file_name)) as file:
            frame = file.read()
            frames.append(frame)

    garbage_frames_files = os.listdir('garbage')
    garbage_frames = []
    for file_name in garbage_frames_files:
        with open(os.path.join('garbage', file_name)) as file:
            garbage_frame = file.read()
            garbage_frames.append(garbage_frame)

    canvas_height, canvas_width = canvas.getmaxyx()
    coroutines = []

    for star in range(STARTS_NUM):
        coroutines.append(
            blink(canvas,
                  random.randint(1, canvas_height - 2),
                  random.randint(1, canvas_width - 2),
                  random.randint(0, 20),
                  symbol=random.choice(STAR_SYMBOLS),
                  ))
    coroutines.append(fire(canvas,
                           canvas_height // 2,
                           canvas_width // 2,
                           rows_speed=-0.5))
    coroutines.append(animate_spaceship(canvas, frames))
    coroutines.append(fill_orbit_with_garbage(canvas,
                                              canvas_width,
                                              garbage_frames))

    canvas.border()
    canvas.nodelay(True)
    curses.curs_set(False)
    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        canvas.refresh()
        time.sleep(TIC_TIMEOUT)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
