import pandas as pd
import matplotlib.pyplot as plt

# 1️⃣ Carregar os dados
df = pd.read_csv("data/metricas/metricas_FOAC.csv")

# 2️⃣ Estatísticas gerais
print("\n=== Estatísticas gerais ===")
print(df.select_dtypes(include=["number"]).describe())

# 3️⃣ Médias das métricas principais
print("\n=== Médias principais ===")
medias = df[[
    "latencia_media_ms",
    "fps_medio",
    "perda_%",
    "duracao_media_fixacao_s",
    "taxa_acerto_piscada_%"
]].mean()
print(medias)

# 4️⃣ Detectar sessões “problemáticas”
problemas = df[
    (df["fps_medio"] < 25) | 
    (df["perda_%"] > 1) | 
    (df["latencia_media_ms"] > 50) | 
    (df["duracao_media_fixacao_s"] < 0.1)
]

if len(problemas) > 0:
    print("\n⚠️ Sessões com possíveis problemas:")
    print(problemas[[
        "jogo",
        "fps_medio",
        "perda_%",
        "latencia_media_ms",
        "duracao_media_fixacao_s",
        "taxa_acerto_piscada_%"
    ]])
else:
    print("\n✅ Nenhuma sessão com problemas graves detectada!")

# 5️⃣ Gráficos

plt.figure(figsize=(14, 6))

# Latência
plt.subplot(2, 2, 1)
plt.plot(df["latencia_media_ms"], label="Latência Média (ms)")
plt.plot(df["latencia_desvio_ms"], label="Desvio Latência", linestyle="--")
plt.title("Latência")
plt.legend()

# FPS
plt.subplot(2, 2, 2)
plt.plot(df["fps_medio"], label="FPS Médio", color="green")
plt.plot(df["fps_desvio"], label="Desvio FPS", linestyle="--", color="lime")
plt.title("FPS")
plt.legend()

# Duração média das fixações
# Duração média das fixações em boxplot
import numpy as np

# Boxplot
plt.subplot(2, 2, 3)
plt.boxplot(df["duracao_media_fixacao_s"], 
            vert=True, 
            patch_artist=True, 
            boxprops=dict(facecolor="orange", color="black"),
            medianprops=dict(color="red"),
            whiskerprops=dict(color="black"),
            capprops=dict(color="black"),
            flierprops=dict(marker='o', markerfacecolor='red', markersize=6, linestyle='none'))

# Adiciona pontos individuais
y = df["duracao_media_fixacao_s"]
x = np.random.normal(1, 0.04, size=len(y))  # pequeno jitter no eixo x para não sobrepor
plt.scatter(x, y, color='blue', alpha=0.7, label='Sessões individuais')

plt.title("Duração Média das Fixações (s)")
plt.ylabel("Segundos")
plt.legend()

# Scatter FPS x Latência com cor pela perda
plt.subplot(2, 2, 4)
plt.scatter(df["fps_medio"], df["latencia_media_ms"], c=df["perda_%"], cmap="coolwarm", s=80)
plt.colorbar(label="Perda (%)")
plt.xlabel("FPS Médio")
plt.ylabel("Latência Média (ms)")
plt.title("Correlação FPS x Latência")

plt.tight_layout()
plt.show()

# 6️⃣ Interpretação automática
print("\n=== Interpretação automática ===")
media_latencia = df["latencia_media_ms"].mean()
media_fps = df["fps_medio"].mean()
media_fix = df["duracao_media_fixacao_s"].mean()
media_piscada = df["taxa_acerto_piscada_%"].mean()

# FPS
if media_fps < 25:
    print("❌ FPS baixo — otimizar loop ou reduzir carga gráfica.")
elif media_fps < 30:
    print("⚠️ FPS razoável, mas pode oscilar sob carga.")
else:
    print("✅ FPS estável!")

# Latência
if media_latencia > 50:
    print("❌ Latência alta — possível gargalo de processamento.")
elif media_latencia > 35:
    print("⚠️ Latência moderada — aceitável, mas pode melhorar.")
else:
    print("✅ Latência ótima!")

# Fixações
if media_fix < 0.2:
    print("⚠️ Fixações curtas — pode indicar dispersão visual.")
elif media_fix > 3:
    print("⚠️ Fixações muito longas — estímulo pouco dinâmico.")
else:
    print("✅ Fixações em faixa ideal.")

# Acerto de piscadas
if media_piscada < 80:
    print("⚠️ Acerto de piscadas baixo — calibrar o rastreador.")
else:
    print("✅ Acerto de piscadas adequado!")


# === Estatísticas das piscadas ===
print("\n=== Estatísticas das Piscadas ===")
print(df["taxa_acerto_piscada_%"].describe())

# Sessões com problemas de piscada
problema_piscada = df[df["taxa_acerto_piscada_%"] < 80]
if len(problema_piscada) > 0:
    print("\n⚠️ Sessões com baixa taxa de acerto de piscadas (<80%):")
    print(problema_piscada[[
        "jogo",
        "fps_medio",
        "latencia_media_ms",
        "taxa_acerto_piscada_%"
    ]])
else:
    print("\n✅ Todas as sessões tiveram boa taxa de acerto de piscadas!")


# === Gráfico: Taxa de acerto das piscadas ===
plt.figure(figsize=(10, 4))
plt.plot(df["taxa_acerto_piscada_%"], marker='o')
plt.title("Taxa de Acerto das Piscadas (%)")
plt.xlabel("Sessão")
plt.ylabel("Acerto (%)")
plt.grid(True)
plt.tight_layout()
plt.show()


# === Interpretação das piscadas ===
print("\n=== Interpretação das Piscadas ===")
media_piscadas = df["taxa_acerto_piscada_%"].mean()

if media_piscadas == 100:
    print("✅ Todas as piscadas foram detectadas corretamente — excelente calibração do rastreador!")
elif media_piscadas >= 90:
    print("🟩 Piscadas muito bem detectadas — sistema confiável.")
elif media_piscadas >= 80:
    print("🟨 Piscadas razoavelmente detectadas — pode melhorar a calibração.")
elif media_piscadas >= 60:
    print("🟧 Taxa baixa — provável problemas de iluminação ou posicionamento.")
else:
    print("🟥 Piscadas mal detectadas — revisar algoritmo ou qualidade do rastreamento.")
