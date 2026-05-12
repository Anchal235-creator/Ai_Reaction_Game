"""
AI-Based Reaction Time Game System — Main Menu
Author : [Your Name]
Version: 1.0.0
Description: Futuristic glassmorphic Pygame menu for a cognitive AI game suite.
"""
 

import pygame
import math
import random
import sys
 
# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
 
WIDTH, HEIGHT = 1280, 720
FPS = 60
 
PALETTE = {
    "bg":           (13,  11,  30),
    "lavender":     (201, 184, 255),
    "blue":         (168, 216, 255),
    "peach":        (255, 214, 184),
    "purple":       (184, 168, 255),
    "soft_white":   (240, 238, 255),
    "muted":        (160, 155, 190),
    "card_bg":      (255, 255, 255),
    "accent":       (180, 140, 255),
    "green":        (140, 240, 180),
    "yellow":       (255, 230, 120),
    "red":          (255, 140, 140),
    "dark_panel":   (22,  18,  48),
    "border":       (255, 255, 255),
    "title":        (220, 210, 255),
}
 
PARTICLE_COLORS = [
    PALETTE["lavender"], PALETTE["blue"], PALETTE["peach"],
    PALETTE["purple"], PALETTE["green"], PALETTE["yellow"],
]
 
FONT_TITLE  = 38
FONT_SUB    = 14
FONT_CARD   = 15
FONT_DESC   = 11
FONT_STAT   = 13
FONT_BADGE  = 11
FONT_FOOTER = 11
 
LEFT_W  = 840
RIGHT_X = 860
RIGHT_W = 380
 
# ─────────────────────────────────────────────────────────────────────────────
# UTILITIES
# ─────────────────────────────────────────────────────────────────────────────
 
def lerp(a, b, t):
    """Linear interpolation between a and b by factor t."""
    return a + (b - a) * t
 
 
def draw_rounded_rect(surface, color, rect, radius=16, width=0):
    """Draw a rounded rectangle with optional border width."""
    pygame.draw.rect(surface, color, rect, width=width, border_radius=radius)
 
 
def draw_glass_panel(surface, rect, alpha=18, border_alpha=45, radius=18):
    """Render a frosted-glass card using alpha-blended surfaces."""
    glass = pygame.Surface(rect.size, pygame.SRCALPHA)
    glass.fill((255, 255, 255, alpha))
    pygame.draw.rect(glass, (255, 255, 255, 0), (0, 0, *rect.size), border_radius=radius)
    surface.blit(glass, rect.topleft)
    border_surf = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(border_surf, (255, 255, 255, border_alpha),
                     (0, 0, *rect.size), width=1, border_radius=radius)
    surface.blit(border_surf, rect.topleft)
 
 
def draw_glow_rect(surface, color, rect, radius=18, layers=4, max_alpha=60):
    """Simulate a neon glow around a rect using concentric alpha rects."""
    for i in range(layers, 0, -1):
        expand = i * 4
        alpha  = int(max_alpha * (1 - i / (layers + 1)))
        glow_rect = pygame.Rect(
            rect.x - expand, rect.y - expand,
            rect.width + expand * 2, rect.height + expand * 2
        )
        glow_surf = pygame.Surface(glow_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (*color, alpha),
                         (0, 0, *glow_rect.size), border_radius=radius + expand)
        surface.blit(glow_surf, glow_rect.topleft)
 
 
def draw_bloom_text(surface, font, text, color, pos, bloom_color=None, bloom_radius=3):
    """Render text with a soft bloom/glow behind it."""
    bc = bloom_color or color
    for ox in range(-bloom_radius, bloom_radius + 1, 2):
        for oy in range(-bloom_radius, bloom_radius + 1, 2):
            if ox == 0 and oy == 0:
                continue
            bloom = font.render(text, True, (*bc[:3], 60))
            bloom.set_alpha(30)
            surface.blit(bloom, (pos[0] + ox, pos[1] + oy))
    surface.blit(font.render(text, True, color), pos)
 
 
# ─────────────────────────────────────────────────────────────────────────────
# PARTICLE
# ─────────────────────────────────────────────────────────────────────────────
 
