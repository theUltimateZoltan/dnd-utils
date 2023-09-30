from __future__ import annotations
from dataclasses import dataclass
from tabulate import tabulate
from typing import List, Set, Dict
from uuid import UUID, uuid4


@dataclass(eq=True, frozen=True)
class Location:
    x: int
    y: int


class ItemNotFoundException(Exception):
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

    def move(self, source: Location, dest: Location) -> None:
        if item := self.clear(source):
            self.place(item, dest)

    def find(self, item: GridItem) -> Location:
        try:
            return self.__items_index[item.uuid]
        except IndexError:
            raise ItemNotFoundException("Item not in grid")

    def get_adjacent_items(self, loc: Location) -> Set[GridItem]:
        all_adjacent_indices = set()
        for x in range(loc.x - 1, loc.x + 2):
            for y in range(loc.y - 1, loc.y + 2):
                adj = Location(x, y)
                if self.location_in_bounds(adj) and adj != loc:
                    if grid_item := self.__cells[x][y]:
                        all_adjacent_indices.add(grid_item)
        return all_adjacent_indices

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
