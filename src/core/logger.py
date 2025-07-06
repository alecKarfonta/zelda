#!/usr/bin/env python3
"""
Enhanced OoT Logging System with function names and relevant emojis
"""

import logging
from typing import Optional


class OoTLogger:
    """Enhanced logging system with function names and relevant emojis"""
    
    def __init__(self, name: str = "OoTGenerator"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Create console handler with custom formatter
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Custom formatter with function names and emojis
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s.%(funcName)s() | %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        # Add handler if not already added
        if not self.logger.handlers:
            self.logger.addHandler(console_handler)
    
    def debug(self, message: str, func_name: Optional[str] = None):
        """Debug level with 🔍 emoji"""
        if func_name:
            self.logger.debug(f"🔍 {message}")
        else:
            self.logger.debug(f"🔍 {message}")
    
    def info(self, message: str, func_name: Optional[str] = None):
        """Info level with ℹ️ emoji"""
        if func_name:
            self.logger.info(f"ℹ️  {message}")
        else:
            self.logger.info(f"ℹ️  {message}")
    
    def warning(self, message: str, func_name: Optional[str] = None):
        """Warning level with ⚠️ emoji"""
        if func_name:
            self.logger.warning(f"⚠️  {message}")
        else:
            self.logger.warning(f"⚠️  {message}")
    
    def error(self, message: str, func_name: Optional[str] = None):
        """Error level with ❌ emoji"""
        if func_name:
            self.logger.error(f"❌ {message}")
        else:
            self.logger.error(f"❌ {message}")
    
    def success(self, message: str, func_name: Optional[str] = None):
        """Success level with ✅ emoji"""
        if func_name:
            self.logger.info(f"✅ {message}")
        else:
            self.logger.info(f"✅ {message}")
    
    def analysis(self, message: str, func_name: Optional[str] = None):
        """Analysis level with 🔍 emoji"""
        if func_name:
            self.logger.info(f"🔍 {message}")
        else:
            self.logger.info(f"🔍 {message}")
    
    def validation(self, message: str, func_name: Optional[str] = None):
        """Validation level with 🛡️ emoji"""
        if func_name:
            self.logger.info(f"🛡️  {message}")
        else:
            self.logger.info(f"🛡️  {message}")
    
    def generation(self, message: str, func_name: Optional[str] = None):
        """Generation level with 🎯 emoji"""
        if func_name:
            self.logger.info(f"🎯 {message}")
        else:
            self.logger.info(f"🎯 {message}")
    
    def refinement(self, message: str, func_name: Optional[str] = None):
        """Refinement level with 🔧 emoji"""
        if func_name:
            self.logger.info(f"🔧 {message}")
        else:
            self.logger.info(f"🔧 {message}")
    
    def diversity(self, message: str, func_name: Optional[str] = None):
        """Diversity level with 🌈 emoji"""
        if func_name:
            self.logger.info(f"🌈 {message}")
        else:
            self.logger.info(f"🌈 {message}")
    
    def stats(self, message: str, func_name: Optional[str] = None):
        """Statistics level with 📊 emoji"""
        if func_name:
            self.logger.info(f"📊 {message}")
        else:
            self.logger.info(f"📊 {message}")
    
    def file_ops(self, message: str, func_name: Optional[str] = None):
        """File operations level with 💾 emoji"""
        if func_name:
            self.logger.info(f"💾 {message}")
        else:
            self.logger.info(f"💾 {message}")


# Global logger instance
logger = OoTLogger() 