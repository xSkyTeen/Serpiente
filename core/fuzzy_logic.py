def trapecio(x, a, b, c, d):
    """Función de pertenencia Trapezoidal"""
    return max(min((x - a) / (b - a), 1, (d - x) / (d - c)), 0)


def triangulo(x, a, b, c):
    """Función de pertenencia Triangular"""
    return max(min((x - a) / (b - a), (c - x) / (c - b)), 0)


def inferencia_mamdani_riesgo(distancia_px, tiene_celular):
    """
    Calcula el % de Riesgo (0-100) usando lógica difusa avanzada.
    Input:
        - Distancia: Pixeles hacia la línea (Negativo = Cruzó).
        - Celular: Booleano.
    """
    # 1. FUZZIFICACIÓN (Entradas)

    # Conjuntos de Distancia
    # Peligro: x < 0 (Cruzó) hasta 50px
    mu_peligro = trapecio(distancia_px, -999, -100, 0, 50)
    # Advertencia: Entre 20px y 150px
    mu_advertencia = triangulo(distancia_px, 20, 100, 200)
    # Seguro: Más de 150px
    mu_seguro = trapecio(distancia_px, 150, 250, 999, 9999)

    # Conjuntos de Distracción
    mu_distraccion = 1.0 if tiene_celular else 0.0
    mu_atento = 1.0 - mu_distraccion

    # 2. EVALUACIÓN DE REGLAS (Inferencia)

    # R1: SI (Peligro) Y (Distracción) -> RIESGO CRITICO (100)
    activacion_r1 = min(mu_peligro, mu_distraccion)

    # R2: SI (Peligro) Y (Atento) -> RIESGO ALTO (80)
    activacion_r2 = min(mu_peligro, mu_atento)

    # R3: SI (Advertencia) Y (Distracción) -> RIESGO MEDIO (60)
    activacion_r3 = min(mu_advertencia, mu_distraccion)

    # R4: SI (Advertencia) Y (Atento) -> RIESGO BAJO (30)
    activacion_r4 = min(mu_advertencia, mu_atento)

    # R5: SI (Seguro) -> RIESGO NULO (0)
    activacion_r5 = mu_seguro

    # 3. DESFUSIFICACIÓN (Centroide Simplificado)
    numerador = (activacion_r1 * 100) + (activacion_r2 * 80) + \
                (activacion_r3 * 60) + (activacion_r4 * 30) + (activacion_r5 * 0)

    denominador = sum([activacion_r1, activacion_r2, activacion_r3, activacion_r4, activacion_r5])

    if denominador == 0: return 0.0
    return numerador / denominador