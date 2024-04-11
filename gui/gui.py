import os
from PyQt5.QtWidgets import (QFileDialog, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QTextEdit, QProgressBar, QApplication)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QFont, QIcon
from pdf_processing.pdf_processing import PDFProcessor


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


class PDFExtractorGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.pdf_path = ''
        self.destination_folder = ''
        self.initUI()
        self.nombres_archivos_creados = {}  # Diccionario para llevar registro de nombres creados

    def initUI(self):
        self.setWindowTitle('Divisor de Planos')
        icon_path = os.path.join(os.path.dirname(__file__), '../resources/icono_separar_pdf.ico')
        self.setWindowIcon(QIcon(icon_path))
        self.resize(500, 600)
        
        layout = QVBoxLayout()

        # File selection
        file_layout = QHBoxLayout()
        
        self.btn_select_pdf = QPushButton('Buscar Planos', self)
        self.btn_select_pdf.setFixedWidth(150)  # Ajusta el ancho a 150 píxeles
        self.btn_select_pdf.setFixedHeight(40)        
        self.btn_select_pdf.clicked.connect(self.openFileNameDialog)
        file_layout.addWidget(self.btn_select_pdf)


        self.file_path_input = QTextEdit(self)  # Cambio aquí: Usamos QTextEdit en lugar de QLineEdit
        self.file_path_input.setFixedHeight(40)  # Ajusta la altura como desees
        self.file_path_input.setPlaceholderText('Selecciona el archivo en formato PDF')
        self.file_path_input.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Oculta la barra de desplazamiento vertical
        self.file_path_input.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Oculta la barra de desplazamiento horizontal
        self.file_path_input.setLineWrapMode(QTextEdit.WidgetWidth)  # Ajusta el texto al ancho del widget
        self.file_path_input.setReadOnly(True)  # Hace que el texto no sea editable, como un QLineEdit
        self.file_path_input.setMaximumHeight(40)  # Establece la altura máxima para limitar a 2 líneas aproximadamente
        file_layout.addWidget(self.file_path_input, 1)  # Asegúrate de agregar el widget al layout con un stretch factor
        document = self.file_path_input.document()
        document.setDocumentMargin(10)  # Ajusta este valor según sea necesario para centrar el texto

        # Destination path selection
        path_layout = QHBoxLayout()

        self.btn_select_path = QPushButton('Seleccionar Ruta', self)
        self.btn_select_path.setFixedWidth(150)  # Ajusta el ancho a 150 píxeles
        self.btn_select_path.setFixedHeight(40)
        self.btn_select_path.clicked.connect(self.openPathDialog)
        path_layout.addWidget(self.btn_select_path)
        
        self.path_input = QTextEdit(self)  # Cambio aquí: Usamos QTextEdit en lugar de QLineEdit
        self.path_input.setFixedHeight(40)  # Ajusta la altura
        self.path_input.setPlaceholderText('Selecciona la carpeta de destino')
        self.path_input.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Oculta la barra de desplazamiento vertical
        self.path_input.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Oculta la barra de desplazamiento horizontal
        self.path_input.setLineWrapMode(QTextEdit.WidgetWidth)  # Ajusta el texto al ancho del widget
        self.path_input.setReadOnly(True)  # Hace que el texto no sea editable, como un QLineEdit
        self.path_input.setMaximumHeight(40)  # Establece la altura máxima para limitar a 2 líneas aproximadamente
        path_layout.addWidget(self.path_input, 1)  # Asegúrate de agregar el widget al layout con un stretch factor
        document_path = self.path_input.document()
        document_path.setDocumentMargin(10)  # Ajusta este valor para centrar el texto verticalmente

        # Progress Bar
        self.progress_bar = CustomProgressBar(self)
        
        # Output list
        self.output = QTextEdit(self)
        self.output.setPlaceholderText('Acá se verá una lista con los archivos generados')
        self.output.setReadOnly(True)
        self.output.setAcceptRichText(True)  # Habilita el soporte de texto enriquecido
        document_path = self.output.document()
        document_path.setDocumentMargin(10)  # Ajusta este valor para centrar el texto verticalmente
        
        # Buttons
        self.btn_create_pdfs = QPushButton('Separar Planos', self)
        self.btn_create_pdfs.clicked.connect(self.createIndividualPDFs)
        self.btn_create_pdfs.setFixedHeight(40)        
        
        self.btn_open_folder = QPushButton('Abrir Ruta', self)
        self.btn_open_folder.setFixedHeight(30)
        self.btn_open_folder.clicked.connect(self.openDestinationFolder)

        self.btn_clear = QPushButton('Limpiar', self)
        self.btn_clear.setFixedHeight(30)
        self.btn_clear.clicked.connect(self.clearOutput)

        self.btn_exit = QPushButton('Finalizar', self)
        self.btn_exit.setFixedHeight(30)        
        self.btn_exit.clicked.connect(self.close)

        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.btn_open_folder)
        button_layout.addWidget(self.btn_clear)
        button_layout.addWidget(self.btn_exit)
        
        # Add widgets to the layout
        layout.addLayout(file_layout)
        layout.addLayout(path_layout)
        layout.addWidget(self.btn_create_pdfs)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.output)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        self.show()

    def openFileNameDialog(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Seleccionar PDF",
                                                  "", "Archivos PDF (*.pdf);;Todos los archivos (*)",
                                                  options=options)
        if fileName:
            if self.pdf_path != fileName:  # Solo proceder si el archivo es diferente
                self.pdf_path = fileName
                nombre_archivo = os.path.basename(fileName)
                self.file_path_input.setText(nombre_archivo)
                self.clearGeneratedFilesList()  # Limpiamos solo la lista de archivos generados

    def openPathDialog(self):
        dir = str(QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta de Destino"))
        if dir:
            self.destination_folder = dir
            self.path_input.setText(dir)

    def clearGeneratedFilesList(self):
        # Método para limpiar solamente la lista de archivos generados
        self.output.clear()
        self.progress_bar.setValue(0)
        

    def clearFilePathInput(self):
        # Método para limpiar solamente el QTextEdit del archivo PDF seleccionado
        self.file_path_input.clear()
        self.progress_bar.setValue(0)

    def createIndividualPDFs(self):
        if self.pdf_path and self.destination_folder:
            # Limpiar la lista de resultados antes de empezar el proceso
            self.clearGeneratedFilesList()
            # Definimos el método 'update_output' para actualizar el widget de salida con HTML
            def update_output(paginas, nombre_archivo):
                self.output.append(f"<table width='100%'><tr>"
                                   f"<td width='80' style='text-align: left;'>Página: {' + '.join(map(lambda p: str(p + 1), paginas))}</td>"
                                   f"<td style='padding-left: 5px;'><b>{nombre_archivo}.pdf</b></td>"
                                   f"</tr></table>")
                QApplication.processEvents()  # Asegurarse de que la GUI se actualice

            # Instanciamos `PDFProcessor` pasando la `progress_bar` y la función de callback `update_output`
            pdf_processor = PDFProcessor(self.progress_bar, update_output)
            pdf_processor.procesar_pdf(self.pdf_path, self.destination_folder)

            self.progress_bar.setMaximum(100)
            self.progress_bar.setValue(100)  # Actualizar la barra de progreso al finalizar
        else:
            # Mostrar algún mensaje de error o advertencia aquí
            pass

    def openDestinationFolder(self):
        if self.destination_folder:
            os.startfile(self.destination_folder)
        else:
            # Mostrar algún mensaje de error o advertencia aquí
            pass
            
    def clearOutput(self):
        # El método 'clearOutput' ahora solo borra la lista de archivos generados
        # y la barra de progreso, no afecta al campo del archivo PDF ni al de carpeta de destino
        self.clearGeneratedFilesList()
        self.output.clear()
        self.file_path_input.clear()
        self.path_input.clear()
        self.progress_bar.setValue(0)