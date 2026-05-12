"""
Catch the Ball — AI-Based Reaction Time Game
=============================================
A modern cognitive-training game that measures reaction speed,
calculates AI-based performance metrics, and logs every session
to a CSV dataset for analysis.

Author  : [Your Name]
Version : 2.0.0
"""

import pygame
import random
import math
import csv
import os
import time

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS & PALETTE
# ─────────────────────────────────────────────────────────────────────────────

WIDTH, HEIGHT = 1100, 700
FPS           = 60
TITLE         = "Catch the Ball — AI Reaction Game"

# Dataset path (relative to this file so it works from any cwd)
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
DATA_DIR    = os.path.join(BASE_DIR, "..", "data")
DATASET_CSV = os.path.join(DATA_DIR, "catch_ball_dataset.csv")
CSV_HEADERS = [
    "session_id", "reaction_time_ms", "score", "hits", "misses",
    "accuracy", "ball_speed", "difficulty_level",
    "performance_label", "heuristic_score",
]

# Colour palette ── all colours referenced by name, never raw tuples mid-code
P = {
    "bg":         (245, 247, 252),
    "bg2":        (235, 238, 248),
    "card":       (255, 255, 255),
    "shadow":     (210, 215, 235),
    "border":     (220, 224, 240),
    "text":       ( 40,  44,  70),
    "muted":      (140, 148, 180),
    "accent":     ( 99, 120, 255),
    "accent2":    (140, 100, 255),
    "ball":       (255,  95,  87),
    "ball2":      (255, 140,  80),
    "hit":        ( 52, 199, 132),
    "miss":       (255,  80,  80),
    "easy":       (120, 210, 160),
    "medium":     ( 99, 170, 255),
    "hard":       (255, 110, 110),
    "white":      (255, 255, 255),
    "overlay":    ( 20,  22,  48),
}

# Difficulty presets: (ball_speed, timeout_ms, ball_radius, label)
DIFFICULTIES = {
    "Easy":   {"speed": 0.0, "timeout": 3000, "radius": 38, "label": "Easy"},
    "Medium": {"speed": 0.0, "timeout": 2000, "radius": 30, "label": "Medium"},
    "Hard":   {"speed": 0.0, "timeout": 1200, "radius": 22, "label": "Hard"},
}

GAME_DURATION = 45          # seconds per session
BALL_MARGIN   = 100         # min px from edges for ball spawn


# ─────────────────────────────────────────────────────────────────────────────
# UTILITIES
# ─────────────────────────────────────────────────────────────────────────────

def lerp(a: float, b: float, t: float) -> float:
    """Smooth linear interpolation."""
    return a + (b - a) * t


def clamp(v, lo, hi):
    """Clamp v between lo and hi."""
    return max(lo, min(hi, v))


def ease_out(t: float) -> float:
    """Quadratic ease-out curve (0→1)."""
    return 1 - (1 - t) ** 2


def draw_rounded_rect(surface, color, rect, radius=14, width=0, alpha=255):
    """Draw a rounded rectangle, optionally with transparency."""
    if alpha == 255:
        pygame.draw.rect(surface, color, rect, width=width, border_radius=radius)
    else:
        s = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(s, (*color, alpha), (0, 0, *rect.size),
                         width=width, border_radius=radius)
        surface.blit(s, rect.topleft)


def draw_shadow(surface, rect, radius=14, offset=4, alpha=28):
    """Render a soft drop shadow beneath a card."""
    sr = pygame.Rect(rect.x + offset, rect.y + offset, rect.width, rect.height)
    draw_rounded_rect(surface, P["shadow"], sr, radius=radius, alpha=alpha)


def draw_card(surface, rect, radius=16, shadow=True):
    """Render a white rounded card with optional shadow."""
    if shadow:
        draw_shadow(surface, rect, radius=radius)
    draw_rounded_rect(surface, P["card"], rect, radius=radius)
    draw_rounded_rect(surface, P["border"], rect, radius=radius, width=1)


