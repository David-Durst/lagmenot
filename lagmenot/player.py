from math import cos, sin, radians, hypot, ceil

# import basic pygame modules
import pygame as pg

class Player(pg.sprite.Sprite):
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
        pg.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0].copy()
        self.orig_image = self.image
        self.angle = 0
        self.x_velocity = 0
        self.y_velocity = 0
        self.rect = self.image.get_rect(midbottom=screenrect.midbottom)
        self.x = self.rect.topleft[0]
        self.y = self.rect.topleft[1]
        self.reloading = 0
        self.origtop = self.rect.top
        self.facing = -1
        self.screenrect = screenrect

    def rotate_image_and_rect(self):
        self.image = pg.transform.rotate(self.orig_image, self.angle)
        self.rect = self.image.get_rect(center=self.rect.center)

    def move_rect(self):
        self.x += self.x_velocity
        self.y += self.y_velocity
        self.rect.topleft = (int(self.x), int(self.y))

    def move(self, right_pressed, left_pressed, up_pressed, down_pressed, stop_pressed, ignore_physics):
        if right_pressed or left_pressed:
            if right_pressed:
                self.angle -= self.rotate_speed
            else:
                self.angle += self.rotate_speed
            self.rotate_image_and_rect()


        compute_angle = radians(self.angle - 90)
        old_x_velocity = self.x_velocity
        old_y_velocity = self.y_velocity
        if up_pressed:
            self.x_velocity -= self.accel*cos(compute_angle)
            self.y_velocity += self.accel*sin(compute_angle)
        elif down_pressed:
            self.x_velocity += self.accel*cos(compute_angle)
            self.y_velocity -= self.accel*sin(compute_angle)

        total_velocity = hypot(self.x_velocity, self.y_velocity) #pow(self.x_velocity, 2) + pow(self.y_velocity, 2)
        if total_velocity > self.max_velocity:
            self.x_velocity = self.x_velocity / total_velocity * self.max_velocity #self.max_velocity * cos(compute_angle) * -1#s
            self.y_velocity = self.y_velocity / total_velocity * self.max_velocity #self.max_velocity * sin(compute_angle)#

        if ignore_physics:
            if right_pressed:
                self.x_velocity = self.max_velocity
                self.y_velocity = 0.0
            if left_pressed:
                self.x_velocity = -1*self.max_velocity
                self.y_velocity = 0.0
            if down_pressed:
                self.x_velocity = 0.0
                self.y_velocity = self.max_velocity
            if up_pressed:
                self.x_velocity = 0.0
                self.y_velocity = -1*self.max_velocity
            if stop_pressed:
                self.x_velocity = 0.0
                self.y_velocity = 0.0

        print(f"x_velocity: {self.x_velocity}")
        print(f"y_velocity: {self.y_velocity}")
        print(f"angle: {self.angle}")
        print(f"ignore_physics: {ignore_physics}")

        #self.x_velocity = min(self.x_velocity, self.max_velocity)
        #self.y_velocity = min(self.y_velocity, self.max_velocity)
        #self.x_velocity = max(self.x_velocity, -1*self.max_velocity)
        #self.y_velocity = max(self.y_velocity, -1*self.max_velocity)

        #self.rect.move_ip(self.x_velocity, self.y_velocity)
        self.move_rect()
        #self.rect = self.rect.clamp(SCREENRECT)
        if self.rect.top < self.screenrect.top-self.bounce_pixels or self.rect.bottom > self.screenrect.bottom+self.bounce_pixels:
            self.y_velocity *= -1

        if self.rect.left < self.screenrect.left-self.bounce_pixels or self.rect.right > self.screenrect.right+self.bounce_pixels:
            self.x_velocity *= -1

        #self.rect.top = self.origtop - (self.rect.left // self.bounce % 2)

    def gunpos(self):
        pos = self.gun_offset + self.rect.centerx
        return pos, self.rect.top
