import sys
import math
import colorsys
import random
import numpy as np
import pygame

pygame.init()
pygame.font.init()

# ---------------- Config ----------------
GRID_W, GRID_H = 240, 160
# factores de zoom: 1.0 = el MUNDO completo encaja en la vista; el resto acerca
ZOOM_FACTORS = [1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 9.0, 13.0]
SPEEDS = [1, 2, 5, 10, 20, 50, 100, 250, 600, 1500, 4000, 12000]  # pasos por SEGUNDO
TURBO_FRAME = 50000     # pasos por frame en modo turbo (lo más rápido posible)
FPS = 60
MARGIN = 0

PRESETS = [
    ("RL", "Clásica · autopista"),
    ("RLR", "Triángulos"),
    ("LLRR", "Simetría cuadrada"),
    ("RRLL", "Copo simétrico"),
    ("LRRRRRLLR", "Cardumen caótico"),
    ("LLRRRLRLRLLR", "Convergente"),
    ("RRLLLRLLLL", "Coral"),
    ("RLLR", "Filigrana"),
    ("RRLRLLLRRR", "Nebulosa"),
]
GIRO = {"R": 1, "L": 3, "U": 2, "N": 0}

# ---------------- Colores UI ----------------
BG = (12, 14, 20)
PANEL_BG = (22, 26, 36)
PANEL_LINE = (40, 48, 64)
TXT = (232, 238, 246)
MUTED = (140, 152, 172)
ACCENT = (245, 200, 80)
BTN_BG = (32, 40, 54)
BTN_HOVER = (44, 54, 72)
BTN_BORDER = (60, 72, 92)
ANT_COLOR = (255, 90, 70)
GRID_BG = (16, 18, 26)

TITLE_FONT = pygame.font.SysFont("Segoe UI", 24, bold=True)
MED_FONT = pygame.font.SysFont("Segoe UI", 15, bold=True)
SMALL_FONT = pygame.font.SysFont("Segoe UI", 14, bold=True)


def hacer_paleta(k):
    pal = np.zeros((k, 3), dtype=np.uint8)
    pal[0] = GRID_BG
    if k == 2:
        pal[1] = (100, 220, 160)
    else:
        for i in range(1, k):
            h = ((i - 1) / max(1, k - 1)) * 0.85
            r, g, b = colorsys.hsv_to_rgb(h, 0.62, 1.0)
            pal[i] = (int(r * 255), int(g * 255), int(b * 255))
    return pal


