import os
import re
from PyPDF2 import PdfReader, PdfWriter
from PyQt5.QtWidgets import QMessageBox

class PDFProcessor:
    def __init__(self, progress_bar=None, update_ui=None):
        self.progress_bar = progress_bar
        self.update_ui = update_ui

    @staticmethod
    def limpiar_nombre_archivo(nombre):
        caracteres_invalidos = '<>:"/\\|?*'
        for ch in caracteres_invalidos:
            nombre = nombre.replace(ch, '')
        return nombre

    def generar_vista_previa_nombres(self, doc):
        nombres_previos = []
        numero_paginas = len(doc.pages)
        for numero_pagina in range(numero_paginas):
            contiene, posicion, letra = None, None, None
            pagina = doc.pages[numero_pagina]
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
                            pass  # Reemplaza esto con la lógica real de extracción

            # Genera el nombre del archivo basado en la lógica proporcionada
            if contiene:
                if letra and posicion:
                    clave = f"{letra}. {contiene} {posicion}"
                else:
                    clave = contiene
                clave = self.limpiar_nombre_archivo(clave)
                # Añadir la página con su letra, contiene, y posición
                nombres_previos.append((numero_pagina + 1, letra if letra else "", contiene if contiene else "", posicion if posicion else ""))
        return nombres_previos


    def procesar_pdf_con_nombres(self, pdf_path, destination_folder, paginas, nombre_archivo):
        try:
            pdf_reader = PdfReader(pdf_path)
            archivo_destino = os.path.join(destination_folder, self.limpiar_nombre_archivo(nombre_archivo) + ".pdf")
            print(f"Intentando escribir en el archivo destino: {archivo_destino}")  # Impresión de depuración
            pdf_writer = PdfWriter()

            for pagina_num in paginas:
                pdf_writer.add_page(pdf_reader.pages[pagina_num - 1])

            with open(archivo_destino, 'wb') as output_pdf:
                pdf_writer.write(output_pdf)
            print(f"El archivo {archivo_destino} debería haberse creado.")  # Impresión de depuración

        except Exception as e:
            QMessageBox.critical(None, "Error", f"Se produjo un error al procesar el archivo: {e}")
            print(f"Error al procesar el archivo: {e}")

        finally:
            if self.progress_bar:
                self.progress_bar.setValue(0) 