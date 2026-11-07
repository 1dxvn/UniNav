# Plan 3 · Mejorar la apariencia del campus y retocar el monito

Fecha: 7 de noviembre de 2026. Estado: plan visual sobre la escena existente.

## 1. Objetivo y prioridad acordada

Mejorar la apariencia general de la universidad: volúmenes, fachadas, materiales, interiores, entorno, iluminación y presentación en el navegador.

**La universidad es la prioridad principal. El monito recibirá una mejora pequeña y proporcionada al tiempo disponible.** Debe seguir siendo sencillo, sin cara y cercano al estilo del personaje actual, con mejores formas y movimientos.

Las fotografías se utilizarán como inspiración para la identidad visual del campus. Este plan puede avanzar con los recursos existentes; no depende de reconstruir con precisión cada imagen ni de inventariar todos los pisos. Las comprobaciones de coordenadas existentes seguirán protegiendo la integración de los recorridos.

La expansión del campus se desarrolla en el [Plan 1](Plan_1_Campus_Completo_Por_Bloques.md), y el Bloque A en el [Plan 2](Plan_2_Bloque_A.md). Este plan mejora la presentación del modelo disponible y sirve como dirección visual para los siguientes bloques.

## 2. Reparto de trabajo

| Responsable | Prioridad principal | Trabajo secundario |
| --- | --- | --- |
| Claude | Mejorar el modelo de la universidad en Blender: geometría visible, materiales, detalles, mobiliario y entorno. | Proponer o entregar una mejora sencilla de las formas del monito si aporta valor frente a reutilizarlo. |
| Codex | Integrar el modelo y ajustar materiales en ejecución, iluminación, sombras, cámara, carga y rendimiento en Three.js. | Mejorar articulaciones, reposo, caminata, giros y transiciones del monito desde TypeScript o integrar sus clips si se entrega un GLB. |

Se elegirá una solución de personaje que permita dedicar la mayor parte del esfuerzo a la universidad. El modelo actual del monito se puede mejorar directamente; un nuevo GLB o un esqueleto complejo no son requisitos de este plan.

## 3. Dirección visual

El campus tendrá apariencia de maqueta arquitectónica cuidada, reconocible desde una cámara elevada y legible al acercarse a los interiores.

| Elemento | Dirección propuesta |
| --- | --- |
| Fachadas | Ladrillo terracota con variación sutil y una escala de material coherente. |
| Ventanas | Vidrios oscuros o azulados, marcos visibles y reflejos moderados. |
| Metal | Grises en cubiertas, barandas y estructura visible. |
| Muros interiores | Tonos claros que permitan leer los espacios. |
| Pisos | Colores cálidos o neutros, con distinción controlada entre usos. |
| Vegetación | Verdes que aporten contraste y ayuden a componer accesos y patios. |
| Mobiliario | Pocos materiales coherentes con el resto del campus. |
| Orientación | Verde de acento para el recorrido y el destino activo. |
| Monito | Formas redondeadas y dos o tres colores sólidos que lo distingan del fondo. |

La paleta es una propuesta de trabajo y se ajustará al verla en Three.js. Las fotografías ayudan a decidir el carácter de los materiales y los elementos reconocibles. Las partes ilustrativas o aproximadas permanecerán documentadas.

## 4. Orden de prioridad

| Prioridad | Trabajo | Motivo |
| --- | --- | --- |
| P0 | Conservar accesos, referencias y recorridos del modelo existente. | La mejora visual debe mantener utilizable la entrega. |
| P1 | Volúmenes principales, fachadas y materiales del campus. | Son los cambios que más afectan a la primera impresión. |
| P1 | Iluminación, sombras y encuadre general. | Permiten apreciar el trabajo de modelado. |
| P2 | Accesos, patio, interiores y mobiliario visible. | Aportan identidad y sensación de un lugar habitado. |
| P3 | Retoque del monito y animaciones sencillas. | Mejora la lectura del recorrido con un esfuerzo acotado. |
| P4 | Detalles pequeños y efectos adicionales. | Se incorporan después de asegurar las mejoras principales y el rendimiento. |

