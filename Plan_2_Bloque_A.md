# Plan 2 · Incorporar el Bloque A a UniNav

Fecha: 7 de noviembre de 2026. Estado: planificación específica del Bloque A; su modelado e integración avanzarán por entregas verificables.

## 1. Objetivo

Incorporar el Bloque A a la escena de UniNav, mejorar su representación visual y completar progresivamente su navegación interna y su conexión con el Bloque B.

La primera entrega será un exterior ubicado en el campus. La primera entrega navegable añadirá el nivel de acceso, un pasillo y tres destinos confirmados. El cierre del bloque incluirá todos los pisos y destinos que se confirmen dentro del alcance.

Este plan aplica el [plan general por bloques](Plan_1_Campus_Completo_Por_Bloques.md). La apariencia se coordina con el [Plan 3](Plan_3_Mejora_Visual_Campus_y_Monito.md), que puede avanzar utilizando las fotografías como inspiración sin esperar un levantamiento completo.

## 2. Referencias disponibles y datos pendientes

### Disponible

- Capturas del campus en `UniNav-Frontend/public/referenciasMaps/` con fachadas, accesos, patio y vista aérea.
- Un modelo funcional de B que sirve como referencia de estilo e integración técnica.
- Convención de coordenadas y comprobaciones de referencias ya utilizadas en el proyecto.
- Frontend con autenticación, rutas y personaje, y un backend que puede ampliarse con nuevos lugares y caminos.

### Pendiente de confirmar para A

- Qué volumen de las imágenes corresponde exactamente al Bloque A.
- Límites del bloque y su posición respecto de B.
- Número de pisos y denominación real de cada nivel.
- Planta interior identificada como A.
- Nombres y usos de los espacios.
- Medidas y elevaciones necesarias para una navegación física coherente.
- Conexiones verticales y trayecto exterior entre bloques.

En la revisión de archivos no se identificó una planta interior de A. El archivo CAD disponible se llama `PLANOS UCC 2025 - B.dwg`; su nombre no demuestra por sí solo que contenga las plantas de A. Debe revisarse su contenido antes de utilizarlo con ese propósito.

Las fotografías se usarán desde el comienzo para guiar volúmenes, colores y materiales. Las partes sin medida se documentarán como aproximadas. La navegación de interiores se habilitará sobre espacios y accesos suficientemente confirmados.

## 3. Responsabilidades

| Área | Claude | Codex |
| --- | --- | --- |
| Identificación | Relacionar vistas, volúmenes y accesos con el bloque. | Preparar el inventario y registrar incertidumbres. |
| Exterior | Modelar estructura, fachadas, cubiertas y elementos reconocibles. | Cargar, posicionar, iluminar y encuadrar A en la web. |
| Interiores | Modelar losa, muros, aberturas, circulación y núcleo vertical. | Incorporar lugares, puntos de paso, caminos y controles. |
| Referencias | Documentar unidades, origen, orientación y posiciones exportadas. | Verificar la transformación contra los datos de la API. |
| Movimiento | Mantener puertas y recorridos libres de obstáculos. | Integrar colisiones, guía, pausa, cancelación y llegada. |
| Acabado | Materiales, mobiliario y detalles del edificio. | Luz, sombras, cámara, rótulos y rendimiento. |
| Cierre | Revisar la captura del recorrido contra sus referencias. | Ejecutar pruebas y preparar la versión publicable. |

Claude conserva el trabajo de modelado. Codex comunica cualquier bloqueo mediante el archivo de revisión y una captura o tramo concreto.

## 4. Hitos de entrega

| Hito | Entrega | Condición de aceptación |
| --- | --- | --- |
| A0 | Identidad, fuentes y ubicación de A registradas. | Existe una referencia común de qué se está representando. |
| A1 | Exterior inicial en la escena. | A se puede reconocer e inspeccionar sin sustituir B. |
| A2 | Nivel de acceso con tres destinos. | FastAPI calcula sus rutas y el personaje llega. |
| A3 | Dos plantas conectadas. | Un recorrido vertical funciona en ambos sentidos. |
| A4 | Pisos confirmados completos. | Lugares y accesos acordados están integrados por planta. |
| A5 | Conexión A ↔ B. | Recorridos completos entre destinos de los dos bloques. |
| A6 | Acabado y ensayo. | Escena cuidada, rendimiento aceptable y evidencia de pruebas. |

El exterior puede avanzar con las fotografías mientras se resuelven los datos interiores. Los hitos de navegación dependen de las referencias físicas correspondientes.

## 5. A0: identificación y ficha del bloque

