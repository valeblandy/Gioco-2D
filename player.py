import arcade
from sprite_animato import SpriteAnimato

# ── Spritesheet ───────────────────────────────────────────────────────────────
# Ordine righe in tutti i file: su / sinistra / giù / destra
IDLE_SOURCE = "idle.png"   # 4 righe × 2 colonne, 64×64 px
WALK_SOURCE = "walk.png"   # 4 righe × 7 colonne, 64×64 px
RUN_SOURCE  = "run.png"    # 4 righe × 6 colonne, 64×64 px
JUMP_SOURCE = "jump.png"   # 4 righe × 4 colonne, 64×64 px

FRAME_W = 64
FRAME_H = 64

IDLE_COLS = 2
WALK_COLS = 7
RUN_COLS  = 6
JUMP_COLS = 4

DURATA_IDLE = 0.8
DURATA_WALK = 0.6
DURATA_RUN  = 0.4
DURATA_JUMP = 0.9   # durata salita (i frame vengono "allungati")

# Velocità
SPEED_WALK = 2.5
SPEED_RUN  = 5.0

# Fisica salto
JUMP_VELOCITY   = 380   # px/s verso l'alto al momento del salto
GRAVITY         = 700   # px/s² di gravità
JUMP_HOLD_TIME  = 0.25  # secondi di pausa sull'ultimo frame (apice del salto)

# Mappa Tiled
MAP_FILE   = "Mondo.tmx"
TILE_SIZE  = 16          # px per tile (come nel .tmx)
MAP_TILES_W = 200        # colonne della mappa
MAP_TILES_H = 200        # righe della mappa
TILE_SCALE  = 1.0        # scala di rendering dei tile (aumenta per pixel art più grande)

MAP_WIDTH  = MAP_TILES_W * TILE_SIZE * TILE_SCALE
MAP_HEIGHT = MAP_TILES_H * TILE_SIZE * TILE_SCALE

# Schermo
SCREEN_W = 800
SCREEN_H = 600


class Player(SpriteAnimato):
    DIREZIONI = ["su", "sinistra", "giu", "destra"]

    def __init__(self):
        super().__init__(scala=2.0)

        for i, d in enumerate(self.DIREZIONI):
            self.aggiungi_animazione(
                nome=f"idle_{d}", percorso=IDLE_SOURCE,
                frame_width=FRAME_W, frame_height=FRAME_H,
                num_frame=IDLE_COLS, colonne=IDLE_COLS,
                durata=DURATA_IDLE, loop=True,
                default=(d == "giu"), riga=i,
            )
            self.aggiungi_animazione(
                nome=f"walk_{d}", percorso=WALK_SOURCE,
                frame_width=FRAME_W, frame_height=FRAME_H,
                num_frame=WALK_COLS, colonne=WALK_COLS,
                durata=DURATA_WALK, loop=True, riga=i,
            )
            self.aggiungi_animazione(
                nome=f"run_{d}", percorso=RUN_SOURCE,
                frame_width=FRAME_W, frame_height=FRAME_H,
                num_frame=RUN_COLS, colonne=RUN_COLS,
                durata=DURATA_RUN, loop=True, riga=i,
            )
            self.aggiungi_animazione(
                nome=f"jump_{d}", percorso=JUMP_SOURCE,
                frame_width=FRAME_W, frame_height=FRAME_H,
                num_frame=JUMP_COLS, colonne=JUMP_COLS,
                durata=DURATA_JUMP, loop=False,
                default=False, riga=i,
            )

        self.direzione    = "giu"
        self.key_su       = False
        self.key_giu      = False
        self.key_sinistra = False
        self.key_destra   = False
        self.key_corsa    = False
        self.sta_saltando = False

        # Fisica salto
        self._vel_y      = 0.0
        self._base_y     = 0.0
        self._offset_y   = 0.0
        self._hold_timer = 0.0

    def update_animation(self, delta_time=1/60):
        if not self.sta_saltando:
            moving = self.key_su or self.key_giu or self.key_sinistra or self.key_destra
            prefisso = ("run" if self.key_corsa else "walk") if moving else "idle"
            self.imposta_animazione(f"{prefisso}_{self.direzione}")
        super().update_animation(delta_time)

    def aggiorna_posizione(self, delta_time: float):
        speed = SPEED_RUN if self.key_corsa else SPEED_WALK
        dx = dy = 0
        if self.key_su:       dy += 1
        if self.key_giu:      dy -= 1
        if self.key_sinistra: dx -= 1
        if self.key_destra:   dx += 1

        if dx != 0 or dy != 0:
            if abs(dy) >= abs(dx):
                self.direzione = "su" if dy > 0 else "giu"
            else:
                self.direzione = "destra" if dx > 0 else "sinistra"

        self.center_x += dx * speed
        self.center_y += dy * speed

        # ── Fisica salto ──────────────────────────────────────────────────────
        if self.sta_saltando:
            anim = self.animazioni.get(f"jump_{self.direzione}")
            ultimo_frame = (anim and
                            self.indice_frame == len(anim["textures"]) - 1 and
                            not anim["loop"])

            if ultimo_frame:
                if self._hold_timer < JUMP_HOLD_TIME:
                    self._hold_timer += delta_time
                    self.tempo_frame = 0
                else:
                    self._vel_y -= GRAVITY * delta_time
            else:
                self._vel_y -= GRAVITY * delta_time

            self._offset_y += self._vel_y * delta_time
            self.center_y  = self._base_y + self._offset_y

            if self._offset_y <= 0:
                self._offset_y   = 0
                self._vel_y      = 0.0
                self._hold_timer = 0.0
                self.sta_saltando = False
                self.center_y    = self._base_y
        # ─────────────────────────────────────────────────────────────────────

        hw = self.width  / 2
        hh = self.height / 2
        self.center_x = max(hw, min(MAP_WIDTH  - hw, self.center_x))
        self.center_y = max(hh, min(MAP_HEIGHT - hh, self.center_y))

    def on_key_press(self, key):
        if key in (arcade.key.UP,    arcade.key.W): self.key_su       = True
        if key in (arcade.key.DOWN,  arcade.key.S): self.key_giu      = True
        if key in (arcade.key.LEFT,  arcade.key.A): self.key_sinistra = True
        if key in (arcade.key.RIGHT, arcade.key.D): self.key_destra   = True
        if key == arcade.key.LSHIFT:                self.key_corsa    = True
        if key == arcade.key.SPACE and not self.sta_saltando:
            self.sta_saltando = True
            self._base_y      = self.center_y
            self._vel_y       = JUMP_VELOCITY
            self._offset_y    = 0.0
            self._hold_timer  = 0.0
            self.imposta_animazione(f"jump_{self.direzione}")

    def on_key_release(self, key):
        if key in (arcade.key.UP,    arcade.key.W): self.key_su       = False
        if key in (arcade.key.DOWN,  arcade.key.S): self.key_giu      = False
        if key in (arcade.key.LEFT,  arcade.key.A): self.key_sinistra = False
        if key in (arcade.key.RIGHT, arcade.key.D): self.key_destra   = False
        if key == arcade.key.LSHIFT:                self.key_corsa    = False


