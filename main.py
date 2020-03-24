"""
Snake game in Python
"""
from __future__ import annotations

import curses
import random
import time
from collections import deque
from dataclasses import dataclass
from typing import Generator, Tuple


class SnakeDied(Exception):
    ...


@dataclass(frozen=True)
class Coordinate:
    y: int
    x: int

    @classmethod
    def from_tuple(cls, tupe: Tuple[int, int]) -> Coordinate:
        return Coordinate(*tupe)

    def __add__(self, other: Coordinate) -> Coordinate:
        return Coordinate(self.y + other.y, self.x + other.x)

    def __iter__(self) -> Generator[int, None, None]:
        yield self.y
        yield self.x


class Snake:
    HEAD = "O"
    BODY = "#"
    BAIT = "✕"

    def __init__(self, direction, length: int, position: Coordinate) -> None:
        self.direction = direction
        self.queue = deque(
            [position + Coordinate(1, i + 1) for i in reversed(range(length))]
        )

    @property
    def head(self) -> Coordinate:
        return self.queue[0]

    @property
    def body(self) -> Generator[Coordinate, None, None]:
        for idx, segment in enumerate(self.queue):
            if idx == 0:
                continue
            yield segment

    def __iter__(self) -> Generator[Tuple[int, int, str], None, None]:
        for idx, segment in enumerate(self.queue):
            if idx == 0:
                yield segment.y, segment.x, Snake.HEAD
            else:
                yield segment.y, segment.x, Snake.BODY

    def move(self) -> None:
        self.queue.pop()
        self.queue.appendleft(self.queue[0] + self.direction)

    def eat(self, bait: Coordinate) -> None:
        self.queue.append(bait)


@dataclass
class Playground:
    max_size: Coordinate

    @property
    def origin(self) -> Coordinate:
        return Coordinate(0, 0)

    @property
    def center(self) -> Coordinate:
        return Coordinate(self.max_size.y // 2, self.max_size.x // 2)

    @property
    def random_point(self) -> Coordinate:
        return Coordinate(
            random.randint(1, self.max_size.y - 2),
            random.randint(1, self.max_size.x - 2),
        )


@dataclass
class Gameplay:
    snake: Snake
    playground: Playground
    bait: Coordinate = None

    __current_speed: float = 0.1
    __current_score: float = 0
    __SCORE_MULTIPLIER: float = 2
    __SPEED_MULTIPLIER: float = 0.99

    DIRECTIONS = {
        curses.KEY_UP: Coordinate(y=-1, x=0),
        curses.KEY_DOWN: Coordinate(y=1, x=0),
        curses.KEY_LEFT: Coordinate(y=0, x=-1),
        curses.KEY_RIGHT: Coordinate(y=0, x=1),
    }

    @property
    def speed(self) -> float:
        return self.__current_speed

    @property
    def score(self) -> int:
        return self.__current_score

    def check_boundary(self) -> bool:
        return (
            self.snake.head in self.snake.body
            or self.snake.head.y in (0, self.playground.max_size.y - 1)
            or self.snake.head.x in (0, self.playground.max_size.x - 1)
        )

    def create_bait(self) -> None:
        self.bait = self.playground.random_point

    def increase_speed(self) -> None:
        self.__current_speed *= Gameplay.__SPEED_MULTIPLIER

    def increase_score(self) -> None:
        self.__current_score = max(
            1, self.__current_score * Gameplay.__SCORE_MULTIPLIER
        )

    def did_ate_bait(self) -> bool:
        return self.snake.head == self.bait

    def is_direction_allowed(self, next_direction: Coordinate) -> bool:
        if not next_direction:
            return False

        return next_direction.y != -(
            self.snake.direction.y
        ) or next_direction.x != -(self.snake.direction.x)


def main(screen: "curses._CursesWindow") -> int:
    curses.curs_set(0)  # hide the cursor
    screen.nodelay(True)  # don't block i/o calls

    playground = Playground(Coordinate.from_tuple(screen.getmaxyx()))
    snake = Snake(
        direction=Gameplay.DIRECTIONS[curses.KEY_RIGHT],
        length=15,
        position=playground.center,
    )

    gameplay = Gameplay(snake, playground)
    gameplay.create_bait()

    screen.refresh()

    try:
        while True:
            screen.erase()
            screen.border()

            screen.addstr(*Coordinate(0, 5), f" Score: {gameplay.score} ")
            screen.addstr(*gameplay.bait, Snake.BAIT)

            if gameplay.check_boundary():
                raise SnakeDied

            if gameplay.did_ate_bait():
                snake.eat(gameplay.bait)
                gameplay.create_bait()
                gameplay.increase_speed()
                gameplay.increase_score()

            for segment in snake:
                screen.addstr(*segment)

            snake.move()
            next_direction = Gameplay.DIRECTIONS.get(screen.getch(), None)

            # can't go opposite direction
            if gameplay.is_direction_allowed(next_direction):
                snake.direction = next_direction

            screen.refresh()
            time.sleep(gameplay.speed)

    except SnakeDied:
        screen.erase()
        screen.addstr(
            *playground.center, f"Snake died at {gameplay.score} points"
        )
    except KeyboardInterrupt:
        screen.erase()
        screen.addstr(*playground.center, "QUITTING...")
    finally:
        screen.refresh()
        time.sleep(2)
    return 0


if __name__ == "__main__":
    exit(curses.wrapper(main))
