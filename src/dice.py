from __future__ import annotations

from dataclasses import dataclass
from typing import Set, List
from random import randint
from functools import reduce
import operator
import math
from enum import Enum


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


class AdvantageSource(Enum):
    terrain = "terrain"
    stealth = "stealth"


@dataclass(eq=True, frozen=True)
class DieRollBonus:
    source_description: str
    amount: int


@dataclass(eq=True, frozen=True)
class DieRollMultiplier:
    source_description: str
    multiplier: float


class RollResult:
    def __init__(self, die: Die) -> None:
        self._die_rolled: Die = die
        self._natural_roll: List[int] = die.roll()
        self.__bonuses: Set[DieRollBonus] = set()
        self.__multipliers: Set[DieRollMultiplier] = set()
        self.tag: str | None = None

    def add_bonus(self, bonus: DieRollBonus) -> None:
        self.__bonuses.add(bonus)

    def add_multiplier(self, multiplier: DieRollMultiplier) -> None:
        self.__multipliers.add(multiplier)

    def __get_final_multiplier(self) -> int | float:
        if len(self.__multipliers) > 0:
            return reduce(operator.mul, {mul.multiplier for mul in self.__multipliers})
        else:
            return 1

    @property
    def result(self) -> int:
        unmultiplied_result = sum(self._natural_roll) + sum(
            bonus.amount for bonus in self.__bonuses
        )
        return int(self.__get_final_multiplier() * unmultiplied_result)

    @property
    def bonuses(self) -> Set[DieRollBonus]:
        return self.__bonuses

    def __repr__(self) -> str:
        bonus_sum = sum(bonus.amount for bonus in self.__bonuses)
        final_multiplier = self.__get_final_multiplier()
        basic_repr = (
            f"{self._die_rolled}+{bonus_sum}"
            if bonus_sum != 0
            else str(self._die_rolled)
        )
        return (
            basic_repr
            if final_multiplier == 1
            else f"{final_multiplier}x({basic_repr})"
        )


class StressDieRollResult(RollResult):
    CRIT_SUCCESS_VALUE: int = 20
    CRIT_FAILURE_VALUE: int = 1

    def __init__(self) -> None:
        super().__init__(Die(1, DieType.d20))
        self.__difficulty_class: int | None = None
        self.__advantages: Set[AdvantageSource] = set()
        self.__disadvantages: Set[AdvantageSource] = set()
        self._secondary_natural_roll: List[int] = self._die_rolled.roll()

    def add_advantage(self, source: AdvantageSource) -> None:
        self.__advantages.add(source)

    def add_disadvantage(self, source: AdvantageSource) -> None:
        self.__disadvantages.add(source)

    @property
    def has_advantage(self) -> bool:
        return len(self.__advantages) > len(self.__disadvantages)

    @property
    def has_disadvantage(self) -> bool:
        return len(self.__advantages) < len(self.__disadvantages)

    def set_dc(self, dc: int) -> None:
        self.__difficulty_class = dc

    @property
    def is_success(self) -> bool:
        if self.__difficulty_class is None:
            raise Exception("No DC was set.")
        return self.result >= self.__difficulty_class

    def __get_determining_natural_roll_result(self) -> int:
        if self.has_advantage or self.has_disadvantage:
            determining_function = max if self.has_advantage else min
            return determining_function(
                self._natural_roll[0], self._secondary_natural_roll[0]
            )
        else:
            return self._natural_roll[0]

    @property
    def is_critical_success(self) -> bool:
        return (
            self.__get_determining_natural_roll_result()
            == StressDieRollResult.CRIT_SUCCESS_VALUE
        )

    @property
    def is_critical_failure(self) -> bool:
        return (
            self.__get_determining_natural_roll_result()
            == StressDieRollResult.CRIT_FAILURE_VALUE
        )

    @property
    def result(self) -> int | float:
        if self.is_critical_success:
            return NAT20
        elif self.is_critical_failure:
            return NAT1
        else:
            return super().result


class ConstantRollResult(RollResult):
    def __init__(self, value: int):
        super().__init__(Die(0, DieType.dummy))
        self._natural_roll = [value]


class Die:
    def __init__(self, amount: int, die_type: DieType) -> None:
        self.__amount = amount
        self.__type = die_type

    def roll(self) -> List[int]:
        return [randint(1, self.__type.value) for _ in range(self.__amount)]

    @property
    def type(self) -> DieType:
        return self.__type

    def __repr__(self) -> str:
        return f"{self.__amount}{self.__type.name}"
