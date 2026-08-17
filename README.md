# 🐜 Hormiga de Langton

Autor: **KALEVI LATVA AIJO ALEGRIA** · Windows · 100 % local

Un **autómata celular**: reglas simplísimas que producen un comportamiento complejo y
sorprendente. Una "hormiga" recorre una cuadrícula girando y pintando celdas; tras miles de
pasos emerge, de la nada, una **"autopista"** periódica. Esta es una versión mejorada de un
proyecto propio, ahora **rápida, con reglas multicolor y zoom fluido**.

## ⬇️ Descargar (sin instalar Python)

En **[Releases](../../releases)**: `HormigaDeLangton_carpeta.zip` → descomprime y ejecuta
**`HormigaDeLangton.exe`**.
*(Es un `.exe` sin firmar: Windows SmartScreen puede pedir "Más info → Ejecutar de todos modos".)*

## ✨ Qué mejoré respecto a la versión original

- ⚡ **Velocidad real:** antes ~10 pasos/seg (la autopista tardaba minutos). Ahora la
  velocidad se mide en **pasos por segundo** (simulación por tiempo, independiente de los
  FPS): desde 1/seg para entenderla hasta miles, más un modo **Turbo**.
- 🌈 **Reglas generalizadas (turmites):** además de la clásica `RL`, reglas multicolor como
  `RLR`, `LLRR`, `LRRRRRLLR`… → patrones emergentes distintos y preciosos.
- 🖼️ **Render vectorizado** con NumPy + recorte por *viewport*: zoom y paneo sin lag aunque
  la cuadrícula sea grande.
- 🐜 **Añade o quita varias hormigas** (interacciones caóticas).
- 🧭 **Mundo acotado con rebote:** la hormiga rebota en los bordes (no se teletransporta) y
  el mundo se muestra completo, sin salirse de lo visible.
- 🖥️ **Pantalla completa** (tecla **F**) y **controles tipo mapa** (＋ − ◎ centrar) en la
  esquina inferior derecha del visualizador.
- 🧹 Código limpio (quité restos del entorno original) y UI en negrita, más legible.

## ▶️ Controles

| Acción | Cómo |
|--------|------|
| Encender/apagar celda | Clic izquierdo |
| Mover el lienzo | Clic derecho + arrastrar |
| Zoom | Rueda del mouse, o botones **＋ / −** del mapa |
| Centrar la vista | Botón **◎** del mapa |
| Play / Pausa | **Espacio** o botón *(empieza en pausa)* |
| Un paso | **→** o botón |
| Reiniciar / Limpiar | **R** / **C** |
| Turbo (máx. velocidad) | **T** o botón |
| Velocidad (pasos/seg) | **+** / **−** o botones |
| Añadir / Quitar hormiga | **A** / **Shift+A** o botones |
| Cambiar de regla | **,** / **.** o botones |
| Pantalla completa | **F** (Esc para salir) |
| Ayuda | **H** |

## 🧠 La regla (clásica `RL`)

- Celda **apagada** → la hormiga gira a la **derecha**, la enciende y avanza.
- Celda **encendida** → gira a la **izquierda**, la apaga y avanza.

Con más letras (colores) el patrón cambia por completo. Fases típicas de la clásica: caótica
(0–500), repetitiva (500–10.000) y **autopista** estable (>10.000 pasos). *(En este mundo
acotado la hormiga rebota en los bordes en vez de seguir al infinito.)*

## ⚙️ Tecnología

- **Python 3.12** + **pygame** 2.6 + **NumPy**.
- Simulación en un `bytearray`; render con `pygame.image.frombuffer` desde una paleta NumPy.
- Reutiliza el entorno `..\.venv_face`; si no, `instalar.bat` crea `.venv`.

## 🔨 Generar el `.exe`

`pip install pyinstaller` y doble clic en **`crear_exe.bat`** → queda en `dist\HormigaDeLangton\`.

---

Desarrollado y documentado por **KALEVI LATVA AIJO ALEGRIA**.
