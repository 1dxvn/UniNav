# Plan 1 · Completar UniNav por bloques y pisos

Fecha: 7 de noviembre de 2026. Estado: plan de trabajo; las tareas pendientes no se consideran implementadas por aparecer aquí.

## 1. Objetivo y relación con los otros planes

Completar un campus navegable de la universidad, organizado por bloques y, dentro de cada bloque, por pisos. El usuario debe poder iniciar sesión, encontrar un destino confirmado y llegar con el personaje utilizando una ruta calculada por FastAPI.

Cada entrega debe conservar una versión que arranque y se pueda presentar. El avance se medirá por pisos y bloques verificados, además de por funciones terminadas.

Este es el plan general. El [Plan 2](Plan_2_Bloque_A.md) desarrolla el trabajo específico del Bloque A. El [Plan 3](Plan_3_Mejora_Visual_Campus_y_Monito.md) mejora la apariencia del modelo existente y puede ejecutarse mientras se consiguen referencias para nuevas plantas. La prioridad visual acordada es la universidad; el monito recibirá un retoque breve, sencillo y sin cara.

El archivo `Plan_UniNav_Una_Noche.md` se conserva como antecedente de la primera entrega.

## 2. Punto de partida revisado

- Backend FastAPI con autenticación, lugares, caminos, cálculo de rutas y otras funciones del proyecto.
- Frontend independiente en `UniNav-Frontend/`, escrito en TypeScript con Vite y Three.js.
- Frontend servido en `/app/`, redirección de `/` y conservación de Swagger y los endpoints existentes.
- Modelo del primer piso del Bloque B, coordenadas documentadas y tres referencias de alineación.
- Inicio de sesión, registro, búsqueda, selección de piso, ruta, seguimiento, pausa, cancelación y movimiento manual.
- Datos reales de desarrollo separados del campus de ejemplo mediante `uninav-campus.db`.
- Código de datos del primer piso con 19 lugares y 16 caminos bidireccionales. La conexión de Preclínica ya está descrita en el modelo y en el backend.
- Nuevas puertas y mobiliario entregados por Claude. Se debe consolidar el ensayo completo de esa revisión y actualizar las pruebas y notas que aún describen Preclínica como desconectada.

El inventario de todos los bloques, sus plantas y sus alturas todavía debe completarse. La lista de niveles 0–7 del backend es una convención del software; la existencia y denominación de cada planta se confirmarán con las referencias disponibles.

## 3. Responsabilidades

| Responsable | Trabajo principal | Evidencia de entrega |
| --- | --- | --- |
| Claude | Geometría, estructura, fachadas, puertas, escaleras, rampas, ascensores, materiales, mobiliario y exportaciones desde Blender. | Fuente editable, GLB, captura superior y referencias del modelo. |
| Codex | Frontend, FastAPI, datos, grafo, rutas, controles, animaciones integradas, carga de modelos, pruebas y publicación. | Código, build, respuestas de API, capturas y resultados de pruebas. |
| Usuario | Confirmar datos que las fuentes no permitan resolver: nombres, servicios, prioridades y referencias físicas. | Correcciones concretas incorporadas al inventario. |

El modelado se reserva para Claude. Codex revisa la integración y comunica problemas de geometría mediante archivos y capturas de rutas. El código y los mensajes de la aplicación siguen la convención de inglés; estos planes están en español.

## 4. Orden de ejecución

| Hito | Alcance | Condición de salida |
| --- | --- | --- |
| H0 | Consolidar la última revisión del piso 1 de B. | Destinos anteriores y Preclínica comprobados con el modelo actual. |
| H1 | Inventariar bloques y preparar el soporte de varios modelos. | Bloques y pisos identificados, con estados de referencia. |
| H2 | Conectar dos pisos de B. | Recorrido vertical real, de ida y vuelta, sin atravesar geometría. |
| H3 | Completar los pisos confirmados de B. | Primer bloque con todos los destinos acordados y sus conexiones verificadas. |
| H4 | Incorporar A siguiendo el Plan 2. | A navegable y conectado con B por un trayecto confirmado. |
| H5 | Incorporar los bloques restantes del inventario. | Cada bloque cerrado de forma independiente. |
| H6 | Completar funciones, rendimiento y entrega del campus. | Recorridos entre bloques, aplicación integrada y arranque reproducible. |

El Plan 3 puede avanzar sobre B desde H0. La mejora de apariencia no necesita esperar al inventario completo de la universidad.

