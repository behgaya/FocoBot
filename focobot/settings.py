import pygame
import sys
from focobot import ui

# ------------------------
# BUTTON CLASS (botões com imagem do menu)
# ------------------------
class Button:
    def __init__(self, text, rect, callback, image_path=None, hover_image_path=None, font=None, show_text=True):
        self.text = text
        self.rect = pygame.Rect(rect)
        self.callback = callback
        self.font = font or pygame.font.SysFont("Segoe UI", 36)
        self.show_text = show_text

        # imagens escaladas uma vez para a largura do botão
        if image_path:
            self.image = ui.load_scaled(image_path, rect[2])
            self.rect.size = self.image.get_size()
        else:
            self.image = None
        self.hover_image = ui.load_scaled(hover_image_path, rect[2]) if hover_image_path else self.image

    def is_hover(self):
        return self.rect.collidepoint(pygame.mouse.get_pos())

    def draw(self, surface):
        is_hover = self.is_hover()
        img_to_draw = self.hover_image if is_hover else self.image

        if img_to_draw:
            surface.blit(img_to_draw, self.rect.topleft)
        else:
            color = (80, 120, 255) if not is_hover else (120, 160, 255)
            pygame.draw.rect(surface, color, self.rect, border_radius=8)

        if self.show_text and self.text:
            txt_surface = self.font.render(self.text, True, (255, 255, 255))
            txt_rect = txt_surface.get_rect(center=self.rect.center)
            surface.blit(txt_surface, txt_rect)

    def check_click(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()


# ------------------------
# CONFIGURATION CLASS
# ------------------------
class GameConfig:
    def __init__(self):
        # FOAC (Missão dos Brinquedos)
        self.foac_snap_radius = 200
        self.foac_objetivos = 3
        self.foac_fixation_time = 0.8  # ainda não usado pelo jogo
        self.foac_max_blur = 12
        self.foac_object_count = 7     # limitado pelas imagens da pasta de objetos (Bear tem 7)

        # SESE (Resgate Espacial)
        self.sese_snap_radius = 120
        self.sese_asteroid_count = 5
        self.sese_speed = 2
        self.sese_required_look_time = 0.2
        self.sese_object_radius = 40  # ainda não usado pelo jogo

        # SUSE (Aventura Aquática)
        self.suse_num_foods = 5
        self.suse_fish_speed = 2
        self.suse_hit_radius = 30      # margem somada ao raio do peixe
        self.suse_food_spacing = 150
        self.suse_object_size = 30


# ------------------------
# SETTINGS SCREEN
# ------------------------
# Mesma ordem dos botões do menu. "disabled" = opção que o jogo ainda não usa.
SECTIONS = [
    {
        "name": "Resgate Espacial",
        "logo": "Assets/MainMenu/Logo/logo_sese.png",
        "color": (171, 120, 255),
        "options": [
            {"label": "Raio de Encaixe", "attr": "sese_snap_radius", "values": [50, 80, 110, 120, 140, 170, 200, 230, 260, 300], "unit": "px"},
            {"label": "Asteroides", "attr": "sese_asteroid_count", "values": [3, 5, 7]},
            {"label": "Velocidade do Foguete", "attr": "sese_speed", "values": [1, 2, 3, 4]},
            {"label": "Tempo de Olhar", "attr": "sese_required_look_time", "values": [0.2, 0.3, 0.5, 0.8, 1.0, 1.2], "unit": "s"},
            {"label": "Tamanho do Objeto", "attr": "sese_object_radius", "values": [20, 30, 40, 50, 60], "unit": "px", "disabled": True},
        ],
    },
    {
        "name": "Aventura Aquática",
        "logo": "Assets/MainMenu/Logo/logo_suse.png",
        "color": (72, 199, 242),
        "options": [
            {"label": "Quantidade de Alimentos", "attr": "suse_num_foods", "values": [3, 5, 7, 10]},
            {"label": "Velocidade do Peixe", "attr": "suse_fish_speed", "values": [1, 2, 3, 10]},
            {"label": "Margem de Colisão", "attr": "suse_hit_radius", "values": [30, 40, 50, 60, 70], "unit": "px"},
            {"label": "Espaçamento dos Alimentos", "attr": "suse_food_spacing", "values": [100, 120, 150, 180, 200], "unit": "px"},
            {"label": "Tamanho dos Alimentos", "attr": "suse_object_size", "values": [20, 30, 40, 50, 60], "unit": "px"},
        ],
    },
    {
        "name": "Missão dos Brinquedos",
        "logo": "Assets/MainMenu/Logo/logo_foac.png",
        "color": (255, 159, 67),
        "options": [
            {"label": "Raio de Encaixe", "attr": "foac_snap_radius", "values": [50, 80, 110, 140, 170, 200, 230, 260, 300], "unit": "px"},
            {"label": "Objetivos", "attr": "foac_objetivos", "values": [1, 2, 3, 4, 5]},
            {"label": "Tempo de Fixação", "attr": "foac_fixation_time", "values": [0.3, 0.6, 0.9, 1.2, 1.5], "unit": "s", "disabled": True},
            {"label": "Desfoque Máximo", "attr": "foac_max_blur", "values": list(range(0, 16))},
            {"label": "Quantidade de Objetos", "attr": "foac_object_count", "values": [4, 5, 6, 7]},
        ],
    },
]

CARD_BG = (22, 18, 48, 205)
TRACK = (255, 255, 255, 45)
DOT = (255, 255, 255, 120)
DISABLED = (70, 66, 96)
TEXT_DIM = (150, 146, 175)


def format_value(value, unit=None):
    txt = f"{value:g}".replace(".", ",")  # 0.2 -> "0,2"
    return f"{txt} {unit}" if unit else txt


class SettingsScreen:
    def __init__(self, tela, largura, altura, clock, config, bg_path="Assets/MainMenu/Background/bg_settings.png"):
        self.tela = tela
        self.largura = largura
        self.altura = altura
        self.clock = clock
        self.config = config
        self.running = True
        self.s = s = min(largura / 1920, altura / 1080)  # escala da interface

        self.label_font = ui.font(26 * s)
        self.value_font = ui.font(28 * s)
        self.tag_font = ui.font(18 * s)
        self.button_font = ui.font(30 * s)

        self.rows = []  # uma entrada por opção, com a geometria dos controles
        self.static = self._build_static(bg_path)

        # --- Rodapé ---
        btn_h = int(64 * s)
        reset_w, back_w, gap = int(300 * s), int(220 * s), int(24 * s)
        x = (largura - reset_w - gap - back_w) // 2
        y = int(965 * s) - btn_h // 2
        self.reset_btn = ui.PillButton("Restaurar padrões", (x, y, reset_w, btn_h), self.reset_defaults,
                                       self.button_font, filled=False)
        self.back_btn = ui.PillButton("Voltar", (x + reset_w + gap, y, back_w, btn_h), self.back, self.button_font)

    # -------------------- layout estático (desenhado uma vez) --------------------
    def _build_static(self, bg_path):
        s = self.s
        static = pygame.Surface((self.largura, self.altura)).convert()
        bg, bg_rect = ui.load_cover(bg_path, self.largura, self.altura)
        static.blit(bg, bg_rect)
        ui.draw_round_rect(static, static.get_rect(), (0, 0, 0, 60), 0)

        title = ui.render_outlined(ui.font(84 * s), "Configurações", outline=max(2, int(4 * s)))
        static.blit(title, title.get_rect(center=(self.largura // 2, int(95 * s))))
        subtitle = ui.font(28 * s).render("Ajuste cada minigame antes de começar", True, (235, 230, 255))
        static.blit(subtitle, subtitle.get_rect(center=(self.largura // 2, int(165 * s))))

        pad, gap = 80 * s, 40 * s
        card_w = (self.largura - 2 * pad - 2 * gap) / 3
        top, header_h, row_h = 210 * s, 120 * s, 106 * s
        card_h = header_h + 20 * s + row_h * 5 + 10 * s
        inner = 28 * s
        name_font = ui.font(34 * s)

        for i, section in enumerate(SECTIONS):
            color = section["color"]
            card = pygame.Rect(int(pad + i * (card_w + gap)), int(top), int(card_w), int(card_h))
            radius = int(28 * s)

            ui.draw_round_rect(static, card.move(0, int(6 * s)), (0, 0, 0, 90), radius)  # sombra
            ui.draw_round_rect(static, card, CARD_BG, radius)
            header = pygame.Surface((card.width, int(header_h)), pygame.SRCALPHA)
            pygame.draw.rect(header, (*color, 45), header.get_rect(),
                             border_top_left_radius=radius, border_top_right_radius=radius)
            static.blit(header, card.topleft)
            ui.draw_round_rect(static, card, (*color, 170), radius, width=max(1, int(2 * s)))

            icon_size = int(112 * s)  # as imagens dos logos têm bastante margem transparente
            icon = pygame.transform.smoothscale(pygame.image.load(section["logo"]).convert_alpha(), (icon_size, icon_size))
            icon_y = card.y + (int(header_h) - icon_size) // 2
            static.blit(icon, (card.x + int(inner * 0.3), icon_y))
            name = name_font.render(section["name"], True, color)
            static.blit(name, name.get_rect(midleft=(card.x + int(inner * 0.3) + icon_size,
                                                     card.y + int(header_h) // 2)))

            y = card.y + header_h + 20 * s
            for opt in section["options"]:
                label_color = TEXT_DIM if opt.get("disabled") else ui.BRANCO
                label = self.label_font.render(opt["label"], True, label_color)
                static.blit(label, label.get_rect(midleft=(card.x + inner, y + 18 * s)))

                ctrl_y = y + 64 * s
                btn_r = 22 * s
                minus_c = (card.x + inner + btn_r, ctrl_y)
                plus_c = (card.right - inner - btn_r, ctrl_y)
                track_x0 = minus_c[0] + btn_r + 22 * s
                track_x1 = plus_c[0] - btn_r - 22 * s
                n = len(opt["values"])
                dots = [track_x0 + (track_x1 - track_x0) * k / (n - 1) for k in range(n)]
                self.rows.append({
                    "opt": opt, "color": color, "value_right": (card.right - inner, y + 18 * s),
                    "minus": minus_c, "plus": plus_c, "btn_r": btn_r, "dots": dots, "ctrl_y": ctrl_y,
                    "area": pygame.Rect(card.x, int(y), card.width, int(row_h)),
                })
                y += row_h
        return static

    # -------------------- lógica dos valores --------------------
    def _index(self, opt):
        current = getattr(self.config, opt["attr"])
        return min(range(len(opt["values"])), key=lambda k: abs(opt["values"][k] - current))

    def step(self, opt, direction):
        # o valor atual pode não estar na lista (ex.: padrão 0.8 com opções 0.6/0.9),
        # então busca o próximo valor menor/maior em vez de usar values.index()
        current = getattr(self.config, opt["attr"])
        if direction > 0:
            candidates = [v for v in opt["values"] if v > current][:1]
        else:
            candidates = [v for v in opt["values"] if v < current][-1:]
        if candidates:
            setattr(self.config, opt["attr"], candidates[0])

    def reset_defaults(self):
        self.config.__dict__.update(GameConfig().__dict__)

    def back(self):
        self.running = False

    # -------------------- hit testing --------------------
    def _hit(self, pos):
        """Retorna (row, alvo) sob o mouse: alvo é 'minus', 'plus' ou o índice de um ponto."""
        for row in self.rows:
            if row["opt"].get("disabled") or not row["area"].collidepoint(pos):
                continue
            for key in ("minus", "plus"):
                cx, cy = row[key]
                if (pos[0] - cx) ** 2 + (pos[1] - cy) ** 2 <= (row["btn_r"] + 4 * self.s) ** 2:
                    return row, key
            if abs(pos[1] - row["ctrl_y"]) <= 20 * self.s:
                for k, dx in enumerate(row["dots"]):
                    if abs(pos[0] - dx) <= 14 * self.s:
                        return row, k
            return row, None
        return None, None

    # -------------------- desenho --------------------
    def _draw_step_button(self, center, radius, symbol, color, enabled, hover):
        s = self.s
        fill = (ui.mix(color, ui.BRANCO, 0.25) if hover else color) if enabled else DISABLED
        ui.draw_circle(self.tela, center, radius, fill)
        cx, cy = int(center[0]), int(center[1])
        half, thick = int(radius * 0.45), max(2, int(4 * s))
        sym_color = ui.BRANCO if enabled else TEXT_DIM
        pygame.draw.line(self.tela, sym_color, (cx - half, cy), (cx + half, cy), thick)
        if symbol == "+":
            pygame.draw.line(self.tela, sym_color, (cx, cy - half), (cx, cy + half), thick)

    def _draw_row(self, row, hover_target):
        s, opt, color = self.s, row["opt"], row["color"]
        disabled = opt.get("disabled", False)
        values = opt["values"]
        current = getattr(self.config, opt["attr"])
        idx = self._index(opt)

        # valor (ou etiqueta "em breve")
        if disabled:
            tag = self.tag_font.render("em breve", True, TEXT_DIM)
            tag_rect = tag.get_rect().inflate(int(20 * s), int(8 * s))
            tag_rect.midright = row["value_right"]
            ui.draw_round_rect(self.tela, tag_rect, (255, 255, 255, 25), tag_rect.height // 2)
            self.tela.blit(tag, tag.get_rect(center=tag_rect.center))
        else:
            val = self.value_font.render(format_value(current, opt.get("unit")), True, color)
            self.tela.blit(val, val.get_rect(midright=row["value_right"]))

        # trilha com um ponto por valor possível
        dots, ty = row["dots"], row["ctrl_y"]
        track = pygame.Rect(int(dots[0]), int(ty - 3 * s), int(dots[-1] - dots[0]), max(2, int(6 * s)))
        ui.draw_round_rect(self.tela, track, TRACK, track.height // 2)
        if not disabled and idx > 0:
            filled = pygame.Rect(track.x, track.y, int(dots[idx] - dots[0]), track.height)
            ui.draw_round_rect(self.tela, filled, (*color, 230), track.height // 2)
        for k, dx in enumerate(dots):
            if disabled:
                ui.draw_circle(self.tela, (dx, ty), 5 * s, (255, 255, 255, 40))
            elif k == idx:
                ui.draw_circle(self.tela, (dx, ty), 13 * s, ui.BRANCO)
                ui.draw_circle(self.tela, (dx, ty), 9 * s, color)
            else:
                r = (8 if hover_target == k else 6) * s
                ui.draw_circle(self.tela, (dx, ty), r, color if k < idx else DOT)

        # botões - / +
        can_dec = not disabled and any(v < current for v in values)
        can_inc = not disabled and any(v > current for v in values)
        self._draw_step_button(row["minus"], row["btn_r"], "-", color, can_dec, hover_target == "minus")
        self._draw_step_button(row["plus"], row["btn_r"], "+", color, can_inc, hover_target == "plus")

    def draw(self):
        self.tela.blit(self.static, (0, 0))
        hover_row, hover_target = self._hit(pygame.mouse.get_pos())
        for row in self.rows:
            self._draw_row(row, hover_target if row is hover_row else None)
        self.reset_btn.draw(self.tela)
        self.back_btn.draw(self.tela)
        ui.set_hand_cursor(hover_target is not None or self.reset_btn.is_hover() or self.back_btn.is_hover())
        pygame.display.flip()

    # -------------------- loop --------------------
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
            self.back()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            row, target = self._hit(event.pos)
            if target == "minus":
                self.step(row["opt"], -1)
            elif target == "plus":
                self.step(row["opt"], +1)
            elif isinstance(target, int):
                setattr(self.config, row["opt"]["attr"], row["opt"]["values"][target])
            self.reset_btn.check_click(event)
            self.back_btn.check_click(event)
        elif event.type == pygame.MOUSEWHEEL:
            row, _ = self._hit(pygame.mouse.get_pos())
            if row and event.y:
                self.step(row["opt"], event.y)

    def run(self):
        self.running = True
        while self.running:
            self.draw()
            for event in pygame.event.get():
                self.handle_event(event)
            self.clock.tick(30)
        ui.set_hand_cursor(False)
