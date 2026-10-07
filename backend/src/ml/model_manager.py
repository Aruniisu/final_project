"""Model Manager — Picks best model for agent to use."""
import json
import pickle
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / 'ml_storage'
BASE.mkdir(parents=True, exist_ok=True)
_CACHE = {}


def _best_meta():
    meta_file = BASE / '_metadata.json'
    if not meta_file.exists():
        return None
    try:
        models = json.loads(meta_file.read_text())
    except Exception:
        return None
    if not models:
        return None
    return max(models, key=lambda m: m.get('accuracy', 0))


def load_best():
    """Load best model into cache."""
    meta = _best_meta()
    if not meta:
        return None
    mid = meta['id']
    if mid in _CACHE:
        return _CACHE[mid]
    try:
        with open(meta['path'], 'rb') as f:
            model = pickle.load(f)
        _CACHE[mid] = model
        print(f"✅ Model loaded: {meta['name']} (acc={meta.get('accuracy', 0):.3f})")
        return model
    except Exception as e:
        print(f"⚠️  Model load error: {e}")
        return None


def predict_success(features):
    """Returns (will_succeed: bool, confidence: float)."""
    model = load_best()
    if not model:
        return None, 0.0
    try:
        proba = model.predict_proba([features])[0]
        p = float(proba[1]) if len(proba) > 1 else 0.5
        return p > 0.5, round(p, 3)
    except Exception:
        return None, 0.0


def clear_cache():
    global _CACHE
    _CACHE = {}


def progress():
    """Learning progress for UI."""
    meta_file = BASE / '_metadata.json'
    if not meta_file.exists():
        return {'generations': 0, 'current_accuracy': 0, 'best_accuracy': 0, 'history': []}
    try:
        models = json.loads(meta_file.read_text())
    except Exception:
        models = []
    if not models:
        return {'generations': 0, 'current_accuracy': 0, 'best_accuracy': 0, 'history': []}
    return {
        'generations': len(models),
        'current_accuracy': models[-1].get('accuracy', 0),
        'best_accuracy': max(m.get('accuracy', 0) for m in models),
        'history': [
            {'gen': m.get('generation', i + 1), 'accuracy': m.get('accuracy', 0)}
            for i, m in enumerate(models)
        ],
    }