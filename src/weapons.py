from enum import Enum
from dice import Die, RollResult


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


class Weapon:
    def __init__(self, name: str, damage_die: Die):
        self.__name: str = name
        self.__damage_die: Die = damage_die

    def roll_damage(self) -> RollResult:
        return RollResult(self.__damage_die)
