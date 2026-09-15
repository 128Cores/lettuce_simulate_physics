import sys
import math
import pygame
import random
from ball import Ball, ashes
from ash import Ash
from utils import *
from dice import Dice
from explosion_effect import ExplosionEffect
from constants import *

## This is all a pretty standard pygame setup. Initalizing the window and a game clock.

pygame.init()
pygame.mixer.init()

## Init sounds
hitmarkerSound = pygame.mixer.Sound(f'assets/sounds/hitmarker.mp3')
damageSound = pygame.mixer.Sound(f'assets/sounds/minecraft-damage.mp3')
deathSound = pygame.mixer.Sound(f'assets/sounds/minecraft-death.mp3')
explosionSound = pygame.mixer.Sound(f'assets/sounds/minecraft-explosion.mp3')

backgroundMusic = pygame.mixer.music.load(f'assets/sounds/fortnite-corail.mp3')
pygame.mixer.music.play(-1)

screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SCALED, vsync=1)
pygame.display.set_caption("FireBall Simulation")

clock = pygame.time.Clock()

font = pygame.font.SysFont(None, 24)
help_text = font.render(
    "Click to spawn ball.", True, "WHITE"
)
help_text2 = font.render("Right click a ball to ignite it.", True, "WHITE")
help_text3 = font.render(
    "Hold shift while dragging mouse to lasso. Lasso around ball to make boom boom.",
    True,
    "WHITE",
)
help_text3 = font.render(
    "Press M to mute background music.",
    True,
    "WHITE",
)
help_text4 = font.render(
    "Hold G + left click and drag to attract balls to your mouse.",
    True,
    "WHITE",
)
big_font = pygame.font.SysFont(None, 32, bold=True)

##GAME VARIABLES
gravity = 0.6
mouse_trajectory = []

balls = []  ##starts empty, click an empty spot to spawn a ball
explosions = []
dice = Dice(900, 25)
current_level = 4
won = False
def draw_max_balls():
    pygame.draw.rect(screen, (20, 20, 20), (880, 15, 135, 105), border_radius=12)
    pygame.draw.rect(screen, (100, 100, 100), (880, 15, 135, 105), 2, border_radius=12)

    if not balls: return
    global current_level

    max_ball = max(balls, key=lambda ball: ball.level)
    current_level = max(4, max_ball.level)
    image = pygame.transform.scale(max_ball.image, (80, 80))
    screen.blit(image, (900, 25))

    text = big_font.render(str(max_ball.level), True, "WHITE")
    screen.blit(text, (990, 50))

def draw_attraction_bar():
    bar_x, bar_y, bar_width, bar_height = 880, 130, 135, 20

    pygame.draw.rect(screen, (20, 20, 20), (bar_x, bar_y, bar_width, bar_height), border_radius=6)

    fill_width = int(bar_width * (attraction_energy / 75))
    if fill_width > 0:
        pygame.draw.rect(screen, (40, 120, 255), (bar_x, bar_y, fill_width, bar_height), border_radius=6)

    pygame.draw.rect(screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height), 2, border_radius=6)

# Calculating explosion forces
def explosion_knockback(explosion_x, explosion_y, balls, blast_radius):
    for ball in balls:
        if not ball.active:
            continue

        # Direction vector
        dx = ball.x_pos - explosion_x
        dy = ball.y_pos - explosion_y

        # Distance
        d = math.sqrt(dx**2 + dy**2)

        # Unit vector for the direction
        if 0 < d <= blast_radius:
            dir_x = dx / d
            dir_y = dy / d

            # Calculate the applied force based on mass, distance, blast radius, base force & direction
            force = (BASE_FORCE / (ball.mass)) * (1 - d / blast_radius)
            force_x = dir_x * force
            force_y = dir_y * force

            # Apply forces and fire effect upon explosion
            ball.apply_forces(force_x, force_y)

            # Heat falloff over the distance
            falloff = 1 - (d / blast_radius)

            transfered_heat = (BASE_EXPLOSION_HEAT / (ball.mass / 100.0)) * falloff
            ball.temperature += transfered_heat

