import sys
import math
import pygame
from ball import Ball
from utils import handle_ball_collisions
from dice import Dice

## This is all a pretty standard pygame setup. Initalizing the window and a game clock.

pygame.init()

WINDOW_WIDTH, WINDOW_HEIGHT = 1029,720 ##70mm IMAX aspect ratio : )

screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT),pygame.SCALED,vsync=1)
pygame.display.set_caption("hello there")

clock = pygame.time.Clock()
FPS = 60

font = pygame.font.SysFont(None, 24)
help_text = font.render("click to spawn ball. click and drag ball to throw ball", True, "WHITE")

##GAME VARIABLES / CONSTS
WALL_THICKNESS = 10
BACKGROUND_COLOR = "BLACK"
gravity = 0.6
active_selection = False
mouse_trajectory = []

balls = [] ##starts empty, click an empty spot to spawn a ball
dice = Dice(900,25)


def draw_walls():
	left = pygame.draw.line(screen,"GREEN",(0,0),(0, WINDOW_HEIGHT), WALL_THICKNESS)
	right = pygame.draw.line(screen,"GREEN",(WINDOW_WIDTH,0),(WINDOW_WIDTH, WINDOW_HEIGHT), WALL_THICKNESS)
	top = pygame.draw.line(screen,"GREEN",(0,0),(WINDOW_WIDTH, 0), WALL_THICKNESS)
	bottom = pygame.draw.line(screen,"GREEN",(0,WINDOW_HEIGHT),(WINDOW_WIDTH, WINDOW_HEIGHT), WALL_THICKNESS)
	wall_list = [left,right,top,bottom]
	return wall_list

##MAIN GAME LOOP (runs 4ever)
running = True
while running:

##EVENT HANDLING
	for event in pygame.event.get():
		if event.type == pygame.QUIT: ##basically if the user closes the window, stop running da game
			running = False

		if event.type == pygame.MOUSEBUTTONDOWN: ##check for mouse clicks
			for ball in balls:
				if ball.check_select(event.pos): #pass the position of the mouse over to the function
					active_selection = True
			if not active_selection: ##clicked an empty spot, spawn a fresh random ball there
				dice.roll()

				ball_gravity = dice.get_gravity()
				balls.append(Ball(x_pos=event.pos[0], y_pos=event.pos[1], id=len(balls), gravity=ball_gravity))
		if event.type == pygame.MOUSEBUTTONUP:
			active_selection = False
			for ball in balls:
				ball.check_select((-1000, -1000)) ##value that's outside of the playable area

	mouse_position = pygame.mouse.get_pos() ## store mouse position
	mouse_trajectory.append(mouse_position) ##populating an array with the mouse's position this frame
	if len(mouse_trajectory) > 20: ##if our mouse_trajectory array is logner than 20 store positions, pop the oldest position. We don't need it.
		mouse_trajectory.pop(0)

##UPDATE POSITIONS
	for ball in balls:
		ball.apply_gravity_and_velocity(WINDOW_HEIGHT, WINDOW_WIDTH, WALL_THICKNESS, mouse_trajectory)
		ball.update_position(mouse_position)

	handle_ball_collisions(balls) ##this makes da balls bounce off eachother

##RENDER ALL STUFF
	screen.fill(BACKGROUND_COLOR)
	draw_walls()
	for ball in balls:
		ball.draw(screen)
	screen.blit(help_text, (WALL_THICKNESS + 5, WALL_THICKNESS + 5)) ##little instructions in the top left corner
	dice.draw(screen)
	pygame.display.flip()
	clock.tick(FPS)

pygame.quit()
sys.exit()