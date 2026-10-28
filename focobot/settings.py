import pygame
import sys

# ------------------------
# BUTTON CLASSES
# ------------------------
class Button:
    def __init__(self, text, rect, callback, image_path=None, hover_image_path=None, font=None, show_text=True):
        self.text = text
        self.rect = pygame.Rect(rect)
        self.callback = callback
        self.font = font or pygame.font.SysFont("Segoe UI", 36)
        self.show_text = show_text

        if image_path:
            self.image = pygame.image.load(image_path).convert_alpha()
            self.image = self.scale_keep_aspect(self.image, rect[2])
            self.rect.size = self.image.get_size()
        else:
            self.image = None

        if hover_image_path:
            self.hover_image = pygame.image.load(hover_image_path).convert_alpha()
            self.hover_image = self.scale_keep_aspect(self.hover_image, rect[2])
        else:
            self.hover_image = self.image

    def scale_keep_aspect(self, image, target_width):
        w, h = image.get_size()
        aspect = h / w
        new_height = int(target_width * aspect)
        return pygame.transform.smoothscale(image, (target_width, new_height))

    def draw(self, surface):
        mouse_pos = pygame.mouse.get_pos()
        is_hover = self.rect.collidepoint(mouse_pos)
        img_to_draw = self.hover_image if is_hover else self.image

        if img_to_draw:
            img_scaled = pygame.transform.smoothscale(img_to_draw, (self.rect.width, self.rect.height))
            surface.blit(img_scaled, self.rect.topleft)
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


