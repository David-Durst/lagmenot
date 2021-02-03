from lagmenot.player import Player, PlayerWithoutSprite, InputCmd, no_input, merge_input_cmds
import pygame as pg
from dataclasses import dataclass
from typing import Deque
from collections import deque
from enum import Enum


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
    client_to_server_queue: Deque[InputCmd]
    server_to_client_queue: Deque[PlayerWithoutSprite]
    # in milliseconds
    latency = 50
    cmd_rate = 50
    next_client_to_server_send_tick: int
    next_client_to_server_recv_tick: int
    next_server_to_client_send_tick: int
    next_server_to_client_recv_tick: int
    next_client_to_server_packet_to_send: InputCmd
    last_server_to_client_packet_received: PlayerWithoutSprite
    predict_type: PredictType
    predict_msg: 'PredictMsg'

    def __init__(self, enemy: Player, predict_msg: 'PredictMsg'):
        self.enemy = enemy
        self.client_to_server_queue = deque()
        self.server_to_client_queue = deque()
        self.next_client_to_server_send_tick = self.latency
        self.next_client_to_server_recv_tick = self.latency*10000
        self.next_server_to_client_send_tick = self.latency*10000
        self.next_server_to_client_recv_tick = self.latency*10000
        self.next_client_to_server_packet_to_send = no_input
        self.last_server_to_client_packet_received = None
        self.predict_type = PredictType(0)
        self.predict_msg = predict_msg
        self.predict_msg.msg = predict_messages[0]

    def send_client_to_server(self, cmd: InputCmd):
        """ Send input commands from the client to the server
        """
        cur_time = pg.time.get_ticks()
        self.next_client_to_server_packet_to_send = merge_input_cmds(self.next_client_to_server_packet_to_send, cmd)
        if self.next_client_to_server_send_tick < cur_time:
            self.next_client_to_server_send_tick = cur_time + self.cmd_rate
            self.next_client_to_server_recv_tick = min(self.next_server_to_client_recv_tick, cur_time + self.latency)
            self.client_to_server_queue.append(self.next_client_to_server_packet_to_send)
            self.next_client_to_server_packet_to_send = no_input

    def receive_client_to_server(self):
        """ Read the next packet to the server off the wire if it's "traveled" long enough time
        """
        cur_time = pg.time.get_ticks()
        if self.next_client_to_server_recv_tick < cur_time:
            self.next_server_to_client_recv_tick = self.next_server_to_client_send_tick + self.latency
            packet = self.client_to_server_queue.popleft()
            self.enemy.move(packet)

    def send_server_to_client(self):
        """ Send state commands from the server to the client
        """
        cur_time = pg.time.get_ticks()
        if self.next_server_to_client_send_tick < cur_time:
            self.next_server_to_client_send_tick = cur_time + self.cmd_rate
            self.next_server_to_client_recv_tick = min(self.next_server_to_client_recv_tick, cur_time + self.latency)
            self.server_to_client_queue.append(self.enemy.clone_no_sprite())

    def receive_server_to_client(self):
        """ Read the next packet to the client off the wire if it's "traveled" long enough time
        """
        cur_time = pg.time.get_ticks()
        if self.next_server_to_client_recv_tick < cur_time:
            self.next_server_to_client_recv_tick = self.next_server_to_client_send_tick + self.latency
            self.last_server_to_client_packet_received = self.server_to_client_queue.popleft()
            return self.last_server_to_client_packet_received
        else:
            if self.predict_type == PredictType.NO_COMMAND:
                return self.last_server_to_client_packet_received
            elif self.predict_type == PredictType.REPLAY_COMMAND:
                self.last_server_to_client_packet_received.move(no_input)
                return self.last_server_to_client_packet_received

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
