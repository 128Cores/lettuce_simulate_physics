import math
import json
from pathlib import Path
import random
import sys

import pygame

from ball import Ball, ashes
from constants import *
from dice import Dice
from explosion_effect import ExplosionEffect
from utils import *

# todo: DELETE ME!!
"""
1. balls are combining into each other right away (maybe increase level variance)
2. balls are spawning too slowly (spawn multiple balls per frame when ballsPerClick is high)


1. dragging a ball into another ball does not apply the correct force
"""


## This is all a pretty standard pygame setup. Initalizing the window and a game clock.

pygame.init()
pygame.mixer.init()

## Init sounds
hitmarkerSound = pygame.mixer.Sound(f"assets/sounds/hitmarker.mp3")
damageSound = pygame.mixer.Sound(f"assets/sounds/minecraft-damage.mp3")
deathSound = pygame.mixer.Sound(f"assets/sounds/minecraft-death.mp3")
explosionSound = pygame.mixer.Sound(f"assets/sounds/minecraft-explosion.mp3")
water_sound = pygame.mixer.Sound("assets/sounds/water-splash.mp3")
water_sound.set_volume(0.6)

backgroundMusic = pygame.mixer.music.load(f"assets/sounds/fortnite-corail.mp3")
# backgroundMusic = pygame.mixer.music.load(f"assets/sounds/monkey.mp3")
pygame.mixer.music.play(-1)

screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SCALED, vsync=1)
pygame.display.set_caption("FireBall Simulation")

clock = pygame.time.Clock()

keyRepeatDelay = 500
keyRepeatInterval = 80
pygame.key.set_repeat(keyRepeatDelay, keyRepeatInterval)

font = pygame.font.SysFont(None, 24)
show_hints = True
trails_enabled = True
water_drops = []
background_image = pygame.image.load("assets/background/background.png")
hint_lines = [
    "Left click: spawn / grab a ball; release to throw",
    "Right click: ignite a ball",
    "Shift + left drag: lasso balls to explode",
    "Hold G: attract balls (uses blue energy bar)",
    "W: to splash a bucket of cooling water.",
    "R: restart from round 1",
    "T: toggle trails    F: switch gravity    M: mute music",
    "+ / -: balls per click    H: hide / show these hints",
]

numFramesToSpawnBalls = 0
ballsToSpawnPerFrame = 0
exactRemainingBalls = 0
ballsPerClick = 1
ballsPerClickFont = pygame.font.SysFont(None, 28, bold=True)


def updateBallsPerClickHelpText():
    global ballsPerClickHelpText
    ballsPerClickString = f"balls per click: {ballsPerClick}"
    ballsPerClickHelpText = ballsPerClickFont.render(ballsPerClickString, True, "GREEN")


updateBallsPerClickHelpText()
ballsPerClickPlusMinusFont = pygame.font.SysFont(None, 24)
ballsPerClickPlusMinusHelpText = ballsPerClickPlusMinusFont.render(
    "(use + or -)", True, "GREEN"
)

big_font = pygame.font.SysFont(None, 32, bold=True)
objective_font = pygame.font.SysFont(None, 38, bold=True)
timer_font = pygame.font.SysFont(None, 48, bold=True)

##GAME VARIABLES
gravity = 0.6
mouse_trajectory = []

balls = []  ##starts empty, click an empty spot to spawn a ball
explosions = []
dice = Dice(900, 25)
current_level = 4
won = False
lost = False
gravity_enabled = True

HOOP_LEFT = 335
HOOP_RIGHT = 375
HOOP_Y = 450


def draw_max_balls():
    pygame.draw.rect(screen, (20, 20, 20), (880, 15, 135, 105), border_radius=12)
    pygame.draw.rect(screen, (100, 100, 100), (880, 15, 135, 105), 2, border_radius=12)

    if not balls:
        return
    global current_level

    max_ball = max(balls, key=lambda ball: ball.level)
    current_level = max(4, max_ball.level)
    image = pygame.transform.scale(max_ball.image, (80, 80))
    screen.blit(image, (888, 25))

    text = big_font.render(str(max_ball.level), True, "WHITE")
    screen.blit(text, text.get_rect(midright=(1007, 65)))


