from __future__ import annotations
from dice import Die, DieType
from grid import Location
from encounter import Encounter
from creatures import Creature
from weapons import Weapon


def main() -> None:
    encounter: Encounter = Encounter()
    player = Creature.Builder().name("Player").level(3).build()
    player.equip_weapon(Weapon("Sword", Die(1, DieType.d8)))
    enemy = Creature.Builder().name("Enemy1").level(3).build()
    enemy2 = Creature.Builder().name("Enemy2").level(2).build()
    encounter.add_player(player, Location(1, 1))
    encounter.add_npc(enemy, Location(1, 0))
    encounter.add_npc(enemy2, Location(2, 0))
    encounter.initialize()
    for turn in encounter.turns():
        print(encounter)
        available_moves = turn.get_all_available_moves()
        print(f"available moves for {turn.player}: ")
        print(available_moves)
        choice = input("Choose move: ")
        for move in available_moves:
            if repr(move) == choice:
                move.execute()
                print(move.describe())


if __name__ == "__main__":
    main()
