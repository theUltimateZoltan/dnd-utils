from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from grid import GridItem, Grid, MovementDirection, LocationOutOfBoundsException
from dice import (
    DieType,
    RollResult,
    ConstantRollResult,
    DieRollBonus,
    DieRollMultiplier,
    StressDieRollResult,
)
from weapons import Weapon, DamageType
from typing import Set, List, cast, Dict
from grid import GridItem, Grid
from dice import (
    DieType,
    RollResult,
    DieRollBonus,
    DieRollMultiplier,
    StressDieRollResult,
)
from weapons import Weapon, CompoundDamageRollResult, AttributedDamageTypes, DamageType
from typing import Set, List, cast
from enum import Enum


@dataclass(eq=True, frozen=True)
class AbilityScores:
    strength: int
    dexterity: int
    constitution: int
    intelligence: int
    wisdom: int
    charisma: int

    def get(self, ability: Ability) -> int:
        return self.__dict__[ability.value]  # type: ignore


class Ability(Enum):
    STR = "strength"
    DEX = "dexterity"
    CON = "constitution"
    INT = "intelligence"
    WIS = "wisdom"
    CHA = "charisma"


class Condition(Enum):
    down = "down"
    prone = "prone"
    poisoned = "poisoned"


class Creature(GridItem):
    class Builder:
        def __init__(self) -> None:
            self.__creature: Creature = Creature()

        def name(self, name: str) -> Creature.Builder:
            self.__creature._name = name
            return self

        def level(self, level: int) -> Creature.Builder:
            self.__creature._level = level
            return self

        def build(self) -> Creature:
            return self.__creature

    def __init__(self) -> None:
        super().__init__()
        self._ability_scores: AbilityScores = AbilityScores(10, 10, 10, 10, 10, 10)
        self.__attributed_damage_types = AttributedDamageTypes([], [], [])
        self._name: str = "Creature"
        self._level: int = 1
        self._hit_die_type: DieType = DieType.d8
        self._damage_taken: int = 0
        self.__main_weapon: Weapon | None = None
        self.__conditions: Set[Condition] = set()
        self.__depletions: Dict[ActionDepletionType, int] = defaultdict(lambda: 0)
        self.__depletion_limits: Dict[ActionDepletionType, int] = defaultdict(lambda: 1)
        self.__depletion_limits[ActionDepletionType.MOVEMENT] = 6

    def get_modifier(self, ability: Ability) -> int | float:
        return (self._ability_scores.get(ability) - 10) // 2

    @property
    def max_hp(self) -> int | float:
        return self._hit_die_type.value + (self._level - 1) * (
            (self._hit_die_type.value // 2) + self.get_modifier(Ability.CON)
        )

    @property
    def proficiency_bonus(self) -> int:
        return 2 + ((self._level - 1) // 4)

    @property
    def current_hp(self) -> int | float:
        return self.max_hp - self._damage_taken

    @property
    def speed(self) -> int:
        return self.__depletion_limits[ActionDepletionType.MOVEMENT]

    def start_turn(self) -> None:
        depletion_types_to_reset = [
            ActionDepletionType.ACTION,
            ActionDepletionType.BONUS,
            ActionDepletionType.MOVEMENT,
            ActionDepletionType.REACTION,
        ]
        for dep_type in depletion_types_to_reset:
            self.__depletions[dep_type] = 0

    def __is_action_type_depleted(
        self, action_depletion_type: ActionDepletionType
    ) -> bool:
        return (
            self.__depletions[action_depletion_type]
            >= self.__depletion_limits[action_depletion_type]
        )

    def deplete_action_type(self, action_depletion_type: ActionDepletionType) -> None:
        if self.__is_action_type_depleted(action_depletion_type):
            raise ActionTypeDepletedException()
        self.__depletions[action_depletion_type] += 1

    def damage(self, damage_roll: CompoundDamageRollResult) -> None:
        self._damage_taken += damage_roll.result(self.__attributed_damage_types)
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
        initiative_roll.add_bonus(
            DieRollBonus(Ability.DEX.value, int(self.get_modifier(Ability.DEX)))
        )
        return initiative_roll

    def __empty_handed_attack_damage(self) -> CompoundDamageRollResult:
        damage = CompoundDamageRollResult()
        damage.add_roll(DamageType.bludgeoning, ConstantRollResult(1))
        return damage

    def roll_melee_damage(self) -> CompoundDamageRollResult:
        if self.__main_weapon:
            base_damage_roll = self.__main_weapon.roll_damage()
            base_damage_roll.add_bonus(
                self.__main_weapon.main_damage_type,
                DieRollBonus(Ability.STR.value, int(self.get_modifier(Ability.STR))),
            )
            base_damage_roll.add_bonus(
                self.__main_weapon.main_damage_type,
                DieRollBonus("proficiency", self.proficiency_bonus),
            )
            return base_damage_roll
        else:
            return self.__empty_handed_attack_damage()

    def roll_melee_hit(self) -> StressDieRollResult:
        hit_roll = StressDieRollResult()
        hit_roll.add_bonus(
            DieRollBonus(Ability.STR.value, int(self.get_modifier(Ability.STR)))
        )
        hit_roll.add_bonus(DieRollBonus("proficiency", self.proficiency_bonus))
        return hit_roll

    def equip_weapon(self, weapon: Weapon) -> None:
        self.__main_weapon = weapon

    def __repr__(self) -> str:
        return f"{self._name} ({self.current_hp if Condition.down not in self.__conditions else 'down'})"

    def __get_available_melee_attacks(self, grid: Grid) -> Set[MeleeAttack]:
        creature_location = grid.find(self)
        return {
            MeleeAttack(self, cast(Creature, target))
            for target in grid.get_adjacent_items(creature_location)
            if issubclass(type(target), Creature)
        }

    def __get_available_movement(self, grid: Grid) -> Set[Movement]:
        creature_location = grid.find(self)
        return {
            Movement(self, grid, direction)
            for direction in MovementDirection.all()
            if grid.location_vacant(creature_location + direction)
        }

    def get_available_actions(self, grid: Grid) -> Set[Action]:
        if Condition.down in self.__conditions:
            return set()

        melee_attacks = self.__get_available_melee_attacks(grid)
        movement = self.__get_available_movement(grid)

        all_actions = melee_attacks | movement

        return {
            action
            for action in all_actions
            if not self.__is_action_type_depleted(action.depletion_type)
        }


class ActionDepletionType(Enum):
    ACTION = "action"
    BONUS = "bonus action"
    REACTION = "reaction"
    MOVEMENT = "movement"


class Action:
    def __init__(self, executing_creature: Creature):
        self.__dice_rolled: List[RollResult | CompoundDamageRollResult] = list()
        self.__executing_creature = executing_creature
        self._depletion_type: ActionDepletionType = ActionDepletionType.ACTION

    @property
    def depletion_type(self) -> ActionDepletionType:
        return self._depletion_type

    def _store_roll(self, roll: RollResult | CompoundDamageRollResult) -> None:
        self.__dice_rolled.append(roll)

    def execute(self) -> None:
        self._deplete()

    def set_depletion_type(self, depletion_type: ActionDepletionType) -> None:
        self._depletion_type = depletion_type

    def _deplete(self) -> None:
        self.__executing_creature.deplete_action_type(self._depletion_type)

    def describe(self) -> List[str]:
        def get_roll_description(roll: RollResult | CompoundDamageRollResult) -> str:
            if isinstance(roll, StressDieRollResult):
                success_description = (
                    "Critical "
                    if (roll.is_critical_success or roll.is_critical_failure)
                    else ""
                )
                success_description += "Success!" if roll.is_success else "Failure..."
                return f"{roll.tag}: rolled {roll} for {roll.result}. {success_description}"
            elif isinstance(roll, CompoundDamageRollResult):
                return f"{roll.tag}: {roll}"
            else:
                return f"{roll.tag}: rolled {roll} for {roll.result}."

        rolls_descriptions: List[str] = list()
        for roll in self.__dice_rolled:
            rolls_descriptions.append(get_roll_description(roll))

        return rolls_descriptions


class MeleeAttack(Action):
    def __init__(self, attacker: Creature, target: Creature) -> None:
        super().__init__(attacker)
        self.__attacker: Creature = attacker
        self.__hit_roll: StressDieRollResult = self.__attacker.roll_melee_hit()
        self.__target: Creature = target
        self.__damage_roll: CompoundDamageRollResult | None = None

    def execute(self) -> None:
        self._deplete()
        self.__hit_roll.set_dc(self.__target.armor_class)
        self.__hit_roll.tag = "hit"
        self._store_roll(self.__hit_roll)

        if self.__hit_roll.is_success:
            self.__damage_roll = self.__attacker.roll_melee_damage()
            self.__damage_roll.tag = "damage"
            if self.__hit_roll.is_critical_success:
                self.__damage_roll.add_multiplier(
                    self.__damage_roll.weapon.main_damage_type
                    if self.__damage_roll.weapon
                    else DamageType.bludgeoning,
                    DieRollMultiplier("critical hit", 2),
                )
            self._store_roll(self.__damage_roll)
            self.__target.damage(self.__damage_roll)

    def __repr__(self) -> str:
        return f"Melee on {self.__target}"


class InvalidActionException(Exception):
    pass


class ActionTypeDepletedException(Exception):
    pass


class Movement(Action):
    def __init__(
        self, creature: Creature, grid: Grid, direction: MovementDirection
    ) -> None:
        super().__init__(creature)
        self.__creature = creature
        self.__grid = grid
        self.__direction = direction
        self.set_depletion_type(ActionDepletionType.MOVEMENT)

    def execute(self) -> None:
        try:
            current_location = self.__grid.find(self.__creature)
            target_location = current_location + self.__direction
            self._deplete()
            self.__grid.move(current_location, target_location)
        except (LocationOutOfBoundsException, ActionTypeDepletedException):
            raise InvalidActionException()

    def describe(self) -> List[str]:
        return [f"{self.__creature} moved {self.__direction.name.lower()}"]

    def __repr__(self) -> str:
        return f"Move {self.__direction.name.lower()}"
