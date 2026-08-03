import pandas as pd
import matplotlib.pyplot as plt

# 1️⃣ Carregar o CSV
df = pd.read_csv("metricas_suse.csv")

# 2️⃣ Estatísticas básicas
print("\n=== Estatísticas gerais ===")
print(df.select_dtypes(include=["number"]).describe())

# 3️⃣ Médias resumidas por métrica
print("\n=== Médias principais ===")
print(df[["latencia_media_ms", "fps_medio", "perda_%", "duracao_media_fixacao_s", "taxa_desvio_px"]].mean())

# 4️⃣ Identificar sessões “problemáticas”
problemas = df[
    (df["fps_medio"] < 25) |
    (df["perda_%"] > 1) |
    (df["latencia_media_ms"] > 50) |
    (df["duracao_media_fixacao_s"] < 0.1)
]

if len(problemas) > 0:
    print("\n⚠️ Sessões com possíveis problemas:")
    print(problemas[["jogo", "fps_medio", "perda_%", "latencia_media_ms", "duracao_media_fixacao_s"]])
else:
    print("\n✅ Nenhuma sessão com problemas graves detectada!")

# 5️⃣ Gráficos com boxplot
plt.figure(figsize=(12, 6))

# Latência
plt.subplot(2, 2, 1)
plt.plot(df["latencia_media_ms"], label="Latência Média (ms)")
plt.plot(df["latencia_desvio_ms"], label="Desvio Latência", linestyle="--")
plt.legend()
plt.title("Latência")

# FPS
plt.subplot(2, 2, 2)
plt.plot(df["fps_medio"], label="FPS Médio", color="green")
plt.plot(df["fps_desvio"], label="Desvio FPS", linestyle="--", color="lime")
plt.legend()
plt.title("FPS")

# Duração média das fixações em boxplot
plt.subplot(2, 2, 3)
plt.boxplot(df["duracao_media_fixacao_s"], vert=True, patch_artist=True, boxprops=dict(facecolor="orange"))
plt.title("Duração Média das Fixações (s)")
plt.ylabel("Segundos")

# Correlação FPS x Latência
plt.subplot(2, 2, 4)
plt.scatter(df["fps_medio"], df["latencia_media_ms"], c=df["perda_%"], cmap="coolwarm", s=80)
plt.colorbar(label="Perda (%)")
plt.xlabel("FPS Médio")
plt.ylabel("Latência Média (ms)")
plt.title("Correlação FPS x Latência")

plt.tight_layout()
plt.show()

# 6️⃣ Interpretação simples
print("\n=== Interpretação automática ===")
media_latencia = df["latencia_media_ms"].mean()
media_fps = df["fps_medio"].mean()
media_fix = df["duracao_media_fixacao_s"].mean()

if media_fps < 25:
    print("❌ FPS baixo — otimizar loop ou reduzir carga gráfica.")
elif media_fps < 30:
    print("⚠️ FPS razoável, mas pode oscilar sob carga.")
else:
    print("✅ FPS estável!")

if media_latencia > 50:
    print("❌ Latência alta — possível gargalo de processamento.")
elif media_latencia > 35:
    print("⚠️ Latência moderada — aceitável, mas pode melhorar.")
else:
    print("✅ Latência ótima!")

if media_fix < 0.2:
    print("⚠️ Fixações curtas — pode indicar dispersão visual.")
elif media_fix > 3:
    print("⚠️ Fixações muito longas — talvez estímulo pouco dinâmico.")
else:
    print("✅ Fixações em faixa ideal.")