class ValueButton:
    def __init__(self, x, y, width, height, callback, text):
        self.rect = pygame.Rect(x, y, width, height)
        self.callback = callback
        self.text = text
        self.font = pygame.font.SysFont("Segoe UI", 30)

    def draw(self, surface):
        pygame.draw.rect(surface, (60, 60, 200), self.rect, border_radius=6)
        txt = self.font.render(self.text, True, (255, 255, 255))
        txt_rect = txt.get_rect(center=self.rect.center)
        surface.blit(txt, txt_rect)

    def check_click(self, pos):
        if self.rect.collidepoint(pos):
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
class SettingsScreen:
    def __init__(self, tela, largura, altura, clock, config, bg_path="Assets/MainMenu/Background/bg_settings.png"):
        self.tela = tela
        self.largura = largura
        self.altura = altura
        self.clock = clock
        self.config = config
        self.font = pygame.font.SysFont("Segoe UI", 30)
        self.title_font = pygame.font.SysFont("Segoe UI Semibold", 60)
        self.section_font = pygame.font.SysFont("Segoe UI Semibold", 36)
        self.buttons = []
        self.running = True

        # Load and scale background
        bg_image = pygame.image.load(bg_path).convert()
        img_w, img_h = bg_image.get_size()
        scale_factor = max(largura / img_w, altura / img_h)
        self.bg_image_scaled = pygame.transform.smoothscale(bg_image, (int(img_w * scale_factor), int(img_h * scale_factor)))
        self.bg_rect = self.bg_image_scaled.get_rect(center=(largura // 2, altura // 2))

        # Settings grouped by game — tudo em botões, valores discretos:
        self.columns = {
            "Missão dos Brinquedos": [
                {"label": "Raio de Encaixe", "attr": "foac_snap_radius", "values": [50, 80, 110, 140, 170, 200, 230, 260, 300], "type": "buttons"},
                {"label": "Objetivos", "attr": "foac_objetivos", "values": [1, 2, 3, 4, 5], "type": "buttons"},
                {"label": "Tempo de Fixação (s)", "attr": "foac_fixation_time", "values": [0.3, 0.6, 0.9, 1.2, 1.5], "type": "buttons"},
                {"label": "Desfoque Máximo", "attr": "foac_max_blur", "values": list(range(0, 16)), "type": "buttons"},
                {"label": "Quantidade de Objetos", "attr": "foac_object_count", "values": [4, 5, 6, 7], "type": "buttons"}
            ],

            "Resgate Espacial": [
                {"label": "Raio de Encaixe", "attr": "sese_snap_radius", "values": [50, 80, 110, 120, 140, 170, 200, 230, 260, 300], "type": "buttons"},
                {"label": "Asteroides", "attr": "sese_asteroid_count", "values": [3, 5, 7], "type": "buttons"},
                {"label": "Velocidade do Foguete", "attr": "sese_speed", "values": [1, 2, 3, 4], "type": "buttons"},
                {"label": "Tempo de Olhar (s)", "attr": "sese_required_look_time", "values": [0.2, 0.3, 0.5, 0.8, 1.0, 1.2], "type": "buttons"},
                {"label": "Tamanho do Objeto", "attr": "sese_object_radius", "values": [20, 30, 40, 50, 60], "type": "buttons"}
            ],

            "Aventura Aquática": [
                {"label": "Quantidade de Alimentos", "attr": "suse_num_foods", "values": [3, 5, 7, 10], "type": "buttons"},
                {"label": "Velocidade do Peixe", "attr": "suse_fish_speed", "values": [1, 2, 3, 10], "type": "buttons"},
                {"label": "Raio de Colisão", "attr": "suse_hit_radius", "values": [30, 40, 50, 60, 70], "type": "buttons"},
                {"label": "Espaçamento dos Alimentos", "attr": "suse_food_spacing", "values": [100, 120, 150, 180, 200], "type": "buttons"},
                {"label": "Tamanho dos Objetos", "attr": "suse_object_size", "values": [20, 30, 40, 50, 60], "type": "buttons"}
            ]
        }

        self._create_ui()

    def draw_panel(self, x, y, width, height, alpha=160):
        """Desenha painel escuro translúcido para contraste"""
        panel = pygame.Surface((width, height), pygame.SRCALPHA)
        panel.fill((0, 0, 0, alpha))
        self.tela.blit(panel, (x, y))

    def _create_ui(self):
        start_y = 120
        screen_padding = 80
        num_cols = len(self.columns)
        col_width = (self.largura - 2 * screen_padding) / num_cols

        # o valor atual pode não estar na lista (ex.: padrão 0.8 com opções 0.6/0.9),
        # então busca o próximo valor menor/maior em vez de usar values.index()
        def make_dec(attr, values):
            def dec():
                current = getattr(self.config, attr)
                menores = [v for v in values if v < current]
                if menores:
                    setattr(self.config, attr, menores[-1])
            return dec

        def make_inc(attr, values):
            def inc():
                current = getattr(self.config, attr)
                maiores = [v for v in values if v > current]
                if maiores:
                    setattr(self.config, attr, maiores[0])
            return inc

        self.buttons.clear()

        for col_idx, (game_name, options) in enumerate(self.columns.items()):
            x_start = screen_padding + col_width * col_idx
            # Coloque os botões com margem maior para garantir que não ultrapassem
            controls_x = x_start + col_width - 140  # mais à esquerda que antes
            y = start_y + 80

            for opt in options:
                opt["y"] = y
                dec_btn = ValueButton(int(controls_x), int(y - 15), 35, 35, make_dec(opt["attr"], opt["values"]), "-")
                inc_btn = ValueButton(int(controls_x + 40), int(y - 15), 35, 35, make_inc(opt["attr"], opt["values"]), "+")
                self.buttons.extend([dec_btn, inc_btn])
                opt["dec_btn"], opt["inc_btn"] = dec_btn, inc_btn
                y += 70

        def back_to_menu():
            self.running = False

        back_btn = Button("Voltar", (self.largura - 160, self.altura - 80, 140, 50), back_to_menu, font=self.font)
        self.buttons.append(back_btn)

    def draw(self):
        self.tela.blit(self.bg_image_scaled, self.bg_rect)

        # Título
        title_surf = self.title_font.render("Configurações", True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(self.largura // 2, 60))
        self.tela.blit(title_surf, title_rect)

        screen_padding = 80
        num_cols = len(self.columns)
        col_width = (self.largura - 2 * screen_padding) / num_cols
        panel_height = self.altura - 200

        for col_idx, (game_name, options) in enumerate(self.columns.items()):
            x_start = screen_padding + col_width * col_idx
            self.draw_panel(x_start - 20, 100, col_width - 40, panel_height)

            section_surf = self.section_font.render(game_name, True, (255, 255, 180))
            self.tela.blit(section_surf, (x_start + 30, 110))

            for opt in options:
                value = getattr(self.config, opt["attr"])
                label_surf = self.font.render(f"{opt['label']}: {value}", True, (255, 255, 255))
                self.tela.blit(label_surf, (x_start + 30, opt["y"]))

        for btn in self.buttons:
            btn.draw(self.tela)

        pygame.display.flip()

    def run(self):
        self.running = True
        while self.running:
            self.draw()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    self.running = False
                elif event.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION]:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        for btn in self.buttons:
                            if isinstance(btn, ValueButton):
                                btn.check_click(event.pos)
                            else:
                                btn.check_click(event)
            self.clock.tick(30)
