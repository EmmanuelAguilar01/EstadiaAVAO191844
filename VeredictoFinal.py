import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns

# Función para realizar el análisis estadístico completo


def analisis_estadistico(datos_yolo, datos_transformer, nombre_metrica):
    print(f"\n{'='*50}")
    print(f"ANÁLISIS ESTADÍSTICO PARA: {nombre_metrica}")
    print(f"{'='*50}")

    # Calcular diferencias pareadas
    diferencias = datos_yolo - datos_transformer

    # Estadísticas descriptivas
    print(f"\nEstadísticas descriptivas:")
    print(
        f"YOLOv5 - Media: {np.mean(datos_yolo):.4f}, Desviación estándar: {np.std(datos_yolo):.4f}")
    print(
        f"Transformer - Media: {np.mean(datos_transformer):.4f}, Desviación estándar: {np.std(datos_transformer):.4f}")
    print(f"Diferencia media: {np.mean(diferencias):.4f}")

    # Prueba de Shapiro-Wilk
    stat_dif, p_value_dif = stats.shapiro(diferencias)
    print("\nPrueba de normalidad (Shapiro-Wilk) para las diferencias:")
    print(f"Estadístico: {stat_dif:.4f}")
    print(f"Valor p: {p_value_dif:.4f}")

    es_normal = p_value_dif > 0.05
    if es_normal:
        print("✓ Los datos siguen una distribución normal (p > 0.05)")
    else:
        print("✗ Los datos NO siguen una distribución normal (p ≤ 0.05)")

    # Prueba de Bartlett (Igualdad de varianzas)
    bartlett_stat, bartlett_p = stats.bartlett(datos_yolo, datos_transformer)
    print("\nPrueba de igualdad de varianzas (Bartlett):")
    print(f"Estadístico: {bartlett_stat:.4f}")
    print(f"Valor p: {bartlett_p:.4f}")

    varianzas_iguales = bartlett_p > 0.05
    if varianzas_iguales:
        print("✓ Las varianzas son iguales (p > 0.05)")
    else:
        print("✗ Las varianzas NO son iguales (p ≤ 0.05)")

    # Selección de prueba estadística según los resultados anteriores
    if es_normal:
        # Prueba t-student para muestras pareadas
        t_stat, t_p_value = stats.ttest_rel(datos_yolo, datos_transformer)
        print("\nPrueba t-student para muestras pareadas:")
        print(f"Estadístico t: {t_stat:.4f}")
        print(f"Valor p: {t_p_value:.4f}")

        if t_p_value <= 0.05:
            if np.mean(datos_yolo) > np.mean(datos_transformer):
                print(
                    "✓ Hay diferencia significativa: YOLOv5 es superior a Transformer (p ≤ 0.05)")
            else:
                print(
                    "✓ Hay diferencia significativa: Transformer es superior a YOLOv5 (p ≤ 0.05)")
        else:
            print("✗ No hay diferencia significativa entre los modelos (p > 0.05)")
    else:
        # Prueba de Wilcoxon para muestras pareadas (alternativa no paramétrica)
        wilcoxon_stat, wilcoxon_p = stats.wilcoxon(
            datos_yolo, datos_transformer)
        print("\nPrueba de Wilcoxon para muestras pareadas (no paramétrica):")
        print(f"Estadístico: {wilcoxon_stat:.4f}")
        print(f"Valor p: {wilcoxon_p:.4f}")

        if wilcoxon_p <= 0.05:
            if np.mean(datos_yolo) > np.mean(datos_transformer):
                print(
                    "✓ Hay diferencia significativa: YOLOv5 es superior a Transformer (p ≤ 0.05)")
            else:
                print(
                    "✓ Hay diferencia significativa: Transformer es superior a YOLOv5 (p ≤ 0.05)")
        else:
            print("✗ No hay diferencia significativa entre los modelos (p > 0.05)")

    # Visualización de los datos
    plt.figure(figsize=(12, 6))

    # Boxplot comparativo
    plt.subplot(1, 2, 1)
    sns.boxplot(data=[datos_yolo, datos_transformer])
    plt.xticks([0, 1], ['YOLOv5', 'Transformer'])
    plt.title(f'Comparación de {nombre_metrica}')

    # Histograma de diferencias
    plt.subplot(1, 2, 2)
    sns.histplot(diferencias, kde=True)
    plt.axvline(x=0, color='red', linestyle='--')
    plt.title(f'Distribución de diferencias en {nombre_metrica}')

    plt.tight_layout()
    plt.show()

    return {
        'metrica': nombre_metrica,
        'media_yolo': np.mean(datos_yolo),
        'media_transformer': np.mean(datos_transformer),
        'diferencia_media': np.mean(diferencias),
        'es_normal': es_normal,
        'varianzas_iguales': varianzas_iguales,
        'p_valor': t_p_value if es_normal else wilcoxon_p,
        'conclusion': 'Diferencia significativa' if (t_p_value if es_normal else wilcoxon_p) <= 0.05 else 'No hay diferencia significativa',
        'modelo_superior': 'YOLOv5' if np.mean(datos_yolo) > np.mean(datos_transformer) else 'Transformer'
    }


