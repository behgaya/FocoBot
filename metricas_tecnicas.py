import csv, statistics, os


class MetricasTecnicas:
    def __init__(self, nome_jogo):
        self.nome_jogo = nome_jogo
        self.latencias = []    
        self.fps_values = []
        self.frames_total = 0
        self.frames_perdidos = 0

    def registrar_gaze(self, gaze_valido, inicio_captura, fim_frame):
        """Registra latência e perda de rastreamento"""
        if gaze_valido:
            latencia = fim_frame - inicio_captura  
            if 0 < latencia < 1:                   # evita valores absurdos
                self.latencias.append(latencia)
        else:
            self.frames_perdidos += 1
        self.frames_total += 1

    def registrar_fps(self, fps):
        self.fps_values.append(fps)


    def salvar_csv(self, dados_jogo, nome_arquivo="metricas_tecnicas.csv"):
        # Calcula métricas em segundos e converte para ms só no final
        lat_media = statistics.mean(self.latencias) if self.latencias else 0
        lat_desvio = statistics.stdev(self.latencias) if len(self.latencias) > 1 else 0
        fps_medio = statistics.mean(self.fps_values) if self.fps_values else 0
        fps_desvio = statistics.stdev(self.fps_values) if len(self.fps_values) > 1 else 0
        perda = (self.frames_perdidos / self.frames_total) * 100 if self.frames_total > 0 else 0

        row = {
            "jogo": self.nome_jogo,
            "latencia_media_ms": round(lat_media * 1000, 2),  # conversão aqui
            "latencia_desvio_ms": round(lat_desvio * 1000, 2), # e aqui
            "fps_medio": round(fps_medio, 2),
            "fps_desvio": round(fps_desvio, 2),
            "perda_%": round(perda, 2)
        }
        row.update(dados_jogo)

        file_exists = os.path.exists(nome_arquivo)
        with open(nome_arquivo, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=row.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)