1. Delimitar el volumen de A en la vista aérea disponible.
2. Relacionar sus fachadas con las capturas de calle o patio.
3. Identificar el acceso principal y otros accesos confirmados.
4. Registrar el recorrido aparente hacia B y las partes que necesitan confirmación.
5. Identificar desniveles entre calle, patio y entrada.
6. Localizar una medida conocida para ajustar escala cuando esté disponible.
7. Enumerar los pisos confirmados y las fuentes de sus nombres.

La ficha distinguirá datos confirmados, aproximados y pendientes. La nomenclatura de software se asignará después de relacionarla con la denominación real; el nivel de acceso no se asumirá automáticamente como piso 0.

Salida: inventario inicial de A con fuentes y prioridades.

## 6. A1: exterior reconocible

### Trabajo de Claude

- Construir los volúmenes principales y su relación entre sí.
- Definir fachadas, ventanas, accesos, cubiertas y estructura visible que correspondan a A.
- Utilizar las referencias para orientar la paleta de ladrillo, vidrio, metal y vegetación.
- Incorporar profundidad visible en marcos, vanos y encuentros principales.
- Representar el apoyo del edificio y sus desniveles conocidos; documentar los aproximados.
- Separar por objetos o colecciones los elementos que después deban ocultarse para ver interiores.
- Priorizar las formas grandes antes de detalles secundarios.

### Trabajo de Codex

- Añadir soporte de bloque en el selector y en la configuración de modelos.
- Mantener A y B como recursos independientes.
- Incorporar transformación, encuadre general y estados de carga.
- Preparar la carga por plantas y la liberación de recursos cuando corresponda.
- Conservar el modelo y las rutas existentes de B durante la ampliación.

Salida: A visible en el campus, con un exterior inicial coherente y sus aproximaciones registradas.

## 7. A2: primer piso navegable

Elegir el nivel de acceso o el piso que tenga mejores referencias interiores y una entrada identificable.

### Geometría inicial

Claude modelará la losa, estructura, muros, puertas, circulación principal, conexión vertical y tres destinos confirmados. Los muebles se incorporarán después de comprobar la circulación básica.

### Datos y navegación

Codex registrará los lugares de A en FastAPI con identificadores estables, bloque, piso y posiciones. Añadirá nodos en giros, puertas y cambios de tramo para que el recorrido respete la planta.

La primera prueba tendrá al menos un giro. Se comprobarán los tres destinos desde la entrada, la nueva ruta desde la posición actual y la cancelación sin reiniciar al personaje.

Los nombres de destinos se tomarán de las fuentes confirmadas. Los códigos de lugares y las etiquetas visibles se mantendrán separados para admitir nombres repetidos en A y B.

Salida: entrada de A → pasillo → destino, calculada por FastAPI y recorrida en navegador.

## 8. A3 y A4: desarrollo piso por piso

| Entrega por planta | Modelado de Claude | Integración de Codex | Evidencia |
| --- | --- | --- | --- |
| Nivel de acceso | Entrada, circulación, aberturas y primeros destinos. | Catálogo inicial y rutas internas. | Tres llegadas comprobadas. |
| Primer nivel contiguo | Planta y conexión vertical compartida. | Tramos entre pisos y cambio de vista. | Ida y vuelta entre plantas. |
| Nivel inferior confirmado | Accesos, elevación y límites propios. | Conexión con las plantas existentes. | Recorrido con desnivel correcto. |
| Cada nivel superior confirmado | Geometría específica de la planta. | Nuevos destinos, caminos y pruebas. | Ruta dentro del piso y desde otro nivel. |
| Terrazas o cubiertas | Límites, elementos visibles y accesos conocidos. | Navegación cuando corresponda a destinos y accesos confirmados. | Comprobación de sus conexiones. |

No se fija un número de pisos para A hasta revisar las fuentes. Cada fila aplicable se convertirá en una tarea identificada por piso.

Tres destinos constituyen la primera integración. El cierre de cada planta incluirá todos sus destinos confirmados dentro del alcance.

## 9. Sistema de coordenadas y conexión vertical

### Referencias de A

Claude documentará tres puntos no alineados: por ejemplo, un umbral, un punto estructural y un punto reconocible de la planta. Se anotarán sus posiciones en el modelo exportado y la fuente de la escala.

Codex comprobará la transformación de A y la elevación de cada planta. El objetivo inicial de alineación será una diferencia máxima de 0,15 m entre modelo y datos.

Las coordenadas de cada dibujo pueden tener un origen distinto. La ubicación conjunta de A y B se resolverá con una transformación documentada y referencias comunes del campus.

### Escaleras, rampas y ascensores

Claude entregará accesos, arranques, descansos y llegadas. Codex representará la geometría necesaria en los tramos y animará la transición con cambios de planta controlados.

Pausar o cancelar conservará una posición válida. La opción de evitar escaleras utilizará los tipos de camino confirmados. Las alturas pendientes se mantendrán identificadas como aproximadas.

