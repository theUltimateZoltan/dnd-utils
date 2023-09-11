from __future__ import annotations
from tabulate import tabulate
from collections import namedtuple
from typing import List, Set, Dict
from uuid import UUID, uuid4


Location = namedtuple("Location", ["x", "y"])


class Grid:
    def __init__(self, size_x: int, size_y: int):
        self.__cells: List[List[GridItem | None]] = [[None for _ in range(size_y)] for _ in range(size_x)]
        self.__items_index: Dict[UUID, Location] = dict()

    def place(self, map_item: GridItem, loc: Location):
        self.__items_index[map_item.uuid] = loc
        self.__cells[loc.y][loc.x] = map_item

    def clear(self, loc: Location) -> GridItem | None:
        content = self.__cells[loc.y][loc.x]
        self.__items_index.pop(content.uuid)
        self.__cells[loc.y][loc.x] = None
        return content

    def move(self, source: Location, dest: Location):
        item = self.clear(source)
        self.place(item, dest)

    def find(self, item) -> Location:
        return self.__items_index.get(item.uuid)

    def get_adjacent_items(self, loc: Location) -> Set[GridItem]:
        all_adjacent_indices = {
                Location(loc.x + 1, loc.y),
                Location(loc.x + 1, loc.y + 1),
                Location(loc.x, loc.y + 1),
                Location(loc.x - 1, loc.y + 1),
                Location(loc.x - 1, loc.y),
                Location(loc.x - 1, loc.y - 1),
                Location(loc.x, loc.y - 1),
                Location(loc.x + 1, loc.y - 1)
            }

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
