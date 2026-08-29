# physics_simulation

A little pygame merge-sandbox with bouncy balls. Click anywhere empty to spawn a ball with random size, color, mass, bounciness, and friction. Balls will merge with balls of the same image to create bigger balls, and a higher level. 37 is the highest level. Balls bounce off the walls and off each other (mass-based elastic collisions, so heavy balls shove light ones around). Balls will turn into ashes after burning for long enough
Balls can also be set on fire, which can transfer to other balls based on their temperature (°C) and kinetic energy. Additionally balls can explode, which also transfers heat. (Both are based on mass & distance) To put out the fires, click rapidly on the ball before it burns up.

## Controls

- **Left click empty space** — spawn a random ball
- **Right click a ball** — set the ball on fire
- **Left click a ball** — put the fire out
- **Hold shift and drag** — draw lasso
- **Draw lasso around ball** — make explosion

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
