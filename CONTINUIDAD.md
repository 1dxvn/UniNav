# Continuidad automática de UniNav

El supervisor local ejecuta el trabajo de Codex descrito en
[`EJECUCION_AUTONOMA.md`](EJECUCION_AUTONOMA.md). Usa una conversación propia y
guarda su identificador en `.uninav-continuity/state.json`. No usa `--last`, por
lo que otro chat o Claude no cambia la conversación que se reanuda.

## Uso en Windows

Desde la raíz del backend, en PowerShell:

```powershell
.\scripts\continuity.ps1 Start
.\scripts\continuity.ps1 Status
.\scripts\continuity.ps1 Logs
.\scripts\continuity.ps1 Stop
```

`Start` registra una tarea del usuario actual y la inicia sin abrir ventanas.
La tarea vuelve a ejecutarse cada cinco minutos y al iniciar sesión en Windows;
si el supervisor sigue vivo, Windows no abre otro. Además, un bloqueo del sistema
operativo protege la carpeta de estado. Tras `Stop`, los disparadores no vuelven
a habilitar el trabajo: se necesita otro `Start` explícito.

`Install` solo registra la tarea; `Uninstall` solicita parar y la elimina. No
cambian la configuración global de Codex ni las instrucciones de Claude. El
supervisor usa Python estándar del entorno existente; no añade dependencias.

## Qué sucede durante la noche

1. Invoca `codex exec --json` con acceso completo y aprobaciones de comandos en
   `never`, usando la autenticación guardada del CLI.
2. Registra cada hito, su respuesta estructurada y la conversación. Sigue con
   `codex exec resume <ID>` mientras quede trabajo independiente.
3. Si Codex informa un límite de uso, consulta `account/rateLimits/read` del
   app-server oficial. Espera a que se restablezcan las ventanas agotadas y añade
   diez segundos de margen. Si no obtiene una hora válida, reintenta a los quince
   minutos. No cambia de cuenta ni compra créditos.
4. Ante errores temporales aplica una espera progresiva. Después de reiniciar el
   supervisor conserva la espera y el identificador. Si se agotó el contexto y
   Codex no pudo compactarlo, abre una conversación nueva que recupera el trabajo
   desde archivos y el último hito guardado. Si el trabajador no produce eventos
   durante treinta minutos, lo reinicia desde su conversación guardada.
5. Si espera una exportación de Claude, revisa de nuevo después del intervalo
   indicado. Los planes incompletos siguen registrados como pendientes.
6. Al completar el objetivo deja de llamar al modelo. Si hacen falta credenciales
   o una intervención indispensable, registra `needs_attention` con la causa.

El trabajo de frontend continúa siendo TypeScript. Este supervisor es una
herramienta local de desarrollo del backend, escrita en Python y PowerShell.

## Estado y registros

La carpeta `.uninav-continuity/` está excluida de Git. Contiene:

- `state.json`: estado, PID del supervisor y trabajador, conversación, hito y hora
  del siguiente intento, si existe.
- `control.json`: habilitado o detenido por el usuario.
- `supervisor.log`: resumen de arranques, esperas, recuperaciones y resultados.
- `turn-*.events.jsonl`, `turn-*.stderr.log`, `turn-*.result.json`: evidencia local
  de cada invocación. Pueden contener código y salidas privadas del proyecto.
- `supervisor.lock`: bloqueo que no queda retenido después de morir el proceso.

El trabajador mantiene también su sección de `ESTADO_EJECUCION.md`, compartida
con Claude. El supervisor nunca lee `auth.json` ni registra tokens de acceso.

## Alcance real

La tarea necesita Windows encendido, una sesión de usuario iniciada, conexión y
autenticación válida. Tras apagar el PC, retoma al iniciar sesión; no trabaja
mientras el equipo está apagado. Usa la cuenta y el modelo configurados en el CLI.
Los límites y la facturación de esa cuenta siguen aplicándose. No habilita pagos
ni recarga automática.

El supervisor termina el árbol de procesos que abre al finalizar cada invocación
o al solicitar `Stop`, para evitar trabajadores huérfanos. Los servidores propios
del usuario que ya estaban abiertos no pertenecen a ese árbol. El trabajador debe
comprobar los servicios existentes antes de volver a iniciarlos.

Los permisos de aplicaciones externas y MCP siguen sus propias reglas. La
automatización no responde por el usuario a consentimientos o autenticaciones.
La falta de login para publicar en GitHub no debe impedir las mejoras locales.

## Verificación realizada

- Pruebas con CLI simulado: agotamiento de cuota seguido de reanudación de la
  misma conversación, continuación entre hitos, conservación de la espera tras
  reiniciar, errores de autenticación, parada y rechazo de procesos duplicados.
- Prueba real: dos turnos de Codex conservaron un dato del primero sin repetirlo
  en el segundo. Evidencia local en `.uninav-continuity/smoke/validation.json`.
- Programador de tareas: se terminó el supervisor de prueba y se volvió a
  iniciarlo; conservó la espera. Un segundo supervisor fue rechazado y `Stop`
  detuvo el primero. Evidencia en `.uninav-continuity/scheduler-validation.json`.
- Windows: se comprobó que cerrar el Job Object termina también los procesos
  descendientes. La consulta real de cuotas respondió con la cuenta guardada.

La prueba de cuota usa un fallo simulado; no consume deliberadamente toda la
cuota real. La recuperación del Programador de tareas se verificó iniciando de
nuevo la tarea registrada; sus disparadores de cinco minutos y de inicio de
sesión quedan instalados para recuperaciones futuras.

Referencias: [ejecución no interactiva y reanudación](https://learn.chatgpt.com/docs/non-interactive-mode),
[endpoint de cuotas](https://learn.chatgpt.com/docs/app-server#6-rate-limits-chatgpt).
