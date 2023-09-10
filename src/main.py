from __future__ import annotations
from collections import namedtuple
from typing import Dict, List, Set, Generator, Callable
from uuid import uuid4, UUID
from tabulate import tabulate
from enum import Enum
from random import randint
from queue import Queue
from functools import reduce
import operator
import math

NAT20 = math.inf
NAT1 = -math.inf


class DieType(Enum):
    dummy = 0
    d4 = 4
    d6 = 6
    d8 = 8
    d10 = 10
    d12 = 12
    d20 = 20
    d100 = 100


DieRollBonus = namedtuple("DieRollBonus", ["source_description", "amount"])
DieRollMultiplier = namedtuple("DieRollBonus", ["source_description", "multiplier"])


class Die:
    class Roll:
        def __init__(self, die: Die, bonuses: Set[DieRollBonus] | None = None):
            self.__die_rolled: Die = die
            self.__natural_roll: int = die.simple_roll()
            self.__bonuses: Set[DieRollBonus] = bonuses or set()
            self.__multipliers: Set[DieRollMultiplier] = set()
            self.__difficulty_class: int | None = None
            self.tag: str | None = None

        def add_bonus(self, bonus: DieRollBonus) -> None:
            self.__bonuses.add(bonus)

        def add_multiplier(self, multiplier: DieRollMultiplier) -> None:
            self.__multipliers.add(multiplier)

        def set_dc(self, dc: int) -> None:
            assert self.is_stress_die, "DC only has meaning for stress dice."
            self.__difficulty_class = dc

        def __get_final_multiplier(self):
            return reduce(operator.mul, {mul.multiplier for mul in self.__multipliers} | {1})

        @property
        def is_stress_die(self) -> bool:
            return self.__die_rolled.type == DieType.d20

        @property
        def result(self) -> int | float:
            if self.is_critical_success:
                return NAT20
            elif self.is_critical_failure:
                return NAT1
            else:
                unmultiplied_result = self.__natural_roll + sum(bonus.amount for bonus in self.__bonuses)
                return self.__get_final_multiplier() * unmultiplied_result

        @property
        def bonuses(self) -> Set[DieRollBonus]:
            return self.__bonuses

        @property
        def is_success(self) -> bool:
            assert self.__difficulty_class, "No DC was set."
            return self.result >= self.__difficulty_class

        @property
        def is_critical_success(self) -> bool:
            return self.is_stress_die and self.__natural_roll == 20

        @property
        def is_critical_failure(self) -> bool:
            return self.is_stress_die and self.__natural_roll == 1

        def __repr__(self):
            bonus_sum = sum(bonus.amount for bonus in self.__bonuses)
            final_multiplier = self.__get_final_multiplier()
            basic_repr = f"{self.__die_rolled}+{bonus_sum}"
            return basic_repr if final_multiplier == 1 else f"{final_multiplier}x({basic_repr})"

    class ConstantRoll(Roll):
        def __init__(self, value: int):
            super().__init__(Die(0, DieType.dummy))
            self.__const_value = value

        @property
        def result(self):
            return self.__const_value

        def __repr__(self):
            return str(self.__const_value)

    def __init__(self, amount: int, die_type: DieType):
        self.__amount = amount
        self.__type = die_type

    def simple_roll(self) -> int:
        return sum(randint(1, self.__type.value) for _ in range(self.__amount))

    @property
    def type(self):
        return self.__type

    def __repr__(self):
        return f"{self.__amount}{self.__type.name}"


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
        self.__damage_die: Die = damage_die

    def roll_damage(self) -> Die.Roll:
        return Die.Roll(self.__damage_die)


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
        return Die(1, DieType.d20).simple_roll() + self.get_modifier("dex")

    def roll_melee_damage(self) -> Die.Roll:
        if self.__main_weapon:
            base_damage_roll = self.__main_weapon.roll_damage()
            base_damage_roll.add_bonus(DieRollBonus("str", self.get_modifier("str")))
            base_damage_roll.add_bonus(DieRollBonus("proficiency", self.proficiency_bonus))
            return base_damage_roll
        else:
            return Die.ConstantRoll(1)

    def roll_melee_hit(self) -> Die.Roll:
        return Die.Roll(Die(1, DieType.d20), bonuses={
            DieRollBonus("str", self.get_modifier("str")),
            DieRollBonus("proficiency", self.proficiency_bonus)
        })

    def equip_weapon(self, weapon: Weapon):
        self.__main_weapon = weapon

    def __repr__(self):
        return self._name

    def get_available_actions(self, grid: Map) -> Set[Action]:
        return {
            MeleeAttack(self, target) for target in grid.get_adjacent_creatures(grid.find(self))
        }

    def get_available_bonus_actions(self, grid: Map) -> Set[Action]:
        return set()

    def get_available_reactions(self, grid: Map) -> Set[Action]:
        return set()


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

    def get_adjacent_creatures(self, loc: Location) -> Set[Creature]:
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


