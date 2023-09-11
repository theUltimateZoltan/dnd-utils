from __future__ import annotations
from typing import Set
from random import randint
from functools import reduce
import operator
import math
from enum import Enum
from collections import namedtuple


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


class RollResult:
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


class ConstantRollResult(RollResult):
    def __init__(self, value: int):
        super().__init__(Die(0, DieType.dummy))
        self.__const_value = value

    @property
    def result(self):
        return self.__const_value

    def __repr__(self):
        return str(self.__const_value)


class Die:
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