from creatures import Creature, Action
from grid import Grid, Location, ItemNotFoundException
from typing import Set, Generator
from queue import Queue


class Turn:
    def __init__(self, grid: Grid, player: Creature):
        try:
            grid.find(player)
        except ItemNotFoundException:
            raise Exception("Turn created with player not on the grid")

        self.__player: Creature = player
        self.__grid: Grid = grid
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
        self.__grid: Grid = Grid(3, 3)
        self.__players: Set[Creature] = set()  # TODO convert to sorted structure for search efficiency (heap?)
        self.__npc: Set[Creature] = set()      # "
        self.__active: Creature | None = None
        self.__initiative_queue: Queue = Queue()

    def __determine_initiative(self) -> None:
        ordered_list = [c for c in self.__players | self.__npc]
        ordered_list.sort(key=lambda c: c.roll_initiative().result)
        for c in ordered_list:
            self.__initiative_queue.put(c)

    def turns(self) -> Generator[Turn, None, None]:
        while not self.__initiative_queue.empty():
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
