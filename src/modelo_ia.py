def detectar_anomalias(df):

    media = df["Cumplimiento"].mean()
    desv = df["Cumplimiento"].std()

    df["z_score"] = (
        df["Cumplimiento"] - media
    ) / desv


    df["Alerta_IA"] = df["z_score"].apply(
        lambda z:
        "Anomalía"
        if abs(z) > 2
        else "Normal"
    )

    return df



def accion_sugerida(c):

    if c < 0.80:
        return "Plan de mejora"

    elif c < 1.00:
        return "Seguimiento"

    elif c < 1.20:
        return "Buen desempeño"

    else:
        return "Reconocimiento"



def clasificar_acciones(df):

    df["Accion_Sugerida"] = (
        df["Cumplimiento"]
        .apply(accion_sugerida)
    )

    return df