class HormigaLangton:
    def __init__(self, size=(1300, 820)):
        self.window_w, self.window_h = size
        self.screen = pygame.display.set_mode(size, pygame.RESIZABLE)
        pygame.display.set_caption("Hormiga de Langton")
        self.fullscreen = False
        self._win_size = size

        self.grid = bytearray(GRID_W * GRID_H)
        self.ants = []
        self.preset_idx = 0
        self._aplicar_regla(PRESETS[0][0], reiniciar=True)

        self.turbo = False
        self.speed_idx = 0          # mínimo: 1 paso/segundo
        self.is_running = False     # empieza en PAUSA (más fácil de entender)
        self._acc = 0.0             # acumulador de pasos (simulación por tiempo)

        self.zoom_idx = 0           # 1.0 = mundo completo visible
        self.pan_x = 0.0
        self.pan_y = 0.0
        self._actualizar_cell()
        self._centrar()

        self.dragging = False
        self.last_drag = None
        self.buttons = {}
        self.hover = None

    # ---------------- reglas / estado ----------------
    def _aplicar_regla(self, regla, reiniciar=False):
        self.regla = regla
        self.k = len(regla)
        self.turn = [GIRO.get(c, 0) for c in regla]
        self.nxt = [(s + 1) % self.k for s in range(self.k)]
        self.paleta = hacer_paleta(self.k)
        if reiniciar:
            self.reiniciar()

    def reiniciar(self):
        for i in range(len(self.grid)):
            self.grid[i] = 0
        self.ants = [[GRID_W // 2, GRID_H // 2, 0]]
        self.steps = 0
        self.is_running = False
        self._acc = 0.0

    def limpiar(self):
        for i in range(len(self.grid)):
            self.grid[i] = 0
        self.steps = 0

    def _centro_vista_grid(self):
        vw, vh = self.view_size()
        ox = MARGIN + self.pan_x
        oy = MARGIN + self.pan_y
        gx = int((vw / 2 - ox) // self.cell)
        gy = int((vh / 2 - oy) // self.cell)
        return max(0, min(GRID_W - 1, gx)), max(0, min(GRID_H - 1, gy))

    def anadir_hormiga(self):
        gx, gy = self._centro_vista_grid()     # aparece donde estás mirando
        self.ants.append([gx, gy, random.randrange(4)])

    def quitar_hormiga(self):
        if len(self.ants) > 1:                 # deja siempre al menos una
            self.ants.pop()

    def cambiar_regla(self, delta):
        self.preset_idx = (self.preset_idx + delta) % len(PRESETS)
        self._aplicar_regla(PRESETS[self.preset_idx][0], reiniciar=True)

    # ---------------- simulación (bucle rápido) ----------------
    def paso(self, n):
        g = self.grid
        W, H = GRID_W, GRID_H
        turn = self.turn
        nxt = self.nxt
        ants = self.ants
        for _ in range(n):
            for a in ants:
                x = a[0]; y = a[1]; d = a[2]
                idx = y * W + x
                s = g[idx]
                d = (d + turn[s]) & 3
                g[idx] = nxt[s]
                if d == 0:                       # arriba
                    if y > 0:
                        y -= 1
                    else:
                        d = 2; y += 1            # rebota (no sale del mundo)
                elif d == 1:                     # derecha
                    if x < W - 1:
                        x += 1
                    else:
                        d = 3; x -= 1
                elif d == 2:                     # abajo
                    if y < H - 1:
                        y += 1
                    else:
                        d = 0; y -= 1
                else:                            # izquierda
                    if x > 0:
                        x -= 1
                    else:
                        d = 1; x += 1
                a[0] = x; a[1] = y; a[2] = d
        self.steps += n

    # ---------------- geometría ----------------
    def panel_w(self):
        return max(300, min(400, int(self.window_w * 0.26)))

    def view_size(self):
        return self.window_w - self.panel_w(), self.window_h

    def _fit_cell(self):
        # tamaño de celda con el que el MUNDO completo cabe justo en la vista
        vw, vh = self.view_size()
        return max(1.0, min(vw / GRID_W, vh / GRID_H))

    def _actualizar_cell(self):
        self.cell = max(1, int(self._fit_cell() * ZOOM_FACTORS[self.zoom_idx]))

    def _centrar(self):
        vw, vh = self.view_size()
        if self.ants:
            ax, ay = self.ants[0][0], self.ants[0][1]
        else:
            ax, ay = GRID_W // 2, GRID_H // 2
        self.pan_x = vw / 2 - (ax + 0.5) * self.cell - MARGIN
        self.pan_y = vh / 2 - (ay + 0.5) * self.cell - MARGIN
        self.limitar_pan()

    def limitar_pan(self):
        # el mundo se centra si cabe en la vista; si está acercado, se limita a sus bordes
        vw, vh = self.view_size()
        cw, ch = GRID_W * self.cell, GRID_H * self.cell
        self.pan_x = (vw - cw) / 2 if cw <= vw else max(min(self.pan_x, 0.0), float(vw - cw))
        self.pan_y = (vh - ch) / 2 if ch <= vh else max(min(self.pan_y, 0.0), float(vh - ch))

    def zoom_en(self, pos, acercar):
        old = self.cell
        if acercar and self.zoom_idx < len(ZOOM_FACTORS) - 1:
            self.zoom_idx += 1
        elif not acercar and self.zoom_idx > 0:
            self.zoom_idx -= 1
        self._actualizar_cell()
        if self.cell == old:
            return
        sx, sy = pos
        ox = MARGIN + self.pan_x; oy = MARGIN + self.pan_y
        cellx = (sx - ox) / old
        celly = (sy - oy) / old
        self.pan_x += (sx - ox) - cellx * self.cell
        self.pan_y += (sy - oy) - celly * self.cell
        self.limitar_pan()

    def screen_to_grid(self, sx, sy):
        ox = MARGIN + self.pan_x; oy = MARGIN + self.pan_y
        return int((sx - ox) // self.cell), int((sy - oy) // self.cell)

    # ---------------- iconos vectoriales ----------------
    def _icono(self, cx, cy, tipo):
        s = self.screen
        c = ACCENT
        if tipo == "play":
            pygame.draw.polygon(s, c, [(cx - 6, cy - 8), (cx - 6, cy + 8), (cx + 8, cy)])
        elif tipo == "pause":
            pygame.draw.rect(s, c, (cx - 7, cy - 8, 5, 16))
            pygame.draw.rect(s, c, (cx + 2, cy - 8, 5, 16))
        elif tipo == "step":
            pygame.draw.polygon(s, c, [(cx - 8, cy - 8), (cx - 8, cy + 8), (cx + 3, cy)])
            pygame.draw.rect(s, c, (cx + 5, cy - 9, 3, 18))
        elif tipo == "reset":
            pygame.draw.circle(s, c, (cx, cy), 8, 2)
            pygame.draw.polygon(s, c, [(cx, cy - 11), (cx, cy - 4), (cx + 6, cy - 8)])
        elif tipo == "clear":
            pygame.draw.line(s, c, (cx - 7, cy - 7), (cx + 7, cy + 7), 3)
            pygame.draw.line(s, c, (cx + 7, cy - 7), (cx - 7, cy + 7), 3)
        elif tipo == "zin":
            pygame.draw.circle(s, c, (cx - 2, cy - 2), 7, 2)
            pygame.draw.line(s, c, (cx + 3, cy + 3), (cx + 9, cy + 9), 3)
            pygame.draw.line(s, c, (cx - 2, cy - 5), (cx - 2, cy + 1), 2)
            pygame.draw.line(s, c, (cx - 5, cy - 2), (cx + 1, cy - 2), 2)
        elif tipo == "zout":
            pygame.draw.circle(s, c, (cx - 2, cy - 2), 7, 2)
            pygame.draw.line(s, c, (cx + 3, cy + 3), (cx + 9, cy + 9), 3)
            pygame.draw.line(s, c, (cx - 5, cy - 2), (cx + 1, cy - 2), 2)
        elif tipo == "slow":
            pygame.draw.polygon(s, c, [(cx + 3, cy - 7), (cx + 3, cy + 7), (cx - 5, cy)])
            pygame.draw.rect(s, c, (cx + 4, cy - 7, 3, 14))
        elif tipo in ("fast", "turbo"):
            pygame.draw.polygon(s, c, [(cx - 8, cy - 7), (cx - 8, cy + 7), (cx - 1, cy)])
            pygame.draw.polygon(s, c, [(cx - 1, cy - 7), (cx - 1, cy + 7), (cx + 6, cy)])
        elif tipo == "ant":
            pygame.draw.polygon(s, ANT_COLOR, [(cx, cy - 7), (cx - 6, cy + 6), (cx + 6, cy + 6)])
        elif tipo == "antdel":
            pygame.draw.polygon(s, ANT_COLOR, [(cx - 7, cy - 6), (cx + 7, cy - 6), (cx, cy + 7)])
        elif tipo == "prev":
            pygame.draw.polygon(s, c, [(cx + 5, cy - 7), (cx + 5, cy + 7), (cx - 5, cy)])
        elif tipo == "next":
            pygame.draw.polygon(s, c, [(cx - 5, cy - 7), (cx - 5, cy + 7), (cx + 5, cy)])
        elif tipo == "help":
            t = MED_FONT.render("?", True, c)
            s.blit(t, (cx - t.get_width() // 2, cy - t.get_height() // 2))
        elif tipo == "plus":
            pygame.draw.line(s, c, (cx - 8, cy), (cx + 8, cy), 3)
            pygame.draw.line(s, c, (cx, cy - 8), (cx, cy + 8), 3)
        elif tipo == "minus":
            pygame.draw.line(s, c, (cx - 8, cy), (cx + 8, cy), 3)
        elif tipo == "target":
            pygame.draw.circle(s, c, (cx, cy), 7, 2)
            pygame.draw.circle(s, c, (cx, cy), 2, 0)
            pygame.draw.line(s, c, (cx - 11, cy), (cx - 5, cy), 2)
            pygame.draw.line(s, c, (cx + 5, cy), (cx + 11, cy), 2)
            pygame.draw.line(s, c, (cx, cy - 11), (cx, cy - 5), 2)
            pygame.draw.line(s, c, (cx, cy + 5), (cx, cy + 11), 2)
        elif tipo == "expand":
            pygame.draw.rect(s, c, (cx - 8, cy - 6, 16, 12), 2)
            pygame.draw.line(s, c, (cx - 8, cy - 2), (cx - 8, cy + 6), 2)

    # ---------------- dibujo ----------------
    def dibujar(self):
        self.screen.fill(BG)
        vw, vh = self.view_size()
        area = pygame.Rect(0, 0, vw, vh)
        pygame.draw.rect(self.screen, GRID_BG, area)

        arr = np.frombuffer(self.grid, dtype=np.uint8).reshape(GRID_H, GRID_W)
        rgb = self.paleta[arr]
        base = pygame.image.frombuffer(rgb.tobytes(), (GRID_W, GRID_H), "RGB")

        cs = self.cell
        ox = MARGIN + self.pan_x; oy = MARGIN + self.pan_y
        gx0 = max(0, int((0 - ox) // cs)); gx1 = min(GRID_W, int((vw - ox) // cs) + 1)
        gy0 = max(0, int((0 - oy) // cs)); gy1 = min(GRID_H, int((vh - oy) // cs) + 1)

        self.screen.set_clip(area)
        if gx1 > gx0 and gy1 > gy0:
            sub = base.subsurface(pygame.Rect(gx0, gy0, gx1 - gx0, gy1 - gy0))
            escalada = pygame.transform.scale(sub, ((gx1 - gx0) * cs, (gy1 - gy0) * cs))
            self.screen.blit(escalada, (int(ox + gx0 * cs), int(oy + gy0 * cs)))
            for a in self.ants:
                if gx0 <= a[0] < gx1 and gy0 <= a[1] < gy1:
                    self._dibujar_hormiga(int(ox + a[0] * cs), int(oy + a[1] * cs), cs, a[2])
        self.screen.set_clip(None)

        self._dibujar_panel(int(np.count_nonzero(arr)))
        self._controles_mapa()
        pygame.display.flip()

    def _dibujar_hormiga(self, sx, sy, cs, d):
        cx, cy = sx + cs / 2, sy + cs / 2
        s = max(3, cs * 0.42)
        if d == 0:
            pts = [(cx, cy - s), (cx - s, cy + s), (cx + s, cy + s)]
        elif d == 1:
            pts = [(cx + s, cy), (cx - s, cy - s), (cx - s, cy + s)]
        elif d == 2:
            pts = [(cx, cy + s), (cx - s, cy - s), (cx + s, cy - s)]
        else:
            pts = [(cx - s, cy), (cx + s, cy - s), (cx + s, cy + s)]
        pygame.draw.polygon(self.screen, ANT_COLOR, pts)

    def _boton(self, rect, label, name, icon=None):
        col = BTN_HOVER if self.hover == name else BTN_BG
        pygame.draw.rect(self.screen, col, rect, border_radius=8)
        pygame.draw.rect(self.screen, BTN_BORDER, rect, 1, border_radius=8)
        cy = rect.y + rect.h // 2
        if icon:
            self._icono(rect.x + 17, cy, icon)
            t = SMALL_FONT.render(label, True, TXT)
            self.screen.blit(t, (rect.x + 32, cy - t.get_height() // 2))
        else:
            t = SMALL_FONT.render(label, True, TXT)
            self.screen.blit(t, (rect.x + (rect.w - t.get_width()) // 2,
                                 cy - t.get_height() // 2))
        self.buttons[name] = rect

    def _boton_mapa(self, rect, name, tipo):
        col = BTN_HOVER if self.hover == name else (26, 32, 46)
        pygame.draw.rect(self.screen, col, rect, border_radius=10)
        pygame.draw.rect(self.screen, BTN_BORDER, rect, 1, border_radius=10)
        self._icono(rect.centerx, rect.centery, tipo)
        self.buttons[name] = rect

    def _controles_mapa(self):
        # controles flotantes tipo mapa, abajo a la derecha del visualizador
        vw, vh = self.view_size()
        sz, gap, m = 44, 8, 18
        x = vw - sz - m
        yb = vh - sz - m
        self._boton_mapa(pygame.Rect(x, yb, sz, sz), "center", "target")
        self._boton_mapa(pygame.Rect(x, yb - (sz + gap), sz, sz), "zoom_out", "minus")
        self._boton_mapa(pygame.Rect(x, yb - 2 * (sz + gap), sz, sz), "zoom_in", "plus")

    def _dibujar_panel(self, vivas):
        pw = self.panel_w()
        px = self.window_w - pw
        panel = pygame.Rect(px, 0, pw, self.window_h)
        pygame.draw.rect(self.screen, PANEL_BG, panel)
        pygame.draw.line(self.screen, PANEL_LINE, (px, 0), (px, self.window_h), 1)

        self.buttons = {}
        mx = px + 18
        bw = pw - 36
        y = 18
        self.screen.blit(TITLE_FONT.render("Hormiga de Langton", True, TXT), (mx, y))
        y += 34
        self.screen.blit(SMALL_FONT.render(f"Regla {self.regla}  ·  {self.k} colores",
                                           True, ACCENT), (mx, y))
        y += 20
        self.screen.blit(SMALL_FONT.render(PRESETS[self.preset_idx][1], True, MUTED), (mx, y))
        y += 30

        bh = 38; gap = 9; hw = bw // 2 - 5
        self._boton(pygame.Rect(mx, y, hw, bh),
                    "Pausa" if self.is_running else "Play",
                    "play", "pause" if self.is_running else "play")
        self._boton(pygame.Rect(mx + hw + 10, y, hw, bh), "Paso", "step", "step")
        y += bh + gap
        self._boton(pygame.Rect(mx, y, hw, bh), "Reiniciar", "reset", "reset")
        self._boton(pygame.Rect(mx + hw + 10, y, hw, bh), "Limpiar", "clear", "clear")
        y += bh + gap
        self.screen.blit(SMALL_FONT.render("Regla", True, MUTED), (mx, y)); y += 20
        self._boton(pygame.Rect(mx, y, hw, bh), "Anterior", "regla_prev", "prev")
        self._boton(pygame.Rect(mx + hw + 10, y, hw, bh), "Siguiente", "regla_next", "next")
        y += bh + gap
        # velocidad (niveles) + Turbo aparte (interruptor)
        if self.turbo:
            vel = "TURBO (máx.)"
        else:
            n = SPEEDS[self.speed_idx]
            vel = f"{n:,} paso{'' if n == 1 else 's'}/segundo"
        self.screen.blit(SMALL_FONT.render("Velocidad: " + vel, True, MUTED), (mx, y))
        y += 20
        self._boton(pygame.Rect(mx, y, hw, bh), "Lento", "slower", "slow")
        self._boton(pygame.Rect(mx + hw + 10, y, hw, bh), "Rápido", "faster", "fast")
        y += bh + gap
        self._boton(pygame.Rect(mx, y, bw, bh),
                    "Turbo: ACTIVADO" if self.turbo else "Turbo (máx. velocidad)",
                    "turbo", "turbo")
        y += bh + gap + 4

        # hormigas: añadir / quitar
        self.screen.blit(SMALL_FONT.render(f"Hormigas: {len(self.ants)}", True, MUTED), (mx, y))
        y += 20
        self._boton(pygame.Rect(mx, y, hw, bh), "Añadir", "add_ant", "ant")
        self._boton(pygame.Rect(mx + hw + 10, y, hw, bh), "Quitar", "del_ant", "antdel")
        y += bh + gap + 4

        self._stat_box(pygame.Rect(mx, y, hw, 56), f"{self.steps:,}", "Pasos")
        self._stat_box(pygame.Rect(mx + hw + 10, y, hw, 56), f"{vivas:,}", "Celdas")
        y += 56 + gap
        fase = "CAÓTICA" if self.steps < 500 else ("REPETITIVA" if self.steps < 10000 else "AUTOPISTA")
        self.screen.blit(SMALL_FONT.render(f"Fase: {fase}", True, ACCENT), (mx, y))
        self.screen.blit(SMALL_FONT.render(
            "Estado: " + ("EJECUTANDO" if self.is_running else "PAUSADO"),
            True, MUTED), (mx, y + 20))

        # opción extra: pantalla completa, justo encima de la ayuda
        self._boton(pygame.Rect(mx, self.window_h - 54 - 48, bw, 40),
                    "Salir de pantalla completa (Esc)" if self.fullscreen else "Pantalla completa (F)",
                    "fullscreen", "expand")
        self._boton(pygame.Rect(mx, self.window_h - 54, bw, 40),
                    "Explicación y controles", "help", "help")

    def _stat_box(self, rect, valor, etq):
        pygame.draw.rect(self.screen, BTN_BG, rect, border_radius=8)
        pygame.draw.rect(self.screen, PANEL_LINE, rect, 1, border_radius=8)
        v = MED_FONT.render(valor, True, ACCENT)
        self.screen.blit(v, (rect.x + (rect.w - v.get_width()) // 2, rect.y + 8))
        e = SMALL_FONT.render(etq, True, MUTED)
        self.screen.blit(e, (rect.x + (rect.w - e.get_width()) // 2, rect.y + 32))

    # ---------------- acciones ----------------
    def accion(self, name):
        if name == "play":
            self.is_running = not self.is_running
        elif name == "step":
            self.is_running = False
            self.paso(1)
        elif name == "reset":
            self.reiniciar()
        elif name == "clear":
            self.limpiar()
        elif name == "regla_prev":
            self.cambiar_regla(-1)
        elif name == "regla_next":
            self.cambiar_regla(1)
        elif name == "zoom_in":
            self.zoom_en((self.view_size()[0] // 2, self.window_h // 2), True)
        elif name == "zoom_out":
            self.zoom_en((self.view_size()[0] // 2, self.window_h // 2), False)
        elif name == "center":
            self.centrar_vista()
        elif name == "fullscreen":
            self.alternar_fullscreen()
        elif name == "slower":
            self.speed_idx = max(0, self.speed_idx - 1)
        elif name == "faster":
            self.speed_idx = min(len(SPEEDS) - 1, self.speed_idx + 1)
        elif name == "turbo":
            self.turbo = not self.turbo
        elif name == "add_ant":
            self.anadir_hormiga()
        elif name == "del_ant":
            self.quitar_hormiga()
        elif name == "help":
            self.ayuda()

    # ---------------- eventos ----------------
    def _aplicar_pantalla(self, screen):
        # cambia la superficie manteniendo centrado lo que estabas viendo
        ovw, ovh = self.view_size()
        ox = MARGIN + self.pan_x; oy = MARGIN + self.pan_y
        cgx = (ovw / 2 - ox) / self.cell
        cgy = (ovh / 2 - oy) / self.cell
        self.screen = screen
        self.window_w, self.window_h = screen.get_size()
        self._actualizar_cell()
        nvw, nvh = self.view_size()
        self.pan_x = nvw / 2 - cgx * self.cell - MARGIN
        self.pan_y = nvh / 2 - cgy * self.cell - MARGIN
        self.limitar_pan()

    def alternar_fullscreen(self):
        if self.fullscreen:
            self.fullscreen = False
            self._aplicar_pantalla(pygame.display.set_mode(self._win_size, pygame.RESIZABLE))
        else:
            self._win_size = (self.window_w, self.window_h)
            self.fullscreen = True
            self._aplicar_pantalla(pygame.display.set_mode((0, 0), pygame.FULLSCREEN))

    def centrar_vista(self):
        self._centrar()

    def evento(self, e):
        if e.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        elif e.type == pygame.VIDEORESIZE:
            if not self.fullscreen:
                self._aplicar_pantalla(pygame.display.set_mode((e.w, e.h), pygame.RESIZABLE))
        elif e.type == pygame.MOUSEMOTION:
            self.hover = None
            for n, r in self.buttons.items():
                if r.collidepoint(e.pos):
                    self.hover = n; break
            if self.dragging:
                x, y = e.pos; lx, ly = self.last_drag
                self.pan_x += x - lx; self.pan_y += y - ly
                self.last_drag = e.pos; self.limitar_pan()
        elif e.type == pygame.MOUSEBUTTONDOWN:
            mx, my = e.pos
            if e.button == 1:
                for n, r in self.buttons.items():
                    if r.collidepoint(mx, my):
                        self.accion(n); return
                if mx < self.view_size()[0]:
                    gx, gy = self.screen_to_grid(mx, my)
                    if 0 <= gx < GRID_W and 0 <= gy < GRID_H:
                        i = gy * GRID_W + gx
                        self.grid[i] = 1 if self.grid[i] == 0 else 0
            elif e.button == 3:
                self.dragging = True; self.last_drag = e.pos
            elif e.button == 4:
                self.zoom_en(e.pos, True)
            elif e.button == 5:
                self.zoom_en(e.pos, False)
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 3:
            self.dragging = False
        elif e.type == pygame.MOUSEWHEEL:
            mx, my = pygame.mouse.get_pos()
            if mx < self.view_size()[0]:
                self.zoom_en((mx, my), e.y > 0)
        elif e.type == pygame.KEYDOWN:
            if e.key == pygame.K_SPACE:
                self.is_running = not self.is_running
            elif e.key == pygame.K_f:
                self.alternar_fullscreen()
            elif e.key == pygame.K_ESCAPE:
                if self.fullscreen:
                    self.alternar_fullscreen()
            elif e.key == pygame.K_RIGHT:
                self.is_running = False; self.paso(1)
            elif e.key == pygame.K_r:
                self.reiniciar()
            elif e.key == pygame.K_c:
                self.limpiar()
            elif e.key == pygame.K_t:
                self.turbo = not self.turbo
            elif e.key == pygame.K_a:
                if e.mod & pygame.KMOD_SHIFT:
                    self.quitar_hormiga()
                else:
                    self.anadir_hormiga()
            elif e.key == pygame.K_h:
                self.ayuda()
            elif e.key == pygame.K_PERIOD:
                self.cambiar_regla(1)
            elif e.key == pygame.K_COMMA:
                self.cambiar_regla(-1)
            elif e.key in (pygame.K_PLUS, pygame.K_EQUALS):
                self.speed_idx = min(len(SPEEDS) - 1, self.speed_idx + 1)
            elif e.key in (pygame.K_MINUS, pygame.K_UNDERSCORE):
                self.speed_idx = max(0, self.speed_idx - 1)

    # ---------------- ayuda ----------------
    def ayuda(self):
        L = [
            ("HORMIGA DE LANGTON", True),
            ("", False),
            ("Un autómata celular: reglas simples, comportamiento complejo.", False),
            ("Creado por Chris Langton (1986).", False),
            ("", False),
            ("Regla clásica (RL):", False),
            ("• Celda apagada → gira DERECHA, se enciende y avanza.", False),
            ("• Celda encendida → gira IZQUIERDA, se apaga y avanza.", False),
            ("Tras ~10.000 pasos emerge una 'autopista' periódica.", False),
            ("", False),
            ("Reglas generalizadas (turmites):", False),
            ("Cada letra (L/R) define el giro en cada color; el color", False),
            ("avanza cíclicamente. Más colores = más patrones.", False),
            ("Cambia de regla con , y . o los botones.", False),
            ("", False),
            ("CONTROLES:", False),
            ("• Clic izq: encender/apagar celda", False),
            ("• Clic der + arrastrar: mover · Rueda: zoom", False),
            ("• Espacio: play/pausa · →: un paso · R: reiniciar", False),
            ("• C: limpiar · T: turbo · F: pantalla completa", False),
            ("• A: añadir hormiga · Shift+A: quitar hormiga", False),
            ("• , .: cambiar regla · +/-: velocidad · H: ayuda", False),
            ("", False),
            ("(Clic o cualquier tecla para cerrar)", False),
        ]
        mw = min(self.window_w - 120, 760)
        mh = min(self.window_h - 120, 620)
        overlay = pygame.Surface((self.window_w, self.window_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        modal = pygame.Rect((self.window_w - mw) // 2, (self.window_h - mh) // 2, mw, mh)
        while True:
            self.screen.blit(overlay, (0, 0))
            pygame.draw.rect(self.screen, (30, 34, 46), modal, border_radius=14)
            pygame.draw.rect(self.screen, (70, 84, 108), modal, 2, border_radius=14)
            y = modal.y + 26
            for txt, es_tit in L:
                f = TITLE_FONT if es_tit else SMALL_FONT
                self.screen.blit(f.render(txt, True, ACCENT if es_tit else TXT),
                                 (modal.x + 26, y))
                y += (30 if es_tit else 23)
            pygame.display.flip()
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    return

    # ---------------- loop ----------------
    def run(self):
        clock = pygame.time.Clock()
        while True:
            dt = clock.tick(FPS) / 1000.0
            for e in pygame.event.get():
                self.evento(e)
            if self.is_running:
                if self.turbo:
                    self.paso(TURBO_FRAME)
                else:
                    # pasos por SEGUNDO reales, independientes de los FPS
                    self._acc += SPEEDS[self.speed_idx] * dt
                    n = int(self._acc + 1e-9)
                    if n > 0:
                        self._acc -= n
                        self.paso(n)
            self.dibujar()


if __name__ == "__main__":
    HormigaLangton().run()