## 5. H0: consolidar el primer piso del Bloque B

1. Revisar la versión actual del GLB, el documento de referencias y los cambios de datos.
2. Confirmar que el modelo servido coincide con la exportación revisada.
3. Probar ICETEX, Laboratorio de Morfología, hall de ascensores y baños, y Preclínica.
4. Comprobar la nueva entrada a Preclínica por la circulación norte y el almacén, tal como está documentada.
5. Actualizar el ensayo de navegador que todavía espera un 404 para Preclínica.
6. Mantener el caso de ruta imposible en una base de pruebas con un lugar aislado creado para ese propósito.
7. Revisar que puertas, mobiliario y elementos decorativos permitan los recorridos en ambos sentidos.
8. Actualizar capturas y notas de revisión, y publicar los cambios comprobados con sus commits separados.

Salida: una base estable y actualizada desde la cual ampliar el campus.

## 6. H1: inventario y base técnica

### Inventario por bloque

Registrar código, nombre, ubicación, fuentes disponibles, niveles reales, entradas, conexiones verticales y exteriores. Para cada piso, registrar nombres de espacios, usos confirmados, elevación y referencias de escala.

Cada dato tendrá una procedencia: plano, documento del modelo, fotografía, medida o confirmación del usuario. Los datos pendientes permanecerán identificados como tales.

### Evolución del backend

- Separar conceptualmente bloque, piso y lugar. La entidad actual `Building` representa un lugar; la ampliación deberá respetar los datos y contratos existentes durante la transición.
- Introducir identificadores estables para lugares y conexiones. Los nombres visibles podrán repetirse en distintos bloques o pisos.
- Incorporar elevaciones por piso. Los 3,5 m actuales serán un valor provisional donde falten medidas.
- Añadir información de bloque y piso a los contratos que la necesiten.
- Extender la respuesta de rutas con identificadores y posiciones suficientes para animar el recorrido, conservando la compatibilidad necesaria con los nombres actuales.
- Mantener A* y Dijkstra en FastAPI y conservar las estructuras de datos del proyecto académico.
- Revisar los pesos y la heurística al incorporar alturas reales para mantener coherente el cálculo de distancias.
- Preparar migraciones y cargas de datos versionadas, repetibles y sin borrar otros bloques. El seed actual de un único piso necesitará evolucionar para aceptar el campus completo.

### Evolución del frontend

- Cargar un modelo independiente por bloque o piso mediante un manifiesto.
- Distinguir el piso observado de la posición del personaje.
- Mantener el modelo activo y los recursos necesarios para la ruta, liberando recursos de GPU cuando corresponda.
- Mostrar claramente un modelo pendiente o un error de carga.
- Relacionar la revisión del modelo con la de sus datos para evitar integrar geometría y caminos incompatibles.

Salida: una nueva planta se incorpora mediante sus recursos y datos, sin duplicar la aplicación.

## 7. Secuencia por pisos del Bloque B

Esta tabla es provisional y se aplica únicamente a plantas cuya existencia y denominación se confirmen.

| Planta | Prioridad y trabajo | Comprobación principal |
| --- | --- | --- |
| Piso 1 existente | Consolidar y ampliar el catálogo a los destinos identificados del piso. | Acceso, puertas, giros y llegada a cada destino acordado. |
| Primer piso contiguo con mejor referencia: 0 o 2 | Modelar un núcleo vertical compartido y sus destinos. | Primera conexión entre plantas. |
| Piso 0, si existe y no fue el anterior | Incorporar el nivel inferior y sus accesos reales. | Elevación y conexión con piso 1. |
| Piso 2, si existe y no fue el anterior | Completar sus espacios confirmados. | Recorridos desde y hacia piso 1. |
| Piso 3 confirmado | Resolver sus diferencias respecto de la estructura común. | Rutas que atraviesen varios niveles. |
| Pisos 4 y 5 confirmados | Incorporar cada planta de forma independiente. | Catálogo, conexiones y pruebas de cada nivel. |
| Terrazas confirmadas | Representar límites, desniveles y accesos. | Recorridos correspondientes a accesos confirmados. |
| Cubiertas | Completar geometría y elementos visibles del edificio. | Navegación cuando exista un destino y acceso confirmado. |

Una integración inicial de tres destinos sirve para comprobar una planta. El cierre completo del piso incluye todos los destinos confirmados dentro del alcance acordado.

