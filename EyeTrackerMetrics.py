import pygame

class EyeTrackerMetrics:
    def __init__(self):
        self.fixations = []  # (x, y, timestamp)
        self.tempo_primeira_fixacao = None
        self.foi_fixado = False
        self.tempo_inicio_jogo = pygame.time.get_ticks() / 1000

    def update_fixation(self, gaze_point, target_rect=None):
        """
        Update fixations based on gaze_point (x, y) and optional target_rect.
        """
        current_time = pygame.time.get_ticks() / 1000 - self.tempo_inicio_jogo
        x, y = gaze_point

        # record fixation if looking at target
        if target_rect and target_rect.collidepoint(x, y):
            if not self.foi_fixado:
                self.tempo_primeira_fixacao = current_time
                self.foi_fixado = True
            self.fixations.append((x, y, current_time))
        else:
            # still record for heatmap if you want overall gaze
            self.fixations.append((x, y, current_time))

    def draw_heatmap(self, surface, radius=25, alpha=50, color=(255,0,0)):
        for x, y, _ in self.fixations:
            s = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*color, alpha), (radius, radius), radius)
            surface.blit(s, (x - radius, y - radius))

    def get_metrics(self):
        """
        Returns dictionary of metrics:
        - first fixation time
        - total fixation duration
        - number of fixations
        """
        if not self.fixations:
            return {}
        duracao_total = self.fixations[-1][2] - self.fixations[0][2]
        return {
            "tempo_primeira_fixacao": self.tempo_primeira_fixacao,
            "duracao_total_fixacoes": duracao_total,
            "num_fixacoes": len(self.fixations)
        }

    def reset(self):
        self.fixations = []
        self.tempo_primeira_fixacao = None
        self.foi_fixado = False
        self.tempo_inicio_jogo = pygame.time.get_ticks() / 1000
