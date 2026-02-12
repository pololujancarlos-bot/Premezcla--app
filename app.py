import streamlit as st
import pdfplumber
import pandas as pd
import re
from io import BytesIO

def extract_data_agrupado(pdf_file):
    all_blocks = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if not table: continue
            
            for row in table:
                row_str = " ".join([str(c) for c in row if c]).replace('\n', ' ')
                
                # Detectar si hay despacho de bidones
                match_bidones = re.search(r'\((\d+)\)', row_str)
                
                if match_bidones:
                    # Extraer Máquina (M o LFM) y Turno (T)
                    # Buscamos patrones como M07, M11 o T05, T1
                    maquina = re.search(r'(M\d+|LFM\d+)', row_str)
                    turno = re.search(r'(T\d+)', row_str)
                    
                    m_val = maquina.group(1) if maquina else "S/M"
                    t_val = turno.group(1) if turno else "S/T"
                    
                    producto_sucio = str(row[0]) if row[0] else "Producto"
                    producto_limpio = producto_sucio.split('\n')[0].strip()
                    
                    match_litros = re.search(r'(\d+\.?\d*)\s*Lts', row_str)
                    litros = float(match_litros.group(1)) if match_litros else 0
                    
                    all_blocks.append({
                        "Máquina": m_val,
                        "Turno": t_val,
                        "Producto": producto_limpio,
                        "Galones Entregados": round(litros / 3.785, 2),
                        "Cantidad": match_bidones.group(1)
                    })
    
    return pd.DataFrame(all_blocks)

st.title("🚀 Danper: Control de Galones por Grupo")
file = st.file_uploader("Subir PDF de Premezcla", type="pdf")

if file:
    df = extract_data_agrupado(file)
    
    # Mostramos los datos agrupados en la pantalla
    for (m, t), group in df.groupby(['Máquina', 'Turno']):
        st.subheader(f"📟 Máquina: {m} | 🕒 Turno: {t}")
        st.table(group[['Producto', 'Galones Entregados', 'Cantidad']])

    # Generar Excel con el formato de bloques
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='INFORME')
    
    st.download_button("📥 Descargar Excel Organizado", output.getvalue(), "Informe_Galones_Grupos.xlsx")
                    
