import arcade
import os
import xml.etree.ElementTree as ET
from sprite_animato import SpriteAnimato

# ── Percorsi ──────────────────────────────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
SPRITES_DIR  = os.path.join(BASE_DIR, "assets", "sprites")
MAPS_DIR     = os.path.join(BASE_DIR, "assets", "maps")
TILESETS_DIR = os.path.join(BASE_DIR, "assets", "tilesets")

def _sp(f): return os.path.join(SPRITES_DIR, f)
def _mp(f): return os.path.join(MAPS_DIR, f)

IDLE_SOURCE = _sp("idle.png")
WALK_SOURCE = _sp("walk.png")
RUN_SOURCE  = _sp("run.png")

# ── Costanti animazioni ────────────────────────────────────────────────────────
FRAME_W, FRAME_H   = 64, 64
IDLE_COLS, WALK_COLS, RUN_COLS = 2, 7, 6
DURATA_IDLE, DURATA_WALK, DURATA_RUN = 0.8, 0.6, 0.4
SPEED_WALK, SPEED_RUN = 6, 8

# ── Costanti mappa ─────────────────────────────────────────────────────────────
TILE_SIZE, TILE_SCALE   = 16, 2.0
PLAYER_TILE_HEIGHT      = 2.0
COLLISION_LAYER         = "Blocchi"
BACKGROUND_LAYERS       = ["Terreno", "Ponte"]
DEPTH_LAYERS            = ["Blocchi"]
FOREGROUND_LAYERS       = ["Blocchi2"]
SCREEN_W, SCREEN_H      = 800, 600

MAPS = {f"interior{i}.tmx": _mp(f"interior{i}.tmx") for i in range(1, 8)}
MAPS["Mondo.tmx"] = _mp("Mondo.tmx")

# ── Costanti inventario ────────────────────────────────────────────────────────
INVENTARIO_SOURCE        = _sp("inventario.png")
INV_SLOT_SRC_X, INV_SLOT_SRC_Y = 1, 1
INV_SLOT_W, INV_SLOT_H  = 18, 18
INV_SLOT_SCALE          = 3.0
INV_NUM_SLOT            = 6
INV_MARGIN_Y, INV_GAP   = 8, 4
INV_MAX_STACK           = 10
RACCOLTA_RAGGIO         = 48
NPC_INTERAZIONE_RAGGIO  = 80

# ── Assets vari ────────────────────────────────────────────────────────────────
PROPS_SOURCE   = _sp("Props.png")
OBJECTS_SOURCE = os.path.join(TILESETS_DIR, "tileset_objects.png")
PESCE_SOURCE   = _sp("pesce.png")
MONETA_SOURCE  = _sp("moneta.png")
PAPIRO_SOURCE  = _sp("papiro.png")
TITLE_SOURCE   = _sp("LIFE VILLAGE.png")

NPC_SPRITES = {k: _sp(f"{k}_idle.png") for k in ("pescivendolo","mercante","ristoratore","falegname")}

NPC_CONFIG = {
    "interior2.tmx": {"tipo":"pescivendolo","tile_x":4,"tile_y":3,"acquista":{"pesce":8},
                      "nome":"Pescivendolo","dialogo":"Che pesce fresco abbiamo oggi!"},
    "interior3.tmx": {"tipo":"mercante","tile_x":5,"tile_y":3,"acquista":{"carota":5,"grano":4,"pesce":6},
                      "nome":"Mercante","dialogo":"Salve! Ho bisogno di carote, grano e pesce."},
    "interior4.tmx": {"tipo":"ristoratore","tile_x":8,"tile_y":5,"acquista":{"carota":4,"grano":4,"pesce":4},
                      "nome":"Ristoratore","dialogo":"Per i miei piatti servono gli ingredienti migliori!"},
    "interior5.tmx": {"tipo":"falegname","tile_x":5,"tile_y":3,"acquista":{"legna":3,"roccia":1},
                      "nome":"Falegname","dialogo":"Chi vuole maneggiare l'ascia al posto mio finisce col tagliarsi!"},
}



