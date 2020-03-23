"""
Snake game in Python
"""
import curses
import random
import time
from collections import deque
from dataclasses import dataclass


class SnakeDied(Exception):
    ...


@dataclass(frozen=True)
class Coordinate:
    y: int
    x: int

    @classmethod
    def from_tuple(cls, tuple):
        return Coordinate(*tuple)

    def __add__(self, other):
        return Coordinate(self.y + other.y, self.x + other.x)

    def __iter__(self):
        yield self.y
        yield self.x


class Snake:
    HEAD = "O"
    BODY = "#"
    BAIT = "✕"

    def __init__(self, direction, length: int, position: Coordinate):
        self.direction = direction
        self.queue = deque(
            [position + Coordinate(1, i + 1) for i in reversed(range(length))]
        )

    @property
    def head(self):
        return self.queue[0]

    @property
    def body(self):
        for idx, segment in enumerate(self.queue):
            if idx == 0:
                continue
            yield segment

    def __iter__(self):
        for idx, segment in enumerate(self.queue):
            if idx == 0:
                yield segment.y, segment.x, Snake.HEAD
            else:
                yield segment.y, segment.x, Snake.BODY

    def move(self):
        self.queue.pop()
        self.queue.appendleft(self.queue[0] + self.direction)

    def eat(self, bait):
        self.queue.append(bait)


@dataclass
class Playground:
    max_size: Coordinate

    @property
    def origin(self):
        return Coordinate(0, 0)

    @property
    def center(self):
        return Coordinate(self.max_size.y // 2, self.max_size.x // 2)

    @property
    def random_point(self):
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
    def speed(self):
        return self.__current_speed

    @property
    def score(self):
        return self.__current_score

    def check_boundary(self):
        return (
            self.snake.head in self.snake.body
            or self.snake.head.y in (0, self.playground.max_size.y - 1)
            or self.snake.head.x in (0, self.playground.max_size.x - 1)
        )

    def create_bait(self):
        self.bait = self.playground.random_point

    def increase_speed(self):
        self.__current_speed *= Gameplay.__SPEED_MULTIPLIER

    def increase_score(self):
        self.__current_score = max(
            1, self.__current_score * Gameplay.__SCORE_MULTIPLIER
        )

    def did_ate_bait(self):
        return self.snake.head == self.bait

    def is_direction_allowed(self, next_direction):
        if not next_direction:
            return False

        return next_direction.y != -(
            self.snake.direction.y
        ) or next_direction.x != -(self.snake.direction.x)


def main(screen):
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
    top_left = Coordinate(0, 5)

    try:
        while True:
            screen.erase()
            screen.border()

            screen.addstr(*top_left, f" Score: {gameplay.score} ")
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
        time.sleep(3)


if __name__ == "__main__":
    curses.wrapper(main)
