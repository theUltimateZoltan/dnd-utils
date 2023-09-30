from __future__ import annotations
from creatures import Creature, Action
from grid import Grid, Location
from typing import Set, Generator
from queue import Queue


class Turn:
    def __init__(self, encounter: Encounter) -> None:
        self.__encounter = encounter
        self.__available_actions = encounter.active_creature.get_available_actions(
            encounter.grid
        )
        self.__available_bonus_actions = (
            encounter.active_creature.get_available_bonus_actions(encounter.grid)
        )
        self.__available_reactions = encounter.active_creature.get_available_reactions(
            encounter.grid
        )

    @property
    def player(self) -> Creature | None:
        return self.__encounter.active_creature

    def get_all_available_moves(self) -> Set[Action]:
        return self.__available_actions | self.__available_bonus_actions

    def take_action(self, action: Action) -> None:
        raise NotImplementedError()

    def move(self, loc: Location) -> None:
        raise NotImplementedError()

    def take_bonus_action(self, action: Action) -> None:
        raise NotImplementedError()


class NoCreatureDefinedForEncounter(Exception):
    ...


class Encounter:
    def __init__(self) -> None:
        self.__grid: Grid = Grid(3, 3)
        self.__players: Set[Creature] = set()
        self.__npc: Set[Creature] = set()
        self.__active: Creature | None = None
        self.__initiative_queue: Queue[Creature] = Queue()

    @property
    def has_creature(self) -> bool:
        return self.__active is not None

    @property
    def active_creature(self) -> Creature:
        if self.has_creature is None:
            raise NoCreatureDefinedForEncounter("No active creature added to encounter!")
        return self.__active

    @property
    def grid(self) -> Grid:
        return self.__grid

    def __determine_initiative(self) -> None:
        ordered_list = [c for c in self.__players | self.__npc]
        ordered_list.sort(key=lambda c: c.roll_initiative().result)
        for c in ordered_list:
            self.__initiative_queue.put(c)

    def turns(self) -> Generator[Turn, None, None]:
        while not self.__initiative_queue.empty():
            self.__active = self.__initiative_queue.get()
            yield Turn(self)
            self.__initiative_queue.put(self.__active)

    def add_player(self, player: Creature, location: Location) -> None:
        self.__players.add(player)
        self.__grid.place(player, location)

    def add_npc(self, npc: Creature, location: Location) -> None:
        self.__players.add(npc)
        self.__grid.place(npc, location)

    def initialize(self) -> None:
        self.__determine_initiative()

    def __repr__(self) -> str:
        return self.__grid.__repr__()
