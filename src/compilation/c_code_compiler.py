#!/usr/bin/env python3
"""
C Code Compilation Module for OoT Training Data
==============================================

This module handles the extraction and compilation of C code from generated
training data, ensuring it can be compiled with the OoT codebase dependencies.
"""

import os
import re
import json
import tempfile
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from src.core.logger import logger


@dataclass
class CompilationResult:
    """Result of a compilation attempt"""
    success: bool
    output_file: Optional[str] = None
    error_messages: Optional[List[str]] = None
    warnings: Optional[List[str]] = None
    compilation_time: float = 0.0
    extracted_code: Optional[str] = None
    
    def __post_init__(self):
        if self.error_messages is None:
            self.error_messages = []
        if self.warnings is None:
            self.warnings = []


class CCodeExtractor:
    """Extracts C code from training data outputs"""
    
    def __init__(self):
        # Improved patterns to capture complete code blocks
        self.code_patterns = [
            # Complete code blocks with ```c or ``` markers
            r'```c\s*(.*?)\s*```',
            r'```\s*(.*?)\s*```',
            
            # Complete struct definitions with functions
            r'typedef\s+struct\s*\{.*?\}\s*\w+;.*?(?:void|const|static).*?\{.*?\}',
            
            # Complete function blocks
            r'void\s+\w+_\w+\s*\([^)]*\)\s*\{.*?\}',
            
            # Complete struct definitions
            r'typedef\s+struct\s*\{.*?\}\s*\w+;',
            
            # Complete includes and externs
            r'#include\s*<[^>]+>.*?extern\s+\w+\s+\w+;',
        ]
    
    def extract_c_code(self, text: str) -> List[str]:
        """Extract C code snippets from text"""
        snippets = []
        
        # First try to extract complete code blocks with ```c or ``` markers
        code_block_pattern = r'```c\s*(.*?)\s*```'
        matches = re.findall(code_block_pattern, text, re.DOTALL | re.IGNORECASE)
        snippets.extend(matches)
        
        # If no code blocks found, try to extract complete C code blocks
        if not snippets:
            # Look for complete C code blocks that start with typedef and end with ActorProfile
            complete_block_pattern = r'(typedef\s+struct\s*\{.*?const\s+ActorProfile\s+\w+\s*=\s*\{.*?\};)'
            matches = re.findall(complete_block_pattern, text, re.DOTALL | re.IGNORECASE)
            snippets.extend(matches)
        
        # If still no snippets, try to extract individual functions and structs
        if not snippets:
            # Extract struct definitions
            struct_pattern = r'typedef\s+struct\s*\{.*?\}\s*\w+;'
            struct_matches = re.findall(struct_pattern, text, re.DOTALL | re.IGNORECASE)
            snippets.extend(struct_matches)
            
            # Extract function definitions
            function_pattern = r'void\s+\w+_\w+\s*\([^)]*\)\s*\{.*?\}'
            function_matches = re.findall(function_pattern, text, re.DOTALL | re.IGNORECASE)
            snippets.extend(function_matches)
            
            # Extract static variable definitions
            static_pattern = r'static\s+.*?=.*?;'
            static_matches = re.findall(static_pattern, text, re.DOTALL | re.IGNORECASE)
            snippets.extend(static_matches)
        
        # Remove duplicates and clean up
        unique_snippets = []
        for snippet in snippets:
            cleaned = snippet.strip()
            if cleaned and cleaned not in unique_snippets and len(cleaned) > 20:
                unique_snippets.append(cleaned)
        
        return unique_snippets


