import os
import sys
from collections import defaultdict
import re
import subprocess
from PyQt5.QtWidgets import (QApplication, QMessageBox, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, 
                             QFileDialog, QTextEdit, QLabel, QProgressBar, QLineEdit, QLabel)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QPainter, QFont, QIcon
from PyPDF2 import PdfReader, PdfWriter
import pdfplumber

def limpiar_nombre_archivo(nombre):
    # Definir caracteres inválidos que no pueden estar en nombres de archivo en Windows
    caracteres_invalidos = '<>:"/\\|?*'
    for ch in caracteres_invalidos:
        nombre = nombre.replace(ch, '')  # Reemplazar cada carácter inválido por nada
    return nombre

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


class PDFExtractorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.pdf_path = ''
        self.destination_folder = ''
        self.initUI()
        self.nombres_archivos_creados = {}  # Diccionario para llevar registro de nombres creados

    def initUI(self):
        self.setWindowTitle('Divisor de Planos')
        icon_path = os.path.join(os.path.dirname(__file__), 'icono_separar_pdf.ico')
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
        fileName, _ = QFileDialog.getOpenFileName(self, "Seleccionar PDF", "", "PDF Files (*.pdf)", options=options)
        if fileName:
            self.pdf_path = fileName
            self.file_path_input.setText(os.path.basename(fileName))

    def openPathDialog(self):
        directory = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta de Destino")
        if directory:
            self.destination_folder = directory
            # Asegúrate de que la siguiente línea solo actualice el texto del QTextEdit y no cree uno nuevo.
            self.path_input.setText(directory)

    def createIndividualPDFs(self):
        if not self.pdf_path or not self.destination_folder:
            QMessageBox.warning(self, "Advertencia", "Por favor, selecciona un archivo PDF y una ruta de destino.")
            return

        self.output.clear()
        self.progress_bar.setValue(0)

        paginas_por_contenido = defaultdict(list)

        with pdfplumber.open(self.pdf_path) as pdf:
            numero_paginas = len(pdf.pages)
            pdf_reader = PdfReader(self.pdf_path)
            self.progress_bar.setMaximum(numero_paginas)            

            for numero_pagina in range(numero_paginas):
                contiene = posicion = letra = None
                pagina = pdf.pages[numero_pagina]
                tablas = pagina.extract_tables()

                for tabla in tablas:
                    for fila in tabla:
                        for celda in fila:
                            if celda:                               
                                if 'CONTIENE:' in celda:
                                    partes = celda.split('CONTIENE:')
                                    if len(partes) > 1:
                                        texto_siguiente = partes[1].strip().split('\n')[0]  # Tomar solo el texto inmediatamente después de "CONTIENE:"
                                        contiene = texto_siguiente
                                        if texto_siguiente:
                                            contiene = texto_siguiente.split('\n')[0]
                                        else:
                                            indice = fila.index(celda)
                                            if indice + 1 < len(fila) and fila[indice + 1]:
                                                contiene = fila[indice + 1].split('\n')[0].strip()

                                match_posicion = re.search(r'(POSICI[NÓ]N|OSICI[NÓ]N)\s*L?\s*(\d+)', celda, re.IGNORECASE)
                                if match_posicion:
                                    posicion = match_posicion.group(2)

                                match_p_seguido = re.search(r'LETRA: P\n([A-Za-z]+(?:-[A-Za-z]+)*)', celda)
                                if match_p_seguido:
                                    letra = match_p_seguido.group(1)
                                else:
                                    # Buscar 'LETRA:' o 'ETRA:' seguido de caracteres permitidos
                                    match_letra = re.search(r'(LETRA:|ETRA:)\s*([A-Za-z]+(?:-[A-Za-z]+)*)', celda, re.IGNORECASE)
                                    if match_letra:
                                        letra = match_letra.group(2)

                if contiene:
                    if letra and posicion:
                        clave = f"{letra}. {contiene} {posicion}"
                    else:
                        clave = contiene
                    clave = limpiar_nombre_archivo(clave)  # Limpia el nombre del archivo
                    paginas_por_contenido[clave].append(numero_pagina)

            # Actualizar la barra de progreso y procesar eventos de la interfaz gráfica
            self.progress_bar.setValue(numero_pagina + 1)
            QApplication.processEvents()                    

            # Creación de archivos PDF basado en agrupación
            for nombre_archivo, paginas in paginas_por_contenido.items():
                # Si solo hay una página y no tiene letra ni posicion, crear archivo individual
                if len(paginas) == 1 and not letra and not posicion:
                    nombre_archivo = f"{contiene} pág. {paginas[0] + 1}"

                archivo_destino = os.path.join(self.destination_folder, f"{nombre_archivo}.pdf")
                pdf_writer = PdfWriter()

                for pagina_num in paginas:
                    pagina = pdf_reader.pages[pagina_num]
                    pdf_writer.add_page(pagina)

                with open(archivo_destino, 'wb') as output_pdf:
                    pdf_writer.write(output_pdf)

                self.output.append(f"<table width='100%'><tr>"
                                f"<td width='80' style='text-align: left;'>Página: {' + '.join(map(lambda p: str(p + 1), paginas))}</td>"
                                f"<td style='padding-left: 5px;'><b>{nombre_archivo}.pdf</b></td>"
                                f"</tr></table>")
                QApplication.processEvents()

        # Asegúrate de que la barra de progreso se complete al final
        self.progress_bar.setValue(numero_paginas)
        QApplication.processEvents()  # Actualizar la interfaz gráfica una vez completado el proceso

        
    def openDestinationFolder(self):
        if self.destination_folder:
            # Reemplazar todas las barras inclinadas hacia adelante con barras invertidas dobles
            folder_path = self.destination_folder.replace('/', '\\')
            subprocess.Popen(["explorer", folder_path])
        else:
            QMessageBox.warning(self, "Advertencia", "No se ha seleccionado ninguna carpeta de destino.")

    def clearOutput(self):
        # Reestablecer los QTextEdit a su placeholder y limpiar cualquier texto
        self.file_path_input.clear()
        self.file_path_input.setPlaceholderText('Selecciona el archivo en formato PDF')
        self.path_input.clear()
        self.path_input.setPlaceholderText('Selecciona la carpeta de destino')
        
        # Reestablecer la barra de progreso a 0%
        self.progress_bar.setValue(0)
        
        # Limpiar la salida en el QTextEdit donde se muestran los archivos generados
        self.output.clear()
        
        # Reestablecer las variables de ruta del archivo PDF y la carpeta de destino
        self.pdf_path = ''
        self.destination_folder = ''


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = PDFExtractorApp()
    sys.exit(app.exec_())