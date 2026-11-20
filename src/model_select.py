import os
from typing import Optional
from config import FORCE_MODEL


def select_model_path() -> Optional[str]:
    """Return a model filepath to load.

    Priority:
    1. If FORCE_MODEL is set -> normalize and return that (accept short name, filename, or full path)
    2. If models/best_model.joblib exists -> return it
    3. Else prefer models/random_forest.joblib if present
    4. Else return first .joblib found in models/
    """
    base = os.path.dirname(os.path.dirname(__file__))
    model_dir = os.path.join(base, 'models')
    if not os.path.exists(model_dir):
        return None

    # handle FORCE_MODEL override
    try:
        if FORCE_MODEL:
            fm = str(FORCE_MODEL)
            # if full path
            if os.path.exists(fm) and fm.lower().endswith('.joblib'):
                return fm
            # if filename provided
            if fm.lower().endswith('.joblib'):
                p = os.path.join(model_dir, fm)
                if os.path.exists(p):
                    return p
            # map short names
            name_map = {
                'logistic': 'logistic.joblib',
                'random_forest': 'random_forest.joblib',
                'svm_rbf': 'svm_rbf.joblib',
                'poly_logistic': 'poly_logistic.joblib',
            }
            key = fm.lower()
            fn = name_map.get(key)
            if fn:
                p = os.path.join(model_dir, fn)
                if os.path.exists(p):
                    return p
            # last attempt: try FM as basename
            p = os.path.join(model_dir, fm + ('' if fm.endswith('.joblib') else '.joblib'))
            if os.path.exists(p):
                return p
    except Exception:
        pass

    # best_model.joblib
    bestp = os.path.join(model_dir, 'best_model.joblib')
    if os.path.exists(bestp):
        return bestp

    # prefer random_forest
    rf = os.path.join(model_dir, 'random_forest.joblib')
    if os.path.exists(rf):
        return rf

    # fallback to any joblib
    for f in os.listdir(model_dir):
        if f.lower().endswith('.joblib'):
            return os.path.join(model_dir, f)

    return None
