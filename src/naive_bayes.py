"""
Clasificador Naive Bayes Gaussiano IMPLEMENTADO POR EL EQUIPO.

Cumple el requisito 2 del enunciado: la tecnica de la Parte 1 debe ser
implementada por el equipo, no solo invocada desde una libreria que ya la
resuelve. Aqui no se usa `sklearn.naive_bayes.GaussianNB`: el ajuste (medias,
varianzas y priors por clase) y la prediccion (log-verosimilitud gaussiana +
log-prior) estan escritos a mano con numpy.

Modelo
------
Para cada clase c y cada feature j, se asume p(x_j | c) ~ Normal(mu_cj, var_cj).
Por independencia condicional (supuesto "naive"):

    log p(c | x) = log p(c) + sum_j log N(x_j; mu_cj, var_cj) + const

Se predice la clase que maximiza esa expresion. Se aplica un suavizado de
varianza (epsilon) para evitar divisiones por cero, igual que hace sklearn.
"""
from __future__ import annotations

import numpy as np


class GaussianNaiveBayes:
    """Naive Bayes Gaussiano escrito a mano (fit/predict con numpy)."""

    def __init__(self, var_smoothing: float = 1e-9) -> None:
        self.var_smoothing = var_smoothing
        self.classes_: np.ndarray | None = None
        self.priors_: np.ndarray | None = None      # log-priors por clase
        self.theta_: np.ndarray | None = None        # medias [n_clases, n_feat]
        self.var_: np.ndarray | None = None          # varianzas [n_clases, n_feat]

    def fit(self, X: np.ndarray, y: np.ndarray) -> "GaussianNaiveBayes":
        X = np.asarray(X, dtype=float)
        y = np.asarray(y)
        self.classes_ = np.unique(y)
        n_clases = len(self.classes_)
        n_feat = X.shape[1]

        self.theta_ = np.zeros((n_clases, n_feat))
        self.var_ = np.zeros((n_clases, n_feat))
        priors = np.zeros(n_clases)

        # Suavizado proporcional a la varianza maxima entre features (como sklearn).
        epsilon = self.var_smoothing * X.var(axis=0).max()

        for i, c in enumerate(self.classes_):
            Xc = X[y == c]
            self.theta_[i, :] = Xc.mean(axis=0)
            self.var_[i, :] = Xc.var(axis=0) + epsilon
            priors[i] = Xc.shape[0] / X.shape[0]

        self.priors_ = np.log(priors)
        return self

    def _log_verosimilitud_conjunta(self, X: np.ndarray) -> np.ndarray:
        """Devuelve matriz [n_muestras, n_clases] con log p(c) + sum_j log N(...)."""
        if self.classes_ is None:
            raise RuntimeError("El modelo no ha sido entrenado. Llama a fit() primero.")
        X = np.asarray(X, dtype=float)
        n_muestras = X.shape[0]
        n_clases = len(self.classes_)
        log_prob = np.zeros((n_muestras, n_clases))

        for i in range(n_clases):
            mu = self.theta_[i]
            var = self.var_[i]
            # log N(x; mu, var) = -0.5*log(2*pi*var) - (x-mu)^2 / (2 var)
            termino = -0.5 * np.sum(np.log(2.0 * np.pi * var))
            termino = termino - 0.5 * np.sum(((X - mu) ** 2) / var, axis=1)
            log_prob[:, i] = self.priors_[i] + termino
        return log_prob

    def predict(self, X: np.ndarray) -> np.ndarray:
        log_prob = self._log_verosimilitud_conjunta(X)
        indices = np.argmax(log_prob, axis=1)
        return self.classes_[indices]

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Probabilidades posteriores normalizadas (softmax de log-probabilidades)."""
        log_prob = self._log_verosimilitud_conjunta(X)
        # Estabilidad numerica: restar el maximo por fila antes de exponenciar.
        log_prob -= log_prob.max(axis=1, keepdims=True)
        prob = np.exp(log_prob)
        return prob / prob.sum(axis=1, keepdims=True)
