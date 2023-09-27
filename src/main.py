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
        choice = None
        while choice != "end":
            print(encounter)
            available_moves = list(turn.get_all_available_moves())
            print(f"available moves for {turn.player}: ")
            for n, move in enumerate(available_moves):
                print(f"{n}) {move}")

            choice = int(input("Choose move by number (or `end`): "))
            chosen_action = available_moves[choice]
            chosen_action.execute()
            print(chosen_action.describe())


if __name__ == "__main__":
    main()
