from lagmenot.player import Player, InputState
import pygame as pg
from dataclasses import dataclass
from typing import Deque
from collections import deque


@dataclass(frozen=True)
class InputPacket:
    receive_time: int
    cmd: InputState


@dataclass
class RemoteRect:
    topleft_x: int
    topleft_y: int

    def get_as_topleft(self):
        return self.topleft_x, self.topleft_y


class Server:
    enemy: pg.rect
    queue: Deque[InputPacket]
    # in milliseconds
    latency = 50

    def __int__(self, enemy: Player):
        self.enemy = enemy.deepcopy()
        self.queue = deque()

    def receive_input(self, cmd):
        self.queue.append(InputPacket(cmd, pg.time.get_ticks()))

    def apply_cmds(self):
        cur_time = pg.time.get_ticks()
        while self.queue[0].receive_time + self.latency > cur_time:
            ready_cmd = self.queue.popleft()