class Action:
    def __init__(self):
        self.__dice_rolled = list()

    def _log_die_roll(self, roll: Die.Roll):
        self.__dice_rolled.append(roll)

    def execute(self) -> None:
        pass

    def describe(self) -> List[str]:
        rolls_descriptions: List[str] = list()
        for roll in self.__dice_rolled:
            roll_result = f"{roll.tag}: rolled {roll} for {roll.result}."
            if roll.is_stress_die:
                success_description = "Critical " if (roll.is_critical_success or roll.is_critical_failure) else ""
                success_description += "Success!" if roll.is_success else "Failure..."
                rolls_descriptions.append(f"{roll_result} {success_description}")
            else:
                rolls_descriptions.append(roll_result)

        return rolls_descriptions


class MeleeAttack(Action):
    def __init__(self, attacker: Creature, target: Creature):
        super().__init__()
        self.__attacker: Creature = attacker
        self.__target: Creature = target
        self.__hit_roll: Die.Roll | None = None
        self.__damage_roll: Die.Roll | None = None

    def execute(self) -> None:
        self.__hit_roll: Die.Roll = self.__attacker.roll_melee_hit()
        self.__hit_roll.set_dc(self.__target.armor_class)
        self.__hit_roll.tag = f"{self.__attacker}'s hit on {self.__target}"
        self._log_die_roll(self.__hit_roll)

        if self.__hit_roll.is_success:
            damage_roll: Die.Roll = self.__attacker.roll_melee_damage()
            if self.__hit_roll.is_critical_success:
                damage_roll.add_multiplier(DieRollMultiplier("critical hit", 2))
            self._log_die_roll(self.__damage_roll)
            self.__target.damage(damage_roll.result, DamageType.bludgeoning)

    def __repr__(self):
        return f"Melee on {self.__target}"


class Turn:
    def __init__(self, grid: Map, player: Creature):
        assert grid.find(player)
        self.__player: Creature = player
        self.__grid: Map = grid
        self.__available_actions = self.__player.get_available_actions(grid)
        self.__available_bonus_actions = self.__player.get_available_bonus_actions(grid)
        self.__available_reactions = self.__player.get_available_reactions(grid)
        self.__used_action, self.__used_bonus_action = False, False

    @property
    def player(self):
        return self.__player

    def get_all_available_moves(self) -> Set[Action]:
        return self.__available_actions | self.__available_bonus_actions

    def take_bonus_action(self, action: Action) -> None:
        raise NotImplementedError()


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

    def add_player(self, player: Creature, location: Location):
        self.__players.add(player)
        self.__grid.place(player, location)

    def add_npc(self, npc: Creature, location: Location):
        self.__players.add(npc)
        self.__grid.place(npc, location)

    def initialize(self):
        self.__determine_initiative()
        # TODO determine surprise

    def __repr__(self):
        return self.__grid.__repr__()


def main() -> None:
    encounter: Encounter = Encounter()
    player = Creature.Builder().name("Player").level(3).build()
    player.equip_weapon(Weapon("Sword", Die(1, DieType.d8)))
    enemy = Creature.Builder().name("Enemy1").level(3).build()
    enemy2 = Creature.Builder().name("Enemy2").level(2).build()
    encounter.add_player(player, Location(1, 1))
    encounter.add_npc(enemy, Location(1, 0))
    encounter.add_npc(enemy2, Location(2, 0))
    print(encounter)
    encounter.initialize()
    for turn in encounter.turns():
        available_moves = turn.get_all_available_moves()
        print(f"available moves for {turn.player}: ")
        print(available_moves)
        input("Choose move: ")


if __name__ == "__main__":
    main()