class Particle:
    """A single floating ambient particle with sinusoidal drift."""
 
    def __init__(self):
        self._reset(spawn=True)
 
    def _reset(self, spawn=False):
        """Reset particle to a random position at the bottom (or anywhere on spawn)."""
        self.x     = random.uniform(0, WIDTH)
        self.y     = random.uniform(0, HEIGHT) if spawn else HEIGHT + 10
        self.speed = random.uniform(0.3, 1.0)
        self.size  = random.randint(2, 5)
        self.color = random.choice(PARTICLE_COLORS)
        self.alpha = random.randint(60, 130)
        self.phase = random.uniform(0, math.pi * 2)
        self.tick  = 0
 
    def update(self):
        """Drift upward with horizontal sine oscillation."""
        self.y -= self.speed
        self.x += math.sin(self.tick * 0.02 + self.phase) * 0.5
        self.tick += 1
        if self.y < -10:
            self._reset()
 
    def draw(self, surface):
        """Render particle as a soft alpha circle."""
        s = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, self.alpha), (self.size, self.size), self.size)
        surface.blit(s, (int(self.x - self.size), int(self.y - self.size)))
 
 
# ─────────────────────────────────────────────────────────────────────────────
# PARTICLE SYSTEM
# ─────────────────────────────────────────────────────────────────────────────
 
class ParticleSystem:
    """Manages a pool of ambient background particles."""
 
    def __init__(self, count=65):
        self.particles = [Particle() for _ in range(count)]
 
    def update(self):
        """Tick all particles."""
        for p in self.particles:
            p.update()
 
    def draw(self, surface):
        """Render all particles."""
        for p in self.particles:
            p.draw(surface)
 
 
# ─────────────────────────────────────────────────────────────────────────────
# GAME CARD
# ─────────────────────────────────────────────────────────────────────────────
 
