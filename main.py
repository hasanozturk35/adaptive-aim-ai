#!/usr/bin/env python3
"""
Adaptif AI Nişan Alma Oyunu - Ana Başlangıç Dosyası
"""

import sys
import os

# src klasörünü path'e ekle
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from game import main

if __name__ == "__main__":
    main()
