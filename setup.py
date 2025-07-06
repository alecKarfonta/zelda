#!/usr/bin/env python3
"""
Setup script for OoT Training Data Generator
"""

from setuptools import setup, find_packages

setup(
    name="oot-training-generator",
    version="2.0.0",
    description="Enhanced OoT romhack training data generator with strict authenticity validation",
    author="OoT Generator Team",
    packages=find_packages(),
    install_requires=[
        "anthropic>=0.18.0",
        "python-dotenv>=1.0.0",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "oot-generator=src.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
) 