## 8. Proceso repetible para cada piso

| Paso | Claude | Codex | Resultado comprobable |
| --- | --- | --- | --- |
| Referencias | Identificar planta, estructura, accesos y escala. | Revisar el contrato de coordenadas y preparar el inventario de lugares. | Referencia utilizable y dudas registradas. |
| Modelo inicial | Exportar estructura, losa, muros, puertas y conexiones verticales. | Preparar carga, transformación y marcadores. | GLB visible con sus referencias alineadas. |
| Datos | Documentar puertas, giros y límites físicos. | Incorporar lugares, puntos de paso y caminos a FastAPI. | Ruta devuelta por la API real. |
| Movimiento | Mantener libre la circulación del modelo. | Integrar control manual y seguimiento con comprobación de obstáculos. | Llegada correcta del personaje. |
| Acabado | Completar materiales y detalles visuales. | Ajustar luz, cámara, rótulos y estados de interfaz. | Escena legible y coherente. |
| Revisión | Comparar la captura de la ruta con el plano. | Repetir recorridos y registrar resultados. | Piso aceptado y listo para publicar. |

El modelo contendrá las superficies físicas. El backend conservará el catálogo y el grafo. Los puntos de paso preservarán los giros y las entradas; el cliente rechazará referencias incompletas en lugar de omitirlas.

## 9. Contrato de entrega entre Claude y Codex

Por cada piso se entregarán:

- Fuente editable de Blender, fuera del build web.
- GLB con unidades y orientación documentadas.
- Captura superior comparable con la planta.
- Documento de escala, origen, orientación, elevación y aproximaciones.
- Tres referencias no alineadas y los nombres de sus nodos exportados.
- Posiciones de accesos y conexiones verticales, incluyendo descansos cuando corresponda.
- Identificación de superficies transitables y obstáculos.
- Identificación de muebles o detalles ilustrativos.

Codex añadirá la configuración de integración, los datos de la API y la evidencia de navegación. El formato y las rutas de archivos se acordarán antes de las siguientes exportaciones.

Se conserva el sistema de planimetría actual: el plano API `(x, y)` se representa como `(x, elevación, -y)` en Three.js. El eje +Y del dibujo no se presenta como norte geográfico. La elevación procede del catálogo del piso; la multiplicación por 3,5 m permanece como convención provisional mientras se amplía el contrato.

Para alinear varias plantas se utilizarán además referencias estructurales comunes. Los dibujos distribuidos en distintas zonas de un CAD pueden necesitar transformaciones distintas para representar el mismo edificio.

## 10. Navegación vertical y entre bloques

### Escaleras, rampas y ascensores

Claude modelará y documentará recorridos, descansos y accesos. Codex representará los tramos con puntos intermedios o geometrías suficientes para seguirlos físicamente.

La aplicación mostrará la secuencia de plantas y tipos de tramo. El personaje conservará una posición válida al pausar o cancelar. La selección de un piso cambiará la vista; la colocación del personaje será una acción explícita o el resultado del recorrido.

La opción de evitar escaleras filtrará conexiones. Una ruta sin escaleras y una accesibilidad física certificada son conceptos distintos; los datos conservarán lo que esté comprobado sobre rampas, puertas y ascensores.

### Conexiones exteriores

Los trayectos entre bloques utilizarán los accesos, patios, pasos, andenes y desniveles confirmados. Todos los bloques se registrarán en un sistema de coordenadas común.

Para aceptar un bloque nuevo se comprobará al menos una ruta de ida y otra de regreso desde un bloque ya integrado. Los destinos con nombres similares se distinguirán por identificador, bloque y piso.

## 11. Funciones de la aplicación completa

| Área | Trabajo de Codex |
| --- | --- |
| Directorio | Búsqueda por nombre, servicio, bloque, piso, tipo y facultad. |
| Sesión | Registro, login, cierre de sesión y recuperación ante 401, 429 o conexión fallida. |
| Navegación | Ruta, instrucciones por tramo, llegada, cancelación y nueva ruta desde la posición actual. |
| Historial y estadísticas | Integrar las funciones existentes del backend en la interfaz. |
| Atrás y adelante | Conectar la navegación personal con sus endpoints existentes. |
| Recorridos guiados | Mostrar paradas y guiar entre ellas. |
| Filas y rankings | Integrar las funciones disponibles y explicar su estado. |
| Administración | Gestionar lugares, caminos, servicios y recorridos según permisos. |
| Asistente | Resolver necesidades contra un catálogo de servicios confirmado y ofrecer navegación. |
| Mapa | Vista superior y minimapa coordinados con el recorrido y el piso. |

