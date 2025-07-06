#!/usr/bin/env python3
"""
Dynamic Source Analyzer for OoT Decompilation
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Optional

from src.core.logger import logger


class DynamicSourceAnalyzer:
    """Analyzes and extracts information from real OoT decompilation source files"""
    
    def __init__(self, oot_root_path: str = "oot"):
        self.oot_root = Path(oot_root_path)
        self.source_cache = {}
        self.analyzed_files = set()
        
        # Source file categories
        self.source_categories = {
            "actors": self.oot_root / "src" / "overlays" / "actors",
            "core": self.oot_root / "src" / "code", 
            "effects": self.oot_root / "src" / "overlays" / "effects",
            "gamestates": self.oot_root / "src" / "overlays" / "gamestates",
            "misc": self.oot_root / "src" / "overlays" / "misc",
            "headers": self.oot_root / "include",
            "assets": self.oot_root / "assets",
        }
        
        # Real function signatures extracted from source
        self.real_functions = {}
        self.real_structs = {}
        self.real_enums = {}
        self.real_constants = {}
        self.real_examples = {}
        
        # Load comprehensive function list from our extraction
        self._load_comprehensive_functions()
        
        # Initialize analysis
        self._analyze_source_files()
    
    def _load_comprehensive_functions(self):
        """Load comprehensive function list from our regex extraction"""
        try:
            with open('oot_valid_functions.txt', 'r') as f:
                for line in f:
                    func_name = line.strip()
                    if func_name:
                        self.real_functions[func_name] = {
                            "signature": f"void {func_name}()",  # Placeholder signature
                            "return_type": "void",
                            "file": "comprehensive_extraction",
                            "category": "extracted",
                        }
            logger.info(f"Loaded {len(self.real_functions)} functions from comprehensive extraction")
        except FileNotFoundError:
            logger.warning("oot_valid_functions.txt not found, will use limited extraction")
            # Fall back to original extraction method
            pass
    
    def _analyze_source_files(self):
        """Analyze all source files and extract patterns"""
        # Skip if we already loaded comprehensive functions
        if len(self.real_functions) > 10000:  # If we loaded comprehensive list
            logger.info("Using comprehensive function list, skipping detailed analysis")
            return
            
        logger.info("🔍 Analyzing OoT decompilation source files...")
        
        # Analyze core files first
        core_files = list(self.source_categories["core"].glob("*.c"))
        for file_path in core_files:
            self._analyze_c_file(file_path, "core")
        
        # Analyze actor files
        actor_dirs = list(self.source_categories["actors"].glob("ovl_*"))
        for actor_dir in actor_dirs:
            c_files = list(actor_dir.glob("*.c"))
            for file_path in c_files:
                self._analyze_c_file(file_path, "actor")
        
        # Analyze header files
        header_files = list(self.source_categories["headers"].glob("*.h"))
        for file_path in header_files:
            self._analyze_h_file(file_path)
        
        logger.success(f"✅ Analyzed {len(self.analyzed_files)} files")
        logger.stats(f"   📊 Found {len(self.real_functions)} functions")
        logger.stats(f"   📊 Found {len(self.real_structs)} structs")
        logger.stats(f"   📊 Found {len(self.real_enums)} enums")
        logger.stats(f"   📊 Found {len(self.real_constants)} constants")
    
    def _analyze_c_file(self, file_path: Path, category: str):
        """Analyze a C source file for patterns"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.analyzed_files.add(str(file_path))
            
            # Extract function signatures
            self._extract_function_signatures(content, file_path, category)
            
            # Extract struct definitions
            self._extract_struct_definitions(content, file_path, category)
            
            # Extract enum definitions
            self._extract_enum_definitions(content, file_path, category)
            
            # Extract constants and macros
            self._extract_constants(content, file_path, category)
            
            # Extract complete examples for specific patterns
            self._extract_examples(content, file_path, category)
            
        except Exception as e:
            logger.error(f"⚠️  Error analyzing {file_path}: {e}")
    
    def _analyze_h_file(self, file_path: Path):
        """Analyze a header file for definitions"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.analyzed_files.add(str(file_path))
            
            # Extract typedefs and struct definitions
            self._extract_struct_definitions(content, file_path, "header")
            self._extract_enum_definitions(content, file_path, "header")
            self._extract_constants(content, file_path, "header")
            
        except Exception as e:
            logger.error(f"⚠️  Error analyzing {file_path}: {e}")
    
    def _extract_function_signatures(self, content: str, file_path: Path, category: str):
        """Extract function signatures from C source"""
        # Pattern for function definitions
        func_pattern = r'(?:^|\n)\s*(\w+(?:\s+\w+)*)\s+(\w+)\s*\([^)]*\)\s*\{'
        
        for match in re.finditer(func_pattern, content, re.MULTILINE):
            return_type = match.group(1).strip()
            func_name = match.group(2)
            
            # Get the full function signature
            start = match.start()
            func_line = content[start:match.end()].strip()
            
            self.real_functions[func_name] = {
                "signature": func_line,
                "return_type": return_type,
                "file": str(file_path),
                "category": category,
            }
    
    def _extract_struct_definitions(self, content: str, file_path: Path, category: str):
        """Extract struct definitions"""
        # Pattern for struct definitions with memory comments
        struct_pattern = r'typedef\s+struct\s*\w*\s*\{([^}]+)\}\s*(\w+);'
        
        for match in re.finditer(struct_pattern, content, re.DOTALL):
            struct_body = match.group(1)
            struct_name = match.group(2)
            
            # Parse struct fields
            fields = []
            for line in struct_body.split('\n'):
                line = line.strip()
                if line and not line.startswith('/*') and not line.startswith('//'):
                    fields.append(line)
            
            self.real_structs[struct_name] = {
                "fields": fields,
                "file": str(file_path),
                "category": category,
                "full_definition": match.group(0)
            }
    
    def _extract_enum_definitions(self, content: str, file_path: Path, category: str):
        """Extract enum definitions"""
        enum_pattern = r'typedef\s+enum\s*\w*\s*\{([^}]+)\}\s*(\w+);'
        
        for match in re.finditer(enum_pattern, content, re.DOTALL):
            enum_body = match.group(1)
            enum_name = match.group(2)
            
            # Parse enum values
            values = []
            for line in enum_body.split('\n'):
                line = line.strip()
                if line and not line.startswith('/*') and not line.startswith('//'):
                    values.append(line.rstrip(','))
            
            self.real_enums[enum_name] = {
                "values": values,
                "file": str(file_path),
                "category": category,
                "full_definition": match.group(0)
            }
    
    def _extract_constants(self, content: str, file_path: Path, category: str):
        """Extract #define constants and macros"""
        define_pattern = r'#define\s+(\w+)\s+([^\n]+)'
        
        for match in re.finditer(define_pattern, content):
            const_name = match.group(1)
            const_value = match.group(2).strip()
            
            self.real_constants[const_name] = {
                "value": const_value,
                "file": str(file_path),
                "category": category,
                "full_definition": match.group(0)
            }
    
    def _extract_examples(self, content: str, file_path: Path, category: str):
        """Extract complete code examples for specific patterns"""
        # Extract actor initialization patterns
        if "Init" in str(file_path) or "_Init(" in content:
            init_pattern = r'void\s+\w+_Init\s*\([^)]+\)\s*\{[^}]+\}'
            for match in re.finditer(init_pattern, content, re.DOTALL):
                example_key = f"{file_path.stem}_init"
                self.real_examples[example_key] = {
                    "code": match.group(0),
                    "type": "actor_init",
                    "file": str(file_path),
                    "category": category
                }
        
        # Extract collision setup patterns
        if "Collider" in content:
            collider_pattern = r'static\s+Collider\w+Init\s+\w+\s*=\s*\{[^}]+\};'
            for match in re.finditer(collider_pattern, content, re.DOTALL):
                example_key = f"{file_path.stem}_collider"
                self.real_examples[example_key] = {
                    "code": match.group(0),
                    "type": "collider_init",
                    "file": str(file_path),
                    "category": category
                }
    
    def get_real_function_signature(self, func_name: str) -> Optional[str]:
        """Get the real function signature from source code"""
        if func_name in self.real_functions:
            return self.real_functions[func_name]["signature"]
        return None
    
    def get_real_struct_definition(self, struct_name: str) -> Optional[str]:
        """Get the real struct definition from source code"""
        if struct_name in self.real_structs:
            return self.real_structs[struct_name]["full_definition"]
        return None
    
    def get_similar_actors(self, actor_type: str, limit: int = 5) -> List[str]:
        """Get similar actors for reference"""
        actor_files = []
        for func_name, func_info in self.real_functions.items():
            if func_info["category"] == "actor" and actor_type.lower() in func_info["file"].lower():
                actor_files.append(func_info["file"])
        
        return list(set(actor_files))[:limit]
    
    def get_authentic_example(self, example_type: str) -> Optional[Dict]:
        """Get an authentic code example of the specified type"""
        matching_examples = [
            example for key, example in self.real_examples.items()
            if example["type"] == example_type
        ]
        
        if matching_examples:
            return matching_examples[0]  # Return first match
        return None
    
    def get_real_constants_by_prefix(self, prefix: str) -> Dict[str, str]:
        """Get real constants starting with a prefix"""
        return {
            name: info["value"] for name, info in self.real_constants.items()
            if name.startswith(prefix)
        }
    
    def validate_against_real_source(self, code: str) -> List[str]:
        """Validate code against real source patterns"""
        issues = []
        
        # Check if functions used exist in real source
        func_pattern = r'(\w+)\s*\('
        for match in re.finditer(func_pattern, code):
            func_name = match.group(1)
            if (func_name not in ['if', 'for', 'while', 'switch', 'sizeof', 'typedef'] and
                not func_name.startswith('g') and not func_name.isupper() and
                len(func_name) > 3 and func_name not in self.real_functions):
                issues.append(f"Function '{func_name}' not found in real OoT source")
        
        # Check if structs used exist
        struct_pattern = r'(\w+)\s*\*?\s+\w+\s*='
        for match in re.finditer(struct_pattern, code):
            struct_name = match.group(1)
            if (struct_name not in ['int', 'char', 'float', 'double', 'void', 'u8', 'u16', 'u32', 's8', 's16', 's32', 'f32'] and
                struct_name not in self.real_structs):
                issues.append(f"Struct '{struct_name}' not found in real OoT source")
        
        return issues 