Si el tiempo se reduce, se cierran materiales, fachadas, iluminación y un encuadre atractivo antes de ampliar el personaje o los efectos.

## 5. Primera pasada: formas grandes de la universidad

Claude revisará el modelo con una cámara general y atenderá primero:

1. Proporciones y relación entre los volúmenes existentes.
2. Diferenciación de estructura, muros, losas y cubiertas.
3. Fachadas y ritmo de ventanas.
4. Profundidad visible de marcos, vanos y encuentros principales.
5. Puertas y accesos reconocibles.
6. Barandas, aleros y estructura metálica donde ayuden a identificar el edificio.
7. Relación visual del edificio con su base, patio y terreno representado.

La vista en corte seguirá permitiendo ver los espacios navegables. Las cubiertas y los elementos que oculten el recorrido se organizarán para poder controlar su visibilidad.

Los cambios mantendrán la transformación del modelo, los puntos de referencia y las puertas utilizadas por el grafo. Cuando un cambio de geometría afecte a un acceso, se registrará para revisar los datos y los recorridos correspondientes.

Entrega: una versión del campus que mejore su silueta y lectura desde el encuadre inicial.

## 6. Segunda pasada: materiales y detalle visible

### Fachadas y estructura

- Ajustar ladrillo, vidrio y metal como una paleta consistente.
- Revisar escala, orientación y repetición de texturas cuando se utilicen.
- Diferenciar superficies mediante color y rugosidad, evitando reflejos excesivos.
- Añadir profundidad y bordes donde se aprecien desde las cámaras de la aplicación.
- Conservar una lectura clara de los cortes de muros y plantas.

### Interiores

- Diferenciar suelo, paredes, puertas y mobiliario.
- Mejorar mesas, sillas, escritorios y elementos de laboratorio ya presentes.
- Dar identidad a las áreas mediante conjuntos pequeños de objetos reconocibles.
- Incorporar señalización sencilla donde ayude a orientar al usuario.
- Mantener giros, puertas y pasillos despejados.

### Exteriores

- Cuidar acceso, patio, jardineras y superficies de circulación visibles.
- Añadir vegetación, bancas y detalles que ayuden a componer la escena.
- Utilizar las capturas como guía del ambiente y los materiales.
- Documentar los elementos aproximados y mantener coherentes sus desniveles con la navegación existente.

Las piezas repetidas compartirán recursos cuando sea posible. La selección de detalles tendrá en cuenta lo que realmente se ve en el navegador.

Entrega: espacios con identidad visual y una circulación fácil de leer.

## 7. Presentación en Three.js

Codex ajustará el modelo dentro de la aplicación, comprobando el resultado real del GLB.

### Luz y materiales en ejecución

- Equilibrar luz ambiental, luz principal y relleno.
- Buscar una sensación de luz diurna suave y un contraste suficiente en interiores.
- Ajustar exposición y representación del color para conservar la paleta del modelo.
- Revisar los materiales transparentes de ventanas y sus reflejos.
- Evitar superficies quemadas, interiores ilegibles y sombras con patrones o artefactos.
- Mantener las sombras estáticas del edificio reutilizadas cuando la escena lo permita.
- Conservar un apoyo visual del personaje mediante su sombra de contacto.

### Cámara y composición

- Preparar un encuadre inicial que muestre la universidad de forma atractiva.
- Conservar vista elevada y vista superior para comprender el recorrido.
- Ajustar los límites de zoom y la comodidad de órbita.
- Facilitar una vista cercana suficiente para apreciar puertas, interiores y monito.
- Mantener el recorrido y el destino visibles frente a los nuevos materiales.
- Evitar que rótulos o paneles cubran los elementos principales de la composición.