def draw_attraction_bar():
    bar_x, bar_y, bar_width, bar_height = 880, 130, 135, 20

    pygame.draw.rect(
        screen, (20, 20, 20), (bar_x, bar_y, bar_width, bar_height), border_radius=6
    )

    fill_width = int(bar_width * (attraction_energy / 75))
    if fill_width > 0:
        pygame.draw.rect(
            screen,
            (40, 120, 255),
            (bar_x, bar_y, fill_width, bar_height),
            border_radius=6,
        )

    pygame.draw.rect(
        screen,
        (100, 100, 100),
        (bar_x, bar_y, bar_width, bar_height),
        2,
        border_radius=6,
    )


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
score_path = Path(__file__).with_name("high_score.json")
try:
    high_score = max(0, int(json.loads(score_path.read_text())["high_score"]))
except (OSError, ValueError, KeyError, TypeError):
    high_score = 0
score = 0
round_number = 1
transition_at = None
attraction_energy = 75


def start_round(number):
    global round_number, round_deadline, countdown_counter, won, lost, transition_at
    global current_level, attraction_energy, numFramesToSpawnBalls, exactRemainingBalls
    global ballsToSpawnPerFrame, lasso_active, lasso_fade_start
    round_number = number
    duration = 30 + 90 / (1 + 0.15 * (number - 1))
    round_deadline = pygame.time.get_ticks() + duration * 1000
    countdown_counter = math.ceil(duration)
    won = lost = False
    transition_at = None
    balls.clear()
    ashes.clear()
    explosions.clear()
    water_drops.clear()
    mouse_trajectory.clear()
    lasso_points.clear()
    lasso_active = False
    lasso_fade_start = None
    current_level = 4
    attraction_energy = 75
    numFramesToSpawnBalls = ballsToSpawnPerFrame = exactRemainingBalls = 0
    pygame.time.set_timer(pygame.USEREVENT, 1000)


def save_high_score():
    global high_score
    if score > high_score:
        high_score = score
        try:
            score_path.write_text(json.dumps({"high_score": high_score}))
        except OSError as error:
            print(f"Could not save high score: {error}")


def splash_water(x, y):
    if won or lost:
        return
    water_sound.play()
    # A wide burst with sideways momentum, rather than a continuous stream.
    for _ in range(60):
        water_drops.append([x + random.uniform(-24, 24), y + random.uniform(-12, 12),
                            random.uniform(-6, 6), random.uniform(-4, 5), 0])


def outlined_text(text, text_font, center, color="WHITE", *, top_left=False):
    image = text_font.render(text, True, color)
    outline = text_font.render(text, True, (10, 12, 18))
    rect = image.get_rect(topleft=center) if top_left else image.get_rect(center=center)
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-2, -2), (2, 2), (-2, 2), (2, -2)):
        screen.blit(outline, rect.move(dx, dy))
    screen.blit(image, rect)


start_round(1)


def activate_attraction():
    return bool(
        pygame.key.get_pressed()[pygame.K_g]
        and attraction_energy > 0
    )


def onLeftClick(mouseX, mouseY):

    global ballsToSpawnPerFrame
    global numFramesToSpawnBalls
    global exactRemainingBalls

    for ball in balls:
        if ball.check_if_selected(
            mouseX, mouseY
        ):  # pass the position of the mouse over to the function
            ball.onClick()
            return

    # WARNING: Don't try to understand this part. It doesn't make any sense!!

    # still spawning current batch of balls
    if numFramesToSpawnBalls > 0:
        return

    ballSpawnRatio = 1 / 3

    ballsToSpawn = ballsPerClick
    numFramesToSpawnBalls = int(ballsToSpawn ** (ballSpawnRatio))
    ballsToSpawnPerFrame = int(ballsToSpawn / numFramesToSpawnBalls)

    roundedTotal = numFramesToSpawnBalls * ballsToSpawnPerFrame

    exactRemainingBalls = ballsToSpawn - roundedTotal


def onLeftClickUp():

    # Sorry
    for ball in balls:
        ball.releaseGrab()


def onRightClick(mouseX, mouseY):
    for ball in balls:
        if ball.check_if_selected(mouseX, mouseY):  # If ball clicked
            ball.temperature = 400
            ball.update_temp()


def onPlusKeyPress():
    global ballsPerClick

    # unlimited cap on number of balls. DO NOT CHANGE <<<<< CRITICAL
    ballsPerClick += 1
    updateBallsPerClickHelpText()


def onMinusKeyPress():
    global ballsPerClick
    if ballsPerClick > 1:
        ballsPerClick -= 1
        updateBallsPerClickHelpText()


def createBall(mouseX, mouseY):
    dice.roll()
    ball_gravity = dice.get_gravity()
    balls.append(
        Ball(
            x_pos=mouseX,
            y_pos=mouseY,
            id=len(balls),
            gravity=ball_gravity,
            max_level=current_level,
            damageSound=damageSound,
            deathSound=deathSound,
        )
    )


