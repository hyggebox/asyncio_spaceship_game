import asyncio
import curses
import random

TIC_TIMEOUT = 0.1
STAR_SYMBOLS = '+*.:'
STARTS_NUM = 160


async def blink(canvas, row, column, timeout, symbol='*'):
    star_stages = [
        (curses.A_DIM, 200),
        (curses.A_NORMAL, 30),
        (curses.A_BOLD, 20),
        (curses.A_NORMAL, 30),
    ]

    for _ in range(timeout):
        await asyncio.sleep(0)
    while True:
        for appearance, tics_num in star_stages:
            for i in range(tics_num):
                canvas.addch(row, column, symbol, appearance)
                await asyncio.sleep(0)


def draw(canvas):
    canvas_height, canvas_width = canvas.getmaxyx()
    coroutines = []

    for star in range(STARTS_NUM):
        coroutines.append(
            blink(canvas,
                  random.randint(1, canvas_height - 2),
                  random.randint(1, canvas_width - 2),
                  random.randint(0, 800),
                  symbol=random.choice(STAR_SYMBOLS),
                  ))

    canvas.border()
    curses.curs_set(False)
    while True:
        canvas.refresh()

        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        if len(coroutines) == 0:
            break


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
