from enum import Enum
from typing import Dict
from dice import Die, RollResult
from dataclasses import dataclass
from collections import defaultdict
from typing import DefaultDict, List


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
class RollAffects:
    immunities: List[DamageType]
    resistances: List[DamageType]
    vulnerabilities: List[DamageType]


class CompoundRollResult:
    def __init__(self) -> None:
        self._rolls: Dict[DamageType, List[RollResult]] = defaultdict(lambda _: [])

    def add_roll(self, damage_type: DamageType, roll: RollResult) -> None:
        self._rolls[damage_type].append(roll)

    def calculate_roll(self, roll_affects: RollAffects) -> int | float:
        uncalculated_rolls = self._rolls.copy()
        total_damage: int | float = 0
        for immunity in roll_affects.immunities:
            uncalculated_rolls.pop(immunity, None)
        for resistance in roll_affects.resistances:
            for roll in uncalculated_rolls.pop(resistance, []):
                uncalculated_rolls += roll.result / 2
        for vulnerability in roll_affects.vulnerabilities:
            for roll in uncalculated_rolls.pop(vulnerability, []):
                uncalculated_rolls += roll.result * 2
        # Calculate the remaining damage types
        for damage_type, rolls in uncalculated_rolls:
            for roll in rolls:
                uncalculated_rolls += roll.result
        return total_damage


class Weapon:
    def __init__(self, name: str, damage_dice: List[Die], damage_type: DamageType):
        self.__name: str = name
        self.__damage_die: List[Die] = damage_dice
        self._base_damage_type: DamageType = damage_type
        self._bonus_damages: DefaultDict[DamageType, List[Die]] = defaultdict(
            lambda _: []
        )

    def roll_damage(self) -> CompoundRollResult:
        total_damage = CompoundRollResult()
        for result_type, dice in self._bonus_damages:
            total_damage.add_roll(result_type, dice)
        return total_damage

    def add_bonus_damage(self, damage_type: DamageType, damage_dice: Die):
        self._bonus_damages[damage_type].append(damage_dice)
