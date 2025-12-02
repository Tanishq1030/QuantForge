# backend/engine/parsers/__init__.py
"""
Text processing and feature extraction for QuantForge AI Engine.

Provides:
- Ticker extraction
- Entity recognition
- Text cleaning
- Deduplication
"""

from .text_preprocessor import TextPreprocessor

__all__ = ["TextPreprocessor"]
