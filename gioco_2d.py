import arcade
import math

SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600
PLAYER_SPEED = 4


class MyGame(arcade.Window):

    def __init__(self, width, height, title):
        super().__init__(width, height, title)

        self.player = None
        self.player_list = arcade.SpriteList()

        self.move_up = False
        self.move_down = False
        self.move_left = False
        self.move_right = False

        self.setup()

    def setup(self):
        self.player = arcade.Sprite("personaggio.png", scale=1.0)
        self.player.center_x = SCREEN_WIDTH // 2
        self.player.center_y = SCREEN_HEIGHT // 2

        self.player_list.append(self.player)

    def on_draw(self):
        self.clear()
        self.player_list.draw()

    def on_update(self, delta_time):
        dx = 0
        dy = 0

        if self.move_up:
            dy += 1
        if self.move_down:
            dy -= 1
        if self.move_left:
            dx -= 1
        if self.move_right:
            dx += 1

        # Normalizzazione diagonale (movimento uniforme)
        length = math.hypot(dx, dy)
        if length > 0:
            dx /= length
            dy /= length

        self.player.center_x += dx * PLAYER_SPEED
        self.player.center_y += dy * PLAYER_SPEED

    def on_key_press(self, key, modifiers):
        if key == arcade.key.W:
            self.move_up = True
        elif key == arcade.key.S:
            self.move_down = True
        elif key == arcade.key.A:
            self.move_left = True
        elif key == arcade.key.D:
            self.move_right = True

    def on_key_release(self, key, modifiers):
        if key == arcade.key.W:
            self.move_up = False
        elif key == arcade.key.S:
            self.move_down = False
        elif key == arcade.key.A:
            self.move_left = False
        elif key == arcade.key.D:
            self.move_right = False


def main():
    game = MyGame(SCREEN_WIDTH, SCREEN_HEIGHT, "Il mio giochino")
    arcade.run()


if __name__ == "__main__":
    main()
