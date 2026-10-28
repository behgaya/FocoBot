import pygame
import sys
import os
from focobot.gaze_controller import GazeController
from focobot.alignment import face_alignment_screen
from focobot.minigames.minigameSESE import SESEGame
from focobot.minigames.minigameSUSE import SUSEGame
from focobot.minigames.minigameFOAC import FOACGame
from focobot.settings import SettingsScreen
from focobot.settings import Button
from focobot.settings import GameConfig


# ------------------------
# SETTINGS SCREEN
# ------------------------
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
        #self._create_difficulty_button()


    def draw_rounded_rect(self, surface, rect, color, radius):
        """
        Draw a rounded rectangle with alpha channel on a surface.
        """
        shape_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(shape_surf, color, (0, 0, rect.width, rect.height), border_radius=radius)
        surface.blit(shape_surf, rect.topleft)


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
                        snap_radius=self.config.foac_snap_radius,
                        objetivos=self.config.foac_objetivos,
                        max_blur=self.config.foac_max_blur,
                        object_count=self.config.foac_object_count
                    )
                elif run_func == SESEGame:
                    game = run_func(
                        self.tela,
                        self.largura,
                        self.altura,
                        self.clock,
                        gaze=gaze,
                        asteroid_count=self.config.sese_asteroid_count,
                        rocket_speed=self.config.sese_speed,
                        snap_radius=self.config.sese_snap_radius,
                        required_look_time=self.config.sese_required_look_time
                    )
                elif run_func == SUSEGame:
                    game = run_func(
                        self.tela,
                        self.largura,
                        self.altura,
                        self.clock,
                        gaze=gaze,
                        num_foods=self.config.suse_num_foods,
                        fish_speed=self.config.suse_fish_speed,
                        hit_radius=self.config.suse_hit_radius,
                        food_spacing=self.config.suse_food_spacing,
                        object_size=self.config.suse_object_size
                    )
                try:
                    game.run()
                finally:
                    gaze.release()  # libera a webcam ao sair de qualquer minigame

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
            ("", SESEGame, "Assets/MainMenu/SESE/Button.png", "Assets/MainMenu/SESE/button_hover.png",
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
        cols, rows = 3, 2  # 2 rows: top for logo, bottom for buttons
        cell_w, cell_h = 350, 180      # bigger buttons
        col_spacing, row_spacing = 380, 250  # adjusted spacing

        total_width = (cols - 1) * col_spacing + cell_w
        total_height = (rows - 1) * row_spacing + cell_h
        start_x = self.largura // 2 - total_width // 2
        start_y = self.altura // 2 - total_height // 2

        # grid with space for the logo on top center, and buttons on bottom row
        grid = [[None for _ in range(cols)] for _ in range(rows)]
        grid[0][1] = ("image", "Assets/MainMenu/Logo/logo_neutral.png")  # logo at top center

        g = iter(game_data)
        for c in range(cols):
            try:
                grid[1][c] = ("game", next(g))  # all 3 buttons in the bottom row
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
        sair_w, sair_h = 200, 200
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
        margin = margem
        settings_w, settings_h = sair_w, sair_h  
        settings_x = margin  
        settings_y = sair_y 

        def open_settings():
            settings = SettingsScreen(self.tela, self.largura, self.altura, self.clock, self.config)
            settings.run()

        settings_button = Button(
            "Settings",
            (settings_x, settings_y, settings_w, settings_h),
            open_settings,
            image_path="Assets/Settings/button.png",
            hover_image_path="Assets/Settings/button_hover.png",
            font=self.font,
            show_text=False  # hide text, only image
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


            # Define rectangle area that covers title, logo and buttons

            # # You can tweak these values for the best fit
            # rect_x = self.largura // 2 - 600
            # rect_y = 50
            # rect_width = 1200
            # rect_height = self.altura - 300

            # # Semi-transparent black: RGBA with low alpha (opacity)
            # black_semi = (0, 0, 0, 150)  # alpha 150 out of 255 (~60% opacity)

            # Draw rounded rectangle behind UI elements
            # self.draw_rounded_rect(self.tela, pygame.Rect(rect_x, rect_y, rect_width, rect_height), black_semi, radius=20)

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
            # self.difficulty_button.draw(self.tela)

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
                # self.difficulty_button.check_click(event)

            pygame.display.flip()
            self.clock.tick(30)



# ------------------------
# MAIN
# ------------------------
if __name__ == "__main__":
    # Assets/ and data/ paths are relative to the project root
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    pygame.init()
    info = pygame.display.Info()
    tela = pygame.display.set_mode((info.current_w, info.current_h), pygame.NOFRAME)
    largura, altura = tela.get_size()
    pygame.display.set_caption("EyeTrax Minigames")
    clock = pygame.time.Clock()

    # CREATE CONFIG
    config = GameConfig()   

    menu = Menu(tela, largura, altura, clock, config)  # pass config to menu
    menu.run()
