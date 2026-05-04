import funciones
from modelo_ia import detectar_anomalias, clasificar_acciones

from sqlalchemy import create_engine
import pandas as pd
import os


# -------------------------
# FUNCIÓN LIMPIEZA TOTAL
# -------------------------
def limpiar_datos(df):
    df = df.copy()

    # FIX: Guardar el ID antes de cualquier conversión
    id_col = None
    if "ID Empleado" in df.columns:
        id_col = df["ID Empleado"].astype(str).str.strip()

    # Limpiar espacios solo en columnas que NO sean ID Empleado
    for col in df.columns:
        if col != "ID Empleado":
            df[col] = df[col].astype(str).str.strip()

    # FIX: Restaurar ID limpio sin convertir a str el resto
    if id_col is not None:
        df["ID Empleado"] = id_col
        df = df[df["ID Empleado"].str.contains("EMP", na=False)]

    return df


# -------------------------
# FUNCIÓN CONVERSIÓN NUMÉRICA (BLINDADA)
# -------------------------
def forzar_numeros(df):
    columnas = [
        "Sueldo Base (S/)",
        "Meta Ventas Trimestre (S/)",
        "Ventas Reales (S/)"
    ]

    for col in columnas:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(",", "", regex=False)
                .str.replace(" ", "", regex=False)
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


# -------------------------
# CARGA
# -------------------------
ruta = "data/"
archivos = [f for f in os.listdir(ruta) if f.endswith(".xlsx")]

lista_df = []

for archivo in archivos:
    df_temp = funciones.cargar_excel(os.path.join(ruta, archivo))

    df_temp.columns = df_temp.columns.str.strip()
    df_temp = df_temp.dropna(how="all")

    if "ID Empleado" in df_temp.columns:
        # FIX: Preservar el ID original limpio desde el inicio
        df_temp["ID Empleado"] = df_temp["ID Empleado"].astype(str).str.strip()
        df_temp = df_temp[df_temp["ID Empleado"] != "ID Empleado"]

    lista_df.append(df_temp)


# Unir
df = pd.concat(lista_df, ignore_index=True)

# FIX: Capturar IDs antes de cualquier transformación
ids_originales = df["ID Empleado"].copy() if "ID Empleado" in df.columns else None


# -------------------------
# LIMPIEZA FORZADA
# -------------------------
df = limpiar_datos(df)
df = forzar_numeros(df)


# -------------------------
# PROCESO BONOS
# -------------------------
df, resumen, detalle = funciones.procesar_bonos(df)

# FIX: Verificar que el ID no se perdió en procesar_bonos
if "ID Empleado" in df.columns:
    # Si quedó vacío o NaN, restaurar desde los originales usando el índice
    mask_vacio = df["ID Empleado"].isna() | (df["ID Empleado"].astype(str).str.strip() == "")
    if mask_vacio.any() and ids_originales is not None:
        df.loc[mask_vacio, "ID Empleado"] = ids_originales[mask_vacio]

# Segunda limpieza numérica
df = forzar_numeros(df)


# -------------------------
# IA
# -------------------------
df = detectar_anomalias(df)
df = clasificar_acciones(df)

# FIX: Copiar detalle DESPUÉS de IA pero asegurar que el ID esté presente
detalle = df.copy()

# FIX: Validación final — alertar si el ID sigue vacío
if "ID Empleado" in detalle.columns:
    n_vacios = detalle["ID Empleado"].isna().sum() + (detalle["ID Empleado"].astype(str).str.strip() == "").sum()
    if n_vacios > 0:
        print(f"⚠ ADVERTENCIA: {n_vacios} filas tienen ID Empleado vacío en el detalle final")


# -------------------------
# SQL
# -------------------------
engine = create_engine("sqlite:///database/bonos.db")

df.to_sql("empleados_bonos", engine, if_exists="replace", index=False)
resumen.to_sql("resumen_areas", engine, if_exists="replace", index=False)


# -------------------------
# KPI
# -------------------------
resumen_empresa = pd.DataFrame({
    "Métrica": [
        "Provision_Total",
        "Cumplimiento_Promedio",
        "Empleados",
        "Pct_Con_Bono"
    ],
    "Valor": [
        df["Bono"].sum(),
        round(df["Cumplimiento"].mean(), 4),
        len(df),
        round((df["Bono"] > 0).mean(), 4)
    ]
})

resumen_empresa = resumen_empresa.set_index("Métrica").T.reset_index(drop=True)


# -------------------------
# EXPORTAR
# -------------------------
with pd.ExcelWriter("outputs/bonos_resultado.xlsx", engine="openpyxl") as writer:
    detalle.to_excel(writer, sheet_name="Detalle_Empleados", index=False)
    resumen.to_excel(writer, sheet_name="Resumen_Areas", index=False)
    resumen_empresa.to_excel(writer, sheet_name="Resumen_Empresa", index=False)


engine.dispose()

print("✔ PROCESO 100% CORRECTO Y LIMPIO")

os.startfile(r".\outputs\bonos_resultado.xlsx")
#venv\Scripts\activate
#python src/main.py