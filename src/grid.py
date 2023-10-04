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

    def __add__(self, direction: MovementDirection) -> Location:
        return direction + self


class MovementDirection(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    def __add__(self, loc: Location) -> Location:
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
    def __init__(self, size_x: int, size_y: int) -> None:
        self.__cells: List[List[GridItem | None]] = [
            [None for _ in range(size_y)] for _ in range(size_x)
        ]
        self.__items_index: Dict[UUID, Location] = dict()

    @property
    def width(self) -> int:
        return len(self.__cells) - 1

    @property
    def height(self) -> int:
        return len(self.__cells[0]) - 1

    def place(self, map_item: GridItem, loc: Location) -> None:
        self.__items_index[map_item.uuid] = loc
        self.__cells[loc.y][loc.x] = map_item

    def clear(self, loc: Location) -> GridItem | None:
        content = self.__cells[loc.y][loc.x]
        if content is None:
            return None
        self.__items_index.pop(content.uuid)
        self.__cells[loc.y][loc.x] = None
        return content

    def location_in_bounds(self, loc: Location) -> bool:
        return 0 <= loc.x <= self.width and 0 <= loc.y <= self.height

    def location_vacant(self, loc: Location) -> bool:
        return self.location_in_bounds(loc) and self.__cells[loc.y][loc.x] is None

    def move(self, source: Location, dest: Location) -> None:
        if self.location_in_bounds(dest):
            if item := self.clear(source):
                self.place(item, dest)
        else:
            raise LocationOutOfBoundsException("Destination out of bounds")

    def find(self, item: GridItem) -> Location:
        if loc := self.__items_index.get(item.uuid, None):
            return loc
        else:
            raise ItemNotFoundException("Item not in grid")

    def get_adjacent_items(self, loc: Location) -> Set[GridItem]:
        adjacent_items: Set[GridItem] = set()
        for x in range(loc.x - 1, loc.x + 2):
            for y in range(loc.y - 1, loc.y + 2):
                adj = Location(x, y)
                if self.location_in_bounds(adj) and adj != loc:
                    adj_content = self.__cells[adj.y][adj.x]
                    if adj_content is not None:
                        adjacent_items.add(adj_content)

        return adjacent_items

    def __repr__(self) -> str:
        return tabulate(self.__cells, tablefmt="grid")


class GridItem:
    def __init__(self) -> None:
        self.__uuid = uuid4()

    @property
    def uuid(self) -> UUID:
        return self.__uuid


class WrittenGridItem(GridItem):
    def __init__(self, text: str) -> None:
        super().__init__()
        self.__text = text

    def __repr__(self) -> str:
        return self.__text