SPAWN_LEGNA  = [(20,48),(33,46),(44,46),(46,29),(7,26),(7,10),(21,5),(30,5),(47,8),(43,13),(47,2)]
SPAWN_ROCCIA = [(13,48),(27,44),(44,45),(44,8),(26,6),(7,7),(5,13)]
SPAWN_CAROTA = [(x,33) for x in range(9,18)]
SPAWN_GRANO  = [(x,34) for x in range(9,18)]
SPAWN_PESCE  = [(7,31),(18,30),(13,30),(9,30),(28,30),(34,32),(38,32),(33,32)]
RESPAWN_TIME = 30.0

ITEM_TEXTURES: dict = {}
PIXEL_FONT = "Pixelify Sans"

# ── Helpers ────────────────────────────────────────────────────────────────────

def _pt(testo, cx, cy, size=11, colore=(20,20,20,255), anchor_x="center", anchor_y="center", bold=False):
    arcade.draw_text(testo, cx, cy, colore, size,
                     anchor_x=anchor_x, anchor_y=anchor_y,
                     bold=bold, font_name=(PIXEL_FONT,))

def _load_tex(path, x=None, y=None, w=None, h=None, fallback=(200,150,50)):
    
    from PIL import Image as _I
    try:
        img = _I.open(path).convert("RGBA")
        if x is not None:
            img = img.crop((x, y, x+w, y+h))
            name = f"{os.path.basename(path)}_{x}_{y}_{w}_{h}"
        elif w is not None:
            img = img.resize((w, h), _I.NEAREST)
            name = f"resized_{os.path.basename(path)}_{w}_{h}"
        else:
            name = f"full_{os.path.basename(path)}"
        return arcade.Texture(name=name, image=img)
    except Exception as e:
        print(f"[tex] {path}: {e}")
        return arcade.make_soft_circle_texture(max(w or 32, h or 32), fallback)

def _draw_tex(texture, cx, cy, w, h):
    spr = arcade.Sprite()
    spr.texture = texture
    spr.center_x, spr.center_y = cx, cy
    spr.width, spr.height = w, h
    arcade.draw_sprite(spr)

def _dist(ax, ay, bx, by):
    return ((ax-bx)**2 + (ay-by)**2)**0.5

def _build_item_textures():
    return {
        "legna":  _load_tex(PROPS_SOURCE,   0,  0, 16, 16),
        "roccia": _load_tex(PROPS_SOURCE,  16,  0, 16, 16),
        "carota": _load_tex(OBJECTS_SOURCE,160, 32, 16, 16),
        "grano":  _load_tex(OBJECTS_SOURCE,176, 32, 16, 16),
        "pesce":  _load_tex(PESCE_SOURCE,   w=16, h=16),
    }

# ── PapiroBox ──────────────────────────────────────────────────────────────────

class PapiroBox:
    PAD_L, PAD_R, PAD_T, PAD_B = 30, 30, 18, 18
    ORIG_W, ORIG_H = 367, 139

    def __init__(self):
        self._tex = _load_tex(PAPIRO_SOURCE)

    def draw(self, cx, cy, w, h):
            _draw_tex(self._tex, cx, cy, w, h)
        
    def draw_testo(self, testo, cx, cy, w, h, font_size=11, colore=(60,30,5,255), max_lines=4):
        self.draw(cx, cy, w, h)
        sx, sy = w/self.ORIG_W, h/self.ORIG_H
        tw = w - (self.PAD_L + self.PAD_R) * sx
        char_w = font_size * 0.62
        lines, line = [], ""
        for word in testo.split():
            test = (line + " " + word).strip()
            if len(test)*char_w > tw:
                if line: lines.append(line)
                line = word
            else:
                line = test
        if line: lines.append(line)
        lines = lines[:max_lines]
        line_h = font_size + 6
        start_y = cy + len(lines)*line_h/2 - line_h/2
        for i, l in enumerate(lines):
            arcade.draw_text(l, cx, start_y - i*line_h, colore, font_size,
                             anchor_x="center", anchor_y="center", font_name=(PIXEL_FONT,))

_PAPIRO = None
def get_papiro():
    global _PAPIRO
    if _PAPIRO is None: _PAPIRO = PapiroBox()
    return _PAPIRO

# ── OggettoMondo ───────────────────────────────────────────────────────────────

