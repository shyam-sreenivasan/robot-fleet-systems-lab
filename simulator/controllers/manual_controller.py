import pygame

from simulator.controllers.controller import Controller


class ManualController(Controller):

    def __init__(self, robot):
        self.robot = robot

    def step(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_UP]:
            self.robot.move_forward()

        if keys[pygame.K_DOWN]:
            self.robot.move_backward()

        if keys[pygame.K_LEFT]:
            self.robot.turn_left()

        if keys[pygame.K_RIGHT]:
            self.robot.turn_right()