while running:
    mouseX, mouseY = pygame.mouse.get_pos()
    ##EVENT HANDLING
    for event in pygame.event.get():
        if (
            event.type == pygame.QUIT
        ):  ##basically if the user closes the window, stop running da game
            running = False

        mouseX, mouseY = pygame.mouse.get_pos()

        if event.type == pygame.USEREVENT:
            # Use the same one second timer for attraction energy
            if activate_attraction():
                attraction_energy = max(0, attraction_energy - 25)
            elif attraction_energy < 75:
                attraction_energy = min(75, attraction_energy + 10)

        if event.type == pygame.KEYDOWN and event.key == pygame.K_m and mute == False:
            pygame.mixer.music.set_volume(0.0)
            mute = True
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_m and mute == True:
            pygame.mixer.music.set_volume(1.0)
            mute = False

        if event.type == pygame.KEYDOWN and not getattr(event, "repeat", False):
            if event.key == pygame.K_r:
                score = 0
                start_round(1)
                continue
            if event.key == pygame.K_h:
                show_hints = not show_hints
            elif event.key == pygame.K_t:
                trails_enabled = not trails_enabled
                for ball in balls:
                    ball.trail.clear()
            elif event.key == pygame.K_w:
                splash_water(mouseX, mouseY)

        if won or lost:
            continue

        # Let user start drawing lasso
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            keys = pygame.key.get_pressed()

            if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                lasso_active = True
                lasso_points = [event.pos]

        if event.type == pygame.MOUSEMOTION and lasso_active:
            lasso_points.append(event.pos)

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            onLeftClickUp()

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

        # # PLUS KEY
        if event.type == pygame.KEYDOWN and (
            event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS
        ):
            onPlusKeyPress()

        # # MINUS KEY
        if event.type == pygame.KEYDOWN and event.key == pygame.K_MINUS:
            onMinusKeyPress()

        # # LEFT CLICK
        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and not lasso_active
            and event.button == 1
        ):  ##check for left mouse clicks
            if not pygame.key.get_pressed()[pygame.K_g] and not pygame.key.get_pressed()[pygame.K_w]:
                onLeftClick(event.pos[0], event.pos[1])

        # # RIGHT CLICK
        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and not lasso_active
            and event.button == 3
        ):  # Check for right mouse clicks
            onRightClick(event.pos[0], event.pos[1])

        if event.type == pygame.KEYDOWN and event.key == pygame.K_f:
            gravity_enabled = not gravity_enabled

    now = pygame.time.get_ticks()
    if transition_at is not None and now >= transition_at:
        if won:
            start_round(round_number + 1)
        else:
            score = 0
            start_round(1)
    if not won and not lost:
        countdown_counter = max(0, math.ceil((round_deadline - now) / 1000))
        if now >= round_deadline:
            lost = True
            transition_at = now + 3000
            numFramesToSpawnBalls = 0
            for ball in balls:
                ball.grabbed = False

    if not won and not lost and numFramesToSpawnBalls > 0:
        extra = exactRemainingBalls if numFramesToSpawnBalls == 1 else 0
        for _ in range(ballsToSpawnPerFrame + extra):
            createBall(mouseX, mouseY)
        numFramesToSpawnBalls -= 1

    if not won and not lost and activate_attraction():
        for ball in balls:
            ball.grabbed = False
            ball.x_speed = (mouseX - ball.x_pos) * 0.1
            ball.y_speed = (mouseY - ball.y_pos) * 0.1
            ball.angular_speed = 0

    remaining_drops = []
    for drop in water_drops:
        drop[3] += 0.3
        drop[0] += drop[2]
        drop[1] += drop[3]
        drop[4] += 1
        for ball in balls:
            if ball.active and ball.check_if_selected(drop[0], drop[1]):
                ball.cool(15)
                break
        else:
            if 0 < drop[0] < WINDOW_WIDTH and drop[1] < WINDOW_HEIGHT - WALL_THICKNESS and drop[4] < 120:
                remaining_drops.append(drop)
    water_drops = remaining_drops

    mouse_trajectory.append(
        (mouseX, mouseY)
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
            # if gravity_enabled:
            distance_x = ball_2.x_pos - ball_1.x_pos
            distance_y = ball_2.y_pos - ball_1.y_pos
            squared_distance = distance_x * distance_x + distance_y * distance_y
            force = gravity * ball_2.mass / (squared_distance + 0.001)

            # get acceleration on each direction
            acceleration_x += force * distance_x
            acceleration_y += force * distance_y

        # apply half of ball_2's force into ball_1 (to make the game not so easy, sorry!)
        if gravity_enabled:
            ball_1.apply_forces(acceleration_x / 2, acceleration_y / 2)

    # update each ball after calculations
    for ball in balls:
        old_x, old_y = ball.get_center()

        ball.update_position(mouseX, mouseY)
        ball.increase_burn()

        if ball.shot_frames > 0 and not ball.scored and old_y < HOOP_Y <= ball.y_pos:
            frac = (HOOP_Y - old_y) / (ball.y_pos - old_y)
            crossing = old_x + frac * (ball.x_pos - old_x)

            if HOOP_LEFT <= crossing <= HOOP_RIGHT:
                ball.scored = True
                ball.update_image()

        if not gravity_enabled:
            ball.apply_gravity_and_velocity(WINDOW_HEIGHT, WALL_THICKNESS)

    # keep track of the trails for each ball
    for ball in balls:
        if trails_enabled:
            ball.trail.append((ball.x_pos, ball.y_pos))
        # remove excess trail points
        if len(ball.trail) > MAX_TRAIL:
            ball.trail.pop(0)

    ashes[:] = [ash for ash in ashes if ash.active]

    for ash in ashes:
        ash.apply_gravity_and_velocity(WINDOW_HEIGHT, WALL_THICKNESS)
        ash.update_position()
        ash.increase_burn()

    handle_ball_collisions(
        balls, hitMarkerSound=hitmarkerSound
    )  ##this makes da balls bounce off eachother
    if not won and not lost and any(ball.active and ball.level >= 38 for ball in balls):
        won = True
        transition_at = pygame.time.get_ticks() + 10000
        score += 1000 + countdown_counter * 10
        save_high_score()
        numFramesToSpawnBalls = 0
        for ball in balls:
            ball.grabbed = False
    handle_ash_collisions(ashes)

    for ball in balls:
        ball.bounds(WINDOW_WIDTH, WINDOW_HEIGHT, WALL_THICKNESS)
    for ash in ashes:
        ash.bounds(WINDOW_WIDTH, WINDOW_HEIGHT, WALL_THICKNESS)

    # Random explosion
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
    screen.blit(background_image, background_image.get_rect())

    for ball in balls:
        trail_color = tuple(random.randint(0, 255) for _ in range(3))
        # ignore first position change
        if trails_enabled and len(ball.trail) >= 2:
            # render trail
            for i in range(1, len(ball.trail)):
                min_width = 2
                max_width = 6
                # keep track of the progress of the trail
                progress = i / (len(ball.trail) - 1)
                # calculate width of the current trail point
                width = max(1, int(min_width + progress * (max_width - min_width)))
                # draw trail on screen
                pygame.draw.line(
                    screen, trail_color, ball.trail[i - 1], ball.trail[i], width
                )
        # render ball
        ball.draw(screen)
    for ash in ashes:
        ash.draw(screen)

    for drop in water_drops:
        pygame.draw.line(screen, (90, 185, 230), (drop[0], drop[1] - 5), (drop[0], drop[1]), 2)

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

    # Draw every HUD element after all world effects.
    outlined_text(f"ROUND {round_number}: MERGE MATCHING BALLS TO LEVEL 38", objective_font, (440, 30))
    if won:
        seconds = max(0, math.ceil((transition_at - pygame.time.get_ticks()) / 1000))
        status = f"ROUND WON! Next round in {seconds}s"
        color = (120, 255, 150)
    elif lost:
        seconds = max(0, math.ceil((transition_at - pygame.time.get_ticks()) / 1000))
        status = f"TIME UP! Restarting in {seconds}s (R: restart now)"
        color = (255, 120, 100)
    else:
        status = f"TIME LEFT: {countdown_counter}s"
        color = (255, 120, 100) if countdown_counter <= 20 else (255, 230, 110)
    outlined_text(status, timer_font, (440, 73), color)
    highest = max((ball.level for ball in balls if ball.active), default=0)
    outlined_text(f"Ball: {highest}/38   Score: {score}   Best: {high_score}", font, (440, 110))
    if show_hints:
        for index, line in enumerate(hint_lines):
            outlined_text(line, font, (15, 155 + index * 21), top_left=True)
    else:
        outlined_text("Press [H] to show controls.", font, (15, 155), top_left=True)
    draw_max_balls()
    draw_attraction_bar()
    outlined_text(f"balls per click: {ballsPerClick}", ballsPerClickFont, (20, WINDOW_HEIGHT - 35), "GREEN", top_left=True)
    outlined_text("(use + or -)", ballsPerClickPlusMinusFont, (220, WINDOW_HEIGHT - 33), "GREEN", top_left=True)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
