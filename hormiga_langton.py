import os
import sys
import time
import pygame
import numpy as np

# ---------------- Inicialización ----------------
pygame.init()
pygame.font.init()

# ---------------- Config & Colores ----------------
BLACK = (12, 14, 20)
WHITE = (240, 244, 248)
PANEL_BG = (28, 36, 48)
PANEL_ACCENT = (72, 148, 200)
ACCENT = (245, 200, 80)
BTN_BG = (36, 46, 60)
BTN_BORDER = (120, 130, 140)
GRID_BG = (18, 22, 30)
GRID_LINE = (40, 48, 60)
CELL_COLOR = (100, 220, 160)
ANT_COLOR = (255, 140, 60)
HELP_BG = (30, 30, 40)

BASE_CELL_SIZE = 8
GRID_W = 120
GRID_H = 100
ZOOM_LEVELS = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0]
FPS = 60

# Fuentes
TITLE_FONT = pygame.font.SysFont('Segoe UI', 26, bold=True)
MED_FONT = pygame.font.SysFont('Segoe UI', 16, bold=True)
SMALL_FONT = pygame.font.SysFont('Segoe UI', 15)

# Ruta de la imagen subida (se usará si existe)
LOGO_PATH = "/mnt/data/cb1011a1-b921-4581-af88-8ceb1fc72800.png"

