import arcade
import random
import math
from dataclasses import dataclass
from typing import Callable, Optional, Dict, List, Tuple


SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
SCREEN_TITLE = "super sandbox pong"

LEFT_PANEL_WIDTH = 260
BOTTOM_PANEL_HEIGHT = 120
MARGIN = 20

FIELD_LEFT = LEFT_PANEL_WIDTH + MARGIN
FIELD_RIGHT = SCREEN_WIDTH - MARGIN
FIELD_BOTTOM = BOTTOM_PANEL_HEIGHT + MARGIN
FIELD_TOP = SCREEN_HEIGHT - MARGIN

FIELD_CENTER_X = (FIELD_LEFT + FIELD_RIGHT) / 2
FIELD_CENTER_Y = (FIELD_BOTTOM + FIELD_TOP) / 2

GRAVITY = -1400.0
BALL_RADIUS = 12
BALL_BASE_SPEED = 650.0
BALL_MAX_SPEED = 1600.0
BALL_BOUNCE_DAMP = 0.98

VERT_PADDLE_LENGTH = 170
VERT_PADDLE_THICKNESS = 18
VERT_PADDLE_TILT_DEG = 30

HOR_PADDLE_WIDTH = 100
HOR_PADDLE_THICKNESS = 18

LEFT_VERTICAL_UP = arcade.key.W
LEFT_VERTICAL_DOWN = arcade.key.S
LEFT_HORIZONTAL_LEFT = arcade.key.A
LEFT_HORIZONTAL_RIGHT = arcade.key.D

RIGHT_VERTICAL_UP = arcade.key.UP
RIGHT_VERTICAL_DOWN = arcade.key.DOWN
RIGHT_HORIZONTAL_LEFT = arcade.key.LEFT
RIGHT_HORIZONTAL_RIGHT = arcade.key.RIGHT

EVENT_INTERVAL = 10.0
EVENT_WARNING_TIME = 1.0
FIRE_STUN_DURATION = 3.0


def clamp(v: float, a: float, b: float) -> float:
    return max(a, min(b, v))

def vec_length(x: float, y: float) -> float:
    return math.sqrt(x * x + y * y)

def normalize(x: float, y: float) -> Tuple[float, float]:
    l = vec_length(x, y)
    if l == 0:
        return 0.0, 0.0
    return x / l, y / l

def reflect(vx: float, vy: float, nx: float, ny: float) -> Tuple[float, float]:
    dot = vx * nx + vy * ny
    rx = vx - 2.0 * dot * nx
    ry = vy - 2.0 * dot * ny
    return rx, ry


@dataclass(frozen=True)
class Material:
    name: str
    color: tuple
    bounce: float
    power: float
    friction: float
    burnable: bool

MATERIALS: Dict[str, Material] = {
    "дерево": Material("дерево", arcade.color.BROWN, bounce=0.95, power=1.00, friction=0.10, burnable=True),
    "сталь": Material("сталь", arcade.color.LIGHT_GRAY, bounce=1.05, power=1.05, friction=0.02, burnable=False),
    "резина": Material("резина", arcade.color.DARK_GREEN, bounce=1.20, power=1.10, friction=0.05, burnable=False),
}


class UIButton:
    def __init__(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        text: str,
        on_click: Callable[[], None],
        font_size: int = 20,
        fill_color: tuple = arcade.color.LIGHT_GRAY,
        outline_color: tuple = arcade.color.WHITE,
        text_color: tuple = arcade.color.BLACK,
    ):
        self.x, self.y = x, y
        self.w, self.h = w, h
        self.text = text
        self.on_click = on_click

        self.font_size = font_size
        self.fill_color = fill_color
        self.outline_color = outline_color
        self.text_color = text_color

        self.enabled = True
        self.hover = False

    def hit_test(self, px: float, py: float) -> bool:
        return (self.x - self.w / 2 <= px <= self.x + self.w / 2 and
                self.y - self.h / 2 <= py <= self.y + self.h / 2)

    def on_mouse_motion(self, x: float, y: float):
        self.hover = self.hit_test(x, y)

    def on_mouse_press(self, x: float, y: float, button: int):
        if not self.enabled:
            return
        if button == arcade.MOUSE_BUTTON_LEFT and self.hit_test(x, y):
            self.on_click()

    def draw(self):
        fill = arcade.color.WHITE if self.hover and self.enabled else self.fill_color
        outline = arcade.color.YELLOW if self.hover and self.enabled else self.outline_color

        left = self.x - self.w / 2
        right = self.x + self.w / 2
        bottom = self.y - self.h / 2
        top = self.y + self.h / 2
        arcade.draw_lrbt_rectangle_filled(left, right, bottom, top, fill)
        arcade.draw_lrbt_rectangle_outline(left, right, bottom, top, outline, 2)

        arcade.draw_text(
            self.text,
            self.x, self.y,
            self.text_color,
            font_size=self.font_size,
            anchor_x="center",
            anchor_y="center",
        )

