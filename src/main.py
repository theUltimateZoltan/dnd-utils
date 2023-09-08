from __future__ import annotations
from collections import namedtuple
from typing import Dict, List, Set, Generator
from uuid import uuid4, UUID
from tabulate import tabulate
from enum import Enum
from random import randint
from queue import Queue
import math

NAT20 = math.inf
NAT1 = -math.inf


class DieType(Enum):
    d4 = 4
    d6 = 6
    d8 = 8
    d10 = 10
    d12 = 12
    d20 = 20
    d100 = 100


class Die:
    def __init__(self, amount: int, die_type: DieType):
        self.__amount = amount
        self.__type = die_type

    def roll(self) -> int:
        return sum(randint(1, self.__type.value) for _ in range(self.__amount))

    @staticmethod
    def stress_d20() -> int | float:
        natural_roll = Die(1, DieType.d20).roll()
        if natural_roll in {1, 20}:
            return NAT20 if natural_roll == 20 else NAT1
        return natural_roll


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


class Weapon:
    def __init__(self, name: str, damage_die: Die):
        self.__name: str = name
        self.__damage_die = damage_die

    def roll_damage(self) -> int:
        return self.__damage_die.roll()


class Creature(MapItem):
    class Builder:
        def __init__(self):
            self.__creature: Creature = Creature()

        def name(self, name: str) -> Creature.Builder:
            self.__creature._name = name
            return self

        def level(self, level: int) -> Creature.Builder:
            self.__creature._level = level
            return self

        def build(self) -> Creature:
            return self.__creature

    def __init__(self):
        super().__init__()
        self._ability_scores: AbilityScores = AbilityScores(10, 10, 10, 10, 10, 10)
        self._name: str = "Creature"
        self._level: float = 1.0
        self._hit_die_type: DieType = DieType.d8
        self._damage_taken: int = 0
        self.__main_weapon: Weapon | None = None

    def get_modifier(self, ability: str):
        return (self._ability_scores._asdict().get(ability) - 10) // 2

    @property
    def max_hp(self) -> int:
        return self._hit_die_type.value + \
               (self._level-1) * ((self._hit_die_type.value // 2) + self.get_modifier("con"))

    @property
    def proficiency_bonus(self):
        return 2 + ((self._level-1) // 4)

    @property
    def current_hp(self) -> int:
        return self.max_hp - self._damage_taken

    def damage(self, amount: int, dmg_type: DamageType) -> None:
        self._damage_taken += amount

    def heal(self, amount: int) -> None:
        self._damage_taken = max(self._damage_taken - amount, 0)

    @property
    def armor_class(self) -> int:
        return 10

    def roll_initiative(self) -> int:
        return Die(1, DieType.d20).roll() + self.get_modifier("dex")

    def roll_melee_damage(self) -> int:
        if self.__main_weapon:
            return self.__main_weapon.roll_damage() + self.get_modifier("str") + self.proficiency_bonus
        else:
            return 1  # unarmed attack

    def roll_melee_hit(self) -> int | float:
        return Die.stress_d20() + self.get_modifier("str") + self.proficiency_bonus

    def equip_weapon(self, weapon: Weapon):
        self.__main_weapon = weapon

    def __repr__(self):
        return self._name

    def get_available_actions(self):
        raise NotImplementedError()

    def get_available_bonus_actions(self):
        raise NotImplementedError()

    def get_available_reactions(self):
        raise NotImplementedError()


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


class Turn:
    def __init__(self, grid: Map, player: Creature):
        assert grid.find(player)
        self.__player = player
        self.__grid = grid
        self.__available_actions = self.__player.get_available_actions()
        self.__available_bonus_actions = self.__player.get_available_bonus_actions()
        self.__available_reactions = self.__player.get_available_reactions()
        self.__used_action, self.__used_bonus_action, self.__used_reaction = False, False, False

    @property
    def player(self):
        return self.__player



class Encounter:
    def __init__(self):
        self.__grid: Map = Map(3, 3)
        self.__players: Set[Creature] = set()  # TODO convert to sorted structure for search efficiency (heap?)
        self.__npc: Set[Creature] = set()      # "
        self.__active: Creature | None = None
        self.__initiative_queue: Queue = Queue()

    def __determine_initiative(self) -> None:
        ordered_list = [c for c in self.__players | self.__npc]
        ordered_list.sort(key=lambda c: c.roll_initiative())
        for c in ordered_list:
            self.__initiative_queue.put(c)

    def turns(self) -> Generator[Turn]:
        if self.__initiative_queue.empty():
            raise StopIteration()
        self.__active = self.__initiative_queue.get()
        yield Turn(self.__grid, self.__active)
        self.__initiative_queue.put(self.__active)

    def initialize(self):
        self.__determine_initiative()
        # TODO determine surprise



def main() -> None:
    grid = Map(3, 3)
    player = Creature.Builder().name("Player").level(3).build()
    player.equip_weapon(Weapon("Sword", Die(1, DieType.d8)))
    enemy = Creature.Builder().name("Enemy").level(3).build()
    grid.place(player, Location(0, 0))
    grid.place(enemy, Location(1, 0))
    print(grid)
    while True:
        user_input = input(f"Command: ").lower()
        if user_input == "exit":
            break
        elif user_input == "move":
            x = int(input("to where? x: "))
            y = int(input("to where? y: "))
            grid.move(grid.find(player), Location(x, y))
            print(grid)
        elif user_input == "melee":
            # TODO choose enemy
            hit_roll = player.roll_melee_hit()
            damage_roll = player.roll_melee_damage()
            if hit_roll == NAT20:
                damage_roll *= 2

            print(f"{player} rolled {hit_roll} to hit over the enemy's AC of {enemy.armor_class}")
            if hit_roll >= enemy.armor_class:
                print("Critical Hit!" if hit_roll == NAT20 else "Hit!")
                enemy.damage(damage_roll, DamageType.bludgeoning)
                print(f"{enemy} has taken {damage_roll} damage and stands at {enemy.current_hp} HP.")
            else:
                print("Critical Miss!" if hit_roll == NAT1 else "Miss!")


if __name__ == "__main__":
    main()