El asistente empezará por un catálogo fiable. Si se incorpora un proveedor generativo, su clave permanecerá en el servidor y los destinos se validarán contra el catálogo.

Las funciones con estado en memoria conservarán ese comportamiento mientras sea suficiente para la entrega. Se decidirá su persistencia antes de prometer que sobreviven a reinicios.

## 12. Criterios de aceptación

### Un piso está terminado cuando

- [ ] La planta, su nombre y sus destinos están confirmados dentro del alcance.
- [ ] Modelo, referencias y datos coinciden dentro de la tolerancia acordada; valor inicial: 0,15 m.
- [ ] Todos los destinos acordados tienen acceso y caminos coherentes.
- [ ] El personaje respeta puertas, giros y obstáculos.
- [ ] Las conexiones con plantas vecinas están comprobadas.
- [ ] El control manual, seguimiento, pausa y cancelación funcionan.
- [ ] La carga y los errores se presentan de forma clara.
- [ ] Hay captura de una ruta con giro y evidencia de llegada.

### Un bloque está terminado cuando

- [ ] Todos sus pisos confirmados cumplen los criterios anteriores.
- [ ] Se han revisado los destinos aislados y documentado sus motivos.
- [ ] Existen recorridos entre plantas y hacia otro bloque integrado, cuando corresponda.
- [ ] La vista general y las plantas conservan rendimiento y legibilidad.
- [ ] La revisión del modelo y la de sus datos se publican de forma compatible.

### El campus está terminado cuando

- [ ] Los bloques del inventario acordado están cerrados.
- [ ] Las conexiones exteriores funcionan.
- [ ] Las funciones de aplicación comprometidas están integradas.
- [ ] El arranque desde cero, las pruebas y el ensayo final pasan.

## 13. Pruebas y evidencia

Las pruebas comprobarán rutas dentro de un piso, rutas verticales, recorridos entre bloques, direcciones de caminos, destinos inexistentes o aislados, sesión vencida y recursos faltantes.

La revisión geométrica utilizará las referencias del GLB y el espacio necesario para el personaje. Las pruebas de navegador observarán tanto el trayecto como la posición final. La evidencia se asociará con la versión probada; una exportación nueva que cambie obstáculos requiere repetir los recorridos afectados.

Los datos de pruebas estarán aislados del campus de ejemplo y de la base de desarrollo. Para cambios de frontend se ejecutarán typecheck y build; los cambios de API o datos tendrán las pruebas correspondientes. Los recorridos de presentación se ensayarán en la máquina de entrega.

## 14. Trabajo paralelo, repositorios y publicación

- Backend en el repositorio principal; frontend en su clon independiente `UniNav-Frontend/`.
- Mantener `UniNav-Frontend/` excluido mediante `.git/info/exclude` del backend.
- Todo el frontend y sus herramientas propias se escriben en TypeScript.
- Conservar `/app/`, Swagger y las rutas existentes de la API.
- FastAPI debe arrancar aunque falte el build del frontend.
- Trabajar en ramas o espacios independientes para evitar compartir cambios de modelo y web a medio terminar.
- Integrar por avance: modelo, datos, navegación, acabado y documentación.
- Verificar autor, committer y cuenta autenticada de `1dxvn` antes de publicar; conservar el correo asociado comprobado y retirar trailers automáticos `Co-authored-by` de asistentes.
- Respetar los cambios locales ajenos al avance que se esté registrando.
- Si falta autenticación, conservar los commits preparados y registrar el paso pendiente.

## 15. Organización del tiempo y siguiente avance

La duración del campus completo se estimará después del inventario y del primer piso adicional. No se fija una fecha de todos los bloques sin conocer sus plantas y referencias.

Cada sesión reservará el último 20–25 % para integración, corrección y ensayo. Si quedan pocas horas, la meta será consolidar el piso 1 y verificar una segunda planta conectada. Las ampliaciones siguientes se ordenarán por calidad de referencias y utilidad para el usuario.

Siguiente avance concreto: consolidar la revisión de B y Preclínica, aplicar la mejora visual prioritaria sobre el modelo existente y preparar el catálogo de bloques, pisos y elevaciones para la siguiente planta.
