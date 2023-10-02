from copy import copy
from enum import Enum
from typing import Dict, DefaultDict
from dice import Die, RollResult, DieRollMultiplier, DieRollBonus, StressDieRollResult
from dataclasses import dataclass
from collections import defaultdict
from typing import List


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


@dataclass
class AttributedDamageTypes:
    immunities: List[DamageType]
    resistances: List[DamageType]
    vulnerabilities: List[DamageType]

    def get_damage_type_multiplier(
        self, damage_type: DamageType
    ) -> DieRollMultiplier | None:
        if damage_type in self.immunities:
            return DieRollMultiplier(f"{damage_type.value} damage immunity", 0)
        if damage_type in self.resistances:
            return DieRollMultiplier(f"{damage_type.value} damage resistance", 0.5)
        if damage_type in self.vulnerabilities:
            return DieRollMultiplier(f"{damage_type.value} damage vulnerability", 2)
        return None


class CannotUseStressDieAsDamageRollException(Exception):
    ...


class CompoundDamageRollResult:
    def __init__(self) -> None:
        self.tag: str | None = None
        self.weapon: Weapon | None = None
        self._rolls: DefaultDict[DamageType, List[RollResult]] = defaultdict(lambda: [])

    def add_roll(self, damage_type: DamageType, roll: RollResult) -> None:
        if isinstance(roll, StressDieRollResult):
            raise CannotUseStressDieAsDamageRollException()
        self._rolls[damage_type].append(roll)

    def result(self, roll_affects: AttributedDamageTypes) -> int:
        if not self._rolls:
            return 1
        final_damage_rolls: List[RollResult] = list()
        for damage_type, roll_results in self._rolls.items():
            for roll in roll_results:
                final_damage_rolls.append(
                    self._apply_on_roll(roll_affects, damage_type, roll)
                )
        return int(
            sum(
                partial_damage_roll.result for partial_damage_roll in final_damage_rolls
            )
        )

    def add_bonus(self, damage_type: DamageType, bonus: DieRollBonus) -> None:
        if not self._rolls[damage_type]:
            return
        self._rolls[damage_type][0].add_bonus(bonus)

    def add_multiplier(self, damage_type: DamageType, bonus: DieRollMultiplier) -> None:
        if not self._rolls[damage_type]:
            return
        for roll in self._rolls[damage_type]:
            roll.add_multiplier(bonus)

    @staticmethod
    def _apply_on_roll(
        roll_affects: AttributedDamageTypes,
        damage_type: DamageType,
        damage_roll: RollResult,
    ) -> RollResult:
        applied_damage_roll = copy(damage_roll)
        if multiplier := roll_affects.get_damage_type_multiplier(damage_type):
            applied_damage_roll.add_multiplier(multiplier)
        return applied_damage_roll


class Weapon:
    def __init__(self, name: str, damage_type: DamageType, damage_dice: List[Die]):
        self.__name: str = name
        self._damage_type = damage_type
        self._bonus_damages: DefaultDict[DamageType, List[Die]] = defaultdict(
            lambda: []
        )
        self._bonus_damages[damage_type] = damage_dice

    @property
    def main_damage_type(self) -> DamageType:
        return self._damage_type

    def roll_damage(self) -> CompoundDamageRollResult:
        total_damage = CompoundDamageRollResult()
        for result_type, dice in self._bonus_damages.items():
            for die in dice:
                total_damage.add_roll(result_type, RollResult(die))
        total_damage.weapon = self
        return total_damage

    def add_bonus_damage(self, damage_type: DamageType, damage_dice: List[Die]) -> None:
        self._bonus_damages[damage_type].extend(damage_dice)
