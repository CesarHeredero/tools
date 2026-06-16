#!/usr/bin/env python3
import anthropic
import sys
from datetime import datetime

USER_PROFILE = """
## Perfil del Usuario - César
- Peso actual: 75.9 kg | Objetivo: 72 kg
- Grasa corporal: 20.7% | Objetivo: 17.1%
- IMC: 26 | TMB: 1670 kcal/día
- Grasa visceral: 8 | Edad metabólica: 39
- Músculo esquelético: 51.2% | Masa muscular: 57.2 kg
- Progreso desde 07/04/2025: -3.15 kg, -1 IMC, -1.4% grasa corporal

## Equipamiento disponible
- Gomas elásticas Fokky (varios niveles de resistencia)
- Mancuernas hasta 20 kg
- Banco de ejercicio
- Barra de dominadas
- Propio peso corporal

## Lesión — IMPORTANTE
- Labrum roto en el hombro
- NUNCA incluir ejercicios que carguen agresivamente el hombro (press militar pesado, dips profundos, etc.)
- La Rutina Labrum es OBLIGATORIA en cada sesión sin excepción

## Objetivos
- Correr más tiempo y mayor distancia (construir base aeróbica)
- Fortalecer el cuerpo completo (respetando el hombro)
- Reducir grasa abdominal
- Mejorar composición corporal global
"""

RUTINA_LABRUM = """
## ⚕️ RUTINA LABRUM — OBLIGATORIA EN CADA SESIÓN (4 ejercicios con goma)
Esta rutina protege y rehabilita el hombro con labrum roto. Debe incluirse SIEMPRE.

1. **Rotación externa de hombro con goma** — 3 series × 15 reps cada lado
   (codo a 90°, pegado al cuerpo, rotación hacia afuera)

2. **Rotación interna de hombro con goma** — 3 series × 15 reps cada lado
   (codo a 90°, pegado al cuerpo, rotación hacia adentro)

3. **Abducción horizontal con goma** — 3 series × 12 reps cada lado
   (brazo al frente, abrir hacia el lado con control)

4. **Row en "W" con goma (retracción escapular)** — 3 series × 12 reps
   (tirar hacia atrás formando W con los brazos, apretar escápulas)

⏱️ Tiempo estimado Rutina Labrum: 15-20 minutos
🔑 Siempre realizarla con goma de resistencia LIGERA-MEDIA con control total del movimiento
"""

PERIODIZACION = """
## Periodización semanal recomendada
- Lunes:     Piernas + Core
- Martes:    Running (rodaje suave o intervalos)
- Miércoles: Tren superior (sin carga agresiva en hombro)
- Jueves:    Descanso activo o running corto suave
- Viernes:   Cuerpo completo (funcional)
- Sábado:    Running largo (rodaje extensivo)
- Domingo:   Descanso total / movilidad
"""

SYSTEM_PROMPT = f"""Eres un entrenador personal experto y fisioterapeuta deportivo especializado en composición corporal, running y rehabilitación de lesiones de hombro.

Tu misión es generar rutinas de ejercicio diarias personalizadas, progresivas y seguras.

{USER_PROFILE}

{RUTINA_LABRUM}

{PERIODIZACION}

## Instrucciones para generar cada rutina

1. **Siempre incluye la Rutina Labrum** (los 4 ejercicios de goma) — es obligatoria e innegociable
2. Adapta la sesión al día de la semana según la periodización
3. Incluye siempre:
   - Calentamiento (5-10 min)
   - Bloque principal con series, repeticiones, descansos y carga orientativa
   - Vuelta a la calma / estiramientos (5-10 min)
   - Rutina Labrum (puede ir al inicio o al final según la sesión)
4. Indica la duración total estimada
5. Si el usuario menciona cómo se siente (cansancio, dolor, tiempo disponible), adapta la rutina
6. Para sesiones de running, incluye calentamiento, el rodaje con ritmo orientativo y enfriamiento
7. Añade motivación breve y un recordatorio de la progresión hacia los objetivos
8. Responde siempre en español

## Principios de entrenamiento
- Progresión gradual (no sobreentrenar)
- Priorizar técnica sobre peso
- El hombro lesionado es una línea roja: ante la duda, omite el ejercicio
- Combinar fuerza y cardio para maximizar pérdida de grasa
- Respetar el descanso como parte del entrenamiento
"""


def get_day_context() -> tuple[str, str]:
    days = {
        0: "lunes",
        1: "martes",
        2: "miércoles",
        3: "jueves",
        4: "viernes",
        5: "sábado",
        6: "domingo",
    }
    now = datetime.now()
    return days[now.weekday()], now.strftime("%d/%m/%Y")


def generate_routine(user_input: str = "") -> None:
    client = anthropic.Anthropic()
    day_name, date_str = get_day_context()

    if user_input:
        message = (
            f"Hoy es {day_name}, {date_str}. Nota del usuario: {user_input}\n\n"
            "Genera mi rutina de ejercicio para hoy. Recuerda incluir siempre la Rutina Labrum."
        )
    else:
        message = (
            f"Hoy es {day_name}, {date_str}. "
            "Genera mi rutina de ejercicio para hoy según la periodización. "
            "Incluye siempre la Rutina Labrum."
        )

    print(f"\n💪 Generando tu rutina para hoy ({day_name}, {date_str})...")
    print("=" * 65)

    with client.messages.stream(
        model="claude-opus-4-7",
        max_tokens=4096,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": message}],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)

    print(f"\n{'=' * 65}")
    print("✅ ¡Rutina generada! Recuerda completar la Rutina Labrum. 🏋️\n")


def interactive_mode() -> None:
    print("\n🏃 AGENTE DE RUTINAS DE EJERCICIO PERSONALIZADO — CÉSAR")
    print("=" * 65)
    print("Escribe 'salir' o pulsa Ctrl+C para terminar.")

    while True:
        try:
            user_input = input(
                "\n¿Algo específico para hoy? (cansancio, tiempo disponible, etc.)\n"
                "Pulsa Enter para rutina automática según el día: "
            ).strip()

            if user_input.lower() in ["salir", "exit", "quit", "q"]:
                print("\n¡Hasta mañana! 💪\n")
                break

            generate_routine(user_input)

            another = input("¿Generar otra rutina o hacer una pregunta? (s/n): ").strip().lower()
            if another not in ["s", "si", "sí", "yes", "y"]:
                print("\n¡Hasta mañana! 💪\n")
                break

        except KeyboardInterrupt:
            print("\n\n¡Hasta mañana! 💪\n")
            break


if __name__ == "__main__":
    if len(sys.argv) > 1:
        generate_routine(" ".join(sys.argv[1:]))
    else:
        interactive_mode()
