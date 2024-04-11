## Separador de Planos - RTA

Este programa está diseñado para facilitar la gestión de documentos PDF que contienen los planos técnicos de los muebles. A continuación, se describen los pasos para utilizar esta herramienta:

### Paso 1: Selección del Archivo PDF

![section_img1](https://github.com/himatts/separador_planos_rta/assets/165041621/41f1441f-febe-4bd1-933c-00adf72be3e9)

- Inicie el programa y presione el botón “Buscar Planos” para abrir la venta de búsqueda.
- Busque el archivo PDF que contiene los planos que desea procesar.


### Paso 2: Elección de la Carpeta de Destino

![section_img2](https://github.com/himatts/separador_planos_rta/assets/165041621/fadeabd4-de02-4a32-ab7a-42e6d25b6f31)

- Presione el botón “Seleccionar Ruta” para abrir la venta de búsqueda.
- Especifique la ruta o carpeta en su sistema donde desea guardar los archivos resultantes. Esto puede ser una carpeta existente o una nueva que el programa creará para usted.

### Paso 3: Generar Vista Previa de los Archivos

![vista general_img3](https://github.com/himatts/separador_planos_rta/assets/165041621/f521d5dd-cdbe-4f91-bc1d-364f7bb659a4)

- Una vez seleccionados el archivo PDF y la carpeta de destino, genere la vista previa de sus archivos presionando el botón “`Generar Vista Previa`”. El programa creará un listado con la información extraída de los planos originales.
- Haciendo doble clic sobre la respectiva celda, se puede editar el nombre del archivo si así lo requiere.

![lista_resultados_img4](https://github.com/himatts/separador_planos_rta/assets/165041621/860e50fd-5c85-4bb2-97d1-25c3038e8c9b)

<br>

### 💡 ¿Qué Sucede Durante el Proceso?

- El software analiza cada página del PDF, identificando los rótulos con información técnica como el nombre de la pieza, la letra de identificación y otros datos relevantes.
- Basándose en esta información, el programa divide el documento original en múltiples archivos PDF. Cada archivo corresponde a una página específica del documento original.


- Haciendo clic sobre cada fila, podrá visualizar el contenido de la página.

![vista_documento](https://github.com/himatts/separador_planos_rta/assets/165041621/2752063b-7d8a-4275-b6e6-ac0be70a403e)


### ¿Qué significan los colores de las filas?

**Color Amarillo:**

- Identifica las filas a las que les falta información en alguna de sus casillas:
  
![lista_resultados_img5](https://github.com/himatts/separador_planos_rta/assets/165041621/5835fa8f-9110-4dd1-8481-25deba6b6689)

<br>

- Esto quiere decir que las páginas: ISOMÉTRICO, EXPLOSIÓN, VISTAS GENERALES, y ENCHAPE GENERAL siempre estarán resaltadas de amarillo, porque éstas páginas no contienen información en su rótulo en “Letra” y en “Posición”.
- Resulta útil para darse identificar si alguna de las páginas que sí debería estar completa, le hace falta información.

<br>

**Color Naranja:**

- Identifica las filas que tienen exactamente la misma información o nombre:

![lista_resultados_img6](https://github.com/himatts/separador_planos_rta/assets/165041621/d2ce6b99-bcbc-4d06-91a9-8696caa1abeb)

<br>

- Cuando los archivos comaprten exactamente el mimso nombre, estos archivos se guardarán juntos en un mismo archivo.
- En el ejemplo de la imagen superior, significaría que “MAPA DE ENCHAPE - MUEBLE SUPERIOR 1.50 LARES” se guardará en un solo documento.
- Pero también permite identificar posibles errores, en éste caso: “CS. LATERAL IZQUIERDO GABINETE 1” no deberían llamarse igual. Esto quiere decir que uno de los planos fue rotulado incorrectamente.

### Paso 4: Procesar Planos

![proceso_terminado_img7](https://github.com/himatts/separador_planos_rta/assets/165041621/731281ab-12a9-47f7-9415-c420df52b232)

- Una vez revisados y ajustados los nombres de los archivos, genere los archivos finales de sus planos presionando el botón “`Procesar Planos`”, estos quedarán en la ruta seleccionada inicialmente.
- Puede revisar la ubicación de sus archivos presionando el botón “`Abrir Ruta`”

![listado_archivos_img8](https://github.com/himatts/separador_planos_rta/assets/165041621/75ff5f86-f918-4e57-afe6-926345389522)

- Puede realizar otro procesamiento presionado el botón “`Limpiar`” y repitiendo todos los pasos.
