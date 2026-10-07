from .auth import auth_bp
from .assistant import assistant_bp
from .upload import upload_bp
from .pipelines import pipelines_bp
from .infrastructure import infrastructure_bp
from .monitoring import monitoring_bp
from .training import training_bp
from .settings import settings_bp

__all__ = [
    'auth_bp',
    'assistant_bp',
    'upload_bp',
    'pipelines_bp',
    'infrastructure_bp',
    'monitoring_bp',
    'training_bp',
    'settings_bp'
]