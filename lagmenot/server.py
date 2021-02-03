from lagmenot.player import Player, PlayerWithoutSprite, InputState, no_input
import pygame as pg
from dataclasses import dataclass
from typing import Deque
from collections import deque
from enum import Enum


@dataclass(frozen=True)
class InputPacket:
    cmd: InputState
    receive_time: int


@dataclass
class RemoteRect:
    topleft_x: int
    topleft_y: int

    def get_as_topleft(self):
        return self.topleft_x, self.topleft_y


predict_messages = ["no command", "replay command"]

class PredictType(Enum):
    NO_COMMAND = 0
    REPLAY_COMMAND = 1


class Server:
    enemy: Player
    queue: Deque[InputPacket]
    # in milliseconds
    latency = 50
    last_server_to_client_tick: int
    last_client_to_server_tick: int
    last_server_to_client_message: PlayerWithoutSprite
    last_applied_cmd: InputState
    predict_type: PredictType
    predict_msg: 'PredictMsg'

    def __init__(self, enemy: Player, predict_msg: 'PredictMsg'):
        self.enemy = enemy
        self.queue = deque()
        self.last_server_to_client_tick = 0
        self.last_client_to_server_tick = 0
        self.last_server_to_client_message = None
        self.predict_type = PredictType(0)
        self.predict_msg = predict_msg
        self.predict_msg.msg = predict_messages[0]
        self.last_applied_cmd = no_input

    def client_to_server(self, cmd: InputState):
        cur_time = pg.time.get_ticks()
        if self.last_client_to_server_tick + self.latency < cur_time:
            self.last_client_to_server_tick = cur_time
            self.queue.append(InputPacket(cmd, pg.time.get_ticks()))

    def server_to_client(self) -> PlayerWithoutSprite:
        cur_time = pg.time.get_ticks()
        if self.last_server_to_client_tick + self.latency < cur_time:
            self.last_server_to_client_tick = cur_time
            self.last_server_to_client_message = self.enemy.clone_no_sprite()
            return self.enemy
        else:
            self.last_server_to_client_message.move(self.last_applied_cmd)
            if self.predict_type == PredictType.NO_COMMAND:
                return None
            else:
                return self.last_server_to_client_message

    def apply_cmds(self):
        cur_time = pg.time.get_ticks()
        applied_at_least_one_command = False
        while self.queue and self.queue[0].receive_time + self.latency > cur_time:
            applied_at_least_one_command = True
            ready_cmd = self.queue.popleft()
            if ready_cmd.cmd.right or ready_cmd.cmd.left:
                print("hi")
            self.enemy.move(ready_cmd.cmd)
        if not applied_at_least_one_command:
            self.enemy.move(no_input)

    def change_predict_type(self, new_type: int):
        self.predict_type = PredictType(new_type)
        self.predict_msg.msg = predict_messages[new_type]


class PredictMsg(pg.sprite.Sprite):
    """ to keep track of the score.
    """

    def __init__(self, screenrect: pg.Rect):
        pg.sprite.Sprite.__init__(self, self.containers)
        self.font = pg.font.Font(None, 40)
        self.color = pg.Color("white")
        self.msg = "N/A"
        self.old_msg = self.msg
        self.image = self.font.render(self.msg, 0, self.color)
        self.update()
        self.rect = self.image.get_rect(topleft=screenrect.topleft)

    def update(self):
        """ We only update the score in update() when it has changed.
        """
        if self.msg != self.old_msg:
            self.image = self.font.render(self.msg, 0, self.color)
            self.old_msg = self.msg