# ── Finestra ──────────────────────────────────────────────────────────────────

class GameWindow(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_W, SCREEN_H,
                         "Demo – WASD muovi | SHIFT corri | SPAZIO salta")
        arcade.set_background_color(arcade.color.AMAZON)
        self.player        = None
        self.sprite_list   = None
        self.tile_map      = None   # tilemap caricata da Mondo.tmx
        self.scene         = None   # arcade.Scene costruita dalla tilemap

        try:
            self.cam_world = arcade.camera.Camera2D()
            self.cam_gui   = arcade.camera.Camera2D()
            self._a3 = True
        except AttributeError:
            self.cam_world = arcade.Camera(SCREEN_W, SCREEN_H)
            self.cam_gui   = arcade.Camera(SCREEN_W, SCREEN_H)
            self._a3 = False

    def setup(self):
        # ── Carica la tilemap Tiled ──────────────────────────────────────────
        self.tile_map = arcade.load_tilemap(MAP_FILE, scaling=TILE_SCALE)
        self.scene    = arcade.Scene.from_tilemap(self.tile_map)

        # ── Player ──────────────────────────────────────────────────────────
        self.sprite_list = arcade.SpriteList()
        self.player = Player()
        self.player.center_x = MAP_WIDTH  / 2
        self.player.center_y = MAP_HEIGHT / 2
        self.sprite_list.append(self.player)

    def _aggiorna_camera(self):
        px, py = self.player.center_x, self.player.center_y

        if self._a3:
            tx = max(SCREEN_W / 2, min(MAP_WIDTH  - SCREEN_W / 2, px))
            ty = max(SCREEN_H / 2, min(MAP_HEIGHT - SCREEN_H / 2, py))
            cx, cy = self.cam_world.position
            self.cam_world.position = (
                cx + (tx - cx) * 0.15,
                cy + (ty - cy) * 0.15,
            )
        else:
            tx = max(0, min(MAP_WIDTH  - SCREEN_W, px - SCREEN_W / 2))
            ty = max(0, min(MAP_HEIGHT - SCREEN_H, py - SCREEN_H / 2))
            cx, cy = self.cam_world.position
            self.cam_world.move_to(
                (cx + (tx - cx) * 0.15, cy + (ty - cy) * 0.15)
            )

    def on_draw(self):
        self.clear()
        self.cam_world.use()

        # Disegna i layer della tilemap
        self.scene.draw()

        # Disegna il player sopra la mappa
        self.sprite_list.draw()

        self.cam_gui.use()
        arcade.draw_text(
            f"Anim: {self.player.animazione_corrente}",
            10, SCREEN_H - 24, arcade.color.WHITE, 14,
        )
        arcade.draw_text(
            "WASD muovi  |  SHIFT sinistro = corri  |  SPAZIO = salta",
            10, 10, arcade.color.LIGHT_GRAY, 12,
        )

    def on_update(self, delta_time: float):
        self.player.aggiorna_posizione(delta_time)
        self.sprite_list.update_animation(delta_time)
        self._aggiorna_camera()

    def on_key_press(self, key, modifiers):
        self.player.on_key_press(key)

    def on_key_release(self, key, modifiers):
        self.player.on_key_release(key)


if __name__ == "__main__":
    window = GameWindow()
    window.setup()
    arcade.run()