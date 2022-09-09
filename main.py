import asyncio
import curses
import os
import random
import time
from itertools import cycle

from curses_tools import (draw_frame, read_controls, get_frame_size)
from explosion import explode
from game_scenario import get_garbage_delay_tics, PHRASES
from obstacles import Obstacle
from physics import update_speed


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


async def show_year(canvas):
    global year
    canvas_height, canvas_width = canvas.getmaxyx()
    previous_phrase = ''

    while True:
        message = 'Year: {} {}'
        row = canvas_height - 2
        column = 2
        canvas.addstr(row, column,
                      message.format(
                          year,
                          PHRASES.get(year, len(previous_phrase)*' ')
                      ))
        previous_phrase = PHRASES.get(year) or ''
        await sleep(15)
        year += 1


async def animate_spaceship(canvas, frames):
    canvas_height, canvas_width = canvas.getmaxyx()
    frame_rows, frame_cols = get_frame_size(frames[0])

    current_row = canvas_height // 2
    current_column = canvas_width // 2 - frame_cols // 2

    for frame in cycle(frames):
        for _ in range(2):
            row_dir, col_dir, space_pressed = read_controls(canvas)

            if year >= 2020 and space_pressed:
                coroutines.append(fire(canvas,
                                       current_row,
                                       current_column + frame_cols // 2,
                                       rows_speed=-0.5))

            row_speed = col_speed = 0
            row_speed, col_speed = update_speed(row_speed, col_speed, row_dir,
                                                col_dir)
            current_row += row_speed
            current_column += col_speed

            left_edge, right_edge = 1, canvas_width - frame_cols - 1
            current_column = max(left_edge, min(current_column, right_edge))

            upper_edge, lower_edge = 1, canvas_height - frame_rows - 1
            current_row = max(upper_edge, min(current_row, lower_edge))

            draw_frame(canvas, current_row, current_column, frame)
            await sleep()
            draw_frame(canvas, current_row, current_column, frame,
                       negative=True)
            for obstacle in obstacles:
                if obstacle.has_collision(current_row, current_column):
                    coroutines.append(show_game_over(canvas))
                    return


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""
    global obstacles_in_last_collisions
    obstacles_in_last_collisions = []

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed

        for obstacle in obstacles:
            if obstacle.has_collision(row,
                                      column,
                                      obj_size_rows=1,
                                      obj_size_columns=1):
                obstacles_in_last_collisions.append(obstacle)
                obstacle_center_row = obstacle.row + obstacle.rows_size // 2
                obstacle_center_column = obstacle.column + obstacle.columns_size // 2
                coroutines.append(
                    explode(canvas, obstacle_center_row, obstacle_center_column)
                )
                return


async def fly_garbage(canvas, column, garbage_frame, frame_col_coord,
                      speed=0.5):
    """
    Animate garbage, flying from top to bottom. Сolumn position will
    stay same, as specified on start.
    """
    frame_height, frame_width = get_frame_size(garbage_frame)
    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, 0)
    column = min(column, columns_number - 1)

    row = 0

    while row < rows_number:
        draw_frame(canvas, row, column, garbage_frame)
        obstacle = Obstacle(row, frame_col_coord, frame_height, frame_width)
        obstacles.append(obstacle)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, garbage_frame, negative=True)
        obstacles.remove(obstacle)
        if obstacle in obstacles_in_last_collisions:
            obstacles_in_last_collisions.remove(obstacle)
            return
        row += speed


async def fill_orbit_with_garbage(canvas, canvas_width, frames):

    while True:
        if year > 1961:
            current_frame = random.choice(frames)
            frame_height, frame_width = get_frame_size(current_frame)
            frame_col_coord = random.randint(1, canvas_width - frame_width - 1)

            coroutines.append(fly_garbage(canvas,
                                          frame_col_coord,
                                          current_frame,
                                          frame_col_coord))
            await sleep(get_garbage_delay_tics(year))
        else:
            await sleep()


async def show_game_over(canvas):
    with open('frames/game_over.txt') as file:
        game_over_frame = file.read()

    canvas_height, canvas_width = canvas.getmaxyx()
    frame_height, frame_width = get_frame_size(game_over_frame)

    row = (canvas_height - frame_height) // 2
    column = (canvas_width - frame_width) // 2

    while True:
        draw_frame(canvas, row, column, game_over_frame)
        await sleep()


def draw(canvas):
    global coroutines
    global obstacles
    obstacles = []
    global year
    year = 1957

    frame_files = os.listdir('frames/rocket_frames')
    frames = []
    for file_name in frame_files:
        with open(os.path.join('frames/rocket_frames', file_name)) as file:
            frame = file.read()
            frames.append(frame)

    garbage_frames_files = os.listdir('frames/garbage_frames')
    garbage_frames = []
    for file_name in garbage_frames_files:
        with open(os.path.join('frames/garbage_frames', file_name)) as file:
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
    coroutines.append(show_year(canvas))

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
