from math import cos, sin, radians, hypot, ceil
from dataclasses import dataclass
import pygame as pg
from typing import Tuple


@dataclass(frozen=True)
class InputCmd:
    up: float
    down: float
    left: float
    right: float
    firing: bool
    # debug mode settings
    ignore_physics: bool
    stop: bool


def create_one_tick_input(up: bool, down: bool, left: bool, right: bool,
                          firing: bool, ignore_physics: bool, stop: bool):
    return InputCmd(1.0 if up else 0.0, 1.0 if down else 0.0, 1.0 if left else 0.0, 1.0 if right else 0.0,
                    firing, ignore_physics, stop)

def merge_input_cmds(input1: InputCmd, input2: InputCmd):
    return InputCmd(input1.up + input2.up, input1.down + input2.down, input1.left + input2.left, input1.right + input2.right,
                    input1.firing or input2.firing, input1.ignore_physics or input2.ignore_physics, input1.stop or input2.stop)

no_input = create_one_tick_input(False, False, False, False, False, False, False)


class PlayerWithoutSprite:
    """ Representing the player as a moon buggy type car.
    """

    speed = 10
    bounce = 24
    gun_offset = -11
    images = []
    accel = 0.1
    rotate_speed = 1.0
    max_velocity = 4.0
    bounce_pixels = 2

    def __init__(self, screenrect: pg.Rect):
        self.image = self.images[0].copy()
        self.orig_image = self.image
        self.angle = 0
        self.x_velocity = 0
        self.y_velocity = 0
        self.rect = self.image.get_rect(midbottom=screenrect.midbottom)
        self.x = self.rect.topleft[0]
        self.y = self.rect.topleft[1]
        self.reloading = 0
        self.facing = -1
        self.screenrect = screenrect
        self.last_move_time = 0

    def set_start(self, r: pg.rect):
        self.rect = r
        self.x = r.topleft[0]
        self.y = r.topleft[1]


    def clone_no_sprite(self) -> 'PlayerWithoutSprite':
        result = PlayerWithoutSprite(self.screenrect)
        result.image = self.image.copy()
        result.orig_image = result.image
        result.angle = self.angle
        result.x_velocity = self.x_velocity
        result.y_velocity = self.y_velocity
        result.rect = self.rect.copy()
        result.x = self.x
        result.y = self.y
        result.reloading = self.reloading
        result.facing = self.facing
        result.screenrect = self.screenrect
        result.last_move_time = self.last_move_time
        return result

    def update_from_clone(self, clone: 'PlayerWithoutSprite'):
        if clone is None:
            return
        self.x_velocity = clone.x_velocity
        self.y_velocity = clone.y_velocity
        self.rect = clone.rect.copy()
        self.x = clone.x
        self.y = clone.y
        self.reloading = clone.reloading
        self.facing = clone.facing
        self.angle = clone.angle
        self.rotate_image_and_rect()

    def rotate_image_and_rect(self):
        self.image = pg.transform.rotate(self.orig_image, self.angle)
        self.rect = self.image.get_rect(center=self.rect.center)

    def move_rect(self):
        self.x += self.x_velocity
        self.y += self.y_velocity
        self.rect.topleft = (int(self.x), int(self.y))

    def move(self, input: InputCmd, cur_time: int):
        time_delta = (cur_time - self.last_move_time) / 10
        self.last_move_time = cur_time
        if input.right != 0.0 or input.left != 0.0:
            self.angle -= self.rotate_speed * (input.right - input.left)
            self.rotate_image_and_rect()

        compute_angle = radians(self.angle - 90)
        self.x_velocity -= (input.up - input.down) * self.accel * cos(compute_angle)
        self.y_velocity += (input.up - input.down) * self.accel * sin(compute_angle)

        total_velocity = hypot(self.x_velocity, self.y_velocity)  # pow(self.x_velocity, 2) + pow(self.y_velocity, 2)
        if total_velocity > self.max_velocity:
            self.x_velocity = self.x_velocity / total_velocity * self.max_velocity * time_delta # self.max_velocity * cos(compute_angle) * -1#s
            self.y_velocity = self.y_velocity / total_velocity * self.max_velocity * time_delta # self.max_velocity * sin(compute_angle)#

        if input.ignore_physics:
            if input.right:
                self.x_velocity = self.max_velocity
                self.y_velocity = 0.0
            if input.left:
                self.x_velocity = -1 * self.max_velocity
                self.y_velocity = 0.0
            if input.down:
                self.x_velocity = 0.0
                self.y_velocity = self.max_velocity
            if input.up:
                self.x_velocity = 0.0
                self.y_velocity = -1 * self.max_velocity
            if input.stop:
                self.x_velocity = 0.0
                self.y_velocity = 0.0

        #print(f"x_velocity: {self.x_velocity}")
        #print(f"y_velocity: {self.y_velocity}")
        #print(f"angle: {self.angle}")
        #print(f"ignore_physics: {input.ignore_physics}")

        # self.x_velocity = min(self.x_velocity, self.max_velocity)
        # self.y_velocity = min(self.y_velocity, self.max_velocity)
        # self.x_velocity = max(self.x_velocity, -1*self.max_velocity)
        # self.y_velocity = max(self.y_velocity, -1*self.max_velocity)

        # self.rect.move_ip(self.x_velocity, self.y_velocity)
        self.move_rect()
        # self.rect = self.rect.clamp(SCREENRECT)
        if self.rect.top < self.screenrect.top - self.bounce_pixels or self.rect.bottom > self.screenrect.bottom + self.bounce_pixels:
            self.y_velocity *= -1
            if self.rect.top < self.screenrect.top - self.bounce_pixels:
                self.y += self.bounce_pixels/2
            if self.rect.bottom > self.screenrect.bottom + self.bounce_pixels:
                self.y -= self.bounce_pixels/2

        if self.rect.left < self.screenrect.left - self.bounce_pixels or self.rect.right > self.screenrect.right + self.bounce_pixels:
            self.x_velocity *= -1
            if self.rect.left < self.screenrect.left - self.bounce_pixels:
                self.x += self.bounce_pixels/2
            if self.rect.right > self.screenrect.right + self.bounce_pixels:
                self.x -= self.bounce_pixels/2

    def gunpos(self):
        pos = self.gun_offset + self.rect.centerx
        return pos, self.rect.top


class Player(pg.sprite.Sprite, PlayerWithoutSprite):

    def __init__(self, screenrect: pg.Rect):
        pg.sprite.Sprite.__init__(self, self.containers)
        PlayerWithoutSprite.__init__(self, screenrect)

    def clone_whole_player(self) -> 'Player':
        result = Player(self.screenrect)
        result.image = self.image.copy()
        result.orig_image = self.orig_image.copy()
        result.angle = self.angle
        result.x_velocity = self.x_velocity
        result.y_velocity = self.y_velocity
        result.rect = self.rect.copy()
        result.x = self.x
        result.y = self.y
        result.reloading = self.reloading
        result.facing = self.facing
        result.screenrect = self.screenrect
        return result

