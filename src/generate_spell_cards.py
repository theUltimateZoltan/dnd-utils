from pathlib import Path
from dnd.spells import SpellBook
from tqdm.auto import tqdm

if __name__ == "__main__":
    all_spells: SpellBook = SpellBook.all_spells()
    for qr in tqdm(all_spells.qr_generator(), total=len(all_spells)):
        ...
    url: Path = all_spells.generate_html_file()
    print(url.as_uri())