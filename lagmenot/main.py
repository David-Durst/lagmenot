import random
import os
import sys
from pathlib import Path
from math import cos, sin, radians, hypot, ceil

# import basic pygame modules
import pygame as pg
from lagmenot.player import Player, PlayerWithoutSprite, InputCmd, create_one_tick_input
from lagmenot.server import Server, PredictMsg

assets_dir = Path(os.path.abspath(__file__)).parent.parent / Path("assets")
SCREENRECT = pg.Rect(0, 0, 1500, 1000)

def change_color(surface: pg.Surface, target_color: pg.Color):
    width, height = surface.get_size()
    for x in range(width):
        for y in range(height):
            if surface.get_at((x,y)).a != 0:
                surface.set_at((x,y), target_color)

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
    PlayerWithoutSprite.images = [img, pg.transform.flip(img, 1, 0)]
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
    Player.containers = players, all
    Shot.containers = shots, all
    PredictMsg.containers = all
    
    # initialize starting sprites
    clock = pg.time.Clock()
    player = Player(SCREENRECT)
    enemy = Player(SCREENRECT)
    change_color(enemy.image, pg.Color(255, 0, 0, 255))
    enemy.angle = -90.0
    enemy.set_start(enemy.image.get_rect(midleft=SCREENRECT.midleft))
    enemy.rotate_image_and_rect()
    enemy_on_server = Player(SCREENRECT)
    change_color(enemy_on_server.image, pg.Color(0, 0, 255, 255))
    enemy_on_server.angle = -90.0
    enemy_on_server.set_start(enemy.image.get_rect(midleft=SCREENRECT.midleft))
    enemy_on_server.rotate_image_and_rect()

    # setup debug messaging
    predict_msg = PredictMsg(SCREENRECT)

    server = Server(enemy_on_server, predict_msg)

    running = True
    while running:
        # get input
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                running = False

        keystate = pg.key.get_pressed()
        
        # clear/erase the last drawn sprites
        all.clear(screen, clear_callback)

        # update all the sprites
        all.update()
        
        # handle player input
        player_input = create_one_tick_input(keystate[pg.K_UP], keystate[pg.K_DOWN], keystate[pg.K_LEFT], keystate[pg.K_RIGHT],
                                             keystate[pg.K_SPACE], keystate[pg.K_LCTRL], keystate[pg.K_SPACE])
        player.move(player_input)

        # handle enemy logic
        enemy_input = create_one_tick_input(True, keystate[pg.K_s], keystate[pg.K_a], keystate[pg.K_d],
                                            keystate[pg.K_f], keystate[pg.K_LCTRL], keystate[pg.K_g])
        #print(f"cur ticks: {pg.time.get_ticks()}")
        #print(f"enemy_on_server x_velocity: {enemy_on_server.x_velocity}")
        #print(f"enemy_on_server y_velocity: {enemy_on_server.y_velocity}")
        #print(f"enemy_on_server angle: {enemy_on_server.angle}")
        #print(f"enemy angle: {enemy.angle}")
        server.send_client_to_server(enemy_input)
        server.receive_client_to_server()
        server.send_server_to_client()
        enemy.update_from_clone(server.receive_server_to_client())

        if not player.reloading and player_input.firing:
            Shot(player.gunpos())
        player.reloading = player_input.firing

        # handle prediction type change
        if keystate[pg.K_0]:
            server.change_predict_type(0)
        if keystate[pg.K_1]:
            server.change_predict_type(1)

        # draw the scene
        dirty = all.draw(screen)
        pg.display.update(dirty)

        # cap the framerate at 100fps. Also called 40HZ or 40 times per second.
        clock.tick(100)
    
    # pygame doesn't quit right all the time https://stackoverflow.com/questions/19882415/closing-pygame-window
    pg.display.quit()
    sys.exit(0)

# call the "main" function if running this script
if __name__ == "__main__":
    main()