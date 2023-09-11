from __future__ import annotations
from collections import namedtuple
from grid import GridItem, Grid
from dice import DieType, RollResult, ConstantRollResult, DieRollBonus, DieRollMultiplier, StressDieRollResult
from weapons import Weapon, DamageType
from typing import Set, List, cast
from enum import Enum


AbilityScores = namedtuple("AbilityScores", ["str", "dex", "con", "int", "wis", "cha"])


class Condition(Enum):
    down = "down"
    prone = "prone"
    poisoned = "poisoned"


class Creature(GridItem):
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
        self.__conditions: Set[Condition] = set()

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
        if self.current_hp <= 0:
            self.gain_condition(Condition.down)

    def heal(self, amount: int) -> None:
        self._damage_taken = max(self._damage_taken - amount, 0)

    def gain_condition(self, condition: Condition) -> None:
        self.__conditions.add(condition)

    @property
    def armor_class(self) -> int:
        return 10

    def roll_initiative(self) -> StressDieRollResult:
        initiative_roll = StressDieRollResult()
        initiative_roll.add_bonus(DieRollBonus("dex", self.get_modifier("dex")))
        return initiative_roll

    def roll_melee_damage(self) -> RollResult:
        if self.__main_weapon:
            base_damage_roll = self.__main_weapon.roll_damage()
            base_damage_roll.add_bonus(DieRollBonus("str", self.get_modifier("str")))
            base_damage_roll.add_bonus(DieRollBonus("proficiency", self.proficiency_bonus))
            return base_damage_roll
        else:
            return ConstantRollResult(1)

    def roll_melee_hit(self) -> StressDieRollResult:
        hit_roll = StressDieRollResult()
        hit_roll.add_bonus(DieRollBonus("str", self.get_modifier("str")))
        hit_roll.add_bonus(DieRollBonus("proficiency", self.proficiency_bonus))
        return hit_roll

    def equip_weapon(self, weapon: Weapon):
        self.__main_weapon = weapon

    def __repr__(self):
        return f"{self._name} ({self.current_hp if Condition.down not in self.__conditions else 'down'})"

    def get_available_actions(self, grid: Grid) -> Set[Action]:
        if "down" in self.__conditions:
            return set()
        return {
            MeleeAttack(self, cast(Creature, target)) for target in grid.get_adjacent_items(grid.find(self))
            if issubclass(type(target), Creature)
        }

    def get_available_bonus_actions(self, grid: Grid) -> Set[Action]:
        return set()

    def get_available_reactions(self, grid: Grid) -> Set[Action]:
        return set()


class Action:
    def __init__(self):
        self.__dice_rolled = list()

    def _log_die_roll(self, roll: RollResult):
        self.__dice_rolled.append(roll)

    def execute(self) -> None:
        pass

    def describe(self) -> List[str]:
        rolls_descriptions: List[str] = list()
        for roll in self.__dice_rolled:
            roll_result = f"{roll.tag}: rolled {roll} for {roll.result}."
            if type(roll) == StressDieRollResult:
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
        self.__hit_roll: RollResult | None = None
        self.__damage_roll: RollResult | None = None

    def execute(self) -> None:
        self.__hit_roll: StressDieRollResult = self.__attacker.roll_melee_hit()
        self.__hit_roll.set_dc(self.__target.armor_class)
        self.__hit_roll.tag = "hit"
        self._log_die_roll(self.__hit_roll)

        if self.__hit_roll.is_success:
            self.__damage_roll: RollResult = self.__attacker.roll_melee_damage()
            self.__damage_roll.tag = "damage"
            if self.__hit_roll.is_critical_success:
                self.__damage_roll.add_multiplier(DieRollMultiplier("critical hit", 2))
            self._log_die_roll(self.__damage_roll)
            self.__target.damage(self.__damage_roll.result, DamageType.bludgeoning)

    def __repr__(self):
        return f"Melee on {self.__target}"
