import os
import pygame
import random
from fire_effect import FireEffect
from explosion_effect import ExplosionEffect
from utils import calc_mouse_vector
from constants import ROOM_TEMP, BALLS_DIR

sprite_paths = [
    os.path.join(BALLS_DIR, f)
    for f in os.listdir(BALLS_DIR)
    if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
]


def make_circular_image(image_path, radius):
    size = radius * 2
    raw_image = pygame.image.load(image_path).convert_alpha()
    scaled_image = pygame.transform.scale(raw_image, (size, size))

    # Create a circular mask
    mask = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(mask, (255, 255, 255, 255), (radius, radius), radius)

    # Apply the circular mask to the scaled image
    circular_surface = pygame.Surface((size, size), pygame.SRCALPHA)
    circular_surface.blit(scaled_image, (0, 0))
    circular_surface.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    return circular_surface


bounce_stop = 0.3  ##this variable is used to check for really tiny bounces and stop them if below the threshold
max_burn_level = (
    100.0  # This variable is maximum burn level before the ball is destroyed
)

# I wanted to add some sort of liquid or something that could extinguish
#     the balls, but I'm not experienced in liquid simulations
# If someone after me could, that might be a cool idea! (or some other extinguish method)
# Setting fire_effect.active to false maintains the burn amount of this ball
#        so it works if the ball is extinguished in some way and then ignited again

# ^ I'm neither experienced, but I added temperature, which will decrease the heat if the 
# ball is not burning yet. You can make the liquid (or whatever else) just decrease the
# temperature. A ball is currently burning above 400°C and also not loosing heat at that temp.


class Ball:
    def __init__(self, x_pos, y_pos, id, gravity, y_speed=0, x_speed=0):
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.radius = random.randint(
            15, 60
        )  ##every ball gets random attributes when its spawned
        self.image = make_circular_image(random.choice(sprite_paths), self.radius)
        self.density = random.uniform(0.5, 2)
        self.mass = int(
            20 + self.radius * 4 * self.density
        )  # 50 - 500, but based on size and random density to feel more natural
        self.retention = random.uniform(0.7, 0.95)
        self.friction = random.uniform(0.05, 0.3)
        self.gravity = gravity
        self.y_speed = y_speed
        self.x_speed = x_speed
        self.id = id
        self.selected = False
        self.fire_effect = FireEffect(self.x_pos, self.y_pos, self.radius)
        self.temperature = ROOM_TEMP  # Temperature is in °C
        self.ignition_temp = 100.0  # Temperature required for a ball to catch on fire
        self.flame_temp = 400.0  # Temperature kept while flame is burning
        self.burn_level: float = 0.0
        self.active = True  # When this is set to false, the ball is removed from the simulation in main.py

    def draw(self, screen):
        # Glow on the objects based on temp
        heat_ratio = min(
            1.0,
            max(0.0, self.temperature - ROOM_TEMP) / (self.ignition_temp - ROOM_TEMP),
        )

        # Make the image to coal
        burn_ratio = min(1.0, self.burn_level / max_burn_level)
        char_factor = 1.0 - burn_ratio

        # Combine the glow with coal effect
        red_color = int(255 * char_factor)
        green_blue_color = int(255 * (1.0 - heat_ratio * 0.5) * char_factor)

        texture = self.image.copy()
        texture.fill(
            (red_color, green_blue_color, green_blue_color, 255),
            special_flags=pygame.BLEND_RGBA_MULT,
        )

        # Fill the texture
        rect = texture.get_rect(center=(int(self.x_pos), int(self.y_pos)))
        screen.blit(texture, rect)
        # Draw the fire effect
        self.fire_effect.draw(screen)

    def get_center(self):
        return (self.x_pos, self.y_pos)

    def update_position(self, mouse_position):
        self.fire_effect.update_pos(self.x_pos, self.y_pos)
        self.fire_effect.update()
        self.update_temp()

        if not self.selected:
            self.y_pos += self.y_speed
            self.x_pos += self.x_speed
        else:
            self.x_pos = mouse_position[0]
            self.y_pos = mouse_position[1]

    def apply_gravity_and_velocity(
        self, WINDOW_HEIGHT, WALL_THICKNESS, mouse_trajectory
    ):
        if (
            not self.selected
        ):  ## apply normal gravity and bounce rules as long as the ball is not selected
            if self.y_pos < self.floor(
                WINDOW_HEIGHT, WALL_THICKNESS
            ):  ## if the ball's y position is less than the bottom of the screen pretty much
                self.y_speed += self.gravity

            if (
                self.y_speed == 0 and self.x_speed != 0
            ):  ## ball is rolling along the ground, slow it down
                if self.x_speed > 0:
                    self.x_speed -= self.friction
                else:
                    self.x_speed += self.friction
                if abs(self.x_speed) < self.friction:
                    self.x_speed = 0

        else:  ## if the ball is selected, reset its x and y speed
            self.x_speed, self.y_speed = calc_mouse_vector(mouse_trajectory)

    def increase_burn(self):
        if self.fire_effect.active:
            self.burn_level = self.burn_level + 0.1
        if self.burn_level >= max_burn_level:
            self.active = False

    def floor(self, WINDOW_HEIGHT, WALL_THICKNESS):
        return WINDOW_HEIGHT - self.radius - (WALL_THICKNESS / 2)

    def bounds(self, WINDOW_WIDTH, WINDOW_HEIGHT, WALL_THICKNESS):
        if self.selected:
            return

        floor_y = self.floor(WINDOW_HEIGHT, WALL_THICKNESS)
        left_x = self.radius + WALL_THICKNESS / 2
        right_x = WINDOW_WIDTH - self.radius - WALL_THICKNESS / 2

        if self.y_pos > floor_y:
            self.y_pos = floor_y

            rebound = (
                self.y_speed * self.retention - self.gravity
            )  ## minus one frame of gravity, else the floor snap-up feeds balls energy and they bounce forever
            if rebound > bounce_stop:
                self.y_speed = -rebound
            else:
                self.y_speed = 0

        if self.x_pos < left_x:
            self.x_pos = left_x

            if self.x_speed < 0:
                self.x_speed *= -1 * self.retention

                if abs(self.x_speed) < bounce_stop:
                    self.x_speed = 0

        elif self.x_pos > right_x:
            self.x_pos = right_x

            if self.x_speed > 0:
                self.x_speed *= -1 * self.retention

                if abs(self.x_speed) < bounce_stop:
                    self.x_speed = 0

    def check_select(self, pos):
        self.selected = False
        dx = pos[0] - self.x_pos
        dy = pos[1] - self.y_pos
        if dx**2 + dy**2 <= self.radius**2:
            self.selected = True
        return self.selected

    # I made this because the other one both checks if it's being selected
    #        and selects it, but I just wanted to check if it was within the click
    def check_if_selected(self, pos):
        dx = pos[0] - self.x_pos
        dy = pos[1] - self.y_pos
        if dx**2 + dy**2 <= self.radius**2:
            return True
        return False

    # Apply additional forces to the balls (for explosion)
    def apply_forces(self, force_x, force_y):
        self.x_speed += force_x
        self.y_speed += force_y

    def update_temp(self):
        # Keep burning balls at high temp
        if self.fire_effect.active:
            self.temperature = self.flame_temp
        else:
            # Cool down if the temp is above room temp
            if self.temperature > ROOM_TEMP:
                self.temperature -= 0.15
                self.temperature = max(ROOM_TEMP, self.temperature)

            if self.temperature >= self.ignition_temp:
                self.fire_effect.active = True
