import streamlit as st
import pdfplumber
import pandas as pd
import re
from io import BytesIO

def extract_data_visual(pdf_file):
    all_data = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if not table: continue
            for row in table:
                row_str = " ".join([str(c) for c in row if c]).replace('\n', ' ')
                match_bidones = re.search(r'\((\d+)\)', row_str)
                if match_bidones:
                    maquina = re.search(r'(M\d+|LFM\d+)', row_str)
                    turno = re.search(r'(T\d+)', row_str)
                    prod = str(row[0]).split('\n')[0].strip() if row[0] else "S/P"
                    match_lts = re.search(r'(\d+\.?\d*)\s*Lts', row_str)
                    galones = round(float(match_lts.group(1))/3.785, 2) if match_lts else 0
                    
                    all_data.append({
                        "Máquina": maquina.group(1) if maquina else "S/M",
                        "Turno": turno.group(1) if turno else "S/T",
                        "Producto": prod,
                        "Galones Entregados": galones,
                        "Cantidad": int(match_bidones.group(1))
                    })
    return pd.DataFrame(all_data)

st.title("🚀 Generador Danper: Formato por Bloques")
file = st.file_uploader("Sube el PDF de Premezcla", type="pdf")

if file:
    df = extract_data_visual(file)
    output = BytesIO()
    
    # Creamos el Excel con formato de bloques
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        start_row = 0
        for (m, t), group in df.groupby(['Máquina', 'Turno']):
            # Escribir el encabezado del bloque
            ws = writer.book.create_sheet(title=f"Bloque_{m}_{t}") if start_row == 0 else writer.book.active
            if start_row == 0: writer.book.remove(writer.book['Sheet']) # Limpiar hoja inicial
            
            # Formato visual del encabezado del grupo
            ws.cell(row=start_row + 1, column=1, value=f"M: {m}    T: {t}")
            
            # Escribir los datos del grupo justo debajo
            group[['Producto', 'Galones Entregados', 'Cantidad']].to_excel(
                writer, startrow=start_row + 1, index=False
            )
            # Saltar filas para el siguiente bloque
            start_row += len(group) + 4 

    st.success("✅ Datos agrupados por Máquina y Turno")
    st.download_button("📥 Descargar Excel por Bloques", output.getvalue(), "Informe_Final_Danper.xlsx")
                
