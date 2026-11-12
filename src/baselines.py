"""
Lineas base para comparar contra el Naive Bayes (requisito 2: metrica frente a
una linea base).

- MajorityClassBaseline: predice siempre la clase mas frecuente del entrenamiento.
- PersistenceBaseline: predice que "mañana = hoy", es decir, la categoria del dia
  siguiente sera igual a la categoria del dia actual. Es una linea base fuerte y
  natural en series de tiempo de calidad del aire.
"""
from __future__ import annotations

import numpy as np


class MajorityClassBaseline:
    """Predice siempre la clase mayoritaria vista en entrenamiento."""

    def __init__(self) -> None:
        self.clase_mayoritaria_ = None

    def fit(self, X, y) -> "MajorityClassBaseline":
        y = np.asarray(y)
        valores, conteos = np.unique(y, return_counts=True)
        self.clase_mayoritaria_ = valores[np.argmax(conteos)]
        return self

    def predict(self, X) -> np.ndarray:
        n = len(X)
        return np.array([self.clase_mayoritaria_] * n)


class PersistenceBaseline:
    """Predice la categoria de mañana como la categoria de hoy.

    No requiere entrenamiento: toma directamente la columna `categoria_hoy`.
    """

    def predict(self, categoria_hoy) -> np.ndarray:
        return np.asarray(categoria_hoy)