class UIToggleButton(UIButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.selected = False

    def draw(self):
        if self.selected:
            fill = arcade.color.SKY_BLUE
            outline = arcade.color.WHITE
        else:
            fill = arcade.color.WHITE if self.hover and self.enabled else self.fill_color
            outline = arcade.color.YELLOW if self.hover and self.enabled else self.outline_color

        left = self.x - self.w / 2
        right = self.x + self.w / 2
        bottom = self.y - self.h / 2
        top = self.y + self.h / 2
        arcade.draw_lrbt_rectangle_filled(left, right, bottom, top, fill)
        arcade.draw_lrbt_rectangle_outline(left, right, bottom, top, outline, 2)

        arcade.draw_text(
            self.text,
            self.x, self.y,
            arcade.color.BLACK,
            font_size=self.font_size,
            anchor_x="center",
            anchor_y="center",
        )


class Ball:
    def __init__(self):
        self.x = FIELD_CENTER_X
        self.y = FIELD_CENTER_Y
        self.vx = 0.0
        self.vy = 0.0
        self.radius = BALL_RADIUS

    def reset(self):
        self.x = FIELD_CENTER_X
        self.y = FIELD_CENTER_Y

        dir_x = random.choice([-1, 1])
        angle = random.uniform(-0.35, 0.35)
        self.vx = dir_x * BALL_BASE_SPEED * math.cos(angle)
        self.vy = BALL_BASE_SPEED * math.sin(angle) * 0.3

    def update(self, dt: float):
        self.vy += GRAVITY * dt

        self.x += self.vx * dt
        self.y += self.vy * dt

        sp = vec_length(self.vx, self.vy)
        if sp > BALL_MAX_SPEED:
            nx, ny = normalize(self.vx, self.vy)
            self.vx = nx * BALL_MAX_SPEED
            self.vy = ny * BALL_MAX_SPEED

    def draw(self):
        arcade.draw_circle_filled(self.x, self.y, self.radius, arcade.color.WHITE)
        arcade.draw_circle_outline(self.x, self.y, self.radius, arcade.color.BLACK, 2)

class VerticalPaddle:
    def __init__(self, side: str):
        self.side = side  # "left" or "right"
        self.length = VERT_PADDLE_LENGTH
        self.thickness = VERT_PADDLE_THICKNESS
        self.tilt_deg = VERT_PADDLE_TILT_DEG

        if side == "left":
            self.x = FIELD_LEFT + 60
        else:
            self.x = FIELD_RIGHT - 60

        self.y = FIELD_CENTER_Y
        self.speed = 900.0

        self.material_name = "дерево"
        self.enabled = True
        self.burned_out = False

    @property
    def material(self) -> Material:
        return MATERIALS[self.material_name]

    def set_material(self, name: str):
        self.material_name = name
        self.burned_out = False

    def get_segment(self) -> Tuple[float, float, float, float]:
        theta = math.radians(self.tilt_deg)
        if self.side == "right":
            theta = math.radians(180 - self.tilt_deg)

        dx = math.cos(theta) * (self.length / 2)
        dy = math.sin(theta) * (self.length / 2)

        x1 = self.x - dx
        y1 = self.y - dy
        x2 = self.x + dx
        y2 = self.y + dy
        return x1, y1, x2, y2

    def update(self, dt: float, move_dir: float):
        if not self.enabled or self.burned_out:
            return

        self.y += move_dir * self.speed * dt
        pad = self.length / 2
        self.y = clamp(self.y, FIELD_BOTTOM + pad, FIELD_TOP - pad)

    def draw(self):
        if self.burned_out:
            return

        x1, y1, x2, y2 = self.get_segment()

        arcade.draw_line(x1, y1, x2, y2, self.material.color, self.thickness)
        arcade.draw_line(x1, y1, x2, y2, arcade.color.BLACK, 2)

class HorizontalPaddle:
    def __init__(self, side: str):
        self.side = side
        self.width = HOR_PADDLE_WIDTH
        self.thickness = HOR_PADDLE_THICKNESS

        self.y = FIELD_BOTTOM + 220
        self.speed = 900.0

        if side == "left":
            self.min_x = FIELD_LEFT + self.width / 2
            self.max_x = FIELD_CENTER_X - 40
            self.x = self.min_x + 50
        else:
            self.min_x = FIELD_CENTER_X + 40
            self.max_x = FIELD_RIGHT - self.width / 2
            self.x = self.max_x - 50

        self.material_name = "дерево"
        self.enabled = True
        self.burned_out = False

    @property
    def material(self) -> Material:
        return MATERIALS[self.material_name]

    def set_material(self, name: str):
        self.material_name = name
        self.burned_out = False

    def update(self, dt: float, move_dir: float):
        if not self.enabled or self.burned_out:
            return

        self.x += move_dir * self.speed * dt
        self.x = clamp(self.x, self.min_x, self.max_x)

    def draw(self):
        if self.burned_out:
            return

        left = self.x - self.width / 2
        right = self.x + self.width / 2
        bottom = self.y - self.thickness / 2
        top = self.y + self.thickness / 2
        arcade.draw_lrbt_rectangle_filled(left, right, bottom, top, self.material.color)
        arcade.draw_lrbt_rectangle_outline(left, right, bottom, top, arcade.color.BLACK, 2)


class Player:
    def __init__(self, side: str, is_cpu: bool = False):
        self.side = side
        self.is_cpu = is_cpu

        self.vert = VerticalPaddle(side)
        self.horz = HorizontalPaddle(side)

        self.score = 0

        self.move_vert = 0.0
        self.move_horz = 0.0

        self.stun_timer = 0.0

    def set_material(self, name: str):
        self.vert.set_material(name)
        self.horz.set_material(name)

    def get_material(self) -> str:
        return self.vert.material_name

    def set_stun(self, duration: float):
        self.stun_timer = max(self.stun_timer, duration)

    def update(self, dt: float, ball: Ball):
        if self.stun_timer > 0:
            self.stun_timer -= dt
            self.vert.enabled = False
            self.horz.enabled = False
            self.move_vert = 0.0
            self.move_horz = 0.0
        else:
            self.vert.enabled = True
            self.horz.enabled = True

        if self.is_cpu:
            self._cpu_control(dt, ball)

        self.vert.update(dt, self.move_vert)
        self.horz.update(dt, self.move_horz)

    def _cpu_control(self, dt: float, ball: Ball):
        if ball.y > self.vert.y + 10:
            self.move_vert = 1.0
        elif ball.y < self.vert.y - 10:
            self.move_vert = -1.0
        else:
            self.move_vert = 0.0

        target_x = clamp(ball.x, self.horz.min_x, self.horz.max_x)
        if target_x > self.horz.x + 8:
            self.move_horz = 1.0
        elif target_x < self.horz.x - 8:
            self.move_horz = -1.0
        else:
            self.move_horz = 0.0


class GameEvent:
    # базовый класс событий
    name: str = "event"

    def apply(self, game: "GameView"):
        pass

class FireEvent(GameEvent):
    name = "пожар на карте"

    def apply(self, game: "GameView"):
        for p in [game.player_left, game.player_right]:
            if p.get_material() == "дерево":
                p.vert.burned_out = True
                p.horz.burned_out = True
                p.set_stun(FIRE_STUN_DURATION)

class EventManager:
    def __init__(self):
        self.timer = 0.0
        self.next_event_in = EVENT_INTERVAL
        self.warning_active = False
        self.warning_timer = 0.0
        self.current_warning_text = ""

        self.events: List[GameEvent] = [
            FireEvent(),
        ]

    def update(self, dt: float, game: "GameView"):
        self.timer += dt
        self.next_event_in -= dt

        if not self.warning_active and self.next_event_in <= EVENT_WARNING_TIME:
            self.warning_active = True
            self.warning_timer = EVENT_WARNING_TIME
            ev = random.choice(self.events)
            game.pending_event = ev
            self.current_warning_text = f"событие через 1 секунду: {ev.name}"

        if self.warning_active:
            self.warning_timer -= dt
            if self.warning_timer <= 0:
                self.warning_active = False

        if self.next_event_in <= 0:
            self.next_event_in = EVENT_INTERVAL
            if game.pending_event is None:
                ev = random.choice(self.events)
                game.pending_event = ev

            game.pending_event.apply(game)
            game.last_event_text = f"событие: {game.pending_event.name}"
            game.last_event_timer = 2.0
            game.pending_event = None


def closest_point_on_segment(px: float, py: float, x1: float, y1: float, x2: float, y2: float) -> Tuple[float, float, float]:
    vx = x2 - x1
    vy = y2 - y1
    denom = vx * vx + vy * vy
    if denom == 0:
        return x1, y1, 0.0
    t = ((px - x1) * vx + (py - y1) * vy) / denom
    t = clamp(t, 0.0, 1.0)
    cx = x1 + t * vx
    cy = y1 + t * vy
    return cx, cy, t

def collide_ball_with_vertical_paddle(ball: Ball, paddle: VerticalPaddle) -> bool:
    if paddle.burned_out:
        return False

    x1, y1, x2, y2 = paddle.get_segment()
    cx, cy, _t = closest_point_on_segment(ball.x, ball.y, x1, y1, x2, y2)

    dx = ball.x - cx
    dy = ball.y - cy
    dist = vec_length(dx, dy)
    capsule_r = paddle.thickness / 2

    if dist <= ball.radius + capsule_r:
        nx, ny = normalize(dx, dy)
        if nx == 0 and ny == 0:
            nx, ny = 1.0, 0.0

        penetration = (ball.radius + capsule_r) - dist
        ball.x += nx * (penetration + 0.5)
        ball.y += ny * (penetration + 0.5)

        rvx, rvy = reflect(ball.vx, ball.vy, nx, ny)

        mat = paddle.material
        rvx *= mat.bounce
        rvy *= mat.bounce

        rvx *= mat.power
        rvy *= mat.power

        tx, ty = -ny, nx
        tang = rvx * tx + rvy * ty
        rvx -= tang * mat.friction * tx
        rvy -= tang * mat.friction * ty

        ball.vx = rvx * BALL_BOUNCE_DAMP
        ball.vy = rvy * BALL_BOUNCE_DAMP
        return True

    return False

def collide_ball_with_horizontal_paddle(ball: Ball, paddle: HorizontalPaddle) -> bool:
    if paddle.burned_out:
        return False

    half_w = paddle.width / 2
    half_h = paddle.thickness / 2

    if (paddle.x - half_w - ball.radius <= ball.x <= paddle.x + half_w + ball.radius and
        paddle.y - half_h - ball.radius <= ball.y <= paddle.y + half_h + ball.radius):

        if ball.y >= paddle.y:
            nx, ny = 0.0, 1.0
            ball.y = paddle.y + half_h + ball.radius + 0.5
        else:
            nx, ny = 0.0, -1.0
            ball.y = paddle.y - half_h - ball.radius - 0.5

        rvx, rvy = reflect(ball.vx, ball.vy, nx, ny)

        mat = paddle.material

        rvy = abs(rvy) + 520.0
        rvy *= mat.bounce * mat.power

        rvx *= mat.bounce

        rvx *= (1.0 - mat.friction)

        ball.vx = rvx * BALL_BOUNCE_DAMP
        ball.vy = rvy * BALL_BOUNCE_DAMP
        return True

    return False


class MainMenuView(arcade.View):
    def __init__(self):
        super().__init__()
        self.buttons: List[UIButton] = []
        self.mode = "cpu"  # cpu или pvp

        self.btn_cpu: Optional[UIToggleButton] = None
        self.btn_pvp: Optional[UIToggleButton] = None

    def on_show_view(self):
        arcade.set_background_color(arcade.color.ASH_GREY)
        self._build_ui()

    def _build_ui(self):
        self.buttons.clear()

        self.btn_cpu = UIToggleButton(
            x=SCREEN_WIDTH / 2,
            y=SCREEN_HEIGHT / 2 + 60,
            w=420,
            h=90,
            text="режим: против cpu",
            on_click=self._select_cpu,
            font_size=28
        )
        self.btn_pvp = UIToggleButton(
            x=SCREEN_WIDTH / 2,
            y=SCREEN_HEIGHT / 2 - 60,
            w=420,
            h=90,
            text="режим: 2 игрока",
            on_click=self._select_pvp,
            font_size=28
        )
        self._sync_mode_buttons()

        self.buttons.append(self.btn_cpu)
        self.buttons.append(self.btn_pvp)

        self.buttons.append(UIButton(
            x=SCREEN_WIDTH / 2,
            y=SCREEN_HEIGHT / 2 - 180,
            w=320,
            h=80,
            text="начать",
            on_click=self._start_game,
            font_size=28
        ))

        self.buttons.append(UIButton(
            x=SCREEN_WIDTH / 2,
            y=SCREEN_HEIGHT / 2 - 280,
            w=320,
            h=80,
            text="выход",
            on_click=self.window.close,
            font_size=28
        ))

    def _sync_mode_buttons(self):
        if self.btn_cpu and self.btn_pvp:
            self.btn_cpu.selected = (self.mode == "cpu")
            self.btn_pvp.selected = (self.mode == "pvp")

    def _select_cpu(self):
        self.mode = "cpu"
        self._sync_mode_buttons()

    def _select_pvp(self):
        self.mode = "pvp"
        self._sync_mode_buttons()

    def _start_game(self):
        view = GameView(mode=self.mode)
        self.window.show_view(view)

    def on_draw(self):
        self.clear()

        arcade.draw_text(
            "пинг понг sandbox",
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT - 140,
            arcade.color.BLACK,
            font_size=54,
            anchor_x="center"
        )

        arcade.draw_text(
            "управление:\n"
            "левый: w/s (верт), a/d (гор)\n"
            "правый: стрелки вверх/вниз (верт), влево/вправо (гор)\n"
            "материалы выбираются снизу для каждого игрока",
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT - 260,
            arcade.color.BLACK,
            font_size=18,
            anchor_x="center",
            multiline=True,
            width=700,
            align="center"
        )

        for b in self.buttons:
            b.draw()

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        for b in self.buttons:
            b.on_mouse_motion(x, y)

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        for b in self.buttons:
            b.on_mouse_press(x, y, button)

class GameView(arcade.View):
    def __init__(self, mode: str):
        super().__init__()
        self.mode = mode

        self.player_left = Player("left", is_cpu=False)
        self.player_right = Player("right", is_cpu=(mode == "cpu"))

        self.ball = Ball()
        self.event_manager = EventManager()

        self.left_panel_buttons: List[UIButton] = []
        self.material_buttons: List[UIButton] = []

        self.selected_player_for_material = "left"

        self.state = "countdown"
        self.countdown = 3.0
        self.countdown_text = "3"

        self.pending_event: Optional[GameEvent] = None
        self.last_event_text = ""
        self.last_event_timer = 0.0

        self.debug = False

    def on_show_view(self):
        arcade.set_background_color(arcade.color.ASH_GREY)
        self._reset_round(first=True)
        self._build_ui()

    def _build_ui(self):
        self.left_panel_buttons.clear()
        self.material_buttons.clear()

        self.left_panel_buttons.append(UIButton(
            x=LEFT_PANEL_WIDTH / 2,
            y=110,
            w=210,
            h=70,
            text="в меню",
            on_click=self._back_to_menu,
            font_size=22
        ))

        self.left_panel_buttons.append(UIButton(
            x=LEFT_PANEL_WIDTH / 2,
            y=220,
            w=210,
            h=70,
            text="материал: левый",
            on_click=self._toggle_material_target,
            font_size=18
        ))

        self.left_panel_buttons.append(UIButton(
            x=LEFT_PANEL_WIDTH / 2,
            y=320,
            w=210,
            h=70,
            text="пауза",
            on_click=self._toggle_pause,
            font_size=22
        ))

        names = list(MATERIALS.keys())
        start_x = FIELD_LEFT + 160
        y = BOTTOM_PANEL_HEIGHT / 2

        for i, n in enumerate(names):
            bx = start_x + i * 220
            self.material_buttons.append(UIButton(
                x=bx,
                y=y,
                w=200,
                h=70,
                text=n,
                on_click=lambda name=n: self._apply_material(name),
                font_size=22
            ))

    def _back_to_menu(self):
        self.window.show_view(MainMenuView())

    def _toggle_pause(self):
        if self.state == "paused":
            self.state = "playing"
        elif self.state == "playing":
            self.state = "paused"

    def _toggle_material_target(self):
        self.selected_player_for_material = "right" if self.selected_player_for_material == "left" else "left"
        for b in self.left_panel_buttons:
            if b.text.startswith("материал:"):
                b.text = "материал: левый" if self.selected_player_for_material == "left" else "материал: правый"

    def _apply_material(self, name: str):
        if self.selected_player_for_material == "left":
            self.player_left.set_material(name)
        else:
            self.player_right.set_material(name)

    def _reset_round(self, first: bool = False):
        self.ball.reset()
        self.ball.vx = 0.0
        self.ball.vy = 0.0

        self.state = "countdown"
        self.countdown = 3.0
        self.countdown_text = "3"

        self.player_left.vert.burned_out = False
        self.player_left.horz.burned_out = False
        self.player_right.vert.burned_out = False
        self.player_right.horz.burned_out = False

        self.player_left.stun_timer = 0.0
        self.player_right.stun_timer = 0.0

        if first:
            self.player_left.score = 0
            self.player_right.score = 0

    def _start_ball_after_countdown(self):
        self.ball.reset()

    def on_draw(self):
        self.clear()

        self._draw_layout()

        self._draw_field()

        self.player_left.vert.draw()
        self.player_left.horz.draw()
        self.player_right.vert.draw()
        self.player_right.horz.draw()
        self.ball.draw()

        for b in self.left_panel_buttons:
            b.draw()
        for b in self.material_buttons:
            b.draw()

        self._draw_hud()

    def _draw_layout(self):
        left = 0
        right = LEFT_PANEL_WIDTH
        bottom = 0
        top = SCREEN_HEIGHT
        arcade.draw_lrbt_rectangle_filled(left, right, bottom, top, (127, 127, 127))
        arcade.draw_lrbt_rectangle_outline(left, right, bottom, top, arcade.color.BLACK, 2)

        left = FIELD_LEFT
        right = FIELD_RIGHT
        bottom = 0
        top = BOTTOM_PANEL_HEIGHT
        arcade.draw_lrbt_rectangle_filled(left, right, bottom, top, (127, 127, 127))
        arcade.draw_lrbt_rectangle_outline(left, right, bottom, top, arcade.color.BLACK, 2)

        left = FIELD_LEFT
        right = FIELD_RIGHT
        bottom = FIELD_BOTTOM
        top = FIELD_TOP
        arcade.draw_lrbt_rectangle_outline(left, right, bottom, top, arcade.color.BLACK, 3)

        arcade.draw_line(
            FIELD_CENTER_X,
            FIELD_BOTTOM,
            FIELD_CENTER_X,
            FIELD_TOP,
            arcade.color.BLACK,
            2
        )

    def _draw_field(self):
        pass

    def _draw_hud(self):
        arcade.draw_text("меню", LEFT_PANEL_WIDTH / 2, SCREEN_HEIGHT - 60,
                         arcade.color.BLACK, 28, anchor_x="center")
        arcade.draw_text("материалы", FIELD_LEFT + 20, BOTTOM_PANEL_HEIGHT - 38,
                         arcade.color.BLACK, 24, anchor_x="left")

        arcade.draw_text(f"{self.player_left.score}", FIELD_CENTER_X - 80, FIELD_TOP - 60,
                         arcade.color.BLACK, 46, anchor_x="center")
        arcade.draw_text(f"{self.player_right.score}", FIELD_CENTER_X + 80, FIELD_TOP - 60,
                         arcade.color.BLACK, 46, anchor_x="center")

        mode_text = "против cpu" if self.mode == "cpu" else "2 игрока"
        arcade.draw_text(f"режим: {mode_text}", LEFT_PANEL_WIDTH / 2, SCREEN_HEIGHT - 120,
                         arcade.color.BLACK, 16, anchor_x="center")

        arcade.draw_text(f"левый: {self.player_left.get_material()}", LEFT_PANEL_WIDTH / 2, SCREEN_HEIGHT - 160,
                         arcade.color.BLACK, 16, anchor_x="center")
        arcade.draw_text(f"правый: {self.player_right.get_material()}", LEFT_PANEL_WIDTH / 2, SCREEN_HEIGHT - 185,
                         arcade.color.BLACK, 16, anchor_x="center")

        target = "левый" if self.selected_player_for_material == "left" else "правый"
        arcade.draw_text(f"выбор материала -> {target}", FIELD_LEFT + 20, 18,
                         arcade.color.BLACK, 16, anchor_x="left")

        if self.player_left.stun_timer > 0:
            arcade.draw_text(f"левый оглушен: {self.player_left.stun_timer:.1f}",
                             FIELD_LEFT + 20, FIELD_TOP - 40, arcade.color.ORANGE_RED, 16)
        if self.player_right.stun_timer > 0:
            arcade.draw_text(f"правый оглушен: {self.player_right.stun_timer:.1f}",
                             FIELD_RIGHT - 20, FIELD_TOP - 40, arcade.color.ORANGE_RED, 16, anchor_x="right")

        if self.event_manager.warning_active:
            arcade.draw_text(self.event_manager.current_warning_text, FIELD_CENTER_X, FIELD_TOP - 110,
                             arcade.color.RED, 22, anchor_x="center")  # ИСПРАВЛЕНО: было YELLOW, стало RED для лучшей видимости

        if self.last_event_timer > 0:
            arcade.draw_text(self.last_event_text, FIELD_CENTER_X, FIELD_TOP - 140,
                             arcade.color.BLACK, 18, anchor_x="center")  # ИСПРАВЛЕНО: было WHITE, стало BLACK

        if self.state == "countdown":
            arcade.draw_text(self.countdown_text, FIELD_CENTER_X, FIELD_CENTER_Y,
                             arcade.color.BLACK, 80, anchor_x="center", anchor_y="center")  # ИСПРАВЛЕНО: было WHITE, стало BLACK

        if self.state == "paused":
            arcade.draw_text("пауза", FIELD_CENTER_X, FIELD_CENTER_Y,
                             arcade.color.BLACK, 60, anchor_x="center", anchor_y="center")  # ИСПРАВЛЕНО: было WHITE, стало BLACK

        if self.debug:
            arcade.draw_text(f"ball: ({self.ball.x:.1f},{self.ball.y:.1f}) v=({self.ball.vx:.1f},{self.ball.vy:.1f})",
                             FIELD_LEFT + 20, FIELD_TOP - 80, arcade.color.BLACK, 14)  # ИСПРАВЛЕНО: было WHITE, стало BLACK

    def on_update(self, dt: float):
        dt = min(dt, 1 / 30)

        if self.last_event_timer > 0:
            self.last_event_timer -= dt

        if self.state == "paused":
            return

        if self.state == "countdown":
            self.countdown -= dt
            if self.countdown > 2:
                self.countdown_text = "3"
            elif self.countdown > 1:
                self.countdown_text = "2"
            elif self.countdown > 0:
                self.countdown_text = "1"
            else:
                self.state = "playing"
                self._start_ball_after_countdown()

            self.player_left.update(dt, self.ball)
            self.player_right.update(dt, self.ball)
            return

        self.event_manager.update(dt, self)

        self.player_left.update(dt, self.ball)
        self.player_right.update(dt, self.ball)

        self.ball.update(dt)

        if self.ball.y - self.ball.radius <= FIELD_BOTTOM:
            self.ball.y = FIELD_BOTTOM + self.ball.radius + 0.5
            self.ball.vy = abs(self.ball.vy) * 0.85
        elif self.ball.y + self.ball.radius >= FIELD_TOP:
            self.ball.y = FIELD_TOP - self.ball.radius - 0.5
            self.ball.vy = -abs(self.ball.vy) * 0.85

        hit = False
        hit |= collide_ball_with_vertical_paddle(self.ball, self.player_left.vert)
        hit |= collide_ball_with_vertical_paddle(self.ball, self.player_right.vert)
        hit |= collide_ball_with_horizontal_paddle(self.ball, self.player_left.horz)
        hit |= collide_ball_with_horizontal_paddle(self.ball, self.player_right.horz)

        if hit:
            self.ball.vx *= 1.01
            self.ball.vy *= 1.01

        if self.ball.x + self.ball.radius < FIELD_LEFT:
            self.player_right.score += 1
            self._reset_round()
        elif self.ball.x - self.ball.radius > FIELD_RIGHT:
            self.player_left.score += 1
            self._reset_round()


    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.ESCAPE:
            self._back_to_menu()

        if symbol == arcade.key.TAB:
            self._toggle_material_target()

        if symbol == arcade.key.P:
            self._toggle_pause()

        if symbol == arcade.key.F3:
            self.debug = not self.debug

        if symbol == LEFT_VERTICAL_UP:
            self.player_left.move_vert = 1.0
        elif symbol == LEFT_VERTICAL_DOWN:
            self.player_left.move_vert = -1.0
        elif symbol == LEFT_HORIZONTAL_LEFT:
            self.player_left.move_horz = -1.0
        elif symbol == LEFT_HORIZONTAL_RIGHT:
            self.player_left.move_horz = 1.0

        if not self.player_right.is_cpu:
            if symbol == RIGHT_VERTICAL_UP:
                self.player_right.move_vert = 1.0
            elif symbol == RIGHT_VERTICAL_DOWN:
                self.player_right.move_vert = -1.0
            elif symbol == RIGHT_HORIZONTAL_LEFT:
                self.player_right.move_horz = -1.0
            elif symbol == RIGHT_HORIZONTAL_RIGHT:
                self.player_right.move_horz = 1.0

    def on_key_release(self, symbol: int, modifiers: int):
        if symbol in (LEFT_VERTICAL_UP, LEFT_VERTICAL_DOWN):
            self.player_left.move_vert = 0.0
        if symbol in (LEFT_HORIZONTAL_LEFT, LEFT_HORIZONTAL_RIGHT):
            self.player_left.move_horz = 0.0

        if not self.player_right.is_cpu:
            if symbol in (RIGHT_VERTICAL_UP, RIGHT_VERTICAL_DOWN):
                self.player_right.move_vert = 0.0
            if symbol in (RIGHT_HORIZONTAL_LEFT, RIGHT_HORIZONTAL_RIGHT):
                self.player_right.move_horz = 0.0

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        for b in self.left_panel_buttons:
            b.on_mouse_motion(x, y)
        for b in self.material_buttons:
            b.on_mouse_motion(x, y)

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        if modifiers == arcade.key.MOD_CTRL and button == arcade.MOUSE_BUTTON_LEFT:
            print(f"x: {x} y: {y}")

        for b in self.left_panel_buttons:
            b.on_mouse_press(x, y, button)
        for b in self.material_buttons:
            b.on_mouse_press(x, y, button)

def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, resizable=False)
    window.show_view(MainMenuView())
    arcade.run()

if __name__ == "__main__":
    main()