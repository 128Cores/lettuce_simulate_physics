# physics_simulation

A little pygame merge-sandbox with bouncy balls. Click anywhere empty to spawn a ball with random size, color, mass, bounciness, and friction. Balls will merge with balls of the same image to create bigger balls, and a higher level. 38 is the highest level. Balls bounce off the walls and off each other (mass-based elastic collisions, so heavy balls shove light ones around). Balls are gravitationally attracted to each other by the mass. The bigger the ball, the bigger the pull. Balls will turn into ashes after burning for long enough
Balls can also be set on fire, which can transfer to other balls based on their temperature (°C) and kinetic energy. Additionally balls can explode, which also transfers heat. (Both are based on mass & distance) Press W to throw a wide bucket splash with a splash sound and no cooldown. Each droplet cools the first ball it hits by 15 degrees C. Clicking a ball also cools it. Cooling stops burning without repairing existing burn damage.

Reach level 38 by merging matching balls before the timer expires. Round 1 gives you 120 seconds. Winning starts a fresh round after 10 seconds; each round has a shorter timer, approaching a 30-second minimum with no final round. Losing automatically restarts the run from round 1 after 10 seconds. Press R to restart immediately. Each win awards 1,000 points plus 10 per second remaining. Your best score is saved locally in high_score.json. The objective and timer use bold outlined text above the simulation, without a background panel.

## Controls

- **Left click empty space:** spawn a random ball
- **Right click a ball:** set the ball on fire
- **Left click a ball:** cool it down; hold and drag to move it, then release to throw it
- **Hold Shift and drag around a ball:** lasso it to cause an explosion
- **Hold G:** attract balls toward the mouse while energy lasts
- **Press W:** splash cooling water (no cooldown)
- **Press R:** restart the run from round 1
- **Press H:** show or hide key binding hints
- **Press T:** toggle color-changing ball trails (on by default)
- **Press F:** switch between downward gravity and attraction between balls
- **Press M:** toggle background music
- **Press + or -:** increase or decrease balls spawned per click

## Setup

**Python 3.13** with **pygame 2.6.1**.

```bash
python3 -m venv venv
source venv/bin/activate   # on Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```
## Layout

- `main.py` — pygame setup, event handling, and the main game loop
- `ball.py` — the `Ball` class: gravity, wall bounces, floor friction, mouse clicking for putting out fires
- `ash.py` — the `Ash` class: gravity, wall collisions, and fades away
- `utils.py` — ball-to-ball and ash-to-ash collision handling
- `particle.py` — reusable particle class for an effect controller to use
- `fire_effect.py` — fire effect that is used when a ball is on fire
- `explosion_effect.py` — explosion effect that is used when you lasso around a ball
- `constants.py` — constants that are used around the project
