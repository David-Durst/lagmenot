from lagmenot.player import Player, PlayerWithoutSprite, InputState, no_input
import pygame as pg
from dataclasses import dataclass
from typing import Deque
from collections import deque


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


class Server:
    enemy: Player
    queue: Deque[InputPacket]
    # in milliseconds
    latency = 50
    last_server_to_client: int
    last_client_to_server: int

    def __init__(self, enemy: Player):
        self.enemy = enemy
        self.queue = deque()
        self.last_server_to_client = 0
        self.last_client_to_server = 0

    def client_to_server(self, cmd: InputState):
        cur_time = pg.time.get_ticks()
        if self.last_client_to_server + self.latency < cur_time:
            self.last_client_to_server = cur_time
            self.queue.append(InputPacket(cmd, pg.time.get_ticks()))

    def server_to_client(self) -> PlayerWithoutSprite:
        cur_time = pg.time.get_ticks()
        if self.last_server_to_client + self.latency < cur_time:
            self.last_server_to_client = cur_time
            return self.enemy
        else:
            return None

    def apply_cmds(self):
        cur_time = pg.time.get_ticks()
        applied_at_least_one_command = False
        while self.queue and self.queue[0].receive_time + self.latency > cur_time:
            applied_at_least_one_command = True
            ready_cmd = self.queue.popleft()
            self.enemy.move(ready_cmd.cmd)
        if not applied_at_least_one_command:
            self.enemy.move(no_input)