class OggettoMondo(arcade.Sprite):
    def __init__(self, tipo, cx, cy, tx, ty):
        super().__init__()
        self.tipo = tipo
        self.tile_x, self.tile_y = tx, ty
        self.center_x, self.center_y = cx, cy
        self._timer = 0.0
        self._set_tex()

    def _set_tex(self):
           self.texture = ITEM_TEXTURES[self.tipo]; self.scale = 1.5
        

    @property
    def visibile(self): return self._timer <= 0.0

    def raccogli(self): self._timer = RESPAWN_TIME

    def update(self, delta_time=1/60):
        if self._timer > 0:
            self._timer -= delta_time
            if self._timer <= 0: self._set_tex()

    def draw_se_visibile(self):
        if self.visibile: arcade.draw_sprite(self)

    def draw_indicatore(self, px, py):
        if self.visibile and _dist(self.center_x,self.center_y,px,py) < RACCOLTA_RAGGIO:
            _pt("[E]", self.center_x, self.center_y+18, size=10, colore=(255,230,0,255))

# ── NPC ────────────────────────────────────────────────────────────────────────

class NPC(arcade.Sprite):
    FRAME_W, FRAME_H, IDLE_ROW = 64, 64, 2

    def __init__(self, tipo, cx, cy, nome, dialogo, acquista):
        super().__init__()
        self.tipo, self.nome, self.dialogo, self.acquista = tipo, nome, dialogo, acquista
        self.center_x, self.center_y = cx, cy
        path = NPC_SPRITES.get(tipo)
        if path and os.path.exists(path):
            self.texture = _load_tex(path, 0, self.IDLE_ROW*self.FRAME_H, self.FRAME_W, self.FRAME_H, (100,100,200))
        else:
            self.texture = arcade.make_soft_circle_texture(32, (100,100,200))
        self.scale = TILE_SCALE

    def vicino(self, px, py):
        return _dist(self.center_x, self.center_y, px, py) < NPC_INTERAZIONE_RAGGIO

    def draw_indicatore(self, px, py):
        if self.vicino(px, py):
            _pt("[E]", self.center_x, self.center_y+self.height/2+8, size=10, colore=(255,255,255,255))

    def draw_nome(self):
        _pt(self.nome, self.center_x, self.center_y+self.height/2+2, size=9, colore=(255,240,180,255))

    def draw_dialogo_papiro(self, sw, sh):
        pw, ph, py = 520, 100, 80
        papiro = get_papiro()
        papiro.draw_testo(f'"{self.dialogo}"', sw//2, py, pw, ph,
                          font_size=12, colore=(50,25,5,255), max_lines=3)
        _pt(self.nome, sw//2 - pw//2 + 40, py + ph//2 - 10,
            size=11, colore=(100,50,10,255), anchor_x="left", bold=True)

# ── FinestraCommercio ──────────────────────────────────────────────────────────

