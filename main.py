import sys
import math
import pygame
from ball import Ball
from utils import *
from dice import Dice

## This is all a pretty standard pygame setup. Initalizing the window and a game clock.

pygame.init()

WINDOW_WIDTH, WINDOW_HEIGHT = 1029,720 ##70mm IMAX aspect ratio : )

screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT),pygame.SCALED,vsync=1)
pygame.display.set_caption("FireBall Simulation")

clock = pygame.time.Clock()
FPS = 60

font = pygame.font.SysFont(None, 24)
help_text = font.render("click to spawn ball. click and drag ball to throw ball. hold shift while dragging to lasso", True, "WHITE")
help_text2 = font.render("right click a ball to ignite it", True, "WHITE")

##GAME VARIABLES / CONSTS
WALL_THICKNESS = 10
BACKGROUND_COLOR = "blue4"
gravity = 0.6
active_selection = False
mouse_trajectory = []

balls = [] ##starts empty, click an empty spot to spawn a ball
dice = Dice(900,25)


def draw_walls():
	left = pygame.draw.line(screen,"darkgreen",(0,0),(0, WINDOW_HEIGHT), WALL_THICKNESS)
	right = pygame.draw.line(screen,"darkgreen",(WINDOW_WIDTH,0),(WINDOW_WIDTH, WINDOW_HEIGHT), WALL_THICKNESS)
	top = pygame.draw.line(screen,"darkgreen",(0,0),(WINDOW_WIDTH, 0), WALL_THICKNESS)
	bottom = pygame.draw.line(screen,"darkgreen",(0,WINDOW_HEIGHT),(WINDOW_WIDTH, WINDOW_HEIGHT), WALL_THICKNESS)
	wall_list = [left,right,top,bottom]
	return wall_list


lasso_active = False
lasso_points = []

lasso_fade_start = None
LASSO_FADE_TIME = 1000 # ms

##MAIN GAME LOOP (runs 4ever)
running = True
while running:

##EVENT HANDLING
	for event in pygame.event.get():
		if event.type == pygame.QUIT: ##basically if the user closes the window, stop running da game
			running = False
		
		# Let user start drawing lasso
		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
			keys = pygame.key.get_pressed()

			if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
				lasso_active = True
				lasso_points = [event.pos]

		if event.type == pygame.MOUSEMOTION and lasso_active:
			lasso_points.append(event.pos)

		if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
			if lasso_active:
				lasso_active = False
				lasso_fade_start = pygame.time.get_ticks()

				# Check which balls are in lasso area
				if len(lasso_points) >= 3:
					for ball in balls:
						if point_in_polygon(ball.get_center(), lasso_points):
							print("Ball explosion")


		if event.type == pygame.MOUSEBUTTONDOWN and not lasso_active and event.button == 1: ##check for left mouse clicks
		
			for ball in balls:
				if ball.check_select(event.pos): #pass the position of the mouse over to the function
					active_selection = True

			if not active_selection: ##clicked an empty spot, spawn a fresh random ball there
				dice.roll()

				ball_gravity = dice.get_gravity()
				balls.append(Ball(x_pos=event.pos[0], y_pos=event.pos[1], id=len(balls), gravity=ball_gravity))
		if event.type == pygame.MOUSEBUTTONDOWN and not lasso_active and event.button == 3: # Check for right mouse clicks
			for ball in balls:
				if ball.check_if_selected(event.pos): # If ball clicked 
					ball.fire_effect.active = True
				

		if event.type == pygame.MOUSEBUTTONUP:
			active_selection = False
			for ball in balls:
				ball.check_select((-1000, -1000)) ##value that's outside of the playable area

	mouse_position = pygame.mouse.get_pos() ## store mouse position
	mouse_trajectory.append(mouse_position) ##populating an array with the mouse's position this frame
	if len(mouse_trajectory) > 20: ##if our mouse_trajectory array is logner than 20 store positions, pop the oldest position. We don't need it.
		mouse_trajectory.pop(0)

##UPDATE POSITIONS
	# Make a copy of the ball list
	for ball in balls.copy():
		# If a ball is inactive
		if not ball.active:
			# Remove it from the original list (this will stop it from being rendered)
			# The copy list is necessary because if you looped through the original list,
			# 	I think it would break because the index you're on is no longer a thing
			balls.remove(ball)

	for ball in balls:
		ball.apply_gravity_and_velocity(WINDOW_HEIGHT, WALL_THICKNESS, mouse_trajectory)
		ball.update_position(mouse_position)
		ball.increase_burn()

	handle_ball_collisions(balls) ##this makes da balls bounce off eachother

	for ball in balls:
		ball.bounds(WINDOW_WIDTH, WINDOW_HEIGHT, WALL_THICKNESS)

##RENDER ALL STUFF
	screen.fill(BACKGROUND_COLOR)
	draw_walls()
	for ball in balls:
		ball.draw(screen)
	screen.blit(help_text, (WALL_THICKNESS + 5, WALL_THICKNESS + 5)) ##little instructions in the top left corner
	screen.blit(help_text2, (WALL_THICKNESS + 5, WALL_THICKNESS + 25))
	dice.draw(screen)

	if len(lasso_points) >= 2:
		alpha = 255

		if not lasso_active and lasso_fade_start is not None:
			elapsed = pygame.time.get_ticks() - lasso_fade_start

			alpha = max(0, 255 * (1 - elapsed / LASSO_FADE_TIME))

			if elapsed >= LASSO_FADE_TIME:
				lasso_points = []
				lasso_fade_start = None
		if lasso_points:
			lasso_surface = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
			
			pygame.draw.lines(lasso_surface, (255, 0, 0, int(alpha)), False, lasso_points, 5)

			screen.blit(lasso_surface, (0, 0))

	pygame.display.flip()
	clock.tick(FPS)

pygame.quit()
sys.exit()