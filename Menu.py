import pygame
import sys
from gaze_controller import GazeController
from alignment import face_alignment_screen
from minigameSESE import SESEGame
from minigameSUSE import SUSEGame
from minigameFOAC import FOACGame


class GameConfig:
    def __init__(self):
        # FOAC
        self.foac_snap_radius = 200
        self.foac_objetivos = 3

        # SESE
        self.sese_asteroid_count = 5
        self.sese_speed = 2

        # SUSE
        self.suse_num_foods = 5
        self.suse_fish_speed = 2

# ------------------------
# BUTTON / SLIDER CLASSES
# ------------------------
class ValueButton:
    def __init__(self, x, y, width, height, callback, text):
        self.rect = pygame.Rect(x, y, width, height)
        self.callback = callback
        self.text = text
        self.font = pygame.font.SysFont(None, 30)

    def draw(self, surface):
        pygame.draw.rect(surface, (80, 80, 200), self.rect, border_radius=6)
        txt = self.font.render(self.text, True, (255, 255, 255))
        txt_rect = txt.get_rect(center=self.rect.center)
        surface.blit(txt, txt_rect)

    def check_click(self, pos):
        if self.rect.collidepoint(pos):
            self.callback()


class Slider:
    def __init__(self, x, y, width, min_val, max_val, value, callback):
        self.rect = pygame.Rect(x, y, width, 8)
        self.min_val = min_val
        self.max_val = max_val
        self.value = value
        self.callback = callback
        self.dragging = False
        self.handle_radius = 10
        self.update_handle_x()

    def update_handle_x(self):
        self.handle_x = self.rect.left + (self.value - self.min_val) / (self.max_val - self.min_val) * self.rect.width

    def draw(self, surface):
        # Track
        pygame.draw.rect(surface, (100, 100, 100), self.rect, border_radius=4)
        # Handle
        pygame.draw.circle(surface, (255, 0, 0), (int(self.handle_x), self.rect.centery), self.handle_radius)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if pygame.Rect(self.handle_x - self.handle_radius, self.rect.centery - self.handle_radius,
                           self.handle_radius*2, self.handle_radius*2).collidepoint(event.pos):
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.handle_x = max(self.rect.left, min(event.pos[0], self.rect.right))
            self.value = self.min_val + (self.handle_x - self.rect.left) / self.rect.width * (self.max_val - self.min_val)
            self.value = round(self.value)
            self.callback(self.value)

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
        self.font = pygame.font.SysFont(None, 36)
        self.buttons = []
        self.sliders = []
        self.running = True

        # Load background image and scale
        bg_image = pygame.image.load(bg_path).convert_alpha()
        img_w, img_h = bg_image.get_size()
        scale_w = self.largura / img_w
        scale_h = self.altura / img_h
        scale_factor = max(scale_w, scale_h)  # ensures it covers the screen

        new_w = int(img_w * scale_factor)
        new_h = int(img_h * scale_factor)
        self.bg_image_scaled = pygame.transform.smoothscale(bg_image, (new_w, new_h))
        self.bg_rect = self.bg_image_scaled.get_rect(center=(self.largura//2, self.altura//2))

        # Column layout by minigame
        self.columns = {
            "Missão dos Brinquedos": [
                {"label": "Snap Radius", "attr": "foac_snap_radius", "min": 50, "max": 300, "type": "slider"},
                {"label": "Objetivos", "attr": "foac_objetivos", "values": [1, 2, 3, 4], "type": "buttons"}
            ],
            "Resgate Espacial": [
                {"label": "Asteroids", "attr": "sese_asteroid_count", "values": [3,5,7], "type": "buttons"},
                {"label": "Speed", "attr": "sese_speed", "min": 1, "max": 4, "type": "slider"}
            ],
            "Aventura Aquática": [
                {"label": "Foods", "attr": "suse_num_foods", "values": [3,5,7,10], "type": "buttons"},
                {"label": "Fish Speed", "attr": "suse_fish_speed", "min": 1, "max": 4, "type": "slider"}
            ]
        }

        self._create_ui()

    def _create_ui(self):
        start_y = 120
        screen_padding = 100
        num_cols = len(self.columns)
        col_width = (self.largura - 2 * screen_padding) / num_cols

        def make_dec(attr, values):
            def dec():
                current = getattr(self.config, attr)
                idx = values.index(current)
                setattr(self.config, attr, values[max(0, idx - 1)])
            return dec

        def make_inc(attr, values):
            def inc():
                current = getattr(self.config, attr)
                idx = values.index(current)
                setattr(self.config, attr, values[(idx + 1) % len(values)])
            return inc

        for col_idx, (game_name, options) in enumerate(self.columns.items()):
            x_start = screen_padding + col_width * col_idx
            label_x = x_start + 50  # labels on left side of column
            controls_x = x_start + col_width/2 + 30  # sliders/buttons to the right
            y = start_y

            # Column header
            header = self.font.render(game_name, True, (255, 255, 0))
            header_rect = header.get_rect(center=(x_start + col_width/2, y))
            self.tela.blit(header, header_rect)
            y += 60

            for opt in options:
                value = getattr(self.config, opt["attr"])

                # Label on the left
                label_surf = self.font.render(f"{opt['label']}: {value}", True, (255, 255, 255))
                label_rect = label_surf.get_rect(midleft=(label_x, y))
                opt["label_rect"] = label_rect
                opt["y"] = y

                # Controls (slider or buttons) on the right
                if opt["type"] == "buttons":
                    dec_btn = ValueButton(int(controls_x), y-15, 30, 30, make_dec(opt["attr"], opt["values"]), "-")
                    inc_btn = ValueButton(int(controls_x + 40), y-15, 30, 30, make_inc(opt["attr"], opt["values"]), "+")
                    self.buttons.append(dec_btn)
                    self.buttons.append(inc_btn)
                    opt["dec_btn"] = dec_btn
                    opt["inc_btn"] = inc_btn
                elif opt["type"] == "slider":
                    slider = Slider(int(controls_x), y-10, 150, opt["min"], opt["max"], value,
                                    callback=lambda v, attr=opt["attr"]: setattr(self.config, attr, v))
                    self.sliders.append(slider)
                    opt["slider"] = slider

                y += 60  # space between options

        # Back button
        def back_to_menu():
            self.running = False

        back_btn = Button(
            "Back",
            (self.largura - 160, self.altura - 80, 140, 50),
            back_to_menu,
            font=self.font
        )
        self.buttons.append(back_btn)

    def draw(self):
        # Draw full-screen background
        self.tela.blit(self.bg_image_scaled, self.bg_rect)

        # Draw main title
        title_font = pygame.font.SysFont(None, 60)
        title_surf = title_font.render("Settings", True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(self.largura // 2, 50))
        self.tela.blit(title_surf, title_rect)

        # Draw semi-transparent, rounded column backgrounds + column titles
        screen_padding = 100
        num_cols = len(self.columns)
        col_width = (self.largura - 2 * screen_padding) / num_cols
        col_height = self.altura - 150
        overlay_color = (50, 50, 50, 180)  # slightly higher opacity for better visibility

        for col_idx, (game_name, options) in enumerate(self.columns.items()):
            x_start = screen_padding + col_width * col_idx
            y_start = 100

            # Rounded rectangle for column
            overlay_surf = pygame.Surface((col_width - 20, col_height), pygame.SRCALPHA)
            pygame.draw.rect(overlay_surf, overlay_color, (0, 0, col_width - 20, col_height), border_radius=20)
            self.tela.blit(overlay_surf, (x_start + 10, y_start))

            # Column title (minigame name)
            col_title_font = pygame.font.SysFont(None, 48)
            col_title_surf = col_title_font.render(game_name, True, (255, 255, 0))
            col_title_rect = col_title_surf.get_rect(center=(x_start + col_width / 2, y_start + 30))
            self.tela.blit(col_title_surf, col_title_rect)

        # Draw labels, sliders, and buttons
        for col_idx, (game_name, options) in enumerate(self.columns.items()):
            for opt in options:
                value = getattr(self.config, opt["attr"])
                label_surf = self.font.render(f"{opt['label']}: {value}", True, (255, 255, 255))
                self.tela.blit(label_surf, (opt["label_rect"].x, opt["y"]))

        # Draw buttons
        for btn in self.buttons:
            btn.draw(self.tela)
        # Draw sliders
        for slider in self.sliders:
            slider.draw(self.tela)

        pygame.display.flip()




    def run(self):
        self.running = True
        while self.running:
            self.draw()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.running = False
                elif event.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION]:
                    # Buttons
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        for btn in self.buttons:
                            if isinstance(btn, ValueButton):
                                btn.check_click(event.pos)  # pass the position
                            else:
                                btn.check_click(event)      # for your normal Button class
                    # Sliders
                    for slider in self.sliders:
                        slider.handle_event(event)

            self.clock.tick(30)

class TutorialScreen:
    def __init__(self, tela, largura, altura, clock, image_path, back_callback, next_callback):
        self.tela = tela
        self.largura = largura
        self.altura = altura
        self.clock = clock
        self.running = True
        self.back_callback = back_callback
        self.next_callback = next_callback

        # Load background/tutorial image
        self.bg_image = pygame.image.load(image_path).convert_alpha()
        w, h = self.bg_image.get_size()
        scale_factor = max(largura / w, altura / h)
        self.bg_image = pygame.transform.smoothscale(self.bg_image, (int(w*scale_factor), int(h*scale_factor)))
        self.bg_rect = self.bg_image.get_rect(center=(largura//2, altura//2))

        # Buttons
        self.font = pygame.font.SysFont(None, 36)
        self.back_btn = Button("Back", (50, altura-80, 150, 50), self.back)
        self.next_btn = Button("Next", (largura-200, altura-80, 150, 50), self.next)

    def back(self):
        self.running = False
        if self.back_callback:
            self.back_callback()

    def next(self):
        self.running = False
        if self.next_callback:
            self.next_callback()

    def run(self):
        self.running = True
        while self.running:
            self.tela.blit(self.bg_image, self.bg_rect)
            self.back_btn.draw(self.tela)
            self.next_btn.draw(self.tela)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                self.back_btn.check_click(event)
                self.next_btn.check_click(event)

            pygame.display.flip()
            self.clock.tick(30)



class Button:
    def __init__(self, text, rect, callback, image_path=None, hover_image_path=None, font=None, show_text=True):
        self.text = text
        self.rect = pygame.Rect(rect)
        self.callback = callback
        self.font = font or pygame.font.SysFont(None, 40)
        self.show_text = show_text

        # Load images
        if image_path:
            self.image = pygame.image.load(image_path).convert_alpha()
            self.image = self.scale_keep_aspect(self.image, rect[2])  # keep width = rect[2]
            self.rect.size = self.image.get_size()  # update rect size to image
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
            pygame.draw.rect(surface, (100, 100, 255), self.rect, border_radius=8)

        # Só desenha o texto se show_text for True
        if self.show_text and self.text:
            txt_surface = self.font.render(self.text, True, (0, 0, 0))
            txt_rect = txt_surface.get_rect(center=self.rect.center)
            surface.blit(txt_surface, txt_rect)

    def check_click(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()
class Menu:
    def __init__(self, tela, largura, altura, clock, config):
        self.tela = tela
        self.largura = largura
        self.altura = altura
        self.clock = clock
        self.config = config  # <--- store it

        self.title_font = pygame.font.SysFont(None, 60)
        self.font = pygame.font.SysFont(None, 40)

        # Load background image once
        bg_image = pygame.image.load("Assets/MainMenu/Background/bg_neutral.png").convert_alpha()

        # Get screen size
        screen_width, screen_height = self.largura, self.altura

        # Scale the image to cover the screen
        img_width, img_height = bg_image.get_size()
        scale_w = screen_width / img_width
        scale_h = screen_height / img_height
        scale_factor = max(scale_w, scale_h)  # ensure image covers entire screen

        new_w = int(img_width * scale_factor)
        new_h = int(img_height * scale_factor)
        self.bg_image_scaled = pygame.transform.smoothscale(bg_image, (new_w, new_h))

        # Center the image
        self.bg_rect = self.bg_image_scaled.get_rect(center=(screen_width // 2, screen_height // 2))

        # Difficulty toggle setup
        self.levels = ["facil", "medio", "dificil"]
        self.nivel_idx = 0  # default

        # Uma imagem para cada dificuldade
        self.level_images = [
            "Assets/MainMenu/difficulty/difficulty_easy.png",
            "Assets/MainMenu/difficulty/difficulty_medium.png",
            "Assets/MainMenu/difficulty/difficulty_hard.png"
        ]

        self.level_hover_images = [
            "Assets/MainMenu/difficulty/difficulty_easy_hover.png",
            "Assets/MainMenu/difficulty/difficulty_medium_hover.png",
            "Assets/MainMenu/difficulty/difficulty_hard_hover.png"
        ]

        self.buttons = []
        self._create_buttons()
        self._create_difficulty_button()

    def _create_difficulty_button(self):
        def toggle_difficulty():
            self.nivel_idx = (self.nivel_idx + 1) % len(self.levels)
            # Atualiza a imagem para o novo nível
            self.difficulty_button.image = pygame.image.load(self.level_images[self.nivel_idx]).convert_alpha()
            self.difficulty_button.hover_image = pygame.image.load(self.level_hover_images[self.nivel_idx]).convert_alpha()

        # Inicializa com a imagem do nível atual
        self.difficulty_button = Button(
            text="",  # não precisa do texto
            rect = (50, self.altura - 150, 100, 100),  # 100x100 quadrado
            callback=toggle_difficulty,
            image_path=self.level_images[self.nivel_idx],
            hover_image_path=self.level_hover_images[self.nivel_idx],
            font=self.font,
            show_text=False  # desativa o texto
        )

    def make_game_callback(self, run_func):
        def start_game():

            # Select tutorial image based on minigame
            if run_func == FOACGame:
                tutorial_image = "Assets/Tutorial/tutorial_foac.png"
            elif run_func == SESEGame:
                tutorial_image = "Assets/Tutorial/tutorial_sese.png"
            elif run_func == SUSEGame:
                tutorial_image = "Assets/Tutorial/tutorial_suse.png"
            else:
                tutorial_image = None  # fallback

            # Callback to run calibration and then the minigame
            def go_to_calibration():
                if not face_alignment_screen():
                    return
                gaze = GazeController()
                nivel_lower = self.levels[self.nivel_idx].lower()

                if run_func == FOACGame:
                    game = run_func(
                        self.tela, self.largura, self.altura, self.clock, gaze=gaze,
                        nivel=nivel_lower,
                        snap_radius=self.config.foac_snap_radius,
                        objetivos=self.config.foac_objetivos
                    )
                elif run_func == SESEGame:
                    game = run_func(
                        self.tela,
                        self.largura,
                        self.altura,
                        self.clock,
                        gaze=gaze,
                        asteroid_count=self.config.sese_asteroid_count,
                        rocket_speed=self.config.sese_speed
                    )
                elif run_func == SUSEGame:
                    game = run_func(
                        self.tela,
                        self.largura,
                        self.altura,
                        self.clock,
                        gaze=gaze,
                        num_foods=self.config.suse_num_foods,
                        fish_speed=self.config.suse_fish_speed
                    )
                game.run()

            # Show the tutorial for this minigame
            tutorial = TutorialScreen(
                self.tela, self.largura, self.altura, self.clock,
                image_path=tutorial_image,
                back_callback=None,
                next_callback=go_to_calibration
            )
            tutorial.run()

        return start_game



    def _create_buttons(self):
        # Seus minigames
        game_data = [
            ("", SESEGame, "Assets/MainMenu/SESE/button.png", "Assets/MainMenu/SESE/button_hover.png",
            "Assets/MainMenu/Background/bg_neutral.png", "Assets/MainMenu/Logo/logo_sese.png"),
            ("", SUSEGame, "Assets/MainMenu/SUSE/button.png", "Assets/MainMenu/SUSE/button_hover.png",
            "Assets/MainMenu/Background/bg_neutral.png", "Assets/MainMenu/Logo/logo_suse.png"),
            ("FOAC", FOACGame, "Assets/MainMenu/FOAC/button.png", "Assets/MainMenu/FOAC/button_hover.png",
            "Assets/MainMenu/Background/bg_neutral.png", "Assets/MainMenu/Logo/logo_foac.png"),
        ]

        def quit_game():
            pygame.quit()
            sys.exit()

        # --- GRID SETUP ---
        cols, rows = 3, 3
        cell_w, cell_h = 250, 120
        col_spacing, row_spacing = 300, 200
        total_width = (cols - 1) * col_spacing + cell_w
        total_height = (rows - 1) * row_spacing + cell_h
        start_x = self.largura // 2 - total_width // 2
        start_y = self.altura // 2 - total_height // 2

        # grid com espaço para os jogos e imagem do meio
        grid = [[None for _ in range(cols)] for _ in range(rows)]
        grid[0][1] = ("image", "Assets/MainMenu/Logo/logo_neutral.png")

        g = iter(game_data)
        for r in range(rows):
            for c in range(cols):
                if grid[r][c] is None:
                    try:
                        grid[r][c] = ("game", next(g))
                    except StopIteration:
                        pass

        # constrói os botões
        self.extra_images = []
        self.buttons_with_images = []

        for r in range(rows):
            for c in range(cols):
                if grid[r][c] is None:
                    continue

                x = start_x + c * col_spacing
                y = start_y + r * row_spacing
                cell = grid[r][c]

                if cell[0] == "game":
                    label, func, img, hover_img, bg_img, logo_img = cell[1]
                    callback = self.make_game_callback(func)
                    button = Button(
                        label,
                        (x, y, cell_w, cell_h),
                        callback,
                        image_path=img,
                        hover_image_path=hover_img,
                        font=self.font,
                        show_text=False
                    )
                    self.buttons.append(button)
                    self.buttons_with_images.append((button, bg_img, logo_img))

                elif cell[0] == "image":
                    img_path = cell[1]
                    img = pygame.image.load(img_path).convert_alpha()
                    w, h = img.get_size()
                    aspect = h / w
                    new_w = int(cell_w * 1.3)
                    new_h = int(new_w * aspect)
                    img = pygame.transform.smoothscale(img, (new_w, new_h))
                    rect = img.get_rect(center=(x + cell_w // 2, y + cell_h // 2))
                    self.extra_images.append((img, rect))

        # --- BOTÃO DE SAIR FIXO NO CANTO INFERIOR DIREITO ---
        margem = 50
        sair_w, sair_h = 150, 150
        sair_x = self.largura - sair_w - margem
        sair_y = self.altura - sair_h - margem

        sair_button = Button(
            "Sair",
            (sair_x, sair_y, sair_w, sair_h),
            quit_game,
            image_path="Assets/MainMenu/QUIT/button.png",
            hover_image_path="Assets/MainMenu/QUIT/button_hover.png",
            font=self.font,
            show_text=False
        )
        self.buttons.append(sair_button)
        def open_settings():
            settings = SettingsScreen(self.tela, self.largura, self.altura, self.clock, config)
            settings.run()
        
        settings_button = Button(
            "Settings",
            (50, 50, 150, 70),
            open_settings,
            font=self.font
        )
        self.buttons.append(settings_button)

    def run(self):
        running = True
        while running:
            mouse_pos = pygame.mouse.get_pos()

            # ------------------------
            # Determine hovered button
            # ------------------------
            hovered_bg = self.bg_image_scaled  # default background
            hovered_logo = None                # default: no hover logo

            for button, bg_path, logo_path in self.buttons_with_images:
                if button.rect.collidepoint(mouse_pos):
                    # Load and scale background
                    bg_image = pygame.image.load(bg_path).convert_alpha()
                    w, h = bg_image.get_size()
                    scale_factor = max(self.largura / w, self.altura / h)
                    hovered_bg = pygame.transform.smoothscale(bg_image, (int(w*scale_factor), int(h*scale_factor)))

                    # Load and scale logo
                    logo_image = pygame.image.load(logo_path).convert_alpha()
                    lw, lh = logo_image.get_size()
                    scale_factor_logo = 1.3 * 250 / lw  # relative to button width
                    hovered_logo = pygame.transform.smoothscale(logo_image, (int(lw*scale_factor_logo), int(lh*scale_factor_logo)))
                    logo_rect = hovered_logo.get_rect(center=(self.largura // 2, self.altura // 2 - hovered_logo.get_height() // 2 - 37))
                    break  # stop after first hovered button

            # ------------------------
            # Draw background
            # ------------------------
            self.tela.blit(hovered_bg, (0, 0))

            # ------------------------
            # Draw title
            # ------------------------
            self.title_font = pygame.font.Font("Assets/Fonts/Fredoka-Regular.ttf", 84)

            # --- Renderizar título com contorno ---
            title_text = "Escolha um Minigame"

            # Cores principais
            text_color = (255, 255, 255)      # branco
            outline_color = (255, 100, 150)   # rosa-choque suave

            # Renderizar várias cópias para simular contorno
            title_surface = self.title_font.render(title_text, True, text_color)
            outline_surface = self.title_font.render(title_text, True, outline_color)

            # Cria superfície maior para acomodar o contorno
            outline_size = 4  # espessura do contorno
            w, h = title_surface.get_size()
            final_surface = pygame.Surface((w + outline_size * 2, h + outline_size * 2), pygame.SRCALPHA)

            # Desenha o contorno em volta (8 direções)
            for dx in [-outline_size, 0, outline_size]:
                for dy in [-outline_size, 0, outline_size]:
                    if dx != 0 or dy != 0:
                        final_surface.blit(outline_surface, (dx + outline_size, dy + outline_size))

            # Desenha o texto principal por cima
            final_surface.blit(title_surface, (outline_size, outline_size))

            # --- Centralizar na tela ---
            title_rect = final_surface.get_rect(center=(self.largura // 2, 120))
            self.tela.blit(final_surface, title_rect)


            # ------------------------
            # Draw buttons
            # ------------------------
            for b in self.buttons:
                b.draw(self.tela)

            # ------------------------
            # Draw difficulty button
            # ------------------------
            self.difficulty_button.draw(self.tela)

            # ------------------------
            # Draw logo
            # ------------------------
            if hovered_logo:
                self.tela.blit(hovered_logo, logo_rect)
            else:
                # draw default logo(s) if no hover
                for img, rect in self.extra_images:
                    self.tela.blit(img, rect)

            # ------------------------
            # Handle events
            # ------------------------
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                for b in self.buttons:
                    b.check_click(event)
                self.difficulty_button.check_click(event)

            pygame.display.flip()
            self.clock.tick(30)



# ------------------------
# MAIN
# ------------------------
if __name__ == "__main__":
    pygame.init()
    info = pygame.display.Info()
    tela = pygame.display.set_mode((info.current_w, info.current_h), pygame.NOFRAME)
    largura, altura = tela.get_size()
    pygame.display.set_caption("EyeTrax Minigames")
    clock = pygame.time.Clock()

    # CREATE CONFIG
    config = GameConfig()   # <--- THIS WAS MISSING

    menu = Menu(tela, largura, altura, clock, config)  # pass config to menu
    menu.run()