class FinestraCommercio:
    W, H = 500, 360

    def __init__(self):
        self.aperta = False; self.npc = None; self.inventario = None
        self.selezione = 0; self.offerte = []; self.msg = ""; self._msg_t = 0.0
        self._moneta_tex = _load_tex(MONETA_SOURCE, w=20, h=20)

    def apri(self, npc, inventario):
        self.npc, self.inventario = npc, inventario
        self.selezione = 0; self.msg = ""
        self._aggiorna_offerte(); self.aperta = True

    def chiudi(self): self.aperta = False; self.npc = None

    def _aggiorna_offerte(self):
        totali = {}
        for slot in self.inventario.contenuto:
            if slot: totali[slot["tipo"]] = totali.get(slot["tipo"],0) + slot["qt"]
        self.offerte = [{"tipo":t,"qt":totali.get(t,0),"prezzo":p}
                        for t,p in self.npc.acquista.items()]

    def vendi_selezionato(self):
        if not self.offerte: return
        off = self.offerte[self.selezione]
        if off["qt"] <= 0:
            self.msg = "Non hai questo oggetto!"; self._msg_t = 2.0; return
        for i, slot in enumerate(self.inventario.contenuto):
            if slot and slot["tipo"] == off["tipo"]:
                slot["qt"] -= 1
                if slot["qt"] <= 0: self.inventario.contenuto[i] = None
                self.inventario.monete += off["prezzo"]
                self.msg = f"+{off['prezzo']} monete!"; self._msg_t = 1.5
                self._aggiorna_offerte(); return

    def update(self, dt):
        if self._msg_t > 0: self._msg_t -= dt

    def on_key_press(self, key):
        if not self.aperta: return False
        if key in (arcade.key.ESCAPE, arcade.key.E): self.chiudi()
        elif key == arcade.key.UP:   self.selezione = max(0, self.selezione-1)
        elif key == arcade.key.DOWN: self.selezione = min(len(self.offerte)-1, self.selezione+1)
        elif key in (arcade.key.RETURN, arcade.key.ENTER, arcade.key.SPACE): self.vendi_selezionato()
        return True

    def draw(self, sw, sh):
        if not self.aperta or not self.npc: return
        p = get_papiro()
        cx, cy = sw//2, sh//2
        p.draw(cx, cy, self.W, self.H)
        _pt(self.npc.nome, cx, cy+self.H//2-28, size=16, colore=(80,35,5,255), bold=True)
        arcade.draw_line(cx-self.W//2+40, cy+self.H//2-48, cx+self.W//2-40, cy+self.H//2-48, (140,90,40,160), 2)
        p.draw_testo(self.npc.dialogo, cx, cy+100, 400, 70, font_size=11, colore=(60,28,5,255), max_lines=2)

        if not self.offerte:
            _pt("Nessun oggetto da vendere.", cx, cy, size=11, colore=(100,60,20,255))
        else:
            for i, off in enumerate(self.offerte):
                oy = cy + 38 - i*46
                is_sel = (i == self.selezione)
                if is_sel:
                    p.draw(cx, oy, self.W-60, 38)
                    _pt(">", cx-self.W//2+28, oy, size=13, colore=(100,50,10,255))
                col = (60,28,5,255) if off["qt"] > 0 else (160,130,100,255)
                tex = ITEM_TEXTURES.get(off["tipo"])
                if tex: _draw_tex(tex, cx-170, oy, 26, 26)
                _pt(off["tipo"].capitalize(), cx-148, oy, size=12, colore=col, anchor_x="left")
                _pt(f"x{off['qt']}", cx+20, oy, size=12, colore=col)
                _pt(str(off["prezzo"]), cx+100, oy, size=12, colore=(150,90,0,255))
                if self._moneta_tex: _draw_tex(self._moneta_tex, cx+128, oy, 20, 20)

        arcade.draw_line(cx-self.W//2+40, cy-self.H//2+50, cx+self.W//2-40, cy-self.H//2+50, (140,90,40,160), 2)
        _pt("SU/GIU scelta   INVIO vendi   E chiudi", cx, cy-self.H//2+30, size=9, colore=(100,60,20,255))
        if self._msg_t > 0:
            _pt(self.msg, cx, cy-self.H//2+62, size=13,
                colore=(20,120,20,255) if "+" in self.msg else (160,40,20,255), bold=True)

# ── Inventario ─────────────────────────────────────────────────────────────────

class Inventario:
    def __init__(self):
        self.slot_selezionato = 0
        self.contenuto = [None] * INV_NUM_SLOT
        self.monete = 0
        self.slot_size = int(INV_SLOT_W * INV_SLOT_SCALE)
        self.slot_texture = _load_tex(INVENTARIO_SOURCE,
                                      INV_SLOT_SRC_X, INV_SLOT_SRC_Y,
                                      INV_SLOT_W, INV_SLOT_H)
        self._moneta_tex = _load_tex(MONETA_SOURCE)

    def aggiungi(self, tipo):
        for i, s in enumerate(self.contenuto):
            if s and s["tipo"] == tipo and s["qt"] < INV_MAX_STACK:
                self.contenuto[i]["qt"] += 1; return True
        for i, s in enumerate(self.contenuto):
            if s is None: self.contenuto[i] = {"tipo":tipo,"qt":1}; return True
        return False

    def pieno(self):
        return all(s and s["qt"] >= INV_MAX_STACK for s in self.contenuto)

    def draw(self, sw, sh):
        s, gap = self.slot_size, INV_GAP
        tw = INV_NUM_SLOT*s + (INV_NUM_SLOT-1)*gap
        start = (sw-tw)//2
        y = INV_MARGIN_Y + s//2

        for i in range(INV_NUM_SLOT):
            cx = start + i*(s+gap) + s//2
            if self.slot_texture:
                _draw_tex(self.slot_texture, cx, y, s, s)
            else:
                arcade.draw_rect_filled(arcade.XYWH(cx,y,s,s),(180,120,70,220))
            if i == self.slot_selezionato:
                x1,x2,y1,y2 = cx-s//2+1, cx+s//2-1, y-s//2+1, y+s//2-1
                for x_a,y_a,x_b,y_b in [(x1,y1,x2,y1),(x1,y2,x2,y2),(x1,y1,x1,y2),(x2,y1,x2,y2)]:
                    arcade.draw_line(x_a,y_a,x_b,y_b,arcade.color.YELLOW,2)
            obj = self.contenuto[i]
            if obj:
                tex = ITEM_TEXTURES.get(obj["tipo"])
                if tex: _draw_tex(tex, cx, y+2, s-8, s-8)
                if obj["qt"] > 1:
                    _pt(str(obj["qt"]), cx+s//2-4, y-s//2+4,
                        size=9, colore=(255,230,0,255), anchor_x="right", anchor_y="bottom")

        cx_c = sw - 28; cy_c = sh - 28
        if self._moneta_tex: _draw_tex(self._moneta_tex, cx_c, cy_c, 36, 36)
        _pt(str(self.monete), cx_c-24, cy_c, size=14, colore=(255,220,0,255),
            anchor_x="right", anchor_y="center", bold=True)

    def on_key_press(self, key):
        if arcade.key.KEY_1 <= key <= arcade.key.KEY_6:
            self.slot_selezionato = key - arcade.key.KEY_1

# ── Player ─────────────────────────────────────────────────────────────────────

class Player(SpriteAnimato):
    DIREZIONI = ["su", "sinistra", "giu", "destra"]
    _ANIMS = [
        ("idle", IDLE_SOURCE, IDLE_COLS, DURATA_IDLE),
        ("walk", WALK_SOURCE, WALK_COLS, DURATA_WALK),
        ("run",  RUN_SOURCE,  RUN_COLS,  DURATA_RUN),
    ]
    _KEYS = {
        arcade.key.UP: "su", arcade.key.W: "su",
        arcade.key.DOWN: "giu", arcade.key.S: "giu",
        arcade.key.LEFT: "sinistra", arcade.key.A: "sinistra",
        arcade.key.RIGHT: "destra", arcade.key.D: "destra",
    }

    def __init__(self, scala=1.0):
        super().__init__(scala=scala)
        self._scala = scala

    def carica_animazioni(self):
        for i, d in enumerate(self.DIREZIONI):
            for nome, src, cols, dur in self._ANIMS:
                self.aggiungi_animazione(
                    nome=f"{nome}_{d}", percorso=src,
                    frame_width=FRAME_W, frame_height=FRAME_H,
                    num_frame=cols, colonne=cols, durata=dur,
                    loop=True, default=(nome=="idle" and d=="giu"), riga=i)
        self.direzione = "giu"
        self.key_su = self.key_giu = self.key_sinistra = self.key_destra = self.key_corsa = False

    def aggiorna_scala(self, ns):
        self._scala = ns; self.scale = ns
        if hasattr(self, "animazioni"): self.animazioni.clear()
        self.carica_animazioni()

    def update_animation(self, delta_time=1/60):
        moving = self.key_su or self.key_giu or self.key_sinistra or self.key_destra
        pre = ("run" if self.key_corsa else "walk") if moving else "idle"
        self.imposta_animazione(f"{pre}_{self.direzione}")
        super().update_animation(delta_time)

    def aggiorna_posizione(self, dt, mw, mh):
        speed = SPEED_RUN if self.key_corsa else SPEED_WALK
        dx = int(self.key_destra) - int(self.key_sinistra)
        dy = int(self.key_su)     - int(self.key_giu)
        if dx or dy:
            self.direzione = (("su" if dy>0 else "giu") if abs(dy)>=abs(dx)
                              else ("destra" if dx>0 else "sinistra"))
        self.change_x, self.change_y = dx*speed, dy*speed
        hw, hh = self.width/2, self.height/2
        self.center_x = max(hw, min(mw-hw, self.center_x))
        self.center_y = max(hh, min(mh-hh, self.center_y))

    def on_key_press(self, key):
        if key in self._KEYS:   setattr(self, f"key_{self._KEYS[key]}", True)
        if key == arcade.key.LSHIFT: self.key_corsa = True

    def on_key_release(self, key):
        if key in self._KEYS:   setattr(self, f"key_{self._KEYS[key]}", False)
        if key == arcade.key.LSHIFT: self.key_corsa = False

# ── TitleScreen ────────────────────────────────────────────────────────────────

class TitleScreen:
    def __init__(self, sw, sh):
        self.sw, self.sh = sw, sh
        self._blink, self._mostra = 0.0, True
        try:    self._tex = arcade.load_texture(TITLE_SOURCE)
        except: self._tex = None

    def update(self, dt):
        self._blink += dt
        if self._blink >= 0.6: self._blink = 0.0; self._mostra = not self._mostra

    def draw(self):
        if self._tex: _draw_tex(self._tex, self.sw//2, self.sh//2, self.sw, self.sh)
        else: arcade.draw_rect_filled(arcade.XYWH(self.sw//2,self.sh//2,self.sw,self.sh), arcade.color.DARK_BLUE_GRAY)
        if self._mostra:
            get_papiro().draw_testo("Premi INVIO per iniziare",
                                    self.sw//2, 80, 400, 60,
                                    font_size=14, colore=(70,30,5,255))

# ── GameWindow ─────────────────────────────────────────────────────────────────

class GameWindow(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_W, SCREEN_H, "Life Village")
        arcade.set_background_color(arcade.color.BLACK)
        global ITEM_TEXTURES
        ITEM_TEXTURES = _build_item_textures()

        self._in_title = True
        self.title_screen = TitleScreen(SCREEN_W, SCREEN_H)
        self.inventario = Inventario()
        self.commercio = FinestraCommercio()
        self.commercio.inventario = self.inventario

        self.player = self.sprite_list = self.tile_map = None
        self.scene = self.physics_engine = self.current_map_name = None
        self.map_width = self.map_height = 0.0
        self._porte = []; self._transizione_pendente = None; self._cooldown_porta = 0.0
        self._oggetti_mondo = []; self._msg_pieno = 0.0; self._npc_corrente = None

        try:
            self.cam_world = arcade.camera.Camera2D()
            self.cam_gui   = arcade.camera.Camera2D(); self._a3 = True
        except AttributeError:
            self.cam_world = arcade.Camera(SCREEN_W, SCREEN_H)
            self.cam_gui   = arcade.Camera(SCREEN_W, SCREEN_H); self._a3 = False

    def setup(self, map_name="Mondo.tmx", spawn_tile_x=None, spawn_tile_y=None):
        map_path = MAPS[map_name]; self.current_map_name = map_name
        root = ET.parse(map_path).getroot()
        tw, th = int(root.get("width")), int(root.get("height"))
        ts = (min(SCREEN_W/(tw*TILE_SIZE), SCREEN_H/(th*TILE_SIZE))
              if tw <= 12 and th <= 10 else TILE_SCALE)
        self.map_width, self.map_height = tw*TILE_SIZE*ts, th*TILE_SIZE*ts
        self.tile_map = arcade.load_tilemap(map_path, scaling=ts)
        self.scene    = arcade.Scene.from_tilemap(self.tile_map)

        ps = (PLAYER_TILE_HEIGHT*TILE_SIZE*ts) / FRAME_H
        if self.player is None:
            self.player = Player(scala=ps); self.player.carica_animazioni()
            self.sprite_list = arcade.SpriteList(); self.sprite_list.append(self.player)
        else:
            self.player.aggiorna_scala(ps)

        self.player.center_x = ((spawn_tile_x+0.5)*TILE_SIZE*ts if spawn_tile_x is not None
                                 else self.map_width/2)
        self.player.center_y = ((th-spawn_tile_y-0.5)*TILE_SIZE*ts if spawn_tile_y is not None
                                 else self.map_height/2)
        self.player.change_x = self.player.change_y = 0

        muri = arcade.SpriteList(use_spatial_hash=True)
        if COLLISION_LAYER in self.scene._name_mapping:
            if "Ponte" in self.scene._name_mapping:
                pp = {(round(s.center_x),round(s.center_y)) for s in self.scene["Ponte"]}
                for s in self.scene[COLLISION_LAYER]:
                    if (round(s.center_x),round(s.center_y)) not in pp: muri.append(s)
            else:
                muri = self.scene[COLLISION_LAYER]
        self.physics_engine = arcade.PhysicsEngineSimple(self.player, muri)
        self._porte = self._leggi_porte(map_path, th, ts)
        self._transizione_pendente = None; self._cooldown_porta = 0.0
        self.commercio.chiudi()

        if map_name == "Mondo.tmx" and not self._oggetti_mondo:
            self._popola_oggetti_mondo(th, ts)

        self._npc_corrente = None
        if map_name in NPC_CONFIG:
            cfg = NPC_CONFIG[map_name]
            self._npc_corrente = NPC(
                cfg["tipo"],
                (cfg["tile_x"]+0.5)*TILE_SIZE*ts,
                (th-cfg["tile_y"]-0.5)*TILE_SIZE*ts,
                cfg["nome"], cfg["dialogo"], cfg["acquista"])
        self._cam_immediata()

    def _popola_oggetti_mondo(self, th, ts):
        self._oggetti_mondo = []
        for tipo, lista in [("legna",SPAWN_LEGNA),("roccia",SPAWN_ROCCIA),
                             ("carota",SPAWN_CAROTA),("grano",SPAWN_GRANO),("pesce",SPAWN_PESCE)]:
            for tx, ty in lista:
                self._oggetti_mondo.append(OggettoMondo(
                    tipo, (tx+0.5)*TILE_SIZE*ts, (th-ty-0.5)*TILE_SIZE*ts, tx, ty))

    def _leggi_porte(self, map_path, th, ts):
        porte = []; root = ET.parse(map_path).getroot()
        for og in root.findall("objectgroup"):
            if og.get("name") != "Porte": continue
            lp = {}
            pe = og.find("properties")
            if pe is not None:
                for p in pe.findall("property"): lp[p.get("name")] = p.get("value")
            for obj in og.findall("object"):
                props = dict(lp)
                ope = obj.find("properties")
                if ope is not None:
                    for p in ope.findall("property"): props[p.get("name")] = p.get("value")
                dest = props.get("destinazione","").strip()
                if not dest or dest not in MAPS: continue
                ox, oy = float(obj.get("x",0)), float(obj.get("y",0))
                w,  h  = float(obj.get("width",TILE_SIZE)), float(obj.get("height",TILE_SIZE))
                l = ox*ts; t = (th*TILE_SIZE - oy)*ts
                porte.append(dict(left=l, right=l+w*ts, bottom=t-h*ts, top=t,
                                  dest=dest, spawn_x=float(props.get("spawn_x",4)),
                                  spawn_y=float(props.get("spawn_y",4))))
        return porte

    def _prova_raccolta(self):
        if self.current_map_name != "Mondo.tmx": return
        if self.inventario.pieno(): self._msg_pieno = 2.0; return
        px, py = self.player.center_x, self.player.center_y
        best, bd = None, RACCOLTA_RAGGIO
        for obj in self._oggetti_mondo:
            if not obj.visibile: continue
            d = _dist(obj.center_x, obj.center_y, px, py)
            if d < bd: bd = d; best = obj
        if best and self.inventario.aggiungi(best.tipo): best.raccogli()

    def _prova_interazione_npc(self):
        if self._npc_corrente and self._npc_corrente.vicino(self.player.center_x, self.player.center_y):
            if self.commercio.aperta: self.commercio.chiudi()
            else: self.commercio.apri(self._npc_corrente, self.inventario)

    def _controlla_porte(self):
        if self._cooldown_porta > 0 or self._transizione_pendente: return
        px, py = self.player.center_x, self.player.center_y
        for p in self._porte:
            if p["left"] <= px <= p["right"] and p["bottom"] <= py <= p["top"]:
                self._transizione_pendente = p; return

    def _clamp_cam(self, px, py):
        if self.map_width < SCREEN_W or self.map_height < SCREEN_H:
            return self.map_width/2, self.map_height/2
        return (max(SCREEN_W/2, min(self.map_width-SCREEN_W/2, px)),
                max(SCREEN_H/2, min(self.map_height-SCREEN_H/2, py)))

    def _cam_immediata(self):
        cx, cy = self._clamp_cam(self.player.center_x, self.player.center_y)
        if self._a3: self.cam_world.position = (cx, cy)
        else: self.cam_world.move_to((cx - SCREEN_W/2, cy - SCREEN_H/2))

    def _aggiorna_camera(self):
        tx, ty = self._clamp_cam(self.player.center_x, self.player.center_y)
        if self._a3:
            cx, cy = self.cam_world.position
            self.cam_world.position = (cx+(tx-cx)*0.15, cy+(ty-cy)*0.15)
        else:
            cx, cy = self.cam_world.position
            self.cam_world.move_to((cx+(tx-cx-SCREEN_W/2)*0.15+cx,
                                    cy+(ty-cy-SCREEN_H/2)*0.15+cy))

    def on_draw(self):
        self.clear()
        if self._in_title:
            self.cam_gui.use(); self.title_screen.draw(); return

        self.cam_world.use()
        for ln in BACKGROUND_LAYERS:
            if ln in self.scene._name_mapping: self.scene[ln].draw()
        if self.current_map_name == "Mondo.tmx":
            for obj in self._oggetti_mondo: obj.draw_se_visibile()

        depth = []
        for ln in DEPTH_LAYERS:
            if ln in self.scene._name_mapping: depth.extend(self.scene[ln].sprite_list)
        if self._npc_corrente: depth.append(self._npc_corrente)
        depth.append(self.player)
        depth.sort(key=lambda s: -s.center_y)
        for s in depth: arcade.draw_sprite(s)

        for ln in FOREGROUND_LAYERS:
            if ln in self.scene._name_mapping: self.scene[ln].draw()

        px, py = self.player.center_x, self.player.center_y
        if self.current_map_name == "Mondo.tmx":
            for obj in self._oggetti_mondo: obj.draw_indicatore(px, py)
        if self._npc_corrente:
            self._npc_corrente.draw_nome()
            self._npc_corrente.draw_indicatore(px, py)

        self.cam_gui.use()
        _pt(f"Mappa: {self.current_map_name}", 10, SCREEN_H-20,
            size=9, colore=(220,220,220,200), anchor_x="left", anchor_y="center")
        if self._msg_pieno > 0:
            get_papiro().draw_testo("Inventario pieno!", SCREEN_W//2, SCREEN_H//2, 340, 70,
                                    font_size=16, colore=(160,40,10,255))
        self.inventario.draw(SCREEN_W, SCREEN_H)
        self.commercio.draw(SCREEN_W, SCREEN_H)
        if self._npc_corrente and not self.commercio.aperta:
            if self._npc_corrente.vicino(px, py):
                self._npc_corrente.draw_dialogo_papiro(SCREEN_W, SCREEN_H)

    def on_update(self, dt):
        if self._in_title: self.title_screen.update(dt); return
        self.commercio.update(dt)
        self._cooldown_porta = max(0.0, self._cooldown_porta - dt)
        if self._msg_pieno > 0: self._msg_pieno -= dt
        if self._transizione_pendente:
            p = self._transizione_pendente; self._transizione_pendente = None
            self.setup(map_name=p["dest"], spawn_tile_x=int(p["spawn_x"]), spawn_tile_y=int(p["spawn_y"]))
            self._cooldown_porta = 1.2; return
        if not self.commercio.aperta:
            self.player.aggiorna_posizione(dt, self.map_width, self.map_height)
            self.physics_engine.update(); self._aggiorna_camera(); self._controlla_porte()
        self.sprite_list.update_animation(dt); self.scene.update_animation(dt)
        if self.current_map_name == "Mondo.tmx":
            for obj in self._oggetti_mondo: obj.update(dt)

    def on_key_press(self, key, modifiers):
        if self._in_title:
            if key in (arcade.key.RETURN, arcade.key.ENTER, arcade.key.SPACE):
                self._in_title = False; self.setup()
            return
        if self.commercio.aperta: self.commercio.on_key_press(key); return
        if key == arcade.key.E:
            if self._npc_corrente: self._prova_interazione_npc()
            else: self._prova_raccolta()
            return
        self.inventario.on_key_press(key); self.player.on_key_press(key)

    def on_key_release(self, key, modifiers):
        if self._in_title or self.commercio.aperta: return
        self.player.on_key_release(key)

if __name__ == "__main__":
    window = GameWindow()
    arcade.run()