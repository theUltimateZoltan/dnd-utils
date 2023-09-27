from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from grid import GridItem, Grid, MovementDirection, ItemNotFoundException, LocationOutOfBoundsException
from dice import DieType, RollResult, ConstantRollResult, DieRollBonus, DieRollMultiplier, StressDieRollResult
from weapons import Weapon, DamageType
from typing import Set, List, cast, Dict
from enum import Enum


@dataclass(eq=True, frozen=True)
class AbilityScores:
    strength: int
    dexterity: int
    constitution: int
    intelligence: int
    wisdom: int
    charisma: int


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
        self._level: int = 1
        self._hit_die_type: DieType = DieType.d8
        self._damage_taken: int = 0
        self.__main_weapon: Weapon | None = None
        self.__conditions: Set[Condition] = set()
        self.__depletions: Dict[ActionDepletionType, int] = defaultdict(lambda: 0)
        self.__depletion_limits: Dict[ActionDepletionType, int] = defaultdict(lambda: 1)
        self.__depletion_limits[ActionDepletionType.MOVEMENT] = 6

    def get_modifier(self, ability: Ability):
        return (self._ability_scores.__dict__.get(ability.value) - 10) // 2

    @property
    def max_hp(self) -> int:
        return self._hit_die_type.value + \
               (self._level-1) * ((self._hit_die_type.value // 2) + self.get_modifier(Ability.CON))

    @property
    def proficiency_bonus(self) -> int:
        return 2 + ((self._level-1) // 4)

    @property
    def current_hp(self) -> int:
        return self.max_hp - self._damage_taken

    @property
    def speed(self) -> int:
        return self.__depletion_limits[ActionDepletionType.MOVEMENT]

    def start_turn(self) -> None:
        depletion_types_to_reset = [
            ActionDepletionType.ACTION,
            ActionDepletionType.BONUS,
            ActionDepletionType.MOVEMENT,
            ActionDepletionType.REACTION
        ]
        for dep_type in depletion_types_to_reset:
            self.__depletions[dep_type] = 0

    def __is_action_type_depleted(self, action_depletion_type: ActionDepletionType) -> bool:
        return self.__depletions[action_depletion_type] >= self.__depletion_limits[action_depletion_type]

    def deplete_action_type(self, action_depletion_type: ActionDepletionType) -> None:
        if self.__is_action_type_depleted(action_depletion_type):
            raise ActionTypeDepletedException()
        self.__depletions[action_depletion_type] += 1

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
        initiative_roll.add_bonus(DieRollBonus(Ability.DEX.value, self.get_modifier(Ability.DEX)))
        return initiative_roll

    def roll_melee_damage(self) -> RollResult:
        if self.__main_weapon:
            base_damage_roll = self.__main_weapon.roll_damage()
            base_damage_roll.add_bonus(DieRollBonus(Ability.STR.value, self.get_modifier(Ability.STR)))
            base_damage_roll.add_bonus(DieRollBonus("proficiency", self.proficiency_bonus))
            return base_damage_roll
        else:
            return ConstantRollResult(1)

    def roll_melee_hit(self) -> StressDieRollResult:
        hit_roll = StressDieRollResult()
        hit_roll.add_bonus(DieRollBonus(Ability.STR.value, self.get_modifier(Ability.STR)))
        hit_roll.add_bonus(DieRollBonus("proficiency", self.proficiency_bonus))
        return hit_roll

    def equip_weapon(self, weapon: Weapon):
        self.__main_weapon = weapon

    def __repr__(self):
        return f"{self._name} ({self.current_hp if Condition.down not in self.__conditions else 'down'})"

    def __get_available_melee_attacks(self, grid: Grid) -> Set[MeleeAttack]:
        creature_location = grid.find(self)
        return {
            MeleeAttack(self, cast(Creature, target)) for target in grid.get_adjacent_items(creature_location)
            if issubclass(type(target), Creature)
        }

    def __get_available_movement(self, grid: Grid) -> Set[Movement]:
        creature_location = grid.find(self)
        return {
            Movement(self, grid, direction) for direction in MovementDirection.all()
            if grid.location_vacant(direction.from_location(creature_location))
        }

    def get_available_actions(self, grid: Grid) -> Set[Action]:
        if Condition.down in self.__conditions:
            return set()

        melee_attacks = self.__get_available_melee_attacks(grid)
        movement = self.__get_available_movement(grid)

        all_actions = melee_attacks | movement

        return {
            action for action in all_actions
            if not self.__is_action_type_depleted(action.depletion_type)
        }


class ActionDepletionType(Enum):
    ACTION = "action"
    BONUS = "bonus action"
    REACTION = "reaction"
    MOVEMENT = "movement"


class Action:
    def __init__(self, executing_creature: Creature):
        self.__dice_rolled = list()
        self.__executing_creature = executing_creature
        self._depletion_type: ActionDepletionType = ActionDepletionType.ACTION

    @property
    def depletion_type(self) -> ActionDepletionType:
        return self._depletion_type

    def _store_roll(self, roll: RollResult):
        self.__dice_rolled.append(roll)

    def execute(self) -> None:
        self._deplete()

    def set_depletion_type(self, depletion_type: ActionDepletionType) -> None:
        self._depletion_type = depletion_type

    def _deplete(self) -> None:
        self.__executing_creature.deplete_action_type(self._depletion_type)

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
        super().__init__(attacker)
        self.__attacker: Creature = attacker
        self.__target: Creature = target
        self.__hit_roll: RollResult | None = None
        self.__damage_roll: RollResult | None = None

    def execute(self) -> None:
        self._deplete()
        self.__hit_roll: StressDieRollResult = self.__attacker.roll_melee_hit()
        self.__hit_roll.set_dc(self.__target.armor_class)
        self.__hit_roll.tag = "hit"
        self._store_roll(self.__hit_roll)

        if self.__hit_roll.is_success:
            self.__damage_roll: RollResult = self.__attacker.roll_melee_damage()
            self.__damage_roll.tag = "damage"
            if self.__hit_roll.is_critical_success:
                self.__damage_roll.add_multiplier(DieRollMultiplier("critical hit", 2))
            self._store_roll(self.__damage_roll)
            self.__target.damage(self.__damage_roll.result, DamageType.bludgeoning)

    def __repr__(self):
        return f"Melee on {self.__target}"


class InvalidActionException(Exception):
    pass


class ActionTypeDepletedException(Exception):
    pass


class Movement(Action):
    def __init__(self, creature: Creature, grid: Grid, direction: MovementDirection) -> None:
        super().__init__(creature)
        self.__creature = creature
        self.__grid = grid
        self.__direction = direction
        self.set_depletion_type(ActionDepletionType.MOVEMENT)

    def execute(self) -> None:
        try:
            current_location = self.__grid.find(self.__creature)
            target_location = self.__direction.from_location(current_location)
            self._deplete()
            self.__grid.move(current_location, target_location)
        except (LocationOutOfBoundsException, ActionTypeDepletedException):
            raise InvalidActionException()

    def describe(self) -> List[str]:
        return [f"{self.__creature} moved {self.__direction.name.lower()}"]

    def __repr__(self) -> str:
        return f"Move {self.__direction.name.lower()}"