def render_text_centered(surface, font, text, color, cx, cy):
    """Blit text centred on (cx, cy)."""
    surf = font.render(text, True, color)
    surface.blit(surf, (cx - surf.get_width() // 2, cy - surf.get_height() // 2))
    return surf


def generate_session_id() -> str:
    """Generate a random session ID like S52341."""
    return "S" + str(random.randint(10000, 99999))


# ─────────────────────────────────────────────────────────────────────────────
# DATASET MANAGER
# ─────────────────────────────────────────────────────────────────────────────

class DatasetManager:
    """Handles automatic CSV dataset creation and row appending."""

    def __init__(self, path: str, headers: list):
        self.path    = path
        self.headers = headers
        os.makedirs(os.path.dirname(path), exist_ok=True)
        # Create file with headers if it does not exist
        if not os.path.exists(path):
            with open(path, "w", newline="") as f:
                csv.writer(f).writerow(headers)

    def append(self, row: dict):
        """Append one session row to the CSV."""
        with open(self.path, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=self.headers)
            w.writerow(row)


# ─────────────────────────────────────────────────────────────────────────────
# AI ANALYSER
# ─────────────────────────────────────────────────────────────────────────────

class AIAnalyser:
    """
    Computes performance metrics and generates AI feedback
    from raw session data.
    """

    @staticmethod
    def analyse(hits: int, misses: int, reaction_times: list, difficulty: str) -> dict:
        """Return a full analytics dict from session results."""
        total = hits + misses
        accuracy = round((hits / total * 100) if total > 0 else 0.0, 2)

        avg_rt = round(sum(reaction_times) / len(reaction_times), 1) if reaction_times else 999.0

        # Performance label
        if avg_rt < 400 and accuracy >= 85:
            label = "Fast"
        elif avg_rt < 700:
            label = "Average"
        else:
            label = "Slow"

        # Heuristic score (higher = better)
        heuristic = round((accuracy * 2) / (avg_rt / 100), 2) if avg_rt > 0 else 0.0

        # Ball speed proxy for dataset
        speed_map = {"Easy": 1.0, "Medium": 2.0, "Hard": 3.5}
        ball_speed = speed_map.get(difficulty, 1.0)

        # AI feedback message
        feedback = AIAnalyser._feedback(label, accuracy, avg_rt)

        return {
            "avg_rt":       avg_rt,
            "accuracy":     accuracy,
            "label":        label,
            "heuristic":    heuristic,
            "ball_speed":   ball_speed,
            "feedback":     feedback,
        }

    @staticmethod
    def _feedback(label: str, accuracy: float, rt: float) -> str:
        """Generate a natural-language AI feedback string."""
        if label == "Fast":
            return "Excellent reflexes and coordination. Top-tier cognitive performance!"
        elif label == "Average":
            if accuracy >= 75:
                return "Good performance, but reaction speed can still improve."
            return "Decent accuracy — focus on reducing your reaction delay."
        else:
            if accuracy < 50:
                return "Needs significant improvement in both timing and accuracy."
            return "Needs improvement in reaction timing. Keep practising!"


# ─────────────────────────────────────────────────────────────────────────────
# BALL
# ─────────────────────────────────────────────────────────────────────────────

class Ball:
    """
    A clickable ball that fades in, stays visible for a timeout,
    then triggers a miss if not clicked.
    """

    def __init__(self, radius: int, timeout_ms: int):
        self.radius     = radius
        self.timeout_ms = timeout_ms
        self.active     = False
        self.x = self.y = 0
        self.spawn_time = 0
        self.alpha      = 0.0        # fade-in alpha (0→255)
        self.scale      = 0.4        # pop-in scale (0.4→1.0)
        self.pulse_tick = 0          # for idle pulse
        self.hit_anim   = False      # True during click burst
        self.hit_tick   = 0

    def spawn(self):
        """Place the ball at a random safe position."""
        self.x          = random.randint(BALL_MARGIN, WIDTH  - BALL_MARGIN)
        self.y          = random.randint(BALL_MARGIN + 80, HEIGHT - BALL_MARGIN)
        self.spawn_time = pygame.time.get_ticks()
        self.active     = True
        self.alpha      = 0.0
        self.scale      = 0.4
        self.hit_anim   = False
        self.hit_tick   = 0
        self.pulse_tick = 0

    def elapsed_ms(self) -> int:
        """Milliseconds since this ball spawned."""
        return pygame.time.get_ticks() - self.spawn_time

    def timed_out(self) -> bool:
        """True if the ball has exceeded its allowed display time."""
        return self.active and self.elapsed_ms() > self.timeout_ms

    def is_clicked(self, mx: int, my: int) -> bool:
        """Return True if (mx, my) falls within the ball."""
        return self.active and math.hypot(mx - self.x, my - self.y) <= self.radius

    def trigger_hit(self):
        """Play the hit burst animation."""
        self.hit_anim = True
        self.hit_tick = 0
        self.active   = False

    def update(self):
        """Animate fade-in, pop-in scale, and idle pulse."""
        # Fade / pop-in
        self.alpha = clamp(lerp(self.alpha, 260, 0.18), 0, 255)
        self.scale = clamp(lerp(self.scale, 1.0, 0.15), 0.4, 1.0)
        self.pulse_tick += 1
        if self.hit_anim:
            self.hit_tick += 1

    def draw(self, surface):
        """Render the ball with glow, pulse, and optional hit burst."""
        if self.hit_anim:
            # Expanding ring burst
            r = self.radius + self.hit_tick * 4
            a = max(0, 200 - self.hit_tick * 25)
            if a > 0:
                s = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(s, (*P["hit"], a), (r + 2, r + 2), r, 3)
                surface.blit(s, (self.x - r - 2, self.y - r - 2))
            return

        if not self.active:
            return

        # Idle pulse radius
        pulse = math.sin(self.pulse_tick * 0.08) * 3
        draw_r = int(self.radius * self.scale)
        alpha  = int(self.alpha)

        # Soft glow halo
        for glow_expand in [14, 8, 3]:
            gr = draw_r + glow_expand
            gs = pygame.Surface((gr * 2, gr * 2), pygame.SRCALPHA)
            ga = max(0, int(alpha * 0.12))
            pygame.draw.circle(gs, (*P["ball"], ga), (gr, gr), gr)
            surface.blit(gs, (self.x - gr, self.y - gr))

        # Main ball with gradient feel (two circles)
        bs = pygame.Surface(((draw_r + 4) * 2, (draw_r + 4) * 2), pygame.SRCALPHA)
        pygame.draw.circle(bs, (*P["ball"],  alpha), (draw_r + 4, draw_r + 4), draw_r)
        pygame.draw.circle(bs, (*P["ball2"], max(0, alpha - 60)),
                           (draw_r + 4 - 6, draw_r + 4 - 6), max(4, draw_r // 2))
        surface.blit(bs, (self.x - draw_r - 4, self.y - draw_r - 4))

        # Timeout ring
        ratio  = self.elapsed_ms() / self.timeout_ms
        ring_r = draw_r + int(pulse) + 5
        arc_s  = pygame.Surface((ring_r * 2 + 4, ring_r * 2 + 4), pygame.SRCALPHA)
        end_a  = max(0.01, math.pi * 2 * (1 - ratio))
        ring_c = P["hit"] if ratio < 0.6 else P["miss"]
        pygame.draw.arc(arc_s, (*ring_c, 180),
                        (2, 2, ring_r * 2, ring_r * 2),
                        math.pi / 2, math.pi / 2 + end_a, 3)
        surface.blit(arc_s, (self.x - ring_r - 2, self.y - ring_r - 2))


# ─────────────────────────────────────────────────────────────────────────────
# HUD PARTICLE (floating +1 / MISS text)
# ─────────────────────────────────────────────────────────────────────────────

class FloatLabel:
    """A short-lived floating label that drifts upward after a hit or miss."""

    def __init__(self, x, y, text, color, font):
        self.x    = x
        self.y    = float(y)
        self.text = text
        self.color= color
        self.font = font
        self.alpha= 255
        self.life = 55   # frames

    def update(self):
        """Rise and fade."""
        self.y    -= 1.4
        self.alpha = max(0, self.alpha - int(255 / self.life))
        self.life -= 1

    def draw(self, surface):
        surf = self.font.render(self.text, True, self.color)
        surf.set_alpha(self.alpha)
        surface.blit(surf, (int(self.x - surf.get_width() // 2), int(self.y)))

    @property
    def alive(self):
        return self.life > 0


# ─────────────────────────────────────────────────────────────────────────────
# SCREEN BASE
# ─────────────────────────────────────────────────────────────────────────────

class Screen:
    """Abstract screen. Subclass and implement update() / draw() / handle()."""

    def __init__(self, app):
        self.app = app

    def handle(self, event): pass
    def update(self): pass
    def draw(self, surface): pass


# ─────────────────────────────────────────────────────────────────────────────
# START SCREEN
# ─────────────────────────────────────────────────────────────────────────────

class StartScreen(Screen):
    """Animated landing screen with branding and Start button."""

    def __init__(self, app):
        super().__init__(app)
        self.tick       = 0
        self.btn_rect   = pygame.Rect(WIDTH // 2 - 120, 420, 240, 52)
        self.btn_hover  = False
        self.btn_alpha  = 0.0
        self.orbs       = [self._make_orb() for _ in range(9)]

    def _make_orb(self):
        return {
            "x": random.uniform(0, WIDTH),
            "y": random.uniform(0, HEIGHT),
            "r": random.uniform(60, 160),
            "dx": random.uniform(-0.25, 0.25),
            "dy": random.uniform(-0.18, 0.18),
            "c": random.choice([P["accent"], P["accent2"], P["ball"]]),
        }

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_rect.collidepoint(event.pos):
                self.app.set_screen("difficulty")

    def update(self):
        self.tick += 1
        mx, my = pygame.mouse.get_pos()
        self.btn_hover  = self.btn_rect.collidepoint(mx, my)
        self.btn_alpha  = lerp(self.btn_alpha, 255 if self.btn_hover else 200, 0.12)
        for o in self.orbs:
            o["x"] = (o["x"] + o["dx"]) % WIDTH
            o["y"] = (o["y"] + o["dy"]) % HEIGHT

    def draw(self, surface):
        surface.fill(P["bg"])

        # Ambient gradient orbs
        for o in self.orbs:
            s = pygame.Surface((int(o["r"]) * 2, int(o["r"]) * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*o["c"], 22), (int(o["r"]), int(o["r"])), int(o["r"]))
            surface.blit(s, (int(o["x"] - o["r"]), int(o["y"] - o["r"])))

        # Hero card
        card_r = pygame.Rect(WIDTH // 2 - 280, 130, 560, 380)
        draw_card(surface, card_r, radius=24)

        # Logo circle
        cx, cy = WIDTH // 2, 235
        pygame.draw.circle(surface, P["bg2"], (cx, cy), 54)
        pygame.draw.circle(surface, P["accent"], (cx, cy), 54, 3)
        pygame.draw.circle(surface, P["ball"], (cx, cy - 12), 16)
        pygame.draw.rect(surface, P["accent"], (cx - 22, cy + 12, 44, 10), border_radius=5)

        # Title
        t = self.app.fonts["title"].render("Catch the Ball", True, P["text"])
        surface.blit(t, (WIDTH // 2 - t.get_width() // 2, 302))

        sub = self.app.fonts["sub"].render(
            "AI-Powered Cognitive Reaction Training", True, P["muted"])
        surface.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 346))

        # Start button
        col = P["accent"] if not self.btn_hover else P["accent2"]
        draw_rounded_rect(surface, col, self.btn_rect, radius=26, alpha=int(self.btn_alpha))
        render_text_centered(surface, self.app.fonts["btn"], "Start Game",
                             P["white"], self.btn_rect.centerx, self.btn_rect.centery)

        # Footer
        f = self.app.fonts["small"].render(
            "Click the ball as fast as you can · Build your AI dataset", True, P["muted"])
        surface.blit(f, (WIDTH // 2 - f.get_width() // 2, HEIGHT - 36))


# ─────────────────────────────────────────────────────────────────────────────
# DIFFICULTY SCREEN
# ─────────────────────────────────────────────────────────────────────────────

class DifficultyScreen(Screen):
    """Three difficulty cards with hover effects."""

    CARDS = [
        ("Easy",   P["easy"],   "Larger target · 3 s timeout · Great for beginners"),
        ("Medium", P["medium"], "Standard target · 2 s timeout · Balanced challenge"),
        ("Hard",   P["hard"],   "Smaller target · 1.2 s timeout · Expert mode"),
    ]

    def __init__(self, app):
        super().__init__(app)
        self.hovers = [False, False, False]
        self.scales = [1.0, 1.0, 1.0]
        self._build_rects()

    def _build_rects(self):
        cw, ch = 280, 170
        gap    = 28
        total  = len(self.CARDS) * cw + (len(self.CARDS) - 1) * gap
        sx     = WIDTH // 2 - total // 2
        cy     = HEIGHT // 2 - ch // 2
        self.rects = [
            pygame.Rect(sx + i * (cw + gap), cy, cw, ch)
            for i in range(len(self.CARDS))
        ]

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, r in enumerate(self.rects):
                if r.collidepoint(event.pos):
                    self.app.difficulty = self.CARDS[i][0]
                    self.app.set_screen("game")

    def update(self):
        mx, my = pygame.mouse.get_pos()
        for i, r in enumerate(self.rects):
            self.hovers[i] = r.collidepoint(mx, my)
            target = 1.04 if self.hovers[i] else 1.0
            self.scales[i] = lerp(self.scales[i], target, 0.14)

    def draw(self, surface):
        surface.fill(P["bg"])
        t = self.app.fonts["title"].render("Select Difficulty", True, P["text"])
        surface.blit(t, (WIDTH // 2 - t.get_width() // 2, 100))
        sub = self.app.fonts["sub"].render(
            "Choose how challenging you want the session to be", True, P["muted"])
        surface.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 148))

        for i, (label, color, desc) in enumerate(self.CARDS):
            r = self.rects[i]
            sc = self.scales[i]
            # Scale card around its centre
            sw = int(r.width * sc)
            sh = int(r.height * sc)
            sr = pygame.Rect(r.centerx - sw // 2, r.centery - sh // 2, sw, sh)
            draw_card(surface, sr, radius=20)

            # Accent top strip
            strip = pygame.Rect(sr.x + 1, sr.y + 1, sr.width - 2, 5)
            draw_rounded_rect(surface, color, strip, radius=20)

            # Icon circle
            pygame.draw.circle(surface, (*color, 60), (sr.centerx, sr.y + 62), 28)
            pygame.draw.circle(surface, color, (sr.centerx, sr.y + 62), 16)

            # Label
            lt = self.app.fonts["card_title"].render(label, True, P["text"])
            surface.blit(lt, (sr.centerx - lt.get_width() // 2, sr.y + 98))

            # Description (word-wrap approximate)
            dt = self.app.fonts["small"].render(desc, True, P["muted"])
            surface.blit(dt, (sr.centerx - dt.get_width() // 2, sr.y + 128))

        back = self.app.fonts["small"].render("← Back to Start", True, P["accent"])
        bx, by = 28, HEIGHT - 38
        surface.blit(back, (bx, by))
        if pygame.Rect(bx, by, back.get_width(), back.get_height()).collidepoint(
                pygame.mouse.get_pos()):
            pygame.draw.line(surface, P["accent"],
                             (bx, by + back.get_height()),
                             (bx + back.get_width(), by + back.get_height()), 1)

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            for i, r in enumerate(self.rects):
                if r.collidepoint(mx, my):
                    self.app.difficulty = self.CARDS[i][0]
                    self.app.set_screen("game")
            bx, by = 28, HEIGHT - 38
            back_r = pygame.Rect(bx, by, 120, 20)
            if back_r.collidepoint(mx, my):
                self.app.set_screen("start")


# ─────────────────────────────────────────────────────────────────────────────
# GAME SCREEN
# ─────────────────────────────────────────────────────────────────────────────

class GameScreen(Screen):
    """
    Core gameplay: spawns balls, measures reaction time,
    tracks hits/misses, runs the game timer.
    """

    def __init__(self, app):
        super().__init__(app)
        diff           = DIFFICULTIES[app.difficulty]
        self.radius    = diff["radius"]
        self.timeout   = diff["timeout"]
        self.ball      = Ball(self.radius, self.timeout)
        self.hits      = 0
        self.misses    = 0
        self.score     = 0
        self.rt_list   = []             # reaction times in ms
        self.labels    = []             # FloatLabel pool
        self.start_time= time.time()
        self.ball.spawn()

    def _remaining(self) -> float:
        """Seconds left in the session."""
        return max(0.0, GAME_DURATION - (time.time() - self.start_time))

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self.ball.active and self.ball.is_clicked(mx, my):
                rt = self.ball.elapsed_ms()
                self.rt_list.append(rt)
                self.hits  += 1
                self.score += max(10, int(500 / max(rt, 1) * 10))
                self.ball.trigger_hit()
                self.labels.append(FloatLabel(
                    mx, my - 20, f"+{self.score // self.hits}  ⚡ {rt} ms",
                    P["hit"], self.app.fonts["float_label"]))
            elif self.ball.active:
                # Wrong-area click
                self.misses += 1
                self.labels.append(FloatLabel(mx, my - 20, "MISS", P["miss"],
                                              self.app.fonts["float_label"]))

    def update(self):
        if self._remaining() <= 0:
            self.app.set_screen("gameover")
            return

        self.ball.update()

        # Timeout miss
        if self.ball.timed_out():
            self.misses += 1
            self.labels.append(FloatLabel(
                self.ball.x, self.ball.y, "TIMEOUT", P["miss"],
                self.app.fonts["float_label"]))
            self.ball.active = False

        # Spawn next ball (after hit animation or timeout)
        if not self.ball.active and (not self.ball.hit_anim or self.ball.hit_tick > 12):
            self.ball.spawn()

        # Update float labels
        for lbl in self.labels:
            lbl.update()
        self.labels = [l for l in self.labels if l.alive]

    def _draw_hud(self, surface):
        """Render the top HUD bar with score, hits, misses, timer, last RT."""
        bar = pygame.Rect(0, 0, WIDTH, 68)
        draw_rounded_rect(surface, P["card"], bar, radius=0)
        draw_rounded_rect(surface, P["border"], pygame.Rect(0, 67, WIDTH, 1), radius=0)

        # Segments
        stats = [
            ("SCORE",   str(self.score),                              P["accent"]),
            ("HITS",    str(self.hits),                               P["hit"]),
            ("MISSES",  str(self.misses),                             P["miss"]),
            ("LAST RT", f"{self.rt_list[-1]} ms" if self.rt_list else "—", P["text"]),
            ("TIME",    f"{int(self._remaining())}s",                 P["text"]),
        ]
        seg_w = WIDTH // len(stats)
        for i, (label, value, color) in enumerate(stats):
            cx = seg_w * i + seg_w // 2
            lbl = self.app.fonts["hud_label"].render(label, True, P["muted"])
            surface.blit(lbl, (cx - lbl.get_width() // 2, 8))
            val = self.app.fonts["hud_value"].render(value, True, color)
            surface.blit(val, (cx - val.get_width() // 2, 28))

        # Timer progress bar
        ratio = self._remaining() / GAME_DURATION
        bar_w = WIDTH - 40
        bg_r  = pygame.Rect(20, 62, bar_w, 4)
        draw_rounded_rect(surface, P["bg2"], bg_r, radius=2)
        fill_c = P["hit"] if ratio > 0.4 else P["miss"]
        draw_rounded_rect(surface, fill_c,
                          pygame.Rect(20, 62, int(bar_w * ratio), 4), radius=2)

    def draw(self, surface):
        surface.fill(P["bg"])
        self._draw_hud(surface)
        self.ball.draw(surface)
        for lbl in self.labels:
            lbl.draw(surface)

        # Difficulty badge
        diff_col = {"Easy": P["easy"], "Medium": P["medium"], "Hard": P["hard"]}
        dc = diff_col[self.app.difficulty]
        db = pygame.Rect(WIDTH - 110, HEIGHT - 40, 100, 26)
        draw_rounded_rect(surface, dc, db, radius=13, alpha=80)
        render_text_centered(surface, self.app.fonts["small"],
                             self.app.difficulty, P["text"], db.centerx, db.centery)


# ─────────────────────────────────────────────────────────────────────────────
# GAME OVER SCREEN
# ─────────────────────────────────────────────────────────────────────────────

class GameOverScreen(Screen):
    """Results screen with AI analysis, metrics cards, and dataset save."""

    def __init__(self, app):
        super().__init__(app)
        gs      = app.game_screen
        self.ai = AIAnalyser.analyse(gs.hits, gs.misses, gs.rt_list, app.difficulty)
        self.hits     = gs.hits
        self.misses   = gs.misses
        self.score    = gs.score
        self.diff     = app.difficulty

        # Save to dataset
        sid = generate_session_id()
        app.dataset.append({
            "session_id":       sid,
            "reaction_time_ms": self.ai["avg_rt"],
            "score":            self.score,
            "hits":             self.hits,
            "misses":           self.misses,
            "accuracy":         self.ai["accuracy"],
            "ball_speed":       self.ai["ball_speed"],
            "difficulty_level": self.diff,
            "performance_label":self.ai["label"],
            "heuristic_score":  self.ai["heuristic"],
        })
        self.session_id = sid

        # Buttons
        self.btn_retry  = pygame.Rect(WIDTH // 2 - 250, HEIGHT - 90, 220, 48)
        self.btn_menu   = pygame.Rect(WIDTH // 2 + 30,  HEIGHT - 90, 220, 48)
        self.hover_r    = self.hover_m = False
        self.fade_alpha = 0.0

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_retry.collidepoint(event.pos):
                self.app.set_screen("game")
            if self.btn_menu.collidepoint(event.pos):
                self.app.set_screen("start")

    def update(self):
        mx, my = pygame.mouse.get_pos()
        self.hover_r    = self.btn_retry.collidepoint(mx, my)
        self.hover_m    = self.btn_menu.collidepoint(mx, my)
        self.fade_alpha = lerp(self.fade_alpha, 255, 0.07)

    def draw(self, surface):
        surface.fill(P["bg"])

        # Title
        title = self.app.fonts["title"].render("Session Complete", True, P["text"])
        surface.blit(title, (WIDTH // 2 - title.get_width() // 2, 28))

        sid_t = self.app.fonts["small"].render(
            f"Session ID: {self.session_id}  ·  Saved to dataset", True, P["muted"])
        surface.blit(sid_t, (WIDTH // 2 - sid_t.get_width() // 2, 72))

        # Metric cards
        metrics = [
            ("Reaction Time",  f"{self.ai['avg_rt']} ms",       P["accent"]),
            ("Accuracy",       f"{self.ai['accuracy']}%",        P["hit"]),
            ("Score",          str(self.score),                   P["ball"]),
            ("Heuristic",      str(self.ai['heuristic']),         P["accent2"]),
            ("Hits",           str(self.hits),                    P["hit"]),
            ("Misses",         str(self.misses),                  P["miss"]),
        ]
        cw, ch = 160, 100
        cols   = 3
        gap    = 20
        total_w= cols * cw + (cols - 1) * gap
        sx     = WIDTH // 2 - total_w // 2
        sy     = 110
        for i, (label, value, color) in enumerate(metrics):
            col = i % cols
            row = i // cols
            r   = pygame.Rect(sx + col * (cw + gap), sy + row * (ch + gap), cw, ch)
            draw_card(surface, r, radius=16)
            strip = pygame.Rect(r.x + 1, r.y + 1, r.width - 2, 4)
            draw_rounded_rect(surface, color, strip, radius=16)
            lbl = self.app.fonts["small"].render(label, True, P["muted"])
            surface.blit(lbl, (r.centerx - lbl.get_width() // 2, r.y + 18))
            val = self.app.fonts["card_value"].render(value, True, color)
            surface.blit(val, (r.centerx - val.get_width() // 2, r.y + 46))

        # AI analysis card
        ai_r = pygame.Rect(WIDTH // 2 - 340, 340, 680, 100)
        draw_card(surface, ai_r, radius=18)
        label_col = {
            "Fast": P["hit"], "Average": P["accent"], "Slow": P["miss"]
        }.get(self.ai["label"], P["accent"])

        badge_r = pygame.Rect(ai_r.x + 20, ai_r.y + 20, 90, 30)
        draw_rounded_rect(surface, label_col, badge_r, radius=15, alpha=50)
        render_text_centered(surface, self.app.fonts["small"],
                             self.ai["label"], label_col,
                             badge_r.centerx, badge_r.centery)

        fb = self.app.fonts["feedback"].render(self.ai["feedback"], True, P["text"])
        surface.blit(fb, (ai_r.x + 130, ai_r.y + 18))

        ai_tag = self.app.fonts["small"].render(
            f"AI Heuristic Score: {self.ai['heuristic']}  ·  "
            f"Difficulty: {self.diff}", True, P["muted"])
        surface.blit(ai_tag, (ai_r.x + 130, ai_r.y + 56))

        # Buttons
        for rect, label, hov in [
            (self.btn_retry, "Play Again", self.hover_r),
            (self.btn_menu,  "Main Menu",  self.hover_m),
        ]:
            col = P["accent2"] if hov else P["accent"]
            draw_rounded_rect(surface, col, rect, radius=24)
            render_text_centered(surface, self.app.fonts["btn"],
                                 label, P["white"], rect.centerx, rect.centery)

        # Fade-in overlay (entry animation)
        if self.fade_alpha < 250:
            ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            ov.fill((245, 247, 252, int(255 - self.fade_alpha)))
            surface.blit(ov, (0, 0))


# ─────────────────────────────────────────────────────────────────────────────
# APP — orchestrates screens and fonts
# ─────────────────────────────────────────────────────────────────────────────

class App:
    """
    Top-level application.
    Manages the Pygame window, font loading, screen switching,
    and the main event/update/draw loop.
    """

    def __init__(self):
        pygame.init()
        self.screen     = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock      = pygame.time.Clock()
        self.difficulty = "Medium"
        self.dataset    = DatasetManager(DATASET_CSV, CSV_HEADERS)
        self.game_screen= None      # last GameScreen instance (for results)
        self.fonts      = self._load_fonts()
        self.current    = StartScreen(self)
        self.running    = True

    def _load_fonts(self) -> dict:
        """Build the font dictionary using system fonts."""
        def F(size, bold=False):
            return pygame.font.SysFont("segoeui", size, bold=bold)
        return {
            "title":       F(32, bold=True),
            "sub":         F(14),
            "btn":         F(15, bold=True),
            "card_title":  F(18, bold=True),
            "card_value":  F(22, bold=True),
            "small":       F(12),
            "hud_label":   F(11),
            "hud_value":   F(17, bold=True),
            "float_label": F(13, bold=True),
            "feedback":    F(13),
        }

    def set_screen(self, name: str):
        """Switch the active screen by name."""
        if name == "start":
            self.current = StartScreen(self)
        elif name == "difficulty":
            self.current = DifficultyScreen(self)
        elif name == "game":
            self.game_screen = GameScreen(self)
            self.current     = self.game_screen
        elif name == "gameover":
            self.current = GameOverScreen(self)

    def run(self):
        """Primary game loop."""
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.running = False
                self.current.handle(event)

            self.current.update()
            self.current.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def run():
    """Launch the Catch the Ball game."""
    App().run()


if __name__ == "__main__":
    run()