from collections import namedtuple
from typing import Dict, List
from uuid import uuid4, UUID
from tabulate import tabulate


class MapItem:
    def __init__(self):
        self.__uuid = uuid4()

    @property
    def uuid(self):
        return self.__uuid


class WrittenMapItem(MapItem):
    def __init__(self, text: str):
        super().__init__()
        self.__text = text

    def __repr__(self):
        return self.__text


Location = namedtuple("Location", ["x", "y"])


class Map:
    def __init__(self, size_x: int, size_y: int):
        self.__cells: List[List[MapItem | None]] = [[None for _ in range(size_y)] for _ in range(size_x)]
        self.__items_index: Dict[UUID, Location] = dict()

    def place(self, map_item: MapItem, loc: Location):
        self.__items_index[map_item.uuid] = loc
        self.__cells[loc.y][loc.x] = map_item

    def clear(self, loc: Location) -> MapItem | None:
        content = self.__cells[loc.y][loc.x]
        self.__items_index.pop(content.uuid)
        self.__cells[loc.y][loc.x] = None
        return content

    def move(self, source: Location, dest: Location):
        item = self.clear(source)
        self.place(item, dest)

    def find(self, item) -> Location:
        return self.__items_index.get(item.uuid)

    def __repr__(self):
        return tabulate(self.__cells, tablefmt='grid')


def main() -> None:
    map = Map(3, 3)
    player = WrittenMapItem("player")
    map.place(player, Location(0, 0))
    print(map)
    while True:
        user_input = input(f"Command: ").lower()
        if user_input == "exit":
            break
        elif user_input == "move":
            x = int(input("to where? x: "))
            y = int(input("to where? y: "))
            map.move(map.find(player), Location(x, y))
            print(map)


if __name__ == "__main__":
    main()
