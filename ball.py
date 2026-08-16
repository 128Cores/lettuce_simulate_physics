import pygame
import random
from utils import calc_mouse_vector

bounce_stop = 0.3 ##this variable is used to check for really tiny bounces and stop them if below the threshold

class Ball:
	def __init__(self, x_pos, y_pos, id, y_speed=0, x_speed=0):
		self.x_pos = x_pos
		self.y_pos = y_pos
		self.radius = random.randint(15, 60) ##every ball gets random attributes when its spawned
		self.color = random.choice(["RED", "YELLOW", "GREEN", "CYAN", "MAGENTA", "ORANGE", "WHITE", "PURPLE"])
		self.mass = random.randint(50, 500)
		self.retention = random.uniform(.7, .95)
		self.friction = random.uniform(.05, .3)
		self.y_speed = y_speed
		self.x_speed = x_speed
		self.id = id
		self.selected = False

	def draw(self, screen): 
		self.circle = pygame.draw.circle(screen, self.color, (self.x_pos,self.y_pos),self.radius)

	def update_position(self, mouse_position):
		if not self.selected:
			self.y_pos += self.y_speed
			self.x_pos += self.x_speed
		else:
			self.x_pos = mouse_position[0]
			self.y_pos = mouse_position[1]

	def apply_gravity_and_velocity(self, WINDOW_HEIGHT, WINDOW_WIDTH, WALL_THICKNESS, gravity, mouse_trajectory):
		if not self.selected: ## apply normal gravity and bounce rules as long as the ball is not selected
			if self.y_pos < WINDOW_HEIGHT - self.radius - (WALL_THICKNESS / 2): ## if the ball's y position is less than the bottom of the screen pretty much
				self.y_speed += gravity
			elif self.y_speed > bounce_stop: ##prevent infinite bounces
				self.y_speed = self.y_speed * -1 * self.retention
			elif abs(self.y_speed) <= bounce_stop: ##prevent infinite bounces
					self.y_speed = 0

			if (self.x_pos < self.radius + (WALL_THICKNESS/2) and self.x_speed < 0) or \
				(self.x_pos > WINDOW_WIDTH - self.radius - (WALL_THICKNESS / 2) and self.x_speed > 0):
					self.x_speed *= -1 * self.retention
					if abs(self.x_speed) < bounce_stop:
						self.x_speed = 0

			if self.y_speed == 0 and self.x_speed != 0: ## ball is rolling along the ground, slow it down
				if self.x_speed > 0:
					self.x_speed -= self.friction
				else:
					self.x_speed += self.friction
				if abs(self.x_speed) < self.friction:
					self.x_speed = 0
		else: ## if the ball is selected, reset its x and y speed
			self.x_speed, self.y_speed = calc_mouse_vector(mouse_trajectory)

	def check_select(self, pos):
		self.selected = False
		if self.circle.collidepoint(pos):
			self.selected = True
		return self.selected