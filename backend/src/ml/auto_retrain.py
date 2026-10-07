"""
Auto-Retrain Loop — Level 3 self-learning.
Trains new model every N seconds using agent feedback.
"""
import json
import time
import pickle
import threading
from datetime import datetime
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score

from core.event_bus import emit_event
from ml.feedback import load_all, count_samples, archive

# ⚙️  CONFIG
CHECK_INTERVAL = 60         # 1 min (demo) / 6h (prod)
MIN_SAMPLES = 10            # 10 (demo) / 500 (prod)
MODEL_TYPE = 'decision_quality'

BASE = Path(__file__).resolve().parent.parent / 'ml_storage'
BASE.mkdir(parents=True, exist_ok=True)
META_FILE = BASE / '_metadata.json'

_retrain_count = 0


def _save_meta(meta):
    existing = []
    if META_FILE.exists():
        try:
            existing = json.loads(META_FILE.read_text())
        except Exception:
            existing = []
    existing.append(meta)
    META_FILE.write_text(json.dumps(existing, indent=2))


def _train(X, y):
    global _retrain_count

    if len(set(y)) < 2:
        print(f"⏸️  [AutoRetrain] Need both success & fail samples")
        return None

    X = np.array(X)
    y = np.array(y)

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, random_state=42,
    )

    model = RandomForestClassifier(n_estimators=50, random_state=42)
    model.fit(X_tr, y_tr)

    pred = model.predict(X_te)
    acc = float(accuracy_score(y_te, pred))
    f1 = float(f1_score(y_te, pred, average='weighted', zero_division=0))

    _retrain_count += 1
    model_id = f'{MODEL_TYPE}_gen{_retrain_count}_{int(time.time())}'
    path = BASE / f'{model_id}.pkl'

    with open(path, 'wb') as f:
        pickle.dump(model, f)

    meta = {
        'id': model_id,
        'name': f'Agent Brain v{_retrain_count}',
        'model_type': MODEL_TYPE,
        'dataset': 'agent_feedback',
        'status': 'completed',
        'accuracy': round(acc, 4),
        'f1': round(f1, 4),
        'precision': 0,
        'recall': 0,
        'loss': round(1 - acc, 4),
        'total_epochs': 1,
        'generation': _retrain_count,
        'samples': len(X),
        'created_at': datetime.now().isoformat(),
        'path': str(path),
        'deployed': True,
        'auto_trained': True,
    }

    _save_meta(meta)

    # Clear cache → agent uses new model
    try:
        from ml.model_manager import clear_cache
        clear_cache()
    except Exception:
        pass

    print(f"✅ [AutoRetrain] Gen {_retrain_count}: acc={acc:.3f} ({len(X)} samples)")

    emit_event('ml:retrain_completed', {
        'model': meta,
        'generation': _retrain_count,
        'accuracy': acc,
        'samples': len(X),
    })

    return meta


def loop():
    print(f"🔄 [AutoRetrain] Started — every {CHECK_INTERVAL}s, min {MIN_SAMPLES} samples")

    while True:
        try:
            time.sleep(CHECK_INTERVAL)

            n = count_samples()
            if n < MIN_SAMPLES:
                print(f"⏳ [AutoRetrain] {n}/{MIN_SAMPLES} samples")
                continue

            X, y = load_all()
            if len(X) < MIN_SAMPLES:
                continue

            print(f"🚀 [AutoRetrain] Training on {len(X)} samples...")
            emit_event('ml:retrain_started', {'samples': len(X)})

            meta = _train(X, y)

            if meta:
                archive()

        except Exception as e:
            print(f"⚠️  [AutoRetrain] Error: {e}")


_thread = None

def start():
    global _thread
    if _thread is None or not _thread.is_alive():
        _thread = threading.Thread(target=loop, daemon=True)
        _thread.start()