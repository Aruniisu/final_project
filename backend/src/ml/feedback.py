"""Feedback Collector — Agent actions become training data."""
import json
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / 'ml_storage'
BASE.mkdir(parents=True, exist_ok=True)
FEEDBACK = BASE / 'feedback.jsonl'


def log_action(tool, features, success, confidence=0.5):
    """Save one agent action as training sample."""
    try:
        entry = {
            'ts': time.time(),
            'tool': tool,
            'features': [float(f) for f in features],
            'success': int(bool(success)),
            'confidence': float(confidence),
        }
        with open(FEEDBACK, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')
    except Exception as e:
        print(f"⚠️  Feedback error: {e}")


def count_samples():
    if not FEEDBACK.exists():
        return 0
    try:
        with open(FEEDBACK, 'r', encoding='utf-8') as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def load_all():
    if not FEEDBACK.exists():
        return [], []
    X, y = [], []
    try:
        with open(FEEDBACK, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    e = json.loads(line)
                    X.append(e['features'] + [e['confidence']])
                    y.append(e['success'])
                except Exception:
                    continue
    except Exception:
        pass
    return X, y


def archive():
    if FEEDBACK.exists():
        try:
            FEEDBACK.rename(FEEDBACK.parent / f'feedback_{int(time.time())}.jsonl')
        except Exception as e:
            print(f"⚠️  Archive error: {e}")


def stats():
    total = count_samples()
    if total == 0:
        return {'total': 0, 'success_rate': 0}
    _, y = load_all()
    return {
        'total': total,
        'success_rate': round(sum(y) / len(y), 3) if y else 0,
    }