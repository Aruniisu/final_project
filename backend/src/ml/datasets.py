"""Dataset generators for ML training (synthetic but realistic)."""
from sklearn.datasets import make_classification


def get_dataset(dataset_name, n_samples=1000):
    """Returns (X, y, labels) tuple."""

    if dataset_name == 'log_classifier':
        X, y = make_classification(
            n_samples=n_samples, n_features=20, n_informative=12,
            n_redundant=4, n_classes=3, random_state=42,
        )
        return X, y, ['INFO', 'WARN', 'ERROR']

    if dataset_name == 'anomaly_detector':
        X, y = make_classification(
            n_samples=n_samples, n_features=15, n_informative=8,
            n_redundant=3, n_classes=2,
            weights=[0.9, 0.1], random_state=42,
        )
        return X, y, ['normal', 'anomalous']

    if dataset_name == 'deploy_predictor':
        X, y = make_classification(
            n_samples=n_samples, n_features=12, n_informative=7,
            n_redundant=3, n_classes=2,
            weights=[0.3, 0.7], random_state=42,
        )
        return X, y, ['failure', 'success']

    if dataset_name == 'decision_quality':
        X, y = make_classification(
            n_samples=n_samples, n_features=9, n_informative=6,
            n_redundant=2, n_classes=2, random_state=42,
        )
        return X, y, ['fail', 'success']

    # Default fallback
    X, y = make_classification(
        n_samples=n_samples, n_features=10, n_classes=2, random_state=42,
    )
    return X, y, ['class_0', 'class_1']