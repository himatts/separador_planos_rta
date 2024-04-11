import os
import re
from collections import defaultdict
from PyPDF2 import PdfReader, PdfWriter
import pdfplumber
from PyQt5.QtWidgets import QApplication

class PDFProcessor:

    def __init__(self, progress_bar, output_callback):
        self.progress_bar = progress_bar
        self.output_callback = output_callback

    @staticmethod
    def limpiar_nombre_archivo(nombre):
        caracteres_invalidos = '<>:"/\\|?*'
        for ch in caracteres_invalidos:
            nombre = nombre.replace(ch, '')
        return nombre

    def procesar_pdf(self, pdf_path, destination_folder):
        paginas_por_contenido = defaultdict(list)
        resultados = []

        with pdfplumber.open(pdf_path) as pdf:
            numero_paginas = len(pdf.pages)
            pdf_reader = PdfReader(pdf_path)

            # Inicializar la barra de progreso
            self.progress_bar.setMaximum(numero_paginas)

            for numero_pagina in range(numero_paginas):
                contiene, posicion, letra = None, None, None
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
                    clave = self.limpiar_nombre_archivo(clave)
                    paginas_por_contenido[clave].append(numero_pagina)

                # Actualizar la barra de progreso y procesar eventos de la interfaz gráfica
                self.progress_bar.setValue(numero_pagina + 1)
                QApplication.processEvents()

            # Creación de archivos PDF basado en agrupación
            for nombre_archivo, paginas in paginas_por_contenido.items():
                # Creación de archivo individual si aplica
                if len(paginas) == 1 and not letra and not posicion:
                    nombre_original = nombre_archivo
                    nombre_archivo = f"{contiene} pág. {paginas[0] + 1}"
                archivo_destino = os.path.join(destination_folder, f"{nombre_archivo}.pdf")
                pdf_writer = PdfWriter()

                for pagina_num in paginas:
                    pagina = pdf_reader.pages[pagina_num]
                    pdf_writer.add_page(pagina)

                with open(archivo_destino, 'wb') as output_pdf:
                    pdf_writer.write(output_pdf)

                resultado = (paginas, nombre_archivo)
                resultados.append(resultado)

                # Llamar a 'output_callback' después de cada creación de archivo
                if len(paginas) == 1 and not letra and not posicion:
                    # Si el archivo individual fue creado, usar nombre original para callback
                    self.output_callback(paginas, nombre_original)
                else:
                    self.output_callback(paginas, nombre_archivo)

                # Actualización de la interfaz gráfica después de cada archivo creado
                QApplication.processEvents()

        return resultados