Salida: movimiento coherente entre niveles y una separación clara entre piso observado y ubicación del personaje.

## 10. A5: conexión con el Bloque B

1. Confirmar las puertas o accesos que utilizará la conexión.
2. Documentar el trayecto exterior: patio, paso, andén, rampa o conexión cubierta que corresponda.
3. Incorporar las elevaciones y obstáculos que afecten al recorrido.
4. Registrar los puntos y caminos exteriores en el grafo de FastAPI.
5. Comprobar una ruta desde un destino integrado de B hacia A.
6. Comprobar otra desde A hacia un destino de B.
7. Revisar encuadre, instrucciones, selección de bloque y continuidad de la ruta.

Claude se encargará de la representación física de esta conexión. Codex mantendrá el cálculo del recorrido en el backend y lo reproducirá en el navegador.

Salida: A y B forman parte de un mismo campus navegable.

## 11. Apariencia, mobiliario y presentación

La mejora visual seguirá el Plan 3: universidad como prioridad, materiales coherentes, fachadas con profundidad, interiores legibles y entorno cuidado.

Claude incorporará mobiliario y señalización sencilla donde aporten identidad. Las piezas ilustrativas quedarán documentadas y no bloquearán puertas ni trayectos. Codex ajustará luz, sombras, exposición, cámara y rótulos para que el resultado se aprecie en la web.

El personaje seguirá siendo un monito sencillo y sin cara. Su retoque no debe desplazar el trabajo principal del Bloque A.

## 12. Estructura propuesta de archivos

Esta estructura se aplicará después de preparar el cargador de varios bloques:

```text
UniNav-Frontend/
  model/blocks/A/
    campus.blend
  public/models/blocks/A/
    exterior.glb
    floors/<floor-id>/
      campus.glb
      campus-top.png
      campus-reference.md
      campus-reference.json
  docs/blocks/A/
    inventory.md
    review.md
    verification/
```

La fuente editable permanece fuera del build. Las fotografías de trabajo se organizarán como referencias; solo los recursos necesarios para la aplicación formarán parte de la entrega web. Los datos de lugares y caminos vivirán en el backend y se importarán de forma repetible.

## 13. Pruebas y aceptación

### Primera entrega navegable

- [ ] A está ubicado en la escena y el bloque correcto está identificado.
- [ ] El nivel de acceso tiene referencias suficientes para navegar.
- [ ] Hay tres destinos confirmados y sus puertas o accesos.
- [ ] FastAPI calcula las rutas reales.
- [ ] El personaje llega por el pasillo y acceso correctos.
- [ ] Control manual, seguimiento, pausa y cancelación funcionan.
- [ ] El modelo de B y sus recorridos siguen disponibles.

### Bloque terminado

- [ ] Todos los pisos confirmados dentro del alcance están incorporados.
- [ ] Sus destinos y conexiones verticales están comprobados.
- [ ] Las referencias y transformaciones están documentadas.
- [ ] Hay recorridos A ↔ B.
- [ ] Se han revisado colisiones de puertas, muebles y desniveles.
- [ ] La interfaz diferencia bloque, piso y destino.
- [ ] Build y pruebas correspondientes pasan.
- [ ] Existen capturas superiores, evidencia de llegada y notas de las aproximaciones.

## 14. Integración, publicación y organización del tiempo

Trabajar en ramas o espacios separados para el modelo y la aplicación. Registrar avances de geometría, datos, navegación y documentación en commits diferenciados, conservando la identidad de `1dxvn` y verificando autenticación antes de publicar.

Una revisión del modelo que cambie obstáculos requiere repetir los recorridos afectados. La exportación debe corresponder con el modelo y los datos probados. El código de frontend continuará en TypeScript y se conservarán `/app/`, Swagger y los endpoints existentes.

La fecha de A completo se estimará después de confirmar sus plantas y comprobar el primer piso. Cada sesión reservará el último 20–25 % para corrección e integración. Si faltan plantas interiores, el trabajo paralelo se concentra en el exterior y en el soporte de varios bloques.

## 15. Encargo inicial para Claude

> Prepara el Bloque A para UniNav. Empieza identificando su volumen y accesos en las referencias disponibles y utiliza las fotografías para orientar apariencia, materiales y proporciones. Documenta qué datos están confirmados y cuáles son aproximados. Modela primero el exterior y después un nivel con referencias interiores suficientes, priorizando entrada, pasillo, puertas, núcleo vertical y tres destinos confirmados. Entrega GLB, captura superior y referencias de escala, origen, orientación, elevación y tres puntos no alineados. Mantén cada piso separado y documenta la conexión exterior con B. Codex integrará los modelos, datos, FastAPI y navegación. Revisaremos una captura de cada primera ruta antes de cerrar la planta.