# Datos de precisión de las experimentaciones
yolo_precision = np.array([
    77.26, 77.26, 84.24, 82.79, 86.72, 82.72, 81.28, 85.93,
    82.12, 82.12, 82.19, 87.45, 80.20, 86.56, 86.56, 82.12
]) / 100

transformer_precision = np.array([
    67.20, 64.70, 66.40, 70.20, 69.80, 68.40, 73.40, 74.80,
    74.70, 75.00, 74.70, 70.40, 67.90, 71.20, 72.10
]) / 100

# Datos de error en las experimentaciones
yolo_error = np.array([
    22.48, 22.48, 19.15, 20.29, 18.14, 20.31, 21.38, 20.44,
    19.94, 19.94, 20.47, 18.77, 19.61, 19.42, 19.42, 19.94
]) / 100

transformer_error = np.array([
    32.80, 35.30, 33.60, 29.80, 30.20, 31.60, 26.60, 25.20,
    25.30, 25.00, 25.30, 29.60, 32.10, 28.80, 27.90
]) / 100

# Convertir los tiempos (HH:MM:SS) a segundos
def tiempo_a_segundos(tiempo_str):
    h, m, s = map(int, tiempo_str.split(':'))
    return h * 3600 + m * 60 + s


yolo_tiempo = np.array([
    tiempo_a_segundos("1:25:50"), tiempo_a_segundos(
        "1:31:02"), tiempo_a_segundos("1:29:22"),
    tiempo_a_segundos("1:20:04"), tiempo_a_segundos(
        "1:24:51"), tiempo_a_segundos("1:29:16"),
    tiempo_a_segundos("1:53:04"), tiempo_a_segundos(
        "1:34:45"), tiempo_a_segundos("2:05:42"),
    tiempo_a_segundos("2:07:23"), tiempo_a_segundos(
        "1:55:34"), tiempo_a_segundos("2:00:14"),
    tiempo_a_segundos("3:24:15"), tiempo_a_segundos(
        "2:11:15"), tiempo_a_segundos("2:26:12"),
    tiempo_a_segundos("2:09:35")
])

transformer_tiempo = np.array([
    tiempo_a_segundos("3:17:29"), tiempo_a_segundos(
        "1:12:30"), tiempo_a_segundos("1:16:46"),
    tiempo_a_segundos("1:11:04"), tiempo_a_segundos(
        "1:19:20"), tiempo_a_segundos("1:56:08"),
    tiempo_a_segundos("1:22:08"), tiempo_a_segundos(
        "1:39:22"), tiempo_a_segundos("2:19:18"),
    tiempo_a_segundos("1:45:04"), tiempo_a_segundos(
        "1:45:35"), tiempo_a_segundos("2:20:54"),
    tiempo_a_segundos("2:01:30"), tiempo_a_segundos(
        "3:07:19"), tiempo_a_segundos("1:46:12")
])

# Ajustar los la longitud de los datos para que tengan la misma cantidad de elementos
min_len = min(len(yolo_precision), len(transformer_precision))
yolo_precision = yolo_precision[:min_len]
transformer_precision = transformer_precision[:min_len]
yolo_error = yolo_error[:min_len]
transformer_error = transformer_error[:min_len]
yolo_tiempo = yolo_tiempo[:min_len]
transformer_tiempo = transformer_tiempo[:min_len]

# Realizar análisis para cada métrica
resultados = []
resultados.append(analisis_estadistico(
    yolo_precision, transformer_precision, "Precisión"))
resultados.append(analisis_estadistico(yolo_error, transformer_error, "Error"))
resultados.append(analisis_estadistico(
    yolo_tiempo, transformer_tiempo, "Tiempo (segundos)"))

# Crear una tabla resumen
df_resultados = pd.DataFrame(resultados)
print("\nTabla resumen de todos los análisis:")
print(df_resultados[['metrica', 'media_yolo', 'media_transformer',
      'diferencia_media', 'p_valor', 'conclusion', 'modelo_superior']])

# Crear un gráfico de barras comparativo para todas las métricas
plt.figure(figsize=(12, 6))
metricas = df_resultados['metrica'].tolist()
media_yolo = df_resultados['media_yolo'].tolist()
media_transformer = df_resultados['media_transformer'].tolist()

x = range(len(metricas))
width = 0.35

plt.bar([i - width/2 for i in x], media_yolo, width, label='YOLOv5')
plt.bar([i + width/2 for i in x], media_transformer,
        width, label='Transformer')

plt.ylabel('Valor medio')
plt.title('Comparación de métricas entre YOLOv5 y Transformer')
plt.xticks(x, metricas)
plt.legend()

for i, metrica in enumerate(metricas):
    if df_resultados.iloc[i]['conclusion'] == 'Diferencia significativa':
        plt.text(i, max(media_yolo[i], media_transformer[i]) + 0.01, '*',
                 ha='center', va='bottom', fontsize=16)

plt.tight_layout()
plt.show()
