import pandas as pd
import matplotlib.pyplot as plt

# 1️⃣ Carregar CSV
df = pd.read_csv("data/metricas/metricas_sese.csv")

# 2️⃣ Estatísticas básicas
print("\n=== Estatísticas gerais ===")
print(df.select_dtypes(include=["number"]).describe())

# 3️⃣ Médias resumidas por métrica
medias = df[[
    "latencia_media_ms", "fps_medio", "perda_%",
    "duracao_media_fixacao_s", "taxa_desvio_px",
    "asteroides_olhados", "taxa_acerto_asteroide_%",
    "tempo_medio_reacao_s"
]].mean()

print("\n=== Médias principais ===")
print(medias)

# 4️⃣ Identificar sessões “problemáticas”
problemas = df[
    (df["fps_medio"] < 25) |
    (df["perda_%"] > 1) |
    (df["latencia_media_ms"] > 50) |
    (df["duracao_media_fixacao_s"] < 0.1) |
    (df["taxa_acerto_asteroide_%"] < 50)
]

if len(problemas) > 0:
    print("\n⚠️ Sessões com possíveis problemas:")
    print(problemas[[
        "jogo", "fps_medio", "perda_%", "latencia_media_ms",
        "duracao_media_fixacao_s", "taxa_acerto_asteroide_%"
    ]])
else:
    print("\n✅ Nenhuma sessão com problemas graves detectada!")

# 5️⃣ Gráficos
plt.figure(figsize=(14, 8))

# Latência
plt.subplot(2, 3, 1)
plt.plot(df["latencia_media_ms"], label="Latência Média (ms)")
plt.plot(df["latencia_desvio_ms"], label="Desvio Latência", linestyle="--")
plt.legend()
plt.title("Latência")

# FPS
plt.subplot(2, 3, 2)
plt.plot(df["fps_medio"], label="FPS Médio", color="green")
plt.plot(df["fps_desvio"], label="Desvio FPS", linestyle="--", color="lime")
plt.legend()
plt.title("FPS")

# Fixações
plt.subplot(2, 3, 3)
plt.bar(range(len(df)), df["duracao_media_fixacao_s"], color="orange")
plt.title("Duração Média das Fixações (s)")

# Asteroides olhados vs acertados
plt.subplot(2, 3, 4)
plt.scatter(df["asteroides_olhados"], df["taxa_acerto_asteroide_%"], c="purple", s=80)
plt.xlabel("Asteroides Olhados")
plt.ylabel("Taxa de Acerto (%)")
plt.title("Acerto de Asteroides")

# Tempo médio de reação
plt.subplot(2, 3, 5)
plt.plot(df["tempo_medio_reacao_s"], marker="o", color="red")
plt.title("Tempo Médio de Reação (s)")

# Frequência de fixações
plt.subplot(2, 3, 6)
plt.bar(range(len(df)), df["frequencia_fixacoes"], color="cyan")
plt.title("Frequência de Fixações")

plt.tight_layout()
plt.show()

# 6️⃣ Interpretação simples
print("\n=== Interpretação automática ===")
if medias["fps_medio"] < 25:
    print("❌ FPS baixo — otimizar loop ou reduzir carga gráfica.")
elif medias["fps_medio"] < 30:
    print("⚠️ FPS razoável — pode oscilar sob carga.")
else:
    print("✅ FPS estável!")

if medias["latencia_media_ms"] > 50:
    print("❌ Latência alta — possível gargalo de processamento.")
elif medias["latencia_media_ms"] > 35:
    print("⚠️ Latência moderada — aceitável, mas pode melhorar.")
else:
    print("✅ Latência ótima!")

if medias["duracao_media_fixacao_s"] < 0.2:
    print("⚠️ Fixações curtas — pode indicar dispersão visual.")
elif medias["duracao_media_fixacao_s"] > 3:
    print("⚠️ Fixações muito longas — talvez estímulo pouco dinâmico.")
else:
    print("✅ Fixações em faixa ideal!")

if medias["taxa_acerto_asteroide_%"] < 80:
    print("⚠️ Acerto de asteroides baixo — atenção ou coordenação pode estar comprometida.")
else:
    print("✅ Acerto de asteroides bom!")

if medias["tempo_medio_reacao_s"] > 0.5:
    print("⚠️ Reação lenta — estímulos podem ser complexos ou tempo de resposta alto.")
else:
    print("✅ Tempo de reação aceitável!")
