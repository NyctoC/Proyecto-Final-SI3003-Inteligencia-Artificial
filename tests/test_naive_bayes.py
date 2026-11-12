"""Tests de la Task 4: Naive Bayes propio, baselines y metricas.

El test clave compara nuestra implementacion contra sklearn.GaussianNB para
validar la correctitud (deben coincidir en predicciones y aproximarse en
probabilidades), sin usar sklearn como el modelo del proyecto.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from sklearn.naive_bayes import GaussianNB

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src.naive_bayes import GaussianNaiveBayes  # noqa: E402
from src.baselines import MajorityClassBaseline, PersistenceBaseline  # noqa: E402
from src import train  # noqa: E402


def _dataset_sintetico(n=200, seed=0):
    rng = np.random.default_rng(seed)
    # Dos clases gaussianas separadas en 2D.
    X0 = rng.normal(loc=[0, 0], scale=[1, 1], size=(n, 2))
    X1 = rng.normal(loc=[4, 4], scale=[1.5, 0.8], size=(n, 2))
    X = np.vstack([X0, X1])
    y = np.array(["A"] * n + ["B"] * n)
    return X, y


def test_coincide_con_sklearn_en_predicciones():
    X, y = _dataset_sintetico()
    propio = GaussianNaiveBayes().fit(X, y)
    sk = GaussianNB().fit(X, y)

    # Puntos de prueba nuevos.
    rng = np.random.default_rng(1)
    X_test = rng.normal(loc=[2, 2], scale=2.0, size=(100, 2))

    pred_propio = propio.predict(X_test)
    pred_sk = sk.predict(X_test)
    # Deben coincidir en todas (misma formulacion matematica).
    assert np.mean(pred_propio == pred_sk) == 1.0


def test_predict_proba_aproxima_sklearn():
    X, y = _dataset_sintetico()
    propio = GaussianNaiveBayes().fit(X, y)
    sk = GaussianNB().fit(X, y)
    X_test = X[:20]
    p_propio = propio.predict_proba(X_test)
    p_sk = sk.predict_proba(X_test)
    assert np.allclose(p_propio, p_sk, atol=1e-6)


def test_supera_clase_mayoritaria():
    X, y = _dataset_sintetico()
    nb = GaussianNaiveBayes().fit(X, y)
    mc = MajorityClassBaseline().fit(X, y)
    acc_nb = np.mean(nb.predict(X) == y)
    acc_mc = np.mean(mc.predict(X) == y)
    # Con clases bien separadas, el NB debe superar claramente a la mayoritaria.
    assert acc_nb > acc_mc


def test_persistence_baseline():
    pers = PersistenceBaseline()
    categoria_hoy = np.array(["Buena", "Moderada", "Buena"])
    assert list(pers.predict(categoria_hoy)) == ["Buena", "Moderada", "Buena"]


def test_pipeline_entrenamiento_end_to_end():
    salida = train.entrenar_y_evaluar()
    nombres = [r.nombre for r in salida["resultados"]]
    assert "Naive Bayes (propio)" in nombres
    # Debe haber 3 modelos evaluados.
    assert len(salida["resultados"]) == 3
    # Todas las metricas en [0, 1].
    for r in salida["resultados"]:
        assert 0.0 <= r.accuracy <= 1.0
        assert 0.0 <= r.f1_macro <= 1.0


def test_guardar_y_cargar_modelo(tmp_path, monkeypatch):
    salida = train.entrenar_y_evaluar()
    nb = salida["modelo"]
    monkeypatch.setattr(train, "DIR_MODELOS", tmp_path)
    train.guardar_modelo(nb, {"test": True})
    nb2 = train.cargar_modelo()
    # El modelo recargado predice igual que el original.
    X = np.array([[20.0, 22.0, 1.5, 0.0]])
    assert nb.predict(X)[0] == nb2.predict(X)[0]
