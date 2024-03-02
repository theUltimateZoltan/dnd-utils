from pathlib import Path
from dnd.spells import SpellBook, Spell

if __name__ == "__main__":
    all_spells: SpellBook = Spell.get_all_spells()
    url: Path = all_spells.generate_html_file()
    print(url.as_uri())