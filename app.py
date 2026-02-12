import streamlit as st
import pdfplumber
import pandas as pd
import re
from io import BytesIO

def extract_data(pdf_file):
    all_data = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    # Buscamos filas que tengan información de bidones (paréntesis)
                    # [span_8](start_span)[span_9](start_span)[span_10](start_span)Basado en la estructura de las fuentes[span_8](end_span)[span_9](end_span)[span_10](end_span)
                    row_str = " ".join([str(cell) for cell in row if cell])
                    
                    if "(" in row_str and "Lts" in row_str:
                        producto = row[0].split('\n')[0] if row[0] else "Desconocido"
                        
                        # Extraer cantidad de bidones: ej "(4) 20Lts" -> 4
                        match_bidones = re.search(r'\((\d+)\)', row_str)
                        cant_bidones = match_bidones.group(1) if match_bidones else "1"
                        
                        # Extraer cantidad de litros: ej "11.72Lts" -> 11.72
                        match_litros = re.search(r'(\d+\.?\d*)Lts', row_str)
                        litros = match_litros.group(1) if match_litros else "0"
                        
                        all_data.append({
                            "Producto": producto,
                            "Galones Entregados": round(float(litros)/3.785, 2),
                            "Cantidad (Envases)": cant_bidones,
                            "Galones Rec. Vacíos": "" # Para llenar a mano
                        })
    return pd.DataFrame(all_data)

# Interfaz de la App
st.set_page_config(page_title="Convertidor Danper", layout="wide")
st.title("🚀 Automatización: Premezcla a Galones Vacíos")
st.write("Sube el PDF del programa diario y descarga el Excel listo.")

uploaded_file = st.file_uploader("Selecciona el PDF de Premezcla", type="pdf")

if uploaded_file:
    df_resultado = extract_data(uploaded_file)
    
    st.subheader("Vista Previa de los Datos Extraídos")
    st.dataframe(df_resultado)
    
    # Crear el Excel en memoria
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_resultado.to_excel(writer, index=False, sheet_name='ESPARRAGO')
    
    st.download_button(
        label="📥 Descargar Excel para Galones Vacíos",
        data=output.getvalue(),
        file_name="Control_Inventario_Galones.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
