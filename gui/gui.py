import os
import fitz
import pdfplumber
from os import path
from PyQt5.QtWidgets import (QFileDialog, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QTextEdit, QApplication, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar, QLabel, QSizePolicy, QScrollArea, QSplitter, QShortcut, QSplashScreen)
from PyQt5.QtCore import Qt, QEvent
from collections import Counter
from PyQt5.QtGui import QIcon, QColor, QFont, QPainter, QImage, QPixmap, QKeySequence
from pdf_processing.pdf_processing import PDFProcessor

class SplashScreen(QSplashScreen):
    def __init__(self):
        super(SplashScreen, self).__init__()
        self.setWindowTitle("Cargando Buscador de Referencias")

        image_path = os.path.join(os.path.dirname(__file__), '../resources/loading.png')
        pixmap = QPixmap(image_path)
        self.setPixmap(pixmap)

class CustomProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextVisible(False)  # Ocultar el texto predeterminado
        self.setValue(0)  # Inicializar en 0%

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        font = QFont()
        font.setBold(True)
        painter.setFont(font)
        
        # Asegurarse de que el valor máximo no sea cero antes de calcular el porcentaje
        if self.maximum() > 0:
            percent = int((self.value() / self.maximum()) * 100)
        else:
            percent = 0
        painter.drawText(self.rect(), Qt.AlignCenter, f"{percent}%")

class Accion:
    def __init__(self, tipo, fila, valores_viejos, valores_nuevos):
        self.tipo = tipo  # "modificar", "insertar", "eliminar"
        self.fila = fila
        self.valores_viejos = valores_viejos
        self.valores_nuevos = valores_nuevos

class PilaDeshacer:
    def __init__(self):
        self.pila = []

    def agregar_accion(self, accion):
        self.pila.append(accion)

    def deshacer(self):
        if not self.pila:
            return None
        return self.pila.pop()

    def limpiar(self):
        self.pila.clear()

class PDFExtractorGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.pdf_path = ''
        self.destination_folder = ''
        self.last_pdf_pixmap = None
        
        # Inicializar la pila de deshacer
        self.pila_deshacer = PilaDeshacer()  # Asegúrate de haber definido PilaDeshacer antes

        self.initUI()
        self.nombres_archivos_creados = []
        self.current_page_number = 1

        # Cargamos recursos externos solo cuando sean necesarios
        self.pdf_processor = None
        self.doc = None
        
    def update_ui(self):
        QApplication.processEvents()

    def initUI(self):
        self.setWindowTitle('Separador de Planos')
        icon_path = os.path.join(os.path.dirname(__file__), '../resources/icon.ico')
        self.setWindowIcon(QIcon(icon_path))
        self.resize(1200, 600)

        # Instalar el filtro de eventos en la aplicación
        QApplication.instance().installEventFilter(self)

        # Main layout - horizontal layout
        main_layout = QVBoxLayout(self)  # Modificado para agregar el QSplitter correctamente

        # QSplitter para dividir la ventana en secciones ajustables
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #d3d3d3; /* Un color gris claro para la línea */
                border: 0px solid #000000; /* Sin borde */
            }
            QSplitter::handle:hover {
                background-color: #c0c0c0; /* Un color gris un poco más oscuro cuando el mouse está encima */
            }
            QSplitter::handle:horizontal {
                width: 1px; /* Una línea delgada para un splitter horizontal */
            }
            QSplitter::handle:vertical {
                height: 1px; /* Una línea delgada para un splitter vertical */
            }
        """)
        main_layout.addWidget(splitter)

        left_widget = QWidget()  # Contenedor para los elementos del lado izquierdo
        left_layout = QVBoxLayout(left_widget)

        # File selection horizontal layout
        file_selection_layout = QHBoxLayout()
        self.btn_select_pdf = QPushButton('Buscar Planos', self)
        self.btn_select_pdf.setFixedWidth(150)
        self.btn_select_pdf.setFixedHeight(40)
        self.btn_select_pdf.clicked.connect(self.openFileNameDialog)
        file_selection_layout.addWidget(self.btn_select_pdf)

        self.file_path_input = QTextEdit(self)
        self.file_path_input.setFixedHeight(40)
        self.file_path_input.setPlaceholderText('Selecciona el archivo en formato PDF')
        self.file_path_input.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.file_path_input.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.file_path_input.setLineWrapMode(QTextEdit.NoWrap)
        self.file_path_input.setReadOnly(True)
        file_selection_layout.addWidget(self.file_path_input, 1)

        # Add file selection layout to the left layout
        left_layout.addLayout(file_selection_layout)

        # Path selection horizontal layout
        path_layout = QHBoxLayout()
        self.btn_select_path = QPushButton('Seleccionar Ruta', self)
        self.btn_select_path.setFixedWidth(150)
        self.btn_select_path.setFixedHeight(40)
        self.btn_select_path.clicked.connect(self.openPathDialog)
        path_layout.addWidget(self.btn_select_path)

        self.path_input = QTextEdit(self)
        self.path_input.setFixedHeight(40)
        self.path_input.setPlaceholderText('Selecciona la carpeta de destino')
        self.path_input.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.path_input.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.path_input.setLineWrapMode(QTextEdit.NoWrap)
        self.path_input.setReadOnly(True)
        path_layout.addWidget(self.path_input, 1)

        # Add path selection layout to the left layout
        left_layout.addLayout(path_layout)

        # Botón para generar vista previa
        self.btn_generate_preview = QPushButton('Generar Vista Previa', self)
        self.btn_generate_preview.clicked.connect(self.generatePreview)
        self.btn_generate_preview.setFixedHeight(40)
        left_layout.addWidget(self.btn_generate_preview)

        # Área de edición para la vista previa de nombres de archivos con QTableWidget
        font = QFont("Sans Serif", 7)  # Ajusta el tamaño y la fuente según prefieras
        font.setBold(True)

        self.preview_table = QTableWidget(self)
        self.preview_table.cellChanged.connect(self.actualizarResaltado)        
        self.preview_table.setColumnCount(3)  # Ajustando para tres columnas
        self.preview_table.setHorizontalHeaderLabels(['LETRA', 'CONTIENE', 'POSICIÓN'])
        self.preview_table.horizontalHeader().setFont(font)
        self.preview_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.preview_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.preview_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.preview_table.setColumnWidth(0, 70)  # Establecer un ancho fijo más pequeño para 'LETRA'
        self.preview_table.setColumnWidth(2, 70)  # Establecer un ancho fijo más pequeño para 'POSICIÓN'
        self.preview_table.setEditTriggers(QTableWidget.DoubleClicked)
        left_layout.addWidget(self.preview_table)

        self.preview_table.currentItemChanged.connect(self.handleCurrentItemChange)
        self.valor_celda_anterior = None
        self.celda_actual = None
        shortcut_undo = QShortcut(QKeySequence("Ctrl+Z"), self)
        shortcut_undo.activated.connect(self.accion_deshacer)  # Asegúrate de que la función accion_deshacer esté bien definida


        # Botón para procesar los planos
        self.btn_process_pdfs = QPushButton('Procesar Planos', self)
        self.btn_process_pdfs.clicked.connect(self.processIndividualPDFs)
        self.btn_process_pdfs.setFixedHeight(40)
        left_layout.addWidget(self.btn_process_pdfs)

        self.progress_bar = CustomProgressBar(self)
        left_layout.addWidget(self.progress_bar)

        buttons_layout = QHBoxLayout()

        self.btn_open_folder = QPushButton('Abrir Ruta', self)
        self.btn_open_folder.clicked.connect(self.openDestinationFolder)
        self.btn_open_folder.setFixedHeight(40)
        buttons_layout.addWidget(self.btn_open_folder)

        self.btn_clear = QPushButton('Limpiar', self)
        self.btn_clear.clicked.connect(self.clearOutput)
        self.btn_clear.setFixedHeight(40)        
        buttons_layout.addWidget(self.btn_clear)

        self.btn_exit = QPushButton('Finalizar', self)
        self.btn_exit.clicked.connect(self.close)
        self.btn_exit.setFixedHeight(40)
        buttons_layout.addWidget(self.btn_exit)

        # Add the buttons layout to the left layout
        left_layout.addLayout(buttons_layout)

        # Add the left layout to the main layout
        main_layout.addLayout(left_layout)

        self.btn_select_path.setEnabled(False)  # Inicialmente deshabilitado
        self.btn_generate_preview.setEnabled(False)  # Inicialmente deshabilitado
        self.btn_process_pdfs.setEnabled(False)  # Inicialmente deshabilitado

        right_widget = QWidget()  # Contenedor para los elementos del lado derecho
        right_layout = QVBoxLayout(right_widget)

        # Configuración del QLabel
        self.pdf_preview_label = QLabel("Vista previa no disponible", self)
        self.pdf_preview_label.setAlignment(Qt.AlignCenter)        
        self.pdf_preview_label.setStyleSheet("border: 1px solid black; background-color: white;")
        self.pdf_preview_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

        # Crear un QScrollArea
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)  # El contenido debe poder cambiar de tamaño

        # Crea un contenedor para el QLabel, que permitirá la alineación central
        label_container = QWidget()
        label_layout = QVBoxLayout(label_container)
        label_layout.addWidget(self.pdf_preview_label)
        label_layout.setAlignment(Qt.AlignCenter)  # Esto centrará el QLabel dentro del contenedor

        # Añadir el contenedor al QScrollArea
        self.scroll_area.setWidget(label_container)
        right_layout.addWidget(self.scroll_area)

        # Añadir el layout de la derecha al layout principal
        main_layout.addLayout(right_layout)

        # Agregando los widgets al QSplitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)

        # Configuraciones adicionales para el QSplitter, si se desean
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 5)

        splitter.splitterMoved.connect(self.handleSplitterMoved)

        self.setLayout(main_layout)
        self.show()

    def handleSplitterMoved(self, pos, index):
        # Este método será llamado cada vez que el QSplitter se mueva.
        self.scale_and_set_pixmap()

    def openFileNameDialog(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Seleccionar PDF",
                                                "", "Archivos PDF (*.pdf);;Todos los archivos (*)",
                                                options=options)
        if fileName:
            self.pdf_path = fileName
            nombre_archivo = os.path.basename(fileName)
            nombre_archivo_sin_extension, _ = os.path.splitext(nombre_archivo)  # Separar la extensión
            self.file_path_input.setText(nombre_archivo_sin_extension)  # Mostrar solo el nombre sin la extensión
            self.btn_select_path.setEnabled(True)  # Habilitar botón después de seleccionar un archivo
            

    def openPathDialog(self):
        dir = str(QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta de Destino"))
        if dir:
            self.destination_folder = dir
            self.path_input.setText(dir)
            self.btn_generate_preview.setEnabled(True)  # Habilitar botón después de seleccionar una ruta



    def generatePreview(self):
        if self.pdf_path and self.destination_folder:
            self.preview_table.clearContents()
            self.preview_table.setRowCount(0)

            # Configurar los anchos de las columnas antes de poblar la tabla
            self.preview_table.setColumnWidth(0, 70)  # Ajustar el ancho para 'LETRA'
            self.preview_table.setColumnWidth(2, 70)  # Ajustar el ancho para 'POSICIÓN'

            # Cargamos los recursos externos solo cuando sean necesarios
            self.pdf_processor = PDFProcessor()
            self.doc = pdfplumber.open(self.pdf_path)
            nombres_previos = self.pdf_processor.generar_vista_previa_nombres(self.doc)

            for indice, (pagina, letra, contiene, posicion) in enumerate(nombres_previos):
                self.preview_table.insertRow(indice)

                # Crear QTableWidgetItem para 'LETRA' y agregar un punto después si hay contenido
                item_letra = QTableWidgetItem(letra + '.' if letra else '')
                item_letra.setTextAlignment(Qt.AlignCenter)
                self.preview_table.setItem(indice, 0, item_letra)

                # Crear QTableWidgetItem para 'CONTIENE'
                item_contiene = QTableWidgetItem(contiene)
                self.preview_table.setItem(indice, 1, item_contiene)

                # Crear QTableWidgetItem para 'POSICIÓN', solo si 'LETRA' tiene contenido
                item_posicion = QTableWidgetItem(posicion if letra else '')
                item_posicion.setTextAlignment(Qt.AlignCenter)
                self.preview_table.setItem(indice, 2, item_posicion)
            self.btn_process_pdfs.setEnabled(True)  # Habilitar botón después de generar la vista previa
        self.preview_table.itemSelectionChanged.connect(self.update_pdf_preview)


    def encontrar_nombres_repetidos(self, nombres):
        """Encuentra y devuelve los nombres que aparecen más de una vez en la lista proporcionada."""
        contador = Counter(nombres)
        return {nombre for nombre, cuenta in contador.items() if cuenta > 1}
    
    def actualizarResaltado(self):
        self.preview_table.cellChanged.disconnect()  # Desconectar la señal para evitar llamadas recursivas
                
        nombres_filas = []
        for row in range(self.preview_table.rowCount()):
            letra = self.preview_table.item(row, 0).text() if self.preview_table.item(row, 0) else ""
            contiene = self.preview_table.item(row, 1).text() if self.preview_table.item(row, 1) else ""
            posicion = self.preview_table.item(row, 2).text() if self.preview_table.item(row, 2) else ""
            nombre_completo = f"{letra} {contiene} {posicion}".strip()
            nombres_filas.append(nombre_completo)

        nombres_repetidos = {nombre for nombre, cuenta in Counter(nombres_filas).items() if cuenta > 1}

        for row in range(self.preview_table.rowCount()):
            letra = self.preview_table.item(row, 0).text() if self.preview_table.item(row, 0) else ""
            contiene = self.preview_table.item(row, 1).text() if self.preview_table.item(row, 1) else ""
            posicion = self.preview_table.item(row, 2).text() if self.preview_table.item(row, 2) else ""
            nombre_completo = f"{letra} {contiene} {posicion}".strip()

            # Verificar si el nombre está repetido
            if nombre_completo in nombres_repetidos:
                color = QColor('#FFC398')
            # Verificar si alguna de las celdas 'LETRA', 'CONTIENE' o 'POSICIÓN' está vacía
            elif not (letra and contiene and posicion):
                color = QColor('#FFFB9D') 
            # Caso por defecto, ninguna de las condiciones anteriores
            else:
                color = QColor('white')

            # Aplicar el color de fondo a cada celda de la fila
            for col in range(self.preview_table.columnCount()):
                item = self.preview_table.item(row, col) or QTableWidgetItem()
                item.setBackground(color)
                if not self.preview_table.item(row, col):
                    self.preview_table.setItem(row, col, item)
        
        self.preview_table.cellChanged.connect(self.actualizarResaltado)  # Reconectar la señal


    def processIndividualPDFs(self):
        if self.pdf_path and self.destination_folder:
            nombres_archivos_agrupados = {}
            for indice_fila in range(self.preview_table.rowCount()):
                letra = self.preview_table.item(indice_fila, 0).text().strip() if self.preview_table.item(indice_fila, 0) else ""
                contiene = self.preview_table.item(indice_fila, 1).text().strip() if self.preview_table.item(indice_fila, 1) else ""
                posicion = self.preview_table.item(indice_fila, 2).text().strip() if self.preview_table.item(indice_fila, 2) else ""
                
                nombre_archivo = f"{letra}. {contiene}" if letra else contiene
                nombre_archivo = f"{nombre_archivo} {posicion}" if letra and posicion else nombre_archivo.strip()
                nombre_archivo = nombre_archivo.replace('..', '.').strip()
                
                if nombre_archivo not in nombres_archivos_agrupados:
                    nombres_archivos_agrupados[nombre_archivo] = []
                nombres_archivos_agrupados[nombre_archivo].append(indice_fila + 1)
            
            self.progress_bar.setMaximum(len(nombres_archivos_agrupados))
            
            contador_progreso = 0
            pdf_processor = PDFProcessor()  # Crear una instancia de PDFProcessor
            for nombre_archivo, paginas in nombres_archivos_agrupados.items():
                contador_progreso += 1
                self.progress_bar.setValue(contador_progreso)
                if hasattr(self, 'update_ui'):
                    self.update_ui()
                
                # Llamar a procesar_pdf_con_nombres por cada grupo de paginas
                pdf_processor.procesar_pdf_con_nombres(self.pdf_path, self.destination_folder, paginas, nombre_archivo)
            
            QMessageBox.information(self, "Éxito", "Los planos han sido procesados correctamente.")
            self.progress_bar.setValue(0)
        else:
            QMessageBox.warning(self, "Advertencia", "Debe seleccionar un archivo PDF y una carpeta de destino antes de procesar.")

    def openDestinationFolder(self):
        if self.destination_folder:
            # Normalizamos la ruta de la carpeta de destino
            normalized_path = path.normpath(self.destination_folder)
            try:
                os.startfile(normalized_path)
            except FileNotFoundError:
                QMessageBox.warning(self, "Advertencia", f"No se pudo abrir la ruta: {normalized_path}")
        else:
            QMessageBox.warning(self, "Advertencia", "No se ha seleccionado una carpeta de destino.")
#            
    def clearOutput(self):
        # Asegúrese de limpiar la vista previa de archivos y cualquier otra UI relacionada
        self.preview_table.clearContents()
        self.preview_table.setRowCount(0)
        self.file_path_input.clear()
        self.path_input.clear()
        self.progress_bar.setValue(0)
        self.nombres_archivos_creados.clear()

    def update_pdf_preview(self):
        selected_items = self.preview_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()  # La fila seleccionada determina la página
            if row != self.current_page_number:  # Cambiar solo si la selección ha cambiado
                self.current_page_number = row
                self.display_pdf_page(self.pdf_path, row)  # Asegúrate de pasar el índice correcto


    def display_pdf_page(self, pdf_path, page_number):
        if not pdf_path:
            self.last_pdf_pixmap = QPixmap()  # Establece un QPixmap vacío para evitar errores
            return
        
        try:
            doc = fitz.open(pdf_path)
            if page_number < doc.page_count:
                page = doc.load_page(page_number)
                zoom_factor = 3.0
                mat = fitz.Matrix(zoom_factor, zoom_factor)
                pix = page.get_pixmap(matrix=mat)
                img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
                self.last_pdf_pixmap = QPixmap.fromImage(img)
                
                aspect_ratio = self.last_pdf_pixmap.width() / self.last_pdf_pixmap.height()
                margins = self.scroll_area.contentsMargins()
                available_width = self.scroll_area.viewport().width() - margins.left() - margins.right()
                available_height = self.scroll_area.viewport().height() - margins.top() - margins.bottom()
                
                if available_width / available_height > aspect_ratio:
                    new_height = available_height
                    new_width = int(new_height * aspect_ratio)
                else:
                    new_width = available_width
                    new_height = int(new_width / aspect_ratio)

                scaled_pixmap = self.last_pdf_pixmap.scaled(new_width, new_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.pdf_preview_label.setPixmap(scaled_pixmap)
                self.pdf_preview_label.resize(scaled_pixmap.size())
                self.pdf_preview_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
                self.pdf_preview_label.setFixedSize(scaled_pixmap.size())
                
            doc.close()
        except Exception as e:
            self.last_pdf_pixmap = QPixmap()  # Establece un QPixmap vacío si hay una excepción

        # Ahora puedes llamar a scale_and_set_pixmap ya que last_pdf_pixmap no será None
        self.scale_and_set_pixmap()

    def scale_and_set_pixmap(self):
            if not self.last_pdf_pixmap:
                return
            
            # Actualizar los márgenes y dimensiones disponibles cada vez para capturar los cambios
            margins = self.scroll_area.contentsMargins()
            available_width = self.scroll_area.viewport().width() - margins.left() - margins.right()
            available_height = self.scroll_area.viewport().height() - margins.top() - margins.bottom()

            # Imprimir las dimensiones para depuración

            if available_width > 0 and available_height > 0:
                aspect_ratio = self.last_pdf_pixmap.width() / self.last_pdf_pixmap.height()
                if available_width / available_height > aspect_ratio:
                    new_height = available_height
                    new_width = int(new_height * aspect_ratio)
                else:
                    new_width = available_width
                    new_height = int(new_width / aspect_ratio)

                scaled_pixmap = self.last_pdf_pixmap.scaled(new_width, new_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.pdf_preview_label.setPixmap(scaled_pixmap)
                self.pdf_preview_label.resize(scaled_pixmap.size())
                self.pdf_preview_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
                self.pdf_preview_label.setFixedSize(scaled_pixmap.size())

            self.pdf_preview_label.update()  # Forzar la actualización de la etiqueta

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.scale_and_set_pixmap()  # Asegura el llamado para reescalar

    def eventFilter(self, source, event):
        # Verificar si el evento es un clic del mouse y si es fuera de la tabla
        if event.type() == QEvent.MouseButtonPress and source is not self.preview_table:
            # Deseleccionar todo en la tabla
            self.preview_table.clearSelection()
        
        # Procesar el resto de los eventos normalmente
        return super().eventFilter(source, event)

    def cambio_en_celda(self, fila, columna):
        valor_viejo = ""  # Deberías buscar cómo obtener el valor anterior
        valor_nuevo = self.preview_table.item(fila, columna).text()
        accion = Accion("modificar", fila, [valor_viejo], [valor_nuevo])
        self.pila_deshacer.agregar_accion(accion)

    def accion_deshacer(self):
        accion = self.pila_deshacer.deshacer()
        if accion:
            # Lógica para revertir la acción
            # La implementación depende del tipo de acción
            # Ejemplo para una acción de tipo "modificar":
            if accion.tipo == "modificar":
                fila, columna = accion.fila
                self.preview_table.item(fila, columna).setText(accion.valores_viejos[0])
            # Añade manejo para otros tipos de acciones aquí

    def handleCurrentItemChange(self, current, previous):
        # Esto se ejecuta cada vez que el ítem actual cambia, ya sea por selección o navegación
        if previous is not None:
            # Acción que captura el valor antes del cambio y lo asocia con la celda
            accion = Accion("modificar", self.celda_actual, [self.valor_celda_anterior], [previous.text()])
            self.pila_deshacer.agregar_accion(accion)

        if current is not None:
            self.celda_actual = (current.row(), current.column())
            self.valor_celda_anterior = current.text() 