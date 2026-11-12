"""
Entrenamiento y evaluacion de la Parte 1.

- Split TEMPORAL (no aleatorio): se entrena con los primeros dias y se evalua con
  los ultimos, respetando el orden del tiempo (evita fuga de informacion).
- Entrena el Naive Bayes propio y lo compara con dos lineas base.
- Reporta accuracy y F1 macro (metricas de `sklearn.metrics`: permitido, no es el
  modelo).
- Guarda el modelo entrenado y los metadatos en `models/` para que el dashboard
  lo use sin reentrenar.

Uso:
    python -m src.train
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score

from src import data_loader as dl
from src.baselines import MajorityClassBaseline, PersistenceBaseline
from src.naive_bayes import GaussianNaiveBayes

RAIZ = Path(__file__).resolve().parents[1]
DIR_MODELOS = RAIZ / "models"


@dataclass
class ResultadoModelo:
    nombre: str
    accuracy: float
    f1_macro: float


def split_temporal(feats: pd.DataFrame, frac_train: float = 0.8):
    """Divide por fecha: primeras `frac_train` como train, resto como test."""
    feats = feats.sort_values(["fecha", "estacion"]).reset_index(drop=True)
    fechas_ordenadas = np.sort(feats["fecha"].unique())
    corte_idx = int(len(fechas_ordenadas) * frac_train)
    fecha_corte = fechas_ordenadas[corte_idx]
    train = feats[feats["fecha"] < fecha_corte].reset_index(drop=True)
    test = feats[feats["fecha"] >= fecha_corte].reset_index(drop=True)
    return train, test, pd.Timestamp(fecha_corte)


def evaluar(y_true, y_pred, nombre: str) -> ResultadoModelo:
    return ResultadoModelo(
        nombre=nombre,
        accuracy=float(accuracy_score(y_true, y_pred)),
        f1_macro=float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
    )


def entrenar_y_evaluar(path_csv=None):
    df, fuente = dl.load_data(path_csv)
    feats = dl.build_features(df)
    train, test, fecha_corte = split_temporal(feats)

    X_train = train[dl.FEATURES].to_numpy()
    y_train = train["objetivo"].to_numpy()
    X_test = test[dl.FEATURES].to_numpy()
    y_test = test["objetivo"].to_numpy()

    # Modelo propio
    nb = GaussianNaiveBayes().fit(X_train, y_train)
    pred_nb = nb.predict(X_test)
    res_nb = evaluar(y_test, pred_nb, "Naive Bayes (propio)")

    # Linea base 1: clase mayoritaria
    mc = MajorityClassBaseline().fit(X_train, y_train)
    res_mc = evaluar(y_test, mc.predict(X_test), "Baseline: clase mayoritaria")

    # Linea base 2: persistencia (mañana = hoy)
    pers = PersistenceBaseline()
    pred_pers = pers.predict(test["categoria_hoy"].to_numpy())
    res_pers = evaluar(y_test, pred_pers, "Baseline: persistencia (mañana=hoy)")

    resultados = [res_nb, res_mc, res_pers]
    return {
        "fuente_datos": fuente,
        "fecha_corte": fecha_corte,
        "n_train": len(train),
        "n_test": len(test),
        "modelo": nb,
        "resultados": resultados,
        "clases": list(nb.classes_),
    }


def guardar_modelo(nb: GaussianNaiveBayes, meta: dict) -> Path:
    DIR_MODELOS.mkdir(parents=True, exist_ok=True)
    ruta_npz = DIR_MODELOS / "naive_bayes.npz"
    np.savez(
        ruta_npz,
        classes=nb.classes_,
        priors=nb.priors_,
        theta=nb.theta_,
        var=nb.var_,
        features=np.array(dl.FEATURES),
    )
    (DIR_MODELOS / "metadata.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    return ruta_npz


def cargar_modelo() -> GaussianNaiveBayes:
    ruta_npz = DIR_MODELOS / "naive_bayes.npz"
    datos = np.load(ruta_npz, allow_pickle=True)
    nb = GaussianNaiveBayes()
    nb.classes_ = datos["classes"]
    nb.priors_ = datos["priors"]
    nb.theta_ = datos["theta"]
    nb.var_ = datos["var"]
    return nb


def main() -> None:
    salida = entrenar_y_evaluar()
    resultados = salida["resultados"]

    meta = {
        "fuente_datos": salida["fuente_datos"],
        "fecha_corte": str(salida["fecha_corte"]),
        "n_train": salida["n_train"],
        "n_test": salida["n_test"],
        "clases": salida["clases"],
        "metricas": {
            r.nombre: {"accuracy": round(r.accuracy, 4), "f1_macro": round(r.f1_macro, 4)}
            for r in resultados
        },
    }
    guardar_modelo(salida["modelo"], meta)

    # Reporte legible en texto.
    lineas = ["=== Parte 1: Naive Bayes vs lineas base ===",
              f"Fuente de datos: {salida['fuente_datos']}",
              f"Train: {salida['n_train']} filas | Test: {salida['n_test']} filas",
              f"Fecha de corte (temporal): {salida['fecha_corte']}",
              "",
              f"{'Modelo':<40}{'Accuracy':>10}{'F1 macro':>10}",
              "-" * 60]
    for r in resultados:
        lineas.append(f"{r.nombre:<40}{r.accuracy:>10.4f}{r.f1_macro:>10.4f}")
    reporte = "\n".join(lineas)

    (DIR_MODELOS / "reporte_parte1.txt").write_text(reporte, encoding="utf-8")
    print(reporte)


if __name__ == "__main__":
    main()
