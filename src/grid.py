from __future__ import annotations
from dataclasses import dataclass
from tabulate import tabulate
from typing import List, Set, Dict
from uuid import UUID, uuid4
from enum import Enum


@dataclass(eq=True, frozen=True)
class Location:
    x: int
    y: int


class MovementDirection(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    def from_location(self, loc: Location) -> Location:
        x_diff, y_diff = self.value
        return Location(loc.x + x_diff, loc.y + y_diff)

    @staticmethod
    def all() -> Set[MovementDirection]:
        return {
            MovementDirection.UP,
            MovementDirection.DOWN,
            MovementDirection.LEFT,
            MovementDirection.RIGHT,
        }


class ItemNotFoundException(Exception):
    pass


class LocationOutOfBoundsException(Exception):
    pass


class Grid:
    def __init__(self, size_x: int, size_y: int):
        self.__cells: List[List[GridItem | None]] = [[None for _ in range(size_y)] for _ in range(size_x)]
        self.__items_index: Dict[UUID, Location] = dict()

    @property
    def width(self):
        return len(self.__cells)

    @property
    def height(self):
        return len(self.__cells[0])

    def place(self, map_item: GridItem, loc: Location):
        self.__items_index[map_item.uuid] = loc
        self.__cells[loc.y][loc.x] = map_item

    def clear(self, loc: Location) -> GridItem | None:
        content = self.__cells[loc.y][loc.x]
        self.__items_index.pop(content.uuid)
        self.__cells[loc.y][loc.x] = None
        return content

    def location_in_bounds(self, loc: Location) -> bool:
        return 0 <= loc.x < self.width and 0 <= loc.y < self.height

    def location_vacant(self, loc: Location) -> bool:
        return self.location_in_bounds(loc) and self.__cells[loc.y][loc.x] is None

    def move(self, source: Location, dest: Location):
        if self.location_in_bounds(dest):
            if item := self.clear(source):
                self.place(item, dest)
        else:
            raise LocationOutOfBoundsException("Destination out of bounds")

    def find(self, item) -> Location:
        try:
            return self.__items_index.get(item.uuid)
        except IndexError:
            raise ItemNotFoundException("Item not in grid")

    def get_adjacent_items(self, loc: Location) -> Set[GridItem]:
        all_adjacent_indices = set()
        for x in range(loc.x-1, loc.x+2):
            for y in range(loc.y-1, loc.y+2):
                adj = Location(x, y)
                if self.location_in_bounds(adj) and adj != loc:
                    all_adjacent_indices.add(adj)

        if loc.x == 0:
            indices_left = {
                Location(loc.x - 1, loc.y),
                Location(loc.x - 1, loc.y + 1),
                Location(loc.x - 1, loc.y - 1)
            }
            all_adjacent_indices = all_adjacent_indices - indices_left

        if loc.x == len(self.__cells)-1:
            indices_right = {
                Location(loc.x + 1, loc.y),
                Location(loc.x + 1, loc.y + 1),
                Location(loc.x + 1, loc.y - 1)
            }
            all_adjacent_indices = all_adjacent_indices - indices_right

        if loc.y == 0:
            indices_above = {
                Location(loc.x - 1, loc.y - 1),
                Location(loc.x + 1, loc.y - 1),
                Location(loc.x, loc.y - 1),
            }
            all_adjacent_indices = all_adjacent_indices - indices_above

        if loc.y == len(self.__cells[0])-1:
            indices_below = {
                Location(loc.x - 1, loc.y + 1),
                Location(loc.x + 1, loc.y + 1),
                Location(loc.x, loc.y + 1),
            }
            all_adjacent_indices = all_adjacent_indices - indices_below

        return {
            self.__cells[adjacent_loc.y][adjacent_loc.x] for adjacent_loc in all_adjacent_indices
            if self.__cells[adjacent_loc.y][adjacent_loc.x] is not None
        }

    def __repr__(self):
        return tabulate(self.__cells, tablefmt='grid')


class GridItem:
    def __init__(self):
        self.__uuid = uuid4()

    @property
    def uuid(self):
        return self.__uuid


class WrittenGridItem(GridItem):
    def __init__(self, text: str):
        super().__init__()
        self.__text = text

    def __repr__(self):
        return self.__text
