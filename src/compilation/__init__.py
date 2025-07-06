"""
C Code Compilation Module for OoT Training Data
==============================================

This module provides functionality to extract and compile C code from generated
training data, ensuring it can be compiled with the OoT codebase dependencies.
"""

from .c_code_compiler import (
    CompilationResult,
    CCodeExtractor,
    OoTCompiler,
    TrainingDataCompiler
)

__all__ = [
    'CompilationResult',
    'CCodeExtractor', 
    'OoTCompiler',
    'TrainingDataCompiler'
] 