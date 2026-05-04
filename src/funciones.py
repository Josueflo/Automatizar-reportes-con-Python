import pandas as pd


def cargar_excel(ruta_excel):
    return pd.read_excel(ruta_excel)


# -------------------------
# BONO (ESCALA 0–1)
# -------------------------
def calcular_bono(cumplimiento, sueldo):

    if cumplimiento < 0.80:
        return 0
    elif cumplimiento < 1.00:
        return sueldo * 0.5
    elif cumplimiento < 1.20:
        return sueldo
    else:
        return sueldo * 1.5


# -------------------------
# TRAMO BONO (TEXTO LIMPIO)
# -------------------------
def tramo_bono(c):

    if c < 0.80:
        return "Sin Bono"
    elif c < 1.00:
        return "Bono 50%"
    elif c < 1.20:
        return "Bono 100%"
    else:
        return "Bono 150%"


# -------------------------
# PROCESO PRINCIPAL
# -------------------------
def procesar_bonos(df):

    # ✔ Cumplimiento en DECIMAL (0–1)
    df["Cumplimiento"] = (
        df["Ventas Reales (S/)"] /
        df["Meta Ventas Trimestre (S/)"]
    )

    # ✔ Bono
    df["Bono"] = df.apply(
        lambda x: calcular_bono(
            x["Cumplimiento"],
            x["Sueldo Base (S/)"]
        ),
        axis=1
    )

    # ✔ Tramo Bono
    df["Tramo Bono"] = df["Cumplimiento"].apply(tramo_bono)

    # -------------------------
    # RESUMEN POR ÁREA
    # -------------------------
    resumen = df.groupby("Área").agg(
        Provision_Total=("Bono", "sum"),
        Cumplimiento_Promedio=("Cumplimiento", "mean"),
        Empleados=("ID Empleado", "count")
    )

    # ✔ % CON BONO EN DECIMAL (0–1)
    resumen["Pct_Con_Bono"] = (
        df.groupby("Área")["Bono"]
        .apply(lambda x: (x > 0).mean())
    )

    resumen["Cumplimiento_Promedio"] = resumen["Cumplimiento_Promedio"].round(4)
    resumen["Pct_Con_Bono"] = resumen["Pct_Con_Bono"].round(4)

    resumen = resumen.reset_index()

    detalle = df.copy()

    return df, resumen, detalle