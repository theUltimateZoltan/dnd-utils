from copy import copy
from enum import Enum
from typing import Dict
from dice import Die, RollResult, DieRollMultiplier
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

    def __get_damage_type_multiplier(self, damage_type: DamageType) -> DieRollMultiplier | None:
        if damage_type in self.immunities:
            return DieRollMultiplier(f"{damage_type.value} damage immunity", 0)
        if damage_type in self.resistances:
            return DieRollMultiplier(f"{damage_type.value} damage resistance", 0.5)
        if damage_type in self.vulnerabilities:
            return DieRollMultiplier(f"{damage_type.value} damage vulnerability", 2)
        return None

    def apply_on_roll(self, damage_type: DamageType, damage_roll: RollResult) -> RollResult:
        applied_damage_roll = copy(damage_roll)
        if multiplier := self.__get_damage_type_multiplier(damage_type):
            applied_damage_roll.add_multiplier(multiplier)
        return applied_damage_roll


class CompoundDamageRollResult:
    def __init__(self) -> None:
        self._rolls: Dict[DamageType, List[RollResult]] = defaultdict(lambda: [])

    def add_roll(self, damage_type: DamageType, roll: RollResult) -> None:
        self._rolls[damage_type].append(roll)

    def result(self, roll_affects: AttributedDamageTypes) -> int:
        final_damage_rolls: List[RollResult] = list()
        for damage_type, roll_results in self._rolls.items():
            for roll in roll_results:
                final_damage_rolls.append(roll_affects.apply_on_roll(damage_type, roll))
        return sum(partial_damage_roll.result for partial_damage_roll in final_damage_rolls)


class Weapon:
    def __init__(self, name: str, base_damage: CompoundDamageRollResult) -> None:
        self.__name: str = name
        self.__damage_die: CompoundDamageRollResult = base_damage

    def roll_damage(self) -> CompoundDamageRollResult:
        return self.__damage_die

    def add_bonus_damage(self, damage_type: DamageType, damage_dice: Die):
        self.__damage_die.add_roll(damage_type, RollResult(damage_dice))