lasso_active = False
lasso_points = []
lasso_fade_start = None

##MAIN GAME LOOP (runs 4ever)
running = True
mute = False
countdown_counter, countdown_text = 120, '120'.rjust(3)
pygame.time.set_timer(pygame.USEREVENT, 1000)

attraction_energy = 75

def activate_attraction():
    if pygame.mouse.get_pressed()[0] and pygame.key.get_pressed()[pygame.K_g] and attraction_energy > 0:
        return True
    return False

while running:
    ##EVENT HANDLING
    for event in pygame.event.get():
        if (
            event.type == pygame.QUIT
        ):  ##basically if the user closes the window, stop running da game
            running = False

        if event.type == pygame.USEREVENT:
            if not won:
                countdown_counter -= 1
                countdown_text = str(countdown_counter).rjust(3) if countdown_counter > 0 else 'You Lose!!'

            # Use the same one second timer for attraction energy
            if activate_attraction():
                attraction_energy -= 25
            elif attraction_energy < 75:
                attraction_energy += 10
            
        if event.type == pygame.KEYDOWN and event.key == pygame.K_m and mute == False:
            pygame.mixer.music.set_volume(0.0)
            mute = True
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_m and mute == True:
            pygame.mixer.music.set_volume(1.0)
            mute = False

        # Let user start drawing lasso
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            keys = pygame.key.get_pressed()

            if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                lasso_active = True
                lasso_points = [event.pos]

        if event.type == pygame.MOUSEMOTION and lasso_active:
            lasso_points.append(event.pos)

        mouse_pos = pygame.mouse.get_pos()
        if activate_attraction():
            for ball in balls:
                tmp_ball_x = mouse_pos[0] - ball.x_pos
                tmp_ball_y = mouse_pos[1] - ball.y_pos
                tmp_ball_x *= 0.1
                tmp_ball_y *= 0.1

                ball.x_speed = 0 
                ball.y_speed = 0 
                ball.angular_speed = 0
                ball.apply_forces(tmp_ball_x, tmp_ball_y);


        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if lasso_active:
                lasso_active = False
                lasso_fade_start = pygame.time.get_ticks()

                # Check which balls are in lasso area
                if len(lasso_points) >= 3:
                    for ball in balls:
                        if point_in_polygon(ball.get_center(), lasso_points):
                            # Cause explosion if the ball gets lassoed
                            explosion = ExplosionEffect(
                                ball.x_pos, ball.y_pos, ball.radius, explosionSound
                            )
                            explosions.append(explosion)

                            explosion_knockback(
                                ball.x_pos, ball.y_pos, balls, explosion.blast_radius
                            )

                            ball.active = False

        if (event.type == pygame.MOUSEBUTTONDOWN and not lasso_active and event.button == 1):  ##check for left mouse clicks
            active_selection = False

            for ball in balls:
                if ball.check_if_selected(event.pos):  # pass the position of the mouse over to the function
                    ball.update_temp()
                    active_selection = True

            if not active_selection:  ##clicked an empty spot, spawn a fresh random ball there
                dice.roll()

                ball_gravity = dice.get_gravity()
                balls.append(Ball(
                        x_pos=event.pos[0],
                        y_pos=event.pos[1],
                        id=len(balls),
                        gravity=ball_gravity,
                        max_level=current_level,
                        damageSound=damageSound,
                        deathSound=deathSound
                    ))
        if (event.type == pygame.MOUSEBUTTONDOWN and not lasso_active and event.button == 3):  # Check for right mouse clicks
            for ball in balls:
                if ball.check_if_selected(event.pos):  # If ball clicked
                    ball.temperature = 400
                    ball.update_temp()

    mouse_position = pygame.mouse.get_pos()  ## store mouse position
    mouse_trajectory.append(
        mouse_position
    )  ##populating an array with the mouse's position this frame
    if (
        len(mouse_trajectory) > 20
    ):  ##if our mouse_trajectory array is logner than 20 store positions, pop the oldest position. We don't need it.
        mouse_trajectory.pop(0)

    ##UPDATE POSITIONS
    # Make a copy of the ball list
    for ball in balls.copy():
        # If a ball is inactive
        if not ball.active:
            # Remove it from the original list (this will stop it from being rendered)
            # The copy list is necessary because if you looped through the original list,
            #     I think it would break because the index you're on is no longer a thing
            balls.remove(ball)

    # Add gravity interaction to each ball
    for i, ball_1 in enumerate(balls):
        acceleration_x = 0
        acceleration_y = 0

        for j, ball_2 in enumerate(balls):

            # doesnt have gravity on itself
            if i == j:
                continue

            # gravity formula
            distance_x = (ball_2.x_pos - ball_1.x_pos)
            distance_y = (ball_2.y_pos - ball_1.y_pos)
            squared_distance = distance_x * distance_x + distance_y * distance_y
            force = gravity * ball_2.mass / squared_distance

            # get acceleration on each direction
            acceleration_x += force * distance_x
            acceleration_y += force * distance_y

        # apply half of ball_2's force into ball_1 (to make the game not so easy, sorry!)
        ball_1.apply_forces(acceleration_x / 2, acceleration_y / 2)

    # update each ball after calculations
    for ball in balls:
        ball.update_position()
        ball.increase_burn()

    ashes[:] = [ash for ash in ashes if ash.active]

    for ash in ashes:
        ash.apply_gravity_and_velocity(WINDOW_HEIGHT, WALL_THICKNESS)
        ash.update_position()
        ash.increase_burn()

    handle_ball_collisions(balls, hitMarkerSound=hitmarkerSound)  ##this makes da balls bounce off eachother
    if any(ball.level >= 37 for ball in balls):
        won = True
    handle_ash_collisions(ashes)

    for ball in balls:
        ball.bounds(WINDOW_WIDTH, WINDOW_HEIGHT, WALL_THICKNESS)
    for ash in ashes:
            ash.bounds(WINDOW_WIDTH, WINDOW_HEIGHT, WALL_THICKNESS)

    # Random explosion
    # if (random.randint(1, 1000) > 100)


    # These are kinda weird / unexpected -> turn in to meteorites?
    if random.randint(1, 4000) < 30:
        x = random.randint(WALL_THICKNESS + 10, WINDOW_WIDTH - WALL_THICKNESS - 10)
        y = random.randint(WALL_THICKNESS + 10, WINDOW_HEIGHT - WALL_THICKNESS - 10)

        explosion = ExplosionEffect(x, y, random.randint(30, 50), explosionSound)
        explosions.append(explosion)

        explosion_knockback(x, y, balls, explosion.blast_radius)
        
    # Update active explosions
    for explosion in explosions:
        explosion.update()

    # Filter completed explosions
    explosions = [explosion for explosion in explosions if not explosion.finished]

    ##RENDER ALL STUFF
    bg_img = pygame.image.load(f'assets/background/background.png')
    screen.blit(bg_img, bg_img.get_rect())

    draw_max_balls()
    draw_attraction_bar()
    for ball in balls:
        ball.draw(screen)
    for ash in ashes:
        ash.draw(screen)
    screen.blit(
        help_text, (WALL_THICKNESS + 5, WALL_THICKNESS + 5)
    )  ##little instructions in the top left corner
    screen.blit(help_text2, (WALL_THICKNESS + 5, WALL_THICKNESS + 25))
    screen.blit(help_text3, (WALL_THICKNESS + 5, WALL_THICKNESS + 45))
    screen.blit(help_text4, (WALL_THICKNESS + 5, WALL_THICKNESS + 65))

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

            pygame.draw.lines(
                lasso_surface, (255, 0, 0, int(alpha)), False, lasso_points, 5
            )

            screen.blit(lasso_surface, (0, 0))

    # Render ball explosion
    for explosion in explosions:
        explosion.draw(screen)

    if won:
        win_text = big_font.render("You win!", True, "WHITE")
        screen.blit(win_text, win_text.get_rect(center=(WINDOW_WIDTH // 2, 100)))
    else:
        clock_text = big_font.render(countdown_text, True, "RED")
        screen.blit(clock_text, clock_text.get_rect(center=(WINDOW_WIDTH // 2, 100)))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
