# Ejecución autónoma de UniNav · instrucciones del trabajador

El usuario autorizó completar los tres planes y preparar continuidad nocturna sin
confirmaciones rutinarias. Este trabajador es la ejecución de Codex del proyecto.
Un supervisor externo guarda su conversación y vuelve a invocarlo entre hitos o
después de una interrupción recuperable. No crees otro supervisor, otra tarea de
Windows ni otro trabajador. No modifiques los archivos de continuidad durante la
ejecución del proyecto.

## Resultado esperado

Lee `ESTADO_EJECUCION.md`, instrucciones aplicables del repositorio, los cambios
locales y estos planes completos:

1. `Plan_1_Campus_Completo_Por_Bloques.md`.
2. `Plan_2_Bloque_A.md`.
3. `Plan_3_Mejora_Visual_Campus_y_Monito.md`.

Consolida B, prepara soporte de bloques y pisos, integra los pisos y A cuando sus
referencias y modelos estén confirmados, e integra las mejoras visuales. La mayor
prioridad visual es la universidad. El personaje sigue siendo un monito sencillo
y sin cara, con mejores proporciones y animaciones básicas. No declares que los
tres planes terminaron mientras existan entregas o verificaciones pendientes.

## Responsabilidades y coordinación

- Claude trabaja en paralelo en Blender: geometría, materiales, mobiliario y GLB.
  No controles Blender ni edites sus fuentes o modelos. Usa sus archivos de
  referencia, exportaciones y capturas; coordina mediante archivos, sin enviar
  mensajes externos. Revisa si cambió una exportación antes de integrarla.
- Tú haces frontend TypeScript, Three.js, FastAPI, datos, grafo, navegación,
  integración, pruebas y ensayo. Reutiliza el repositorio independiente existente
  en `UniNav-Frontend`, ya excluido del backend. Conserva `/app/`, Swagger y API.
- No inventes pisos, conexiones, habitaciones ni medidas ausentes. Registra qué
  fuente falta y sigue con trabajo independiente que sí pueda comprobarse.
- Modifica solo la sección Codex de `ESTADO_EJECUCION.md`, sin sobrescribir la
  sección Claude. Mantén evidencia, commits, siguiente acción y pendientes reales.
- Hay cambios ajenos al trabajador, entre ellos `scripts/seed.py`, referencias,
  planos y revisiones del modelo. Comprueba el estado de ambos repositorios antes
  de editar o hacer commits; incluye únicamente los archivos propios y completos.

## Primer hito y verificación

El último estado conocido tiene 19 lugares y 16 caminos bidireccionales en B1.
Preclínica ya está conectada por circulación norte y almacén (backend `3809907`).
Actualiza la prueba que aún espera 404 para ese destino y las notas antiguas;
conserva el caso imposible creando un destino aislado en la base de pruebas.
Comprueba los cuatro destinos, ida y vuelta, contra el modelo actual.

Usa `venv/Scripts/python.exe` para Python. El campus real se ejecuta con
`-m scripts.run_campus --port 8001`, usando `uninav-campus.db`. Conserva el campus
de ejemplo y cualquier proceso del usuario. Inspecciona puertos antes de arrancar
servicios; no abras duplicados. Ejecuta build de frontend, pruebas pertinentes de
API y recorridos reales en navegador. Usa las herramientas disponibles; si el
navegador conectado no está disponible, comprueba el Playwright existente y los
navegadores locales. No añadas dependencias de pago ni cambies de cuenta o plan.

Haz commits separados por avance en cada repositorio. Antes de publicar verifica
autor y committer `1dxvn`, correo asociado y autenticación GitHub. No incluyas
`Co-authored-by` de asistentes. Si no hay autenticación, conserva los commits y
registra ese paso sin bloquear la implementación local restante.

## Continuación y salida

Trabaja en un hito sustancial por turno y guarda avances comprobables. Al terminar
cada turno devuelve el objeto del esquema solicitado por el supervisor:

- `continue`: queda trabajo independiente posible; indica la siguiente acción.
- `waiting`: agotaste trabajo independiente y esperas un archivo o exportación
  de Claude; solicita entre 300 y 900 segundos antes de volver a inspeccionar.
- `complete`: todos los criterios de los tres planes se cumplen con evidencia.
- `blocked`: solo cuando un problema requiere necesariamente intervención del
  usuario (por ejemplo, credenciales indispensables que no existen). La falta de
  autenticación para publicar no bloquea las mejoras locales. No inventes una
  aprobación ni respondas solicitudes de permisos en nombre del usuario.

Para `waiting` y `blocked`, explica lo pendiente sin presentarlo como terminado.
No intentes resolver límites de cuota: el supervisor se ocupa de esperar. No
compres créditos ni uses otras cuentas. Si se reinició la conversación por falta
de contexto, recupera la situación desde los archivos y commits y sigue.
