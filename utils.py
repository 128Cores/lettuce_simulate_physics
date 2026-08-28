import math
import pygame
from constants import BASE_CONDUCT_MULT, IMPACT_HEAT_MULT


def calc_mouse_vector(mouse_trajectory):
    x_speed = 0
    y_speed = 0
    if len(mouse_trajectory) > 19:
        x_speed = (mouse_trajectory[-1][0] - mouse_trajectory[0][0]) / len(
            mouse_trajectory
        )
        y_speed = (mouse_trajectory[-1][1] - mouse_trajectory[0][1]) / len(
            mouse_trajectory
        )
    return x_speed, y_speed


def handle_ball_collisions(balls):
    for i in range(len(balls)):
        for j in range(i + 1, len(balls)):  ##check every pair of balls exactly once
            ball1 = balls[i]
            ball2 = balls[j]
            x_dist = ball2.x_pos - ball1.x_pos
            y_dist = ball2.y_pos - ball1.y_pos
            distance = math.sqrt(x_dist**2 + y_dist**2)
            if 0 < distance < ball1.radius + ball2.radius:  ##the balls are overlapping
                normal_x = x_dist / distance  ##direction pointing from ball1 to ball2
                normal_y = y_dist / distance
                overlap = (ball1.radius + ball2.radius) - distance

                ##push the balls apart so they aren't inside eachother. a held ball shouldn't get shoved off the mouse tho
                if ball1.selected:
                    ball2.x_pos += normal_x * overlap
                    ball2.y_pos += normal_y * overlap
                elif ball2.selected:
                    ball1.x_pos -= normal_x * overlap
                    ball1.y_pos -= normal_y * overlap
                else:
                    ball1.x_pos -= normal_x * overlap / 2
                    ball1.y_pos -= normal_y * overlap / 2
                    ball2.x_pos += normal_x * overlap / 2
                    ball2.y_pos += normal_y * overlap / 2

                ##elastic collision, heavier balls shove lighter balls around more
                rel_speed = (ball1.x_speed - ball2.x_speed) * normal_x + (
                    ball1.y_speed - ball2.y_speed
                ) * normal_y
                if (
                    rel_speed > 0
                ):  ##only bounce if the balls are actually moving towards eachother
                    impulse = 2 * rel_speed / (ball1.mass + ball2.mass)
                    if not ball1.selected:
                        ball1.x_speed -= impulse * ball2.mass * normal_x
                        ball1.y_speed -= impulse * ball2.mass * normal_y
                    if not ball2.selected:
                        ball2.x_speed += impulse * ball1.mass * normal_x
                        ball2.y_speed += impulse * ball1.mass * normal_y

                # Check if impacted ball is on fire
                #     if so, they will set each other on fire
                #    This currently will immediately engulf all balls in flames if they are near each other
                # If you feel like making it spread cooler then please go ahead
                # (I'm burning out) - sure I did that with temperature :)

                temp_diff = ball1.temperature - ball2.temperature

                avg_density = (ball1.density + ball2.density) / 2
                avg_radius = (ball1.radius + ball2.radius) / 2
                conductivity = (
                    avg_density * avg_radius * BASE_CONDUCT_MULT
                )  # Value how fast heat gets transfered

                impact_heat = (
                    max(0.0, rel_speed) * IMPACT_HEAT_MULT
                )  # Kinetic impacts should generate heat

                # Transfer the heat based on the temp, conductivity, impact heat and ball mass
                if temp_diff > 0:  # Ball 1 is hotter
                    transfered_heat = (temp_diff * conductivity + impact_heat) / (
                        ball2.mass / 100
                    )
                    ball2.temperature += transfered_heat

                if temp_diff < 0:  # Ball 2 is hotter
                    transfered_heat = (abs(temp_diff) * conductivity + impact_heat) / (
                        ball1.mass / 100
                    )
                    ball1.temperature += transfered_heat


def point_in_polygon(point, polygon):
    x, y = point

    inside = False

    j = len(polygon) - 1

    for i in range(len(polygon)):
        xi, yi = polygon[i]
        xj, yj = polygon[j]

        if (yi > y) != (yj > y):
            x_intersection = (xj - xi) * (y - yi) / (yj - yi) + xi
            if x < x_intersection:
                inside = not inside

        j = i

    return inside


# Useful if you want to add an animation from a single file of multiple sprites.
# Loads individual sprites from images with slicing
def load_spritesheet(filepath, rows, cols):
    sheet = pygame.image.load(filepath).convert_alpha()

    # Get the sheet & sprite sizes
    sheet_width, sheet_height = sheet.get_size()
    frame_width = sheet_width / cols
    frame_height = sheet_height / rows

    frames = []

    for row in range(rows):
        for col in range(cols):
            # Get the rectangles of each sprite from the sheet
            rectangle = pygame.Rect(
                frame_width * col, frame_height * row, frame_width, frame_height
            )
            frame = sheet.subsurface(rectangle)

            frames.append(frame)

    return frames