La presentación de la universidad tiene prioridad frente a una cámara centrada permanentemente en el personaje. Los efectos adicionales se incorporarán solo cuando aporten una mejora visible y mantengan la fluidez.

Entrega: el modelo se aprecia de forma consistente desde la vista general y las vistas cercanas.

## 8. Especificación del monito

### Apariencia acordada

El personaje será una evolución del monito actual. Mantendrá una cabeza limpia y redondeada, sin ojos, boca ni otros rasgos faciales.

- Mejor relación entre cabeza, torso y extremidades.
- Torso más definido y hombros sencillos.
- Brazos completos y piernas diferenciadas.
- Manos y pies básicos, fáciles de leer desde arriba.
- Uniones suaves y formas redondeadas.
- Dos o tres colores sólidos con materiales lisos.
- Una silueta visible dentro de la maqueta.

El acabado del personaje será sencillo. El trabajo de ropa detallada, rasgos realistas y microdetalle no forma parte de este retoque. La mochila actual puede conservarse de forma simple si encaja con la silueta y los pasos disponibles.

La escala seguirá siendo compatible con el campus, con el origen en los pies. El cambio de apariencia mantendrá coherente el volumen utilizado por las colisiones y comprobará el paso por las puertas existentes.

### Forma de implementación

La primera opción será mejorar las piezas y articulaciones del personaje existente desde TypeScript. Si Claude entrega un GLB sencillo, Codex lo integrará bajo el mismo sistema de colocación y controles.

La elección técnica debe reducir el trabajo adicional del monito y permitir concentrarse en la universidad.

Entrega: un monito sencillo y sin cara, mejor proporcionado y reconocible en movimiento.

## 9. Animaciones sencillas, mejor resueltas

| Estado | Comportamiento esperado |
| --- | --- |
| Reposo | Respiración muy leve y pequeño cambio de postura. |
| Caminata | Alternancia de brazos y piernas, flexión sencilla y balanceo moderado. |
| Giro | Orientación gradual hacia la dirección de movimiento. |
| Inicio | Entrada suave desde reposo a caminata. |
| Parada o pausa | Salida gradual de la caminata y vuelta a reposo. |

Codex sincronizará el movimiento con la velocidad real del recorrido. Los pies deben conservar la sensación de apoyo y reducir su deslizamiento. La amplitud de la animación será contenida para que no domine la maqueta.

El mismo comportamiento se utilizará con teclado y seguimiento automático. Al pausar una ruta el personaje volverá a reposo; al continuar recuperará la marcha.

Se pueden usar animaciones procedurales sencillas o los clips `Idle` y `Walk` de un GLB. Ambas soluciones deben mantener el control y las transiciones previstos.

Entrega: movimiento claramente mejor que el actual, con una implementación y un coste visual moderados.

## 10. Recursos e integración

- Conservar la fuente de Blender fuera del build web.
- Mantener el contrato y la ubicación del GLB del campus durante esta mejora, salvo una migración de recursos documentada.
- Si se utiliza un modelo independiente del personaje, colocarlo en una carpeta propia, por ejemplo `public/models/avatar/avatar.glb`.
- Mantener los materiales, las texturas y las animaciones necesarios para la versión entregada.
- Revisar recursos compartidos y liberar geometrías, materiales y texturas al sustituir modelos.
- Registrar cambios de obstáculos que requieran repetir rutas.
- Conservar la identidad visual común para las siguientes exportaciones de A y B.

Las capturas de trabajo sirven como referencia y revisión. La aplicación debe cargar los recursos necesarios para mostrar la escena, con una organización que facilite su mantenimiento.

## 11. Revisión visual de antes y después

Guardar capturas con encuadres comparables:

1. Vista general del campus: comparación principal de la entrega.
2. Acceso o fachada representativa.
3. Interior representativo con puertas y mobiliario.
4. Patio o conexión exterior visible.
5. Monito de cerca, como evidencia secundaria.
6. Recorrido en ejecución y llegada al destino.

