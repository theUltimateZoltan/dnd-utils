from __future__ import annotations
from collections import namedtuple, defaultdict
from typing import Dict, List
from uuid import uuid4, UUID
from tabulate import tabulate
from enum import Enum


class DiceType(Enum):
    d4 = 4
    d6 = 6
    d8 = 8
    d10 = 10
    d12 = 12
    d20 = 20
    d100 = 100


class DamageType(Enum):
    acid = "acid"
    bludgeoning = "bludgeoning"
    cold = "cold"
    fire = "fire"
    force = "force"
    lightning = "lightning"
    necrotic = "necrotic"
    piercing = "piercing"
    poison = "poison"
    psychic = "psychic"
    radiant = "radiant"
    slashing = "slashing"
    thunder = "thunder"


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


AbilityScores = namedtuple("AbilityScores", ["str", "dex", "con", "int", "wis", "cha"])
Bonus = namedtuple("Bonus", ["amount", "source"])


class Creature(MapItem):
    class Builder:
        def __init__(self):
            self.__creature: Creature = Creature()

        def name(self, name: str) -> Creature:
            self.__creature._name = name
            return self.__creature

        def level(self, level: int) -> Creature:
            self.__creature._level = level
            return self.__creature



    def __init__(self):
        super().__init__()
        self._ability_scores: AbilityScores = AbilityScores(10, 10, 10, 10, 10, 10)
        self._name: str = "Creature"
        self._level: float = 1.0
        self._hit_die_type: DiceType = DiceType.d8
        self._damage_taken: int = 0
        self._bonuses: defaultdict[str, List[Bonus]] = defaultdict(list)

    def get_modifier(self, ability: str):
        return (self._ability_scores._asdict().get(ability) - 10) // 2

    @property
    def max_hp(self) -> int:
        return self._hit_die_type.value + \
               (self._level-1) * ((self._hit_die_type.value // 2) + self.get_modifier("con"))

    @property
    def current_hp(self) -> int:
        return self.max_hp - self._damage_taken

    def damage(self, amount: int, dmg_type: DamageType) -> None:
        self._damage_taken += amount

    def heal(self, amount: int) -> None:
        self._damage_taken = max(self._damage_taken - amount, 0)

    def get_bonus(self, key: str) -> int:
        return sum(bonus.amount for bonus in self._bonuses.get(key))

    @property
    def armor_class(self) -> int:
        return 10 + self.get_bonus("armor class")

    def __repr__(self):
        return self._name


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
        elif user_input == "melee":
            enemy =


if __name__ == "__main__":
    main()