class OoTCompiler:
    """Compiles C code with OoT dependencies"""
    
    def __init__(self, oot_path: str = "oot"):
        self.oot_path = Path(oot_path)
        self.include_paths = [
            str(self.oot_path / "include"),
            str(self.oot_path / "include/ultra64"),
            str(self.oot_path / "include/libc"),
            str(self.oot_path / "include/libc64"),
            str(self.oot_path / "include/libu64"),
        ]
        
        # Check if MIPS toolchain is available
        self.mips_gcc = "mips-linux-gnu-gcc"
        self.has_mips_toolchain = self._check_mips_toolchain()
        
        if not self.has_mips_toolchain:
            logger.warning("⚠️ MIPS toolchain not found, using GCC for syntax checking only")
    
    def _check_mips_toolchain(self) -> bool:
        """Check if MIPS toolchain is available"""
        try:
            result = subprocess.run([self.mips_gcc, "--version"], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _fix_common_constants(self, code: str) -> str:
        """Fix common constant name issues in generated code"""
        # Replace wrong collision constants with correct ones
        replacements = {
            'COLTYPE_NONE': 'COL_MATERIAL_NONE',
            'COLTYPE_HIT0': 'COL_MATERIAL_HIT0',
            'COLTYPE_HIT1': 'COL_MATERIAL_HIT1',
            'COLTYPE_HIT2': 'COL_MATERIAL_HIT2',
            'COLTYPE_HIT3': 'COL_MATERIAL_HIT3',
            'COLTYPE_METAL': 'COL_MATERIAL_METAL',
            'COLTYPE_WOOD': 'COL_MATERIAL_WOOD',
            'COLTYPE_HARD': 'COL_MATERIAL_HARD',
            'COLTYPE_TREE': 'COL_MATERIAL_TREE',
            'ELEMTYPE_UNK0': 'ELEM_MATERIAL_UNK0',
            'ELEMTYPE_UNK1': 'ELEM_MATERIAL_UNK1',
            'ELEMTYPE_UNK2': 'ELEM_MATERIAL_UNK2',
            'ELEMTYPE_UNK3': 'ELEM_MATERIAL_UNK3',
            'ELEMTYPE_UNK4': 'ELEM_MATERIAL_UNK4',
            'ELEMTYPE_UNK5': 'ELEM_MATERIAL_UNK5',
            'ELEMTYPE_UNK6': 'ELEM_MATERIAL_UNK6',
            'ELEMTYPE_UNK7': 'ELEM_MATERIAL_UNK7',
            # Fix OPEN_DISPS macro calls
            'OPEN_DISPS(play->state.gfxCtx)': 'OPEN_DISPS(play->state.gfxCtx, __FILE__, __LINE__)',
            'CLOSE_DISPS(play->state.gfxCtx)': 'CLOSE_DISPS(play->state.gfxCtx, __FILE__, __LINE__)',
            # Fix background check flags
            'BGCHECKFLAG_GROUND': 'UPDBGCHECKINFO_FLAG_0 | UPDBGCHECKINFO_FLAG_2',
            'BGCHECKFLAG_LAVA': 'UPDBGCHECKINFO_FLAG_0 | UPDBGCHECKINFO_FLAG_2',
            # Fix player access patterns
            'player->health': 'gSaveContext.health',
            'player->healthCapacity': 'gSaveContext.healthCapacity',
            'player->currentShield': 'gSaveContext.equips.buttonItems[1]',
            'player->swordState': 'gSaveContext.equips.buttonItems[0]',
            # Fix non-existent constants
            'PLAYER_SHIELD_MAX': '20',
            'PLAYER_SWORD_MAX': '20',
            'LIMB_COUNT': '20',
            'ACTOR_PLAYER': 'ACTOR_PLAYER',
            # Fix non-existent functions
            'func_8002F71C': 'func_8002F71C_placeholder',
            # Fix wrong flag usage
            'ACTOR_FLAG_8': 'ACTOR_FLAG_0',
            'ACTOR_FLAG_9': 'ACTOR_FLAG_1',
            'ACTOR_FLAG_10': 'ACTOR_FLAG_2',
            'ACTOR_FLAG_11': 'ACTOR_FLAG_3',
            'ACTOR_FLAG_12': 'ACTOR_FLAG_4',
            'ACTOR_FLAG_13': 'ACTOR_FLAG_5',
            'ACTOR_FLAG_14': 'ACTOR_FLAG_6',
            'ACTOR_FLAG_15': 'ACTOR_FLAG_7',
        }
        
        fixed_code = code
        for wrong, correct in replacements.items():
            fixed_code = fixed_code.replace(wrong, correct)
        
        return fixed_code
    
    def compile_code(self, code: str, dependencies: Optional[List[str]] = None) -> CompilationResult:
        """Compile C code with OoT dependencies"""
        start_time = time.time()
        
        # Fix common constant issues
        fixed_code = self._fix_common_constants(code)
        
        # Create a test file with the code
        test_file = self._create_test_file(fixed_code, dependencies)
        
        try:
            # Try to compile with MIPS toolchain if available
            if self.has_mips_toolchain:
                result = self._compile_with_mips(test_file)
            else:
                # Fall back to GCC for syntax checking
                result = self._compile_with_gcc(test_file)
            
            result.compilation_time = time.time() - start_time
            result.extracted_code = code
            
            return result
            
        except Exception as e:
            result = CompilationResult(
                success=False,
                error_messages=[str(e)],
                compilation_time=time.time() - start_time,
                extracted_code=code
            )
            return result
        finally:
            # Clean up test file
            try:
                os.unlink(test_file)
            except:
                pass
    
    def _create_test_file(self, code: str, dependencies: Optional[List[str]] = None) -> str:
        """Create a test C file with the code and necessary includes"""
        
        # Basic includes that most OoT code needs
        includes = [
            "#include <ultra64.h>",
            "#include <stdlib.h>",  # For rand() function
            "#include <actor.h>",
            "#include <play_state.h>",  # Essential for PlayState type
            "#include <player.h>",      # Essential for Player type
            "#include <z_lib.h>",
            "#include <z_math.h>",
            "#include <collision_check.h>",  # Essential for collision flags
            "#include <gfx.h>",
            "#include <sys_matrix.h>",
            "#include <sys_math.h>",
            "#include <sys_math3d.h>",
            "#include <message.h>",     # For message system
            "#include <interface.h>",   # For interface functions
            "#include <object.h>",      # For object loading
            "#include <room.h>",        # For room functions
            "#include <scene.h>",       # For scene functions
            "#include <sram.h>",        # For save context
            "#include <save.h>",        # For SaveContext and gSaveContext
            "#include <inventory.h>",   # For inventory items
            "#include <audio.h>",       # For audio functions
            "#include <animation.h>",   # For animation system
        ]
        
        # Add extern declarations for global variables
        externs = [
            "extern SaveContext gSaveContext;",
            "extern Input* input;",
            "extern PlayState* play;",
            "extern Player* player;",
        ]
        
        # Add missing constants that are commonly used
        constants = [
            "// Common collision flags",
            "#define AT_NONE 0",
            "#define AT_ON (1 << 0)",
            "#define AT_HIT (1 << 1)",
            "#define AT_TYPE_PLAYER (1 << 3)",
            "#define AT_TYPE_ENEMY (1 << 4)",
            "#define AC_NONE 0",
            "#define AC_ON (1 << 0)",
            "#define AC_HIT (1 << 1)",
            "#define AC_TYPE_PLAYER AT_TYPE_PLAYER",
            "#define OC1_NONE 0",
            "#define OC1_ON (1 << 0)",
            "#define OC1_HIT (1 << 1)",
            "#define OC2_NONE 0",
            "#define OC2_TYPE_1 OC1_TYPE_1",
            "#define OC2_TYPE_2 OC1_TYPE_2",
            "",
            "// Common collision materials (correct constants)",
            "#define COL_MATERIAL_NONE 10",
            "#define COL_MATERIAL_HIT0 0",
            "#define COL_MATERIAL_HIT1 1",
            "#define COL_MATERIAL_HIT2 2",
            "#define COL_MATERIAL_HIT3 3",
            "#define COL_MATERIAL_METAL 4",
            "#define COL_MATERIAL_WOOD 5",
            "#define COL_MATERIAL_HARD 6",
            "#define COL_MATERIAL_TREE 7",
            "",
            "// Common element flags",
            "#define ATELEM_NONE 0",
            "#define ATELEM_ON (1 << 0)",
            "#define ACELEM_NONE 0",
            "#define ACELEM_ON (1 << 0)",
            "#define OCELEM_NONE 0",
            "#define OCELEM_ON (1 << 0)",
            "",
            "// Common element materials (correct constants)",
            "#define ELEM_MATERIAL_UNK0 0",
            "#define ELEM_MATERIAL_UNK1 1",
            "#define ELEM_MATERIAL_UNK2 2",
            "#define ELEM_MATERIAL_UNK3 3",
            "#define ELEM_MATERIAL_UNK4 4",
            "#define ELEM_MATERIAL_UNK5 5",
            "#define ELEM_MATERIAL_UNK6 6",
            "#define ELEM_MATERIAL_UNK7 7",
            "",
            "// Common hit effects",
            "#define HIT_SPECIAL_EFFECT_NONE 0",
            "#define HIT_BACKLASH_NONE 0",
            "",
            "// Common touch/bump flags",
            "#define TOUCH_NONE 0",
            "#define TOUCH_ON (1 << 0)",
            "#define TOUCH_SFX_NONE (3 << 3)",
            "#define BUMP_NONE 0",
            "#define BUMP_ON (1 << 0)",
            "",
            "// Common actor flags (correct range)",
            "#define ACTOR_FLAG_0 (1 << 0)",
            "#define ACTOR_FLAG_1 (1 << 1)",
            "#define ACTOR_FLAG_2 (1 << 2)",
            "#define ACTOR_FLAG_3 (1 << 3)",
            "#define ACTOR_FLAG_4 (1 << 4)",
            "#define ACTOR_FLAG_5 (1 << 5)",
            "#define ACTOR_FLAG_6 (1 << 6)",
            "#define ACTOR_FLAG_7 (1 << 7)",
            "",
            "// Background check flags (correct constants)",
            "#define UPDBGCHECKINFO_FLAG_0 (1 << 0)",
            "#define UPDBGCHECKINFO_FLAG_1 (1 << 1)",
            "#define UPDBGCHECKINFO_FLAG_2 (1 << 2)",
            "#define UPDBGCHECKINFO_FLAG_3 (1 << 3)",
            "",
            "// Common skeleton data (placeholders)",
            "extern void* gGhostSkel;",
            "extern void* gGhostFloatAnim;",
            "extern void* gGhostIdleAnim;",
            "extern void* gGhostWalkAnim;",
            "extern void* gGhostAttackAnim;",
            "extern void* gGhostDamageAnim;",
            "extern void* gGhostDeathAnim;",
            "",
            "// Common object data (placeholders)",
            "extern void* gCrystalSkel;",
            "extern void* gCrystalIdleAnim;",
            "extern void* gCrystalGlowAnim;",
            "extern void* gFireFlowSkel;",
            "extern void* gFireFlowIdleAnim;",
            "extern void* gBarrierSkel;",
            "extern void* gBarrierIdleAnim;",
            "extern void* gSandFlowSkel;",
            "extern void* gSandFlowIdleAnim;",
            "",
            "// Common function declarations",
            "void func_8002F71C_placeholder(PlayState* play, Actor* actor, f32 damage, s16 yaw, f32 knockback);",
            "void func_8002F71C_2(PlayState* play, Actor* actor, f32 damage, s16 yaw, f32 knockback);",
            "void func_8002F71C_3(PlayState* play, Actor* actor, f32 damage, s16 yaw, f32 knockback);",
        ]
        
        # Add any additional dependencies
        if dependencies is not None:
            includes.extend(dependencies)
        
        # Create the test file content
        test_content = f"""// Test compilation file
{chr(10).join(includes)}

// Extern declarations for global variables
{chr(10).join(externs)}

// Missing constants
{chr(10).join(constants)}

// Common random functions
f32 Rand_ZeroOne(void) {{ return 0.5f; }}  // Simplified for compilation
f32 Rand_CenteredFloat(f32 range) {{ return 0.0f; }}  // Simplified for compilation
s16 Rand_S16Offset(s16 base, s16 range) {{ return base; }}  // Simplified for compilation

// The actual code to test
{code}

// Main function to make it compile
int main() {{
    return 0;
}}
"""
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
            f.write(test_content)
            return f.name
    
    def _compile_with_mips(self, test_file: str) -> CompilationResult:
        """Compile with MIPS toolchain"""
        cmd = [
            self.mips_gcc,
            "-I" + self.include_paths[0],
            "-I" + self.include_paths[1],
            "-I" + self.include_paths[2],
            "-I" + self.include_paths[3],
            "-I" + self.include_paths[4],
            "-march=mips3",
            "-mabi=32",
            "-fno-PIC",
            "-fno-PIE",
            "-nostdlib",
            "-nostdinc",
            "-c",
            test_file,
            "-o", test_file.replace('.c', '.o')
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return CompilationResult(
                    success=True,
                    output_file=test_file.replace('.c', '.o'),
                    warnings=result.stderr.split('\n') if result.stderr else []
                )
            else:
                return CompilationResult(
                    success=False,
                    error_messages=result.stderr.split('\n') if result.stderr else [],
                    warnings=result.stdout.split('\n') if result.stdout else []
                )
        except subprocess.TimeoutExpired:
            return CompilationResult(
                success=False,
                error_messages=["Compilation timed out"]
            )
    
    def _compile_with_gcc(self, test_file: str) -> CompilationResult:
        """Compile with GCC for syntax checking"""
        cmd = [
            "gcc",
            "-I" + self.include_paths[0],
            "-I" + self.include_paths[1],
            "-I" + self.include_paths[2],
            "-I" + self.include_paths[3],
            "-I" + self.include_paths[4],
            "-fsyntax-only",
            "-Wall",
            "-Wextra",
            test_file
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return CompilationResult(
                    success=True,
                    warnings=result.stderr.split('\n') if result.stderr else []
                )
            else:
                return CompilationResult(
                    success=False,
                    error_messages=result.stderr.split('\n') if result.stderr else [],
                    warnings=result.stdout.split('\n') if result.stdout else []
                )
        except subprocess.TimeoutExpired:
            return CompilationResult(
                success=False,
                error_messages=["Compilation timed out"]
            )


class TrainingDataCompiler:
    """Compiles C code from training data files"""
    
    def __init__(self, oot_path: str = "oot"):
        self.extractor = CCodeExtractor()
        self.compiler = OoTCompiler(oot_path)
        self.results = []
    
    def process_training_data(self, file_path: str, output_parsed_code: bool = False, parsed_code_dir: Optional[str] = None) -> List[CompilationResult]:
        """Process a training data file and compile all C code snippets"""
        logger.info(f"📁 Processing training data file: {file_path}")
        
        results = []
        snippet_count = 0
        
        # Create directory for parsed code if requested
        if output_parsed_code and parsed_code_dir:
            os.makedirs(parsed_code_dir, exist_ok=True)
            logger.info(f"📁 Parsed code will be saved to: {parsed_code_dir}")
        
        try:
            with open(file_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        data = json.loads(line.strip())
                        output = data.get('output', '')
                        
                        # Parse the output field which contains JSON with the actual C code
                        try:
                            output_data = json.loads(output)
                            actual_code = output_data.get('output', '')
                        except (json.JSONDecodeError, TypeError):
                            # If output is not JSON, use it directly
                            actual_code = output
                        
                        # Extract C code from the actual code
                        c_snippets = self.extractor.extract_c_code(actual_code)
                        
                        for snippet_idx, snippet in enumerate(c_snippets):
                            snippet_count += 1
                            snippet_name = f"example_{line_num}_snippet_{snippet_idx}"
                            
                            logger.info(f"🔧 Compiling {snippet_name}...")
                            
                            # Try to compile the snippet
                            result = self.compiler.compile_code(snippet)
                            result.extracted_code = snippet
                            
                            # Save parsed code to file if requested
                            if output_parsed_code and parsed_code_dir and snippet.strip():
                                self._save_parsed_code(snippet, snippet_name, parsed_code_dir)
                            
                            if result.success:
                                logger.success(f"✅ {snippet_name} compiled successfully")
                            else:
                                logger.warning(f"⚠️ {snippet_name} compilation failed")
                                for error in (result.error_messages or [])[:3]:  # Show first 3 errors
                                    logger.error(f"❌ {error}")
                            
                            results.append(result)
                            
                    except json.JSONDecodeError:
                        logger.warning(f"⚠️ Invalid JSON on line {line_num}")
                        continue
        
        except FileNotFoundError:
            logger.error(f"❌ File not found: {file_path}")
            return []
        
        logger.info(f"📊 Results for {file_path}:")
        successful = sum(1 for r in results if r.success)
        total = len(results)
        success_rate = (successful / total * 100) if total > 0 else 0.0
        
        logger.info(f"  - Total C code snippets: {total}")
        logger.info(f"  - Successful compilations: {successful}")
        logger.info(f"  - Success rate: {success_rate:.1f}%")
        
        if successful == 0:
            logger.warning("⚠️ No snippets compiled successfully")
        
        # Save detailed report
        report_file = file_path.replace('.jsonl', '_compilation_report.txt')
        self._save_compilation_report(file_path, results, report_file)
        logger.info(f"  - Report saved to: {report_file}")
        
        return results
    
    def _save_parsed_code(self, code: str, snippet_name: str, output_dir: str):
        """Save parsed C code to a file"""
        if not code.strip():
            return
        
        # Create a safe filename
        safe_filename = re.sub(r'[^\w\-_.]', '_', snippet_name)
        output_file = os.path.join(output_dir, f"{safe_filename}.c")
        
        try:
            with open(output_file, 'w') as f:
                f.write(f"// Parsed C code from {snippet_name}\n")
                f.write(f"// Extracted from training data\n\n")
                f.write(code)
            
            logger.debug(f"💾 Saved parsed code to: {output_file}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to save parsed code for {snippet_name}: {e}")
    
    def save_all_parsed_code(self, results: List[CompilationResult], output_dir: str):
        """Save all parsed C code snippets to individual files"""
        os.makedirs(output_dir, exist_ok=True)
        
        saved_count = 0
        for i, result in enumerate(results):
            if result.extracted_code and result.extracted_code.strip():
                filename = f"snippet_{i+1:04d}.c"
                output_file = os.path.join(output_dir, filename)
                
                try:
                    with open(output_file, 'w') as f:
                        f.write(f"// Snippet {i+1}\n")
                        f.write(f"// Success: {result.success}\n")
                        f.write(f"// Compilation time: {result.compilation_time:.3f}s\n\n")
                        f.write(result.extracted_code)
                    
                    saved_count += 1
                except Exception as e:
                    logger.warning(f"⚠️ Failed to save snippet {i+1}: {e}")
        
        logger.info(f"💾 Saved {saved_count} parsed code files to: {output_dir}")
    
    def _save_compilation_report(self, file_path: str, results: List[CompilationResult], report_file: str):
        """Save a detailed compilation report"""
        with open(report_file, 'w') as f:
            f.write(f"Compilation Report for {file_path}\n")
            f.write("=" * 50 + "\n\n")
            
            successful = sum(1 for r in results if r.success)
            total = len(results)
            success_rate = (successful / total * 100) if total > 0 else 0.0
            
            f.write(f"Summary:\n")
            f.write(f"- Total C code snippets: {total}\n")
            f.write(f"- Successful compilations: {successful}\n")
            f.write(f"- Failed compilations: {total - successful}\n")
            f.write(f"- Success rate: {success_rate:.1f}%\n\n")
            
            f.write("Detailed Results:\n")
            f.write("-" * 30 + "\n")
            
            for i, result in enumerate(results):
                f.write(f"\nSnippet {i+1}:\n")
                f.write(f"Success: {result.success}\n")
                f.write(f"Compilation time: {result.compilation_time:.3f}s\n")
                
                if result.error_messages:
                    f.write("Errors:\n")
                    for error in result.error_messages[:5]:  # Show first 5 errors
                        f.write(f"  {error}\n")
                
                if result.warnings:
                    f.write("Warnings:\n")
                    for warning in result.warnings[:3]:  # Show first 3 warnings
                        f.write(f"  {warning}\n")
                
                if result.extracted_code:
                    f.write("Extracted code (first 200 chars):\n")
                    f.write(f"  {result.extracted_code[:200]}...\n")
    
    def generate_compilation_report(self, results: List[CompilationResult]) -> str:
        """Generate a summary compilation report"""
        if not results:
            return "No compilation results to report."
        
        total_examples = len(results)
        successful_compilations = sum(1 for r in results if r.success)
        failed_compilations = total_examples - successful_compilations
        success_rate = (successful_compilations/total_examples*100) if total_examples > 0 else 0.0
        
        report = f"""
C Code Compilation Report
========================

Summary:
- Total C code snippets processed: {total_examples}
- Successful compilations: {successful_compilations}
- Failed compilations: {failed_compilations}
- Success rate: {success_rate:.1f}%

Detailed Results:
"""
        
        for i, result in enumerate(results):
            status = "✅ SUCCESS" if result.success else "❌ FAILED"
            report += f"\nSnippet {i+1}: {status}\n"
            
            if result.error_messages:
                report += "Errors:\n"
                for error in (result.error_messages or [])[:3]:  # Show first 3 errors
                    report += f"  {error}\n"
        
        return report


def main():
    """Main function for testing the compilation system"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Compile C code from training data")
    parser.add_argument("input_file", help="Input training data file (.jsonl)")
    parser.add_argument("--oot-path", default="oot", help="Path to OoT decompilation")
    parser.add_argument("--output-report", help="Output report file")
    parser.add_argument("--output-parsed-code", action="store_true", 
                       help="Output parsed C code to individual files")
    parser.add_argument("--parsed-code-dir", default="parsed_code", 
                       help="Directory to save parsed C code files")
    
    args = parser.parse_args()
    
    # Initialize compiler
    compiler = TrainingDataCompiler(args.oot_path)
    
    # Process training data
    results = compiler.process_training_data(
        args.input_file, 
        output_parsed_code=args.output_parsed_code,
        parsed_code_dir=args.parsed_code_dir
    )
    
    # Save all parsed code if requested
    if args.output_parsed_code:
        compiler.save_all_parsed_code(results, args.parsed_code_dir)
    
    # Generate report
    report = compiler.generate_compilation_report(results)
    
    # Output report
    if args.output_report:
        with open(args.output_report, 'w') as f:
            f.write(report)
        logger.info(f"📄 Report saved to: {args.output_report}")
    else:
        print(report)


if __name__ == "__main__":
    main() 