Registrar qué cambió y cualquier aproximación importante. La aprobación visual se basará en el resultado dentro del navegador, además de las capturas de Blender.

## 12. Verificación funcional y de rendimiento

- Comprobar carga del GLB y materiales, escala, orientación y apoyo de los objetos.
- Repetir los recorridos afectados por muebles, puertas, fachadas o desniveles modificados.
- Comprobar que el monito pasa por los accesos y mantiene sus controles.
- Revisar marcha, giros, pausa, cancelación y llegada.
- Comprobar que la línea de ruta y los rótulos conservan contraste.
- Revisar fluidez, memoria y tiempos de carga en la máquina de presentación.
- Utilizar como objetivo inicial una interacción de al menos 30 FPS en el encuadre de presentación, sujeta a medición en esa máquina.
- Ejecutar typecheck y build del frontend y las pruebas relacionadas con los cambios.
- Repetir pruebas de API si también se modifican datos o contratos del backend.

La geometría nueva se revisará con las referencias existentes y las colisiones reales. Los detalles decorativos tendrán un coste proporcional a su visibilidad en la aplicación.

## 13. Criterios de cierre

### Universidad: entrega principal

- [ ] Fachadas y volúmenes principales tienen una lectura más cuidada.
- [ ] Materiales y colores forman una paleta coherente.
- [ ] Puertas, estructura, interiores y mobiliario se distinguen.
- [ ] El acceso y el entorno visible tienen mejor composición.
- [ ] Iluminación y sombras permiten apreciar el modelo en el navegador.
- [ ] La vista inicial destaca el campus.
- [ ] Las rutas y referencias siguen siendo utilizables.
- [ ] Hay capturas comparables de antes y después.

### Monito: entrega secundaria

- [ ] Conserva su aspecto sencillo y sin cara.
- [ ] Tiene mejores proporciones, brazos, manos y pies básicos.
- [ ] Reposo y caminata son sencillos y más suaves.
- [ ] Gira y se detiene de forma gradual.
- [ ] Funciona con teclado y seguimiento.
- [ ] Su escala y volumen permiten recorrer el campus.

### Integración

- [ ] Build y comprobaciones correspondientes pasan.
- [ ] Los recorridos afectados se han ensayado con la exportación final.
- [ ] El rendimiento se ha medido en la máquina de presentación.
- [ ] Los cambios están registrados en sus repositorios con la identidad de `1dxvn` y sin trailers automáticos de coautoría de asistentes.

## 14. Organización de la sesión

1. Capturar el estado inicial y elegir los cambios de mayor impacto en la universidad.
2. Claude mejora formas grandes y materiales; Codex prepara luz y cámara.
3. Integrar una primera exportación y corregir cómo se ve en el navegador.
4. Completar los detalles visibles de interiores y exteriores.
5. Dedicar un bloque breve al monito y a sus movimientos sencillos.
6. Reservar el último 20–25 % para rendimiento, recorridos y comparación final.

Las decisiones se tomarán por impacto visible y tiempo disponible. El retoque del personaje y los efectos adicionales no desplazarán los trabajos principales del campus.

## 15. Encargo para Claude

> Enfoca el trabajo en mejorar la universidad: fachadas, materiales, ventanas, puertas, interiores y entorno visible. Utiliza las capturas disponibles como inspiración para ladrillo, vidrio, metal, vegetación y ambiente. Trabaja sobre el modelo existente, conserva sus referencias y deja libres los accesos y recorridos. Prioriza las formas grandes y el resultado que se aprecia desde la cámara general. El personaje es secundario: si lo retocas, mantén el monito sencillo y sin cara, con mejores proporciones y formas redondeadas. Codex puede mejorar sus articulaciones y animaciones sencillas desde TypeScript. Codex se encargará de integrar la exportación, iluminación, sombras, cámara, controles y pruebas. Compararemos capturas del campus antes y después y repetiremos las rutas afectadas.
