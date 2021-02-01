import random
import os
from pathlib import Path
from math import cos, sin, radians

# import basic pygame modules
import pygame as pg

assets_dir = Path(os.path.abspath(__file__)).parent.parent / Path("assets")
SCREENRECT = pg.Rect(0, 0, 1500, 1000)

def load_image(file, zoom):
    """ loads an image, prepares it for play
    """
    file = str(assets_dir / Path(file))
    try:
        surface = pg.transform.rotozoom(pg.image.load(file), 0, zoom)
    except pg.error:
        raise SystemExit('Could not load image "%s" %s' % (file, pg.get_error()))
    return surface.convert_alpha()


def load_sound(file):
    """ because pygame can be be compiled without mixer.
    """
    if not pg.mixer:
        return None
    file = str(assets_dir / Path(file))
    try:
        sound = pg.mixer.Sound(file)
        return sound
    except pg.error:
        print("Warning, unable to load, %s" % file)
    return None

class Player(pg.sprite.Sprite):
    """ Representing the player as a moon buggy type car.
    """

    speed = 10
    bounce = 24
    gun_offset = -11
    images = []
    accel = 0.1
    rotate_speed = 1
    max_velocity = 2
    bounce_pixels = 2


    def __init__(self):
        pg.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        self.orig_image = self.image
        self.angle = 0
        self.x_velocity = 0
        self.y_velocity = 0
        self.rect = self.image.get_rect(midbottom=SCREENRECT.midbottom)
        self.reloading = 0
        self.origtop = self.rect.top
        self.facing = -1

    def move(self, right_pressed, left_pressed, up_pressed, down_pressed):
        if False: #right_pressed or left_pressed:
            if right_pressed:
                self.angle -= self.rotate_speed
            else:
                self.angle += self.rotate_speed
            self.image = pg.transform.rotate(self.orig_image, self.angle)
            self.rect = self.image.get_rect()


        compute_angle = radians(self.angle - 90)
        if up_pressed:
            self.x_velocity += self.accel*cos(compute_angle)
            self.y_velocity += self.accel*sin(compute_angle)
            print(f"new x_velocity: {self.x_velocity}")
            print(f"new y_velocity: {self.y_velocity}")
        elif down_pressed:
            self.x_velocity -= self.accel*cos(compute_angle)
            self.y_velocity -= self.accel*sin(compute_angle)
            print(f"new x_velocity: {self.x_velocity}")
            print(f"new y_velocity: {self.y_velocity}")

        self.x_velocity = min(self.x_velocity, self.max_velocity)
        self.y_velocity = min(self.y_velocity, self.max_velocity)
        self.x_velocity = max(self.x_velocity, -1*self.max_velocity)
        self.y_velocity = max(self.y_velocity, -1*self.max_velocity)

        self.rect.move_ip(self.x_velocity, self.y_velocity)
        #self.rect = self.rect.clamp(SCREENRECT)
        if self.rect.top < SCREENRECT.top-self.bounce_pixels or self.rect.bottom > SCREENRECT.bottom+self.bounce_pixels:
            self.y_velocity *= -1

        if self.rect.left > SCREENRECT.left or self.rect.right < SCREENRECT.right:
            self.x_velocity *= -1

        #self.rect.top = self.origtop - (self.rect.left // self.bounce % 2)

    def gunpos(self):
        pos = self.gun_offset + self.rect.centerx
        return pos, self.rect.top


class Shot(pg.sprite.Sprite):
    """ a bullet the Player sprite fires.
    """

    speed = -11
    images = []

    def __init__(self, pos):
        pg.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect(midbottom=pos)

    def update(self):
        """ called every time around the game loop.
        Every tick we move the shot upwards.
        """
        self.rect.move_ip(0, self.speed)
        if self.rect.top <= 0:
            self.kill()

def clear_callback(surf, rect):
    """ redraw background
    """
    color = 0, 0, 0
    surf.fill(color, rect)

def main(winstyle=0):
    # Initialize pygame
    if pg.get_sdl_version()[0] == 2:
        pg.mixer.pre_init(44100, 32, 2, 1024)
    pg.init()
    if pg.mixer and not pg.mixer.get_init():
        print("Warning, no sound")
        pg.mixer = None

    fullscreen = False
    # Set the display mode
    winstyle = 0  # |FULLSCREEN
    bestdepth = pg.display.mode_ok(SCREENRECT.size, winstyle, 32)
    screen = pg.display.set_mode(SCREENRECT.size, winstyle, bestdepth)
    
    
    # Load images, assign to sprite classes
    # (do this before the classes are used, after screen setup)
    img = load_image("ship.png", 0.25)
    Player.images = [img, pg.transform.flip(img, 1, 0)]
    Shot.images = [load_image("shot.png", 0.25)]

    # decorate the game window
    icon = pg.transform.scale(Player.images[0], (32, 32))
    pg.display.set_icon(icon)
    pg.display.set_caption("LagMeNot Testbench")
    pg.mouse.set_visible(0)
    
    # Initialize Game Groups
    players = pg.sprite.Group()
    shots = pg.sprite.Group()
    all = pg.sprite.RenderUpdates()

    # assign default groups to each sprite class
    Player.containers = all
    Shot.containers = shots, all
    
    # initialize starting sprites
    clock = pg.time.Clock()
    player = Player()
    
    while True:
        # get input
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                return
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_f:
                    if not fullscreen:
                        print("Changing to FULLSCREEN")
                        screen_backup = screen.copy()
                        screen = pg.display.set_mode(
                            SCREENRECT.size, winstyle | pg.FULLSCREEN, bestdepth
                        )
                        screen.blit(screen_backup, (0, 0))
                    else:
                        print("Changing to windowed mode")
                        screen_backup = screen.copy()
                        screen = pg.display.set_mode(
                            SCREENRECT.size, winstyle, bestdepth
                        )
                        screen.blit(screen_backup, (0, 0))
                    pg.display.flip()
                    fullscreen = not fullscreen

        keystate = pg.key.get_pressed()
        
        # clear/erase the last drawn sprites
        all.clear(screen, clear_callback)

        # update all the sprites
        all.update()
        
        # handle player input
        right_pressed = keystate[pg.K_RIGHT]
        left_pressed = keystate[pg.K_LEFT]
        up_pressed = keystate[pg.K_UP]
        down_pressed = keystate[pg.K_DOWN]
        player.move(right_pressed, left_pressed, up_pressed, down_pressed)
        firing = keystate[pg.K_SPACE]
        if not player.reloading and firing:
            Shot(player.gunpos())
        player.reloading = firing
        
        # draw the scene
        dirty = all.draw(screen)
        pg.display.update(dirty)

        # cap the framerate at 100fps. Also called 40HZ or 40 times per second.
        clock.tick(100)

# call the "main" function if running this script
if __name__ == "__main__":
    main()