# ---------------- Clase principal ----------------
class LangtonsAntApp:
    def __init__(self, window_size=(1300, 820)):
        self.window_w, self.window_h = window_size
        self.screen = pygame.display.set_mode((self.window_w, self.window_h), pygame.RESIZABLE)
        pygame.display.set_caption("Hormiga de Langton - Viewport (Clip)")

        # Estado lógico
        self.grid = np.zeros((GRID_H, GRID_W), dtype=np.uint8)
        self.ant = {'x': GRID_W // 2, 'y': GRID_H // 2, 'dir': 0}
        self.is_running = False
        self.speed = 5  # 1..10
        self.steps = 0

        # Zoom & cell size
        self.zoom_idx = 2  # start at 1.0
        self.cell_size = max(1, int(BASE_CELL_SIZE * ZOOM_LEVELS[self.zoom_idx]))

        # Canvas overall pixel size
        self.canvas_w = GRID_W * self.cell_size
        self.canvas_h = GRID_H * self.cell_size

        # Pan / drag
        self.pan_x = 0
        self.pan_y = 0
        self.dragging = False
        self.last_drag_pos = None

        # Timing
        self.last_update = time.time()

        # Buttons rects (recalculated every draw)
        self.buttons = {}

        # Optional logo
        self.logo = None
        if os.path.exists(LOGO_PATH):
            try:
                img = pygame.image.load(LOGO_PATH)
                maxw = 240
                scale = maxw / img.get_width()
                new_h = int(img.get_height() * scale)
                self.logo = pygame.transform.smoothscale(img, (maxw, new_h))
            except Exception:
                self.logo = None

    # ---------------- Utilidades ----------------
    def controls_width(self):
        # Panel lateral responsivo: ocupa ~28% ancho, mínimo 300, máximo 420
        w = int(self.window_w * 0.28)
        return max(300, min(420, w))

    def update_sizes(self):
        self.cell_size = max(1, int(BASE_CELL_SIZE * ZOOM_LEVELS[self.zoom_idx]))
        self.canvas_w = GRID_W * self.cell_size
        self.canvas_h = GRID_H * self.cell_size
        self.limit_pan()

    def limit_pan(self):
        view_w = self.window_w - self.controls_width()
        view_h = self.window_h
        min_x = min(0, view_w - self.canvas_w - 20)
        max_x = 20
        min_y = min(0, view_h - self.canvas_h - 20)
        max_y = 20
        self.pan_x = max(min(self.pan_x, max_x), min_x)
        self.pan_y = max(min(self.pan_y, max_y), min_y)

    # ---------------- Reglas ----------------
    def move_ant_step(self):
        x, y = self.ant['x'], self.ant['y']
        if self.grid[y, x] == 0:
            self.ant['dir'] = (self.ant['dir'] + 1) % 4
            self.grid[y, x] = 1
        else:
            self.ant['dir'] = (self.ant['dir'] - 1) % 4
            self.grid[y, x] = 0

        # avanzar con wrap-around
        if self.ant['dir'] == 0:
            self.ant['y'] = (self.ant['y'] - 1) % GRID_H
        elif self.ant['dir'] == 1:
            self.ant['x'] = (self.ant['x'] + 1) % GRID_W
        elif self.ant['dir'] == 2:
            self.ant['y'] = (self.ant['y'] + 1) % GRID_H
        else:
            self.ant['x'] = (self.ant['x'] - 1) % GRID_W

    # ---------------- Coordenadas ----------------
    def screen_to_grid(self, sx, sy):
        # canvas origin = (20 + pan_x, 20 + pan_y)
        canvas_x = 20 + int(self.pan_x)
        canvas_y = 20 + int(self.pan_y)
        gx = (sx - canvas_x) // self.cell_size
        gy = (sy - canvas_y) // self.cell_size
        return int(gx), int(gy)

    # ---------------- Zoom (centrado) ----------------
    def zoom_at(self, screen_pos, zoom_in=True):
        old_cell_size = self.cell_size
        old_idx = self.zoom_idx
        if zoom_in and self.zoom_idx < len(ZOOM_LEVELS) - 1:
            self.zoom_idx += 1
        elif not zoom_in and self.zoom_idx > 0:
            self.zoom_idx -= 1
        if self.zoom_idx == old_idx:
            return
        self.update_sizes()
        sx, sy = screen_pos
        # ajustar pan para mantener la celda bajo el mouse
        canvas_x = 20 + self.pan_x
        canvas_y = 20 + self.pan_y
        rel_x = sx - canvas_x
        rel_y = sy - canvas_y
        if rel_x < 0 or rel_y < 0:
            return
        cell_x = rel_x / old_cell_size
        cell_y = rel_y / old_cell_size
        new_rel_x = cell_x * self.cell_size
        new_rel_y = cell_y * self.cell_size
        self.pan_x += (rel_x - new_rel_x)
        self.pan_y += (rel_y - new_rel_y)
        self.limit_pan()

    # ---------------- Dibujo de la hormiga ----------------
    def draw_ant_icon(self, surface, cell_x, cell_y, cs):
        center_x = cell_x * cs + cs // 2
        center_y = cell_y * cs + cs // 2
        size = max(2, cs // 2)
        if self.ant['dir'] == 0:
            pts = [(center_x, center_y - size), (center_x - size, center_y + size), (center_x + size, center_y + size)]
        elif self.ant['dir'] == 1:
            pts = [(center_x + size, center_y), (center_x - size, center_y - size), (center_x - size, center_y + size)]
        elif self.ant['dir'] == 2:
            pts = [(center_x, center_y + size), (center_x - size, center_y - size), (center_x + size, center_y - size)]
        else:
            pts = [(center_x - size, center_y), (center_x + size, center_y - size), (center_x + size, center_y + size)]
        pygame.draw.polygon(surface, ANT_COLOR, pts)

    # ---------------- Dibujar UI ----------------
    def draw(self):
        # fondo
        self.screen.fill(BLACK)

        cw = self.controls_width()
        panel_rect = pygame.Rect(self.window_w - cw, 0, cw, self.window_h)

        # area del canvas (izquierda). OPCIÓN A: recorte lateral solamente
        canvas_area_rect = pygame.Rect(0, 0, self.window_w - cw, self.window_h)
        pygame.draw.rect(self.screen, GRID_BG, canvas_area_rect)

        # actualizar tamaños según zoom
        self.update_sizes()

        # crear surface para el canvas (rendera la totalidad pero será recortado por set_clip)
        # NOTA: usar tamaño del canvas lógico puede ser grande; aquí lo creamos con canvas_w/canvas_h
        canvas_surf = pygame.Surface((self.canvas_w, self.canvas_h))
        canvas_surf.fill(GRID_BG)

        cs = self.cell_size
        # dibujar celdas vivas
        if cs >= 2:
            ys, xs = np.where(self.grid == 1)
            for yy, xx in zip(ys, xs):
                rect = pygame.Rect(xx * cs, yy * cs, cs, cs)
                pygame.draw.rect(canvas_surf, CELL_COLOR, rect)
        else:
            ys, xs = np.where(self.grid == 1)
            for yy, xx in zip(ys, xs):
                canvas_surf.set_at((xx, yy), CELL_COLOR)

        # dibujar hormiga encima del canvas surface
        self.draw_ant_icon(canvas_surf, self.ant['x'], self.ant['y'], cs)

        # BLIT del canvas en la pantalla con pan y margen de 20px
        canvas_pos = (20 + int(self.pan_x), 20 + int(self.pan_y))

        # USAR CLIP: fijamos el clip al área del canvas (no invade el panel derecho)
        self.screen.set_clip(canvas_area_rect)

        # dibujar el canvas dentro del clipado (si el canvas_surf es más grande que la ventana,
        # blit se recorta automáticamente gracias al clip)
        try:
            self.screen.blit(canvas_surf, canvas_pos)
        except Exception:
            # en caso de que canvas_surf sea demasiado grande en algunas plataformas, escalar temporalmente
            scaled_w = min(canvas_surf.get_width(), canvas_area_rect.width - 40)
            scaled_h = min(canvas_surf.get_height(), canvas_area_rect.height - 40)
            temp = pygame.transform.smoothscale(canvas_surf, (max(1, scaled_w), max(1, scaled_h)))
            self.screen.blit(temp, canvas_pos)

        # dibujar marco de visualización (solo sobre la parte visible)
        visible_w = min(self.canvas_w, canvas_area_rect.width - 40)
        visible_h = min(self.canvas_h, canvas_area_rect.height - 40)
        border_rect = pygame.Rect(canvas_pos[0] - 2, canvas_pos[1] - 2, visible_w + 4, visible_h + 4)

        # desactivar clip — ahora el panel se dibujará encima
        self.screen.set_clip(None)

        # dibujar panel lateral (siempre encima)
        self.draw_panel(panel_rect)

        # swap buffers
        pygame.display.flip()

    def draw_panel(self, panel_rect):
        # fondo del panel
        pygame.draw.rect(self.screen, PANEL_BG, panel_rect)

        # título
        title = TITLE_FONT.render("Hormiga de Langton", True, WHITE)
        self.screen.blit(title, (panel_rect.x + 18, 18))

        # logo si existe
        y_offset = 60
        if self.logo:
            self.screen.blit(self.logo, (panel_rect.x + 18, y_offset))
            y_offset += self.logo.get_height() + 8

        # indicador de zoom debajo del título
        zoom_text = MED_FONT.render(f"Zoom: {ZOOM_LEVELS[self.zoom_idx]:.2f}x", True, PANEL_ACCENT)
        self.screen.blit(zoom_text, (panel_rect.x + 18, y_offset))
        y_offset += 36

        # botones (dibujados como rects; manejados por self.buttons)
        margin_x = panel_rect.x + 18
        cur_y = y_offset
        bw = panel_rect.w - 36
        bh = 38
        gap = 10

        # Play / Pause
        b_play = pygame.Rect(margin_x, cur_y, bw // 2 - 6, bh)
        b_pause = pygame.Rect(margin_x + bw // 2 + 6, cur_y, bw // 2 - 6, bh)
        self.draw_button(self.screen, b_play, "Play", icon_type='play')
        self.draw_button(self.screen, b_pause, "Pause", icon_type='pause')
        cur_y += bh + gap

        # Step / Reset
        b_step = pygame.Rect(margin_x, cur_y, bw // 2 - 6, bh)
        b_reset = pygame.Rect(margin_x + bw // 2 + 6, cur_y, bw // 2 - 6, bh)
        self.draw_button(self.screen, b_step, "Step", icon_type='step')
        self.draw_button(self.screen, b_reset, "Reset", icon_type='reset')
        cur_y += bh + gap

        # Zoom in/out
        z_label = SMALL_FONT.render("Zoom", True, WHITE)
        self.screen.blit(z_label, (margin_x, cur_y))
        cur_y += 22
        b_zoom_in = pygame.Rect(margin_x, cur_y, bw // 2 - 6, bh)
        b_zoom_out = pygame.Rect(margin_x + bw // 2 + 6, cur_y, bw // 2 - 6, bh)
        self.draw_button(self.screen, b_zoom_in, "+", icon_type='zoom_in')
        self.draw_button(self.screen, b_zoom_out, "-", icon_type='zoom_out')
        cur_y += bh + gap

        # Speed
        s_label = SMALL_FONT.render("Velocidad", True, WHITE)
        self.screen.blit(s_label, (margin_x, cur_y))
        cur_y += 22
        b_faster = pygame.Rect(margin_x, cur_y, bw // 2 - 6, bh)
        b_slower = pygame.Rect(margin_x + bw // 2 + 6, cur_y, bw // 2 - 6, bh)
        self.draw_button(self.screen, b_faster, "Más rápido", icon_type='faster')
        self.draw_button(self.screen, b_slower, "Más lento", icon_type='slower')
        cur_y += bh + gap

        # Stats boxes
        sb_h = 64
        sb_w = (bw - gap) // 2
        sbox1 = pygame.Rect(margin_x, cur_y, sb_w, sb_h)
        sbox2 = pygame.Rect(margin_x + sb_w + gap, cur_y, sb_w, sb_h)
        pygame.draw.rect(self.screen, PANEL_ACCENT, sbox1, border_radius=8)
        pygame.draw.rect(self.screen, PANEL_ACCENT, sbox2, border_radius=8)
        steps_text = MED_FONT.render(f"{self.steps:,}", True, ACCENT)
        self.screen.blit(steps_text, (sbox1.x + (sbox1.w - steps_text.get_width()) // 2, sbox1.y + 10))
        steps_label = SMALL_FONT.render("Pasos", True, WHITE)
        self.screen.blit(steps_label, (sbox1.x + (sbox1.w - steps_label.get_width()) // 2, sbox1.y + 38))
        speed_text = MED_FONT.render(f"{self.speed}/10", True, ACCENT)
        self.screen.blit(speed_text, (sbox2.x + (sbox2.w - speed_text.get_width()) // 2, sbox2.y + 10))
        speed_label = SMALL_FONT.render("Velocidad", True, WHITE)
        self.screen.blit(speed_label, (sbox2.x + (sbox2.w - speed_label.get_width()) // 2, sbox2.y + 38))
        cur_y += sb_h + gap

        # Estado y dirección
        st_label = SMALL_FONT.render("Estado: " + ("EJECUTANDO" if self.is_running else "PAUSADO"), True, WHITE)
        self.screen.blit(st_label, (margin_x, cur_y))
        dir_names = ["NORTE", "ESTE", "SUR", "OESTE"]
        dir_label = SMALL_FONT.render("Dirección: " + dir_names[self.ant['dir']], True, WHITE)
        self.screen.blit(dir_label, (margin_x, cur_y + 20))
        cur_y += 48

        # Fase actual
        fase = self.get_phase()
        fase_label = SMALL_FONT.render("Fase: " + fase, True, ACCENT)
        self.screen.blit(fase_label, (margin_x, cur_y))
        cur_y += 36

        # Help button abajo
        bh2 = 40
        b_help = pygame.Rect(margin_x, panel_rect.h - bh2 - 20, bw, bh2)
        self.draw_button(self.screen, b_help, "Ver explicación y reglas")
        # registrar botones para manejo de clics
        self.buttons = {
            'play': b_play, 'pause': b_pause, 'step': b_step, 'reset': b_reset,
            'zoom_in': b_zoom_in, 'zoom_out': b_zoom_out, 'faster': b_faster, 'slower': b_slower,
            'help': b_help
        }

    def draw_button(self, surface, rect, label, icon_type=None):
        pygame.draw.rect(surface, BTN_BG, rect, border_radius=8)
        pygame.draw.rect(surface, BTN_BORDER, rect, 2, border_radius=8)
        if icon_type:
            ix = rect.x + 10
            cy = rect.y + rect.h // 2
            if icon_type == 'play':
                pts = [(ix, cy - 8), (ix, cy + 8), (ix + 14, cy)]
                pygame.draw.polygon(surface, ACCENT, pts)
            elif icon_type == 'pause':
                pygame.draw.rect(surface, ACCENT, (ix, cy - 8, 5, 16))
                pygame.draw.rect(surface, ACCENT, (ix + 8, cy - 8, 5, 16))
            elif icon_type == 'step':
                pygame.draw.polygon(surface, ACCENT, [(ix, cy - 8), (ix, cy + 8), (ix + 10, cy)])
                pygame.draw.rect(surface, ACCENT, (ix + 12, cy - 10, 2, 20))
            elif icon_type == 'reset':
                pygame.draw.circle(surface, ACCENT, (ix + 8, cy), 9, 2)
                pygame.draw.polygon(surface, ACCENT, [(ix + 8, cy - 9), (ix + 8, cy - 3), (ix + 12, cy - 3)])
            elif icon_type == 'zoom_in':
                pygame.draw.circle(surface, ACCENT, (ix + 8, cy), 7, 2)
                pygame.draw.line(surface, ACCENT, (ix + 8, cy - 3), (ix + 8, cy + 3), 2)
                pygame.draw.line(surface, ACCENT, (ix + 5, cy), (ix + 11, cy), 2)
            elif icon_type == 'zoom_out':
                pygame.draw.circle(surface, ACCENT, (ix + 8, cy), 7, 2)
                pygame.draw.line(surface, ACCENT, (ix + 5, cy), (ix + 11, cy), 2)
            elif icon_type == 'faster':
                pygame.draw.polygon(surface, ACCENT, [(ix, cy+8), (ix+10, cy), (ix, cy-8)])
                pygame.draw.polygon(surface, ACCENT, [(ix+8, cy+8), (ix+18, cy), (ix+8, cy-8)])
            elif icon_type == 'slower':
                pygame.draw.polygon(surface, ACCENT, [(ix+18, cy+8), (ix+8, cy), (ix+18, cy-8)])
            text_surf = SMALL_FONT.render(label, True, WHITE)
            surface.blit(text_surf, (rect.x + 44, rect.y + (rect.h - text_surf.get_height()) // 2))
        else:
            text_surf = SMALL_FONT.render(label, True, WHITE)
            surface.blit(text_surf, (rect.x + (rect.w - text_surf.get_width()) // 2,
                                     rect.y + (rect.h - text_surf.get_height()) // 2))

    def get_phase(self):
        if self.steps < 500:
            return "CAÓTICA"
        elif self.steps < 10000:
            return "REPETITIVA"
        else:
            return "CARRERA ESTABLE"

    # ---------------- Eventos ----------------
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        elif event.type == pygame.VIDEORESIZE:
            self.window_w, self.window_h = event.w, event.h
            self.screen = pygame.display.set_mode((self.window_w, self.window_h), pygame.RESIZABLE)
            self.limit_pan()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # click izquierdo
                mx, my = event.pos
                # comprobar botones en panel
                for name, rect in self.buttons.items():
                    if rect.collidepoint(mx, my):
                        self.handle_action(name)
                        return
                # si clic en canvas, alternar celda
                if mx < self.window_w - self.controls_width():
                    gx, gy = self.screen_to_grid(mx, my)
                    if 0 <= gx < GRID_W and 0 <= gy < GRID_H:
                        self.grid[gy, gx] ^= 1
            elif event.button == 3:  # click derecho -> comenzar drag pan
                self.dragging = True
                self.last_drag_pos = event.pos
            # ruedas (compatibilidad)
            elif event.button == 4:  # rueda arriba
                self.zoom_at(event.pos, zoom_in=True)
            elif event.button == 5:  # rueda abajo
                self.zoom_at(event.pos, zoom_in=False)

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 3:
                self.dragging = False
                self.last_drag_pos = None

        elif event.type == pygame.MOUSEMOTION and self.dragging:
            x, y = event.pos
            lx, ly = self.last_drag_pos
            dx, dy = x - lx, y - ly
            self.pan_x += dx
            self.pan_y += dy
            self.limit_pan()
            self.last_drag_pos = (x, y)

        elif event.type == pygame.MOUSEWHEEL:
            # evento moderno de rueda
            mx, my = pygame.mouse.get_pos()
            if mx < self.window_w - self.controls_width():
                if event.y > 0:
                    self.zoom_at((mx, my), zoom_in=True)
                else:
                    self.zoom_at((mx, my), zoom_in=False)

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.is_running = not self.is_running
            elif event.key == pygame.K_RIGHT:
                self.move_ant_step()
                self.steps += 1
            elif event.key == pygame.K_r:
                self.reset()
            elif event.key == pygame.K_h:
                # mostrar modal de ayuda (bloqueante)
                self.display_help_modal()
            elif event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                self.speed = min(10, self.speed + 1)
            elif event.key == pygame.K_MINUS or event.key == pygame.K_UNDERSCORE:
                self.speed = max(1, self.speed - 1)

    def handle_action(self, name):
        if name == 'play':
            self.is_running = True
        elif name == 'pause':
            self.is_running = False
        elif name == 'step':
            self.move_ant_step()
            self.steps += 1
        elif name == 'reset':
            self.reset()
        elif name == 'zoom_in':
            self.zoom_at((self.window_w // 2, self.window_h // 2), zoom_in=True)
        elif name == 'zoom_out':
            self.zoom_at((self.window_w // 2, self.window_h // 2), zoom_in=False)
        elif name == 'faster':
            self.speed = min(10, self.speed + 1)
        elif name == 'slower':
            self.speed = max(1, self.speed - 1)
        elif name == 'help':
            self.display_help_modal()

    def display_help_modal(self):
        # Tamaño del modal
        modal_w = min(self.window_w - 160, 820)
        modal_h = min(self.window_h - 160, 640)

        # Fondo oscuro semitransparente
        overlay = pygame.Surface((self.window_w, self.window_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))

        # --- COLOR ÚNICO PARA EL MODAL ---
        MODAL_COLOR = (38, 38, 48)          # fondo
        CONTENT_COLOR = (48, 48, 60)        # contenido scrollable
        BORDER_COLOR = (180, 180, 200)      # borde

        # Crear modal
        modal = pygame.Surface((modal_w, modal_h))
        modal.fill(MODAL_COLOR)
        pygame.draw.rect(modal, BORDER_COLOR, modal.get_rect(), 3, border_radius=12)

        padding = 24
        inner_w = modal_w - padding * 2
        inner_h = modal_h - padding * 2

        # Área scrollable
        content = pygame.Surface((inner_w, 2000))  # lo ajustaremos luego
        content.fill(CONTENT_COLOR)

        # Textos
        L = [
            "HORMIGA DE LANGTON",
            "",
            "¿Qué es?",
            "La Hormiga de Langton es un autómata celular bidimensional",
            "con reglas simples pero comportamiento complejo emergente.",
            "Fue creada por Chris Langton en 1986.",
            "",
            "Reglas simples:",
            "• Celda BLANCA → gira 90° a la DERECHA, se vuelve NEGRA y avanza.",
            "• Celda NEGRA → gira 90° a la IZQUIERDA, se vuelve BLANCA y avanza.",
            "",
            "Comportamiento emergente:",
            "• 0–500 pasos → Fase CAÓTICA.",
            "• 500–10,000 pasos → Fase de patrones repetitivos.",
            "• >10,000 pasos → Fase de “autopista” estable.",
            "",
            "Aplicaciones:",
            "• Computación",
            "• Biología",
            "• Filosofía",
            "",
            "",
            "CONTROLES:",
            "- Click izquierdo: alternar celda",
            "- Click derecho + arrastrar: mover canvas",
            "- Rueda del mouse: zoom",
            "- SPACE: iniciar/pausar",
            "- FLECHA DERECHA: paso manual",
            "- R: reiniciar",
            "- H: abrir/cerrar ayuda",
            "",
            "",
            "El zoom real mantiene fija la celda bajo el puntero mientras ajustas nivel."
        ]

        # Render del texto
        y = 0
        TITLE = pygame.font.SysFont("Segoe UI", 30, bold=True)
        BODY = pygame.font.SysFont("Segoe UI", 20)

        for i, ln in enumerate(L):
            font = TITLE if ln == "HORMIGA DE LANGTON" else BODY
            txt = font.render(ln, True, (230, 230, 240))
            content.blit(txt, (10, y))
            y += txt.get_height() + 10

        # Ajustar alto real del contenido
        real_h = y + 20
        if real_h < content.get_height():
            content = content.subsurface((0, 0, inner_w, real_h))

        scroll_y = 0
        max_scroll = max(0, real_h - inner_h)

        # Posición del modal centrado
        modal_rect = modal.get_rect(center=(self.window_w // 2, self.window_h // 2))

        running_modal = True
        while running_modal:
            self.screen.blit(overlay, (0, 0))

            # Redibujar modal base
            modal.fill(MODAL_COLOR)
            pygame.draw.rect(modal, BORDER_COLOR, modal.get_rect(), 3, border_radius=12)

            # Dibujar contenido scrollable
            modal.blit(content, (padding, padding), pygame.Rect(0, scroll_y, inner_w, inner_h))

            # Dibujar modal en pantalla
            self.screen.blit(modal, modal_rect.topleft)
            pygame.display.flip()

            # Eventos
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit(); sys.exit()

                # Cerrar con clic o tecla
                if e.type == pygame.KEYDOWN:
                    running_modal = False

                if e.type == pygame.MOUSEBUTTONDOWN:
                    if e.button == 1:
                        running_modal = False

                    # Scroll rueda tradicional
                    if e.button == 4: 
                        scroll_y = max(0, scroll_y - 40)
                    if e.button == 5:
                        scroll_y = min(max_scroll, scroll_y + 40)

                # Scroll con eventos modernos
                if e.type == pygame.MOUSEWHEEL:
                    if e.y > 0:
                        scroll_y = max(0, scroll_y - 40)
                    else:
                        scroll_y = min(max_scroll, scroll_y + 40)



    def reset(self):
        self.grid.fill(0)
        self.ant = {'x': GRID_W // 2, 'y': GRID_H // 2, 'dir': 0}
        self.is_running = False
        self.steps = 0
        self.zoom_idx = 2
        self.pan_x = 0
        self.pan_y = 0
        self.update_sizes()

    # ---------------- Loop principal ----------------
    def run(self):
        clock = pygame.time.Clock()
        while True:
            dt = clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                self.handle_event(event)

            # actualizar simulación segun velocidad
            now = time.time()
            period = max(0.02, 1.1 - self.speed * 0.1)
            if self.is_running and (now - self.last_update) >= period:
                self.move_ant_step()
                self.steps += 1
                self.last_update = now

            # dibujar todo
            self.draw()

# ---------------- Ejecutar ----------------
if __name__ == "__main__":
    app = LangtonsAntApp((1300, 820))
    app.run()

