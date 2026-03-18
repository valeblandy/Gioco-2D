import arcade
from PIL import Image

_PLACEHOLDER = None

def _placeholder_texture():
    global _PLACEHOLDER
    if _PLACEHOLDER is None:
        _PLACEHOLDER = arcade.Texture.create_empty("_placeholder_", (1, 1))
    return _PLACEHOLDER


class SpriteAnimato(arcade.Sprite):
    def __init__(self, scala: float = 1.0):
        super().__init__(_placeholder_texture(), scale=scala)
        self.animazioni = {}
        self.animazione_corrente = None
        self.animazione_default = None
        self.tempo_frame = 0.0
        self.indice_frame = 0

    def aggiungi_animazione(
        self,
        nome: str,
        percorso: str,
        frame_width: int,
        frame_height: int,
        num_frame: int,
        colonne: int,
        durata: float,
        loop: bool = True,
        default: bool = False,
        riga: int = 0,
    ):
        sheet = arcade.load_spritesheet(percorso)
        offset = riga * colonne
        tutti = sheet.get_texture_grid(
            size=(frame_width, frame_height),
            columns=colonne,
            count=offset + num_frame,
        )
        self._registra(nome, tutti[offset:], durata, loop, default)

    def _registra(self, nome, textures, durata, loop, default=False):
        self.animazioni[nome] = {
            "textures": textures,
            "durata_frame": durata / len(textures),
            "loop": loop,
        }
        if default or self.animazione_default is None:
            self.animazione_default = nome
        if self.animazione_corrente is None:
            self._vai(nome)

    def imposta_animazione(self, nome: str):
        if nome != self.animazione_corrente:
            self._vai(nome)

    def _vai(self, nome: str):
        self.animazione_corrente = nome
        self.indice_frame = 0
        self.tempo_frame = 0.0
        self.texture = self.animazioni[nome]["textures"][0]

    def update_animation(self, delta_time: float = 1 / 60):
        anim = self.animazioni[self.animazione_corrente]
        self.tempo_frame += delta_time

        if self.tempo_frame < anim["durata_frame"]:
            return

        self.tempo_frame -= anim["durata_frame"]
        prossimo = self.indice_frame + 1

        if prossimo < len(anim["textures"]):
            self.indice_frame = prossimo
        elif anim["loop"]:
            self.indice_frame = 0
        else:
            # Rimani sull'ultimo frame; il chiamante decide quando cambiare
            self.indice_frame = len(anim["textures"]) - 1
            return

        self.texture = anim["textures"][self.indice_frame]