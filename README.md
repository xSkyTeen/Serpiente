# S.E.R.P.I.E.N.T.E.

## Sistema de Evaluación de Riesgos y Prevención con Inferencia Entrópica

S.E.R.P.I.E.N.T.E. es un sistema industrial de seguridad activa basado en Visión Artificial y Lógica Difusa, orientado a la prevención de accidentes en zonas de maquinaria pesada.

El sistema utiliza YOLOv8 para detección en tiempo real y un motor de inferencia difusa para evaluar el riesgo de manera dinámica y ejecutar acciones preventivas automáticas.

---

## Arquitectura del Proyecto

El sistema está organizado de forma modular para garantizar escalabilidad, mantenibilidad y despliegue flexible.

### Estructura de Carpetas

* agents/: contiene los tres motores principales del sistema (Vision, Brain y Executor).
* backend/: servidor y lógica de API para el manejo de datos y eventos.
* core/: librerías compartidas y gestión de base de datos mediante DatabaseManager.
* frontend/: interfaz de monitoreo y dashboard en tiempo real.
* main_launcher.py: script maestro para la ejecución orquestada de los agentes.

---

## Componentes del Sistema

### Vision Core (Detector)

* Inferencia en tiempo real utilizando YOLOv8.
* Tracking de centroide para mayor estabilidad en la detección.
* Streaming de video mediante ZeroMQ.

### Agent Brain (Cerebro)

* Motor de inferencia con 12 reglas de Lógica Difusa.
* Evaluación de riesgo basada en distancia, velocidad y uso de celular.

### Agent Executor (Físico)

* Control de interlocks y sistemas de parada.
* Activación de sirenas y alertas.
* Envío de notificaciones críticas vía Telegram con lógica de persistencia.

---

## Requisitos Técnicos

* Python 3.9 o superior
* OpenCV para procesamiento de imagen
* Ultralytics YOLOv8
* ZeroMQ para streaming de alta velocidad
* Supabase o PostgreSQL para persistencia de telemetría y logs

---

## Instalación y Uso

### Instalación de dependencias

```
pip install -r requirements.txt
```

### Configuración

Configurar el archivo `.env` con las credenciales de la base de datos y el token de Telegram.

### Ejecución del sistema completo

Para iniciar los tres agentes simultáneamente (Vision, Brain y Executor), ejecutar el lanzador principal:

```
python main_launcher.py
```

---

## Consideraciones

Este sistema ha sido desarrollado para entornos de alta exigencia industrial, donde la seguridad operativa es crítica y no admite compromisos.
