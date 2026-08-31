#!/usr/bin/env python
import os
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.tasks.celery_app import celery

if __name__ == '__main__':
    celery.start()