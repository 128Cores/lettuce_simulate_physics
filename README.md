# physics_simulation

A little pygame sandbox with bouncy balls. Click anywhere empty to spawn a ball with random size, color, mass, bounciness, and friction. Click and drag a ball to pick it up, then release to throw it — the throw velocity comes from your recent mouse movement. Balls bounce off the walls and off each other (mass-based elastic collisions, so heavy balls shove light ones around).

## Controls

- **Click empty space** — spawn a random ball
- **Click + drag a ball** — pick it up
- **Release while moving the mouse** — throw it
- **Hold shift and drag** — draw lasso

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
- `ball.py` — the `Ball` class: gravity, wall bounces, floor friction, mouse selection
- `utils.py` — throw vector calculation and ball-to-ball collision handling