class GameCard:
    """A glassmorphic card representing one game or action."""
 
    def __init__(self, rect, title, description, color, icon_id, callback):
        self.rect        = pygame.Rect(rect)
        self.base_rect   = pygame.Rect(rect)
        self.title       = title
        self.description = description
        self.color       = color
        self.icon_id     = icon_id
        self.callback    = callback
        self.hovered     = False
        self.glow_alpha  = 0.0
        self.float_tick  = random.uniform(0, math.pi * 2)
        self.float_off   = 0.0
 
    def update(self, mouse_pos, tick):
        """Update hover state, glow lerp, and idle float animation."""
        self.hovered    = self.rect.collidepoint(mouse_pos)
        target_glow     = 90.0 if self.hovered else 0.0
        self.glow_alpha = lerp(self.glow_alpha, target_glow, 0.12)
 
        # idle vertical float (staggered per card via phase)
        self.float_off = math.sin(tick * 0.03 + self.float_tick) * 3.5
        lift           = -4.0 if self.hovered else 0.0
        self.rect.y    = self.base_rect.y + int(self.float_off + lift)
 
    def handle_click(self, event):
        """Fire callback if this card is clicked."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback(self.title)
 
    def _draw_icon(self, surface, cx, cy):
        """Draw a unique programmatic icon for each game."""
        c = self.color
 
        if self.icon_id == "catch":
            # Ball falling toward a paddle
            pygame.draw.circle(surface, c, (cx, cy - 10), 8, 0)
            pygame.draw.rect(surface, c, (cx - 14, cy + 6, 28, 6), border_radius=3)
 
        elif self.icon_id == "stroop":
            # Two overlapping colored rectangles (Stroop effect)
            r1 = pygame.Surface((22, 14), pygame.SRCALPHA)
            r1.fill((*PALETTE["blue"], 200))
            r2 = pygame.Surface((22, 14), pygame.SRCALPHA)
            r2.fill((*PALETTE["peach"], 200))
            surface.blit(r1, (cx - 18, cy - 10))
            surface.blit(r2, (cx - 4,  cy - 2))
 
        elif self.icon_id == "aim":
            # Concentric circles with crosshair
            for r, a in [(16, 60), (10, 120), (5, 220)]:
                s = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*c, a), (r + 1, r + 1), r, 2)
                surface.blit(s, (cx - r - 1, cy - r - 1))
            pygame.draw.line(surface, c, (cx - 18, cy), (cx + 18, cy), 1)
            pygame.draw.line(surface, c, (cx, cy - 18), (cx, cy + 18), 1)
 
        elif self.icon_id == "perf":
            # Bar chart (3 bars)
            for i, h in enumerate([10, 18, 13]):
                bx = cx - 14 + i * 10
                pygame.draw.rect(surface, c, (bx, cy + 8 - h, 7, h), border_radius=2)
 
        elif self.icon_id == "exit":
            # Power / × icon
            pygame.draw.line(surface, c, (cx - 10, cy - 10), (cx + 10, cy + 10), 2)
            pygame.draw.line(surface, c, (cx + 10, cy - 10), (cx - 10, cy + 10), 2)
 
    def draw(self, surface, font_title, font_desc):
        """Render the card with glow, glass panel, icon, title, description."""
        # Glow behind card when hovered
        if self.glow_alpha > 2:
            draw_glow_rect(surface, self.color, self.rect,
                           radius=18, layers=4, max_alpha=int(self.glow_alpha))
 
        # Glass panel
        draw_glass_panel(surface, self.rect, alpha=22, border_alpha=50, radius=18)
 
        # Accent top bar
        top_bar = pygame.Rect(self.rect.x + 12, self.rect.y + 10, 40, 3)
        bar_surf = pygame.Surface((40, 3), pygame.SRCALPHA)
        bar_surf.fill((*self.color, 200))
        surface.blit(bar_surf, top_bar.topleft)
 
        # Icon
        icon_cx = self.rect.centerx
        icon_cy = self.rect.y + 52
        self._draw_icon(surface, icon_cx, icon_cy)
 
        # Title
        t_surf = font_title.render(self.title, True, PALETTE["soft_white"])
        surface.blit(t_surf, (self.rect.centerx - t_surf.get_width() // 2,
                               self.rect.y + 82))
 
        # Description
        d_surf = font_desc.render(self.description, True, PALETTE["muted"])
        surface.blit(d_surf, (self.rect.centerx - d_surf.get_width() // 2,
                               self.rect.y + 104))
 
 
# ─────────────────────────────────────────────────────────────────────────────
# ANALYTICS PANEL
# ─────────────────────────────────────────────────────────────────────────────
 
class AnalyticsPanel:
    """Right-side AI analytics dashboard panel."""
 
    STATS = [
        ("Avg Reaction", "312 ms",   PALETTE["blue"],    0.72),
        ("Accuracy",     "87.4 %",   PALETTE["green"],   0.87),
        ("Sessions",     "14",       PALETTE["lavender"],0.55),
        ("AI Grade",     "A",        PALETTE["peach"],   0.90),
    ]
 
    def __init__(self):
        self.rect       = pygame.Rect(RIGHT_X, 90, RIGHT_W, HEIGHT - 130)
        self.badge_tick = 0.0
        self.badge_alpha= 200
 
    def update(self, tick):
        """Pulse the AI badge alpha."""
        self.badge_alpha = int(180 + 60 * math.sin(tick * 0.05))
 
    def draw(self, surface, fonts):
        """Render the full analytics panel."""
        font_title, font_stat, font_badge, font_desc = fonts
 
        # Panel background
        draw_glass_panel(surface, self.rect, alpha=25, border_alpha=55, radius=20)
 
        # Panel title
        pt = font_title.render("AI Analytics", True, PALETTE["accent"])
        surface.blit(pt, (self.rect.x + 20, self.rect.y + 18))
 
        # Divider
        div_surf = pygame.Surface((self.rect.width - 40, 1), pygame.SRCALPHA)
        div_surf.fill((255, 255, 255, 40))
        surface.blit(div_surf, (self.rect.x + 20, self.rect.y + 52))
 
        # Stat rows
        for i, (label, value, color, ratio) in enumerate(self.STATS):
            row_y = self.rect.y + 72 + i * 72
 
            # Label
            lbl = font_stat.render(label, True, PALETTE["muted"])
            surface.blit(lbl, (self.rect.x + 20, row_y))
 
            # Value
            val = font_title.render(value, True, PALETTE["soft_white"])
            surface.blit(val, (self.rect.x + 20, row_y + 18))
 
            # Progress bar track
            bar_rect = pygame.Rect(self.rect.x + 20, row_y + 46, self.rect.width - 40, 5)
            track = pygame.Surface(bar_rect.size, pygame.SRCALPHA)
            track.fill((255, 255, 255, 30))
            surface.blit(track, bar_rect.topleft)
 
            # Progress bar fill
            fill_w = int(bar_rect.width * ratio)
            fill   = pygame.Surface((fill_w, 5), pygame.SRCALPHA)
            fill.fill((*color, 200))
            surface.blit(fill, bar_rect.topleft)
 
        # AI badge
        badge_y  = self.rect.y + self.rect.height - 54
        badge_w, badge_h = 160, 32
        badge_x  = self.rect.centerx - badge_w // 2
        badge_s  = pygame.Surface((badge_w, badge_h), pygame.SRCALPHA)
        badge_s.fill((*PALETTE["accent"], self.badge_alpha))
        pygame.draw.rect(badge_s, (255, 255, 255, 80),
                         (0, 0, badge_w, badge_h), width=1, border_radius=16)
        surface.blit(badge_s, (badge_x, badge_y))
 
        badge_txt = font_badge.render("⚡  AI-Powered Analysis", True, PALETTE["bg"])
        surface.blit(badge_txt, (badge_x + badge_w // 2 - badge_txt.get_width() // 2,
                                  badge_y + badge_h // 2 - badge_txt.get_height() // 2))
 
 
# ─────────────────────────────────────────────────────────────────────────────
# APP — main loop and state management
# ─────────────────────────────────────────────────────────────────────────────
 
class App:
    """Main application: manages the game loop, rendering, and event dispatch."""
 
    def __init__(self):
        pygame.init()
        self.screen  = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("AI-Based Reaction Time Game System")
        self.clock   = pygame.time.Clock()
        self.tick    = 0
        self.running = True
 
        # Fonts
        self._init_fonts()
 
        # Systems
        self.particles = ParticleSystem(65)
        self.analytics = AnalyticsPanel()
        self.cards     = self._build_cards()
 
    # ── Font initialisation ──────────────────────────────────────────────────
 
    def _init_fonts(self):
        """Load system fonts at required sizes."""
        def F(size, bold=False):
            return pygame.font.SysFont("segoeui", size, bold=bold)
 
        self.f_title  = F(FONT_TITLE,  bold=True)
        self.f_sub    = F(FONT_SUB)
        self.f_card   = F(FONT_CARD,   bold=True)
        self.f_desc   = F(FONT_DESC)
        self.f_stat   = F(FONT_STAT)
        self.f_badge  = F(FONT_BADGE,  bold=True)
        self.f_footer = F(FONT_FOOTER)
 
    # ── Card layout ──────────────────────────────────────────────────────────
 
    def _build_cards(self):
        """Construct game cards in a 2-column grid on the left zone."""
        CARD_W, CARD_H = 178, 135
        GAP_X, GAP_Y   = 18, 18
        COLS           = 3
        START_X        = 40
        START_Y        = 195
 
        configs = [
            ("Catch the Ball",  "Reflex & tracking",    PALETTE["blue"],     "catch",  self._launch),
            ("Color Text",      "Stroop cognition",      PALETTE["peach"],    "stroop", self._launch),
            ("Aim Trainer",     "Precision & speed",     PALETTE["lavender"], "aim",    self._launch),
            ("View Performance","AI stats & history",    PALETTE["green"],    "perf",   self._launch),
            ("Exit",            "Close the system",      PALETTE["red"],      "exit",   self._exit_game),
        ]
 
        cards = []
        for i, (title, desc, color, icon, cb) in enumerate(configs):
            col = i % COLS
            row = i // COLS
            x   = START_X + col * (CARD_W + GAP_X)
            y   = START_Y + row * (CARD_H + GAP_Y)
            cards.append(GameCard((x, y, CARD_W, CARD_H), title, desc, color, icon, cb))
        return cards
 
    # ── Callbacks ────────────────────────────────────────────────────────────
    # ── Callbacks ────────────────────────────────────────────────────────────

    def _launch(self, name):

        if name == "Catch the Ball":

            from games.catch_the_ball import run
            run()

        elif name == "Exit":

            self.running = False

        else:

            print(f"{name} coming soon...")


    def _exit_game(self, _):
        """Cleanly quit the application."""
        self.running = False


    # ── Drawing helpers ──────────────────────────────────────────────────────

    def _draw_background(self):
        """Fill background with dark base color."""
        self.screen.fill(PALETTE["bg"])


    def _draw_scanlines(self):
        """Subtle scanline overlay for depth."""

        for y in range(0, HEIGHT, 6):

            s = pygame.Surface((WIDTH, 1), pygame.SRCALPHA)
            s.fill((0, 0, 0, 12))

            self.screen.blit(s, (0, y))


    def _draw_title(self):
        """Render the main title and subtitle with bloom glow."""

        title_text = "AI-Based Reaction Time Game System"

        sub_text = (
            "Train reflexes, attention, and cognitive "
            "performance using AI-powered mini games."
        )

        t_surf = self.f_title.render(
            title_text,
            True,
            PALETTE["title"]
        )

        tx = LEFT_W // 2 - t_surf.get_width() // 2
 
        # Bloom: draw offset copies at low alpha
        for ox, oy in [(-2, -2), (2, -2), (-2, 2), (2, 2)]:
            bloom = self.f_title.render(title_text, True, PALETTE["accent"])
            bloom.set_alpha(35)
            self.screen.blit(bloom, (tx + ox, 28 + oy))
        self.screen.blit(t_surf, (tx, 28))
 
        # Subtitle
        s_surf = self.f_sub.render(sub_text, True, PALETTE["muted"])
        sx     = LEFT_W // 2 - s_surf.get_width() // 2
        self.screen.blit(s_surf, (sx, 80))
 
        # Accent underline
        ul = pygame.Surface((320, 2), pygame.SRCALPHA)
        ul.fill((*PALETTE["accent"], 160))
        self.screen.blit(ul, (LEFT_W // 2 - 160, 108))
 
        # Section label
        lbl = self.f_stat.render("SELECT A GAME", True, PALETTE["muted"])
        self.screen.blit(lbl, (40, 168))
        pygame.draw.line(self.screen, (*PALETTE["muted"], 80),
                         (40, 186), (LEFT_W - 40, 186), 1)
 
    def _draw_footer(self):
        """Render footer text at the bottom center."""
        text  = "AI analyzes user reaction speed and cognitive performance.  |  v1.0.0"
        f_surf= self.f_footer.render(text, True, PALETTE["muted"])
        self.screen.blit(f_surf, (WIDTH // 2 - f_surf.get_width() // 2, HEIGHT - 24))
 
        # Footer divider
        div = pygame.Surface((WIDTH - 60, 1), pygame.SRCALPHA)
        div.fill((255, 255, 255, 25))
        self.screen.blit(div, (30, HEIGHT - 36))
 
    def _draw_left_panel_bg(self):
        """Subtle panel behind the card grid."""
        rect = pygame.Rect(20, 140, LEFT_W - 40, HEIGHT - 170)
        draw_glass_panel(self.screen, rect, alpha=8, border_alpha=20, radius=24)
 
    # ── Main loop ────────────────────────────────────────────────────────────
 
    def run(self):
        """Primary game loop."""
        while self.running:
            mouse_pos = pygame.mouse.get_pos()
 
            # ── Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.running = False
                for card in self.cards:
                    card.handle_click(event)
 
            # ── Update
            self.particles.update()
            self.analytics.update(self.tick)
            for card in self.cards:
                card.update(mouse_pos, self.tick)
 
            # ── Draw
            self._draw_background()
            self.particles.draw(self.screen)
            self._draw_scanlines()
            self._draw_left_panel_bg()
            self._draw_title()
 
            for card in self.cards:
                card.draw(self.screen, self.f_card, self.f_desc)
 
            self.analytics.draw(
                self.screen,
                (self.f_card, self.f_stat, self.f_badge, self.f_desc)
            )
 
            self._draw_footer()
 
            pygame.display.flip()
            self.clock.tick(FPS)
            self.tick += 1
 
        pygame.quit()
        sys.exit()
 
 
# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
 
if __name__ == "__main__":
    App().run()