from __future__ import annotations
from dnd.dice import Die, DieType
from dnd.grid import Location
from dnd.encounter import Encounter
from dnd.creatures import Creature
from dnd.weapons import Weapon, DamageType


def main() -> None:
    encounter: Encounter = Encounter()
    player = Creature.Builder().name("Player").level(3).build()
    player.equip_weapon(Weapon("Sword", DamageType.slashing, [Die(1, DieType.d8)]))
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
            if available_moves:
                print(f"Available moves for {turn.player}: ")
                for n, move in enumerate(available_moves):
                    print(f"{n}) {move}")
            else:
                print(f"{turn.player}: No available moves. Type 'end' to end turn.")

            choice = input("Choose move by number (or `end`): ")
            if choice != "end":
                chosen_action = available_moves[int(choice)]
                chosen_action.execute()
                print(chosen_action.describe())


if __name__ == "__main__":
    main()
