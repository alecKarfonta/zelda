#!/usr/bin/env python3
"""
JSONL Log Parser and Report Generator
Parses large_generation_20.jsonl and creates a comprehensive human-readable report.
"""

import json
import re
from datetime import datetime
from collections import defaultdict, Counter
import os

class LogParser:
    def __init__(self, jsonl_file):
        self.jsonl_file = jsonl_file
        self.entries = []
        self.actor_types = []
        self.feature_categories = defaultdict(list)
        self.code_patterns = []
        
    def parse_jsonl(self):
        """Parse the JSONL file and extract structured data."""
        print(f"Parsing {self.jsonl_file}...")
        
        with open(self.jsonl_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    entry = json.loads(line.strip())
                    
                    # Handle nested JSON structures in output field
                    entry = self.flatten_nested_structures(entry)
                    
                    self.entries.append(entry)
                    
                    # Extract actor types from code
                    if 'output' in entry:
                        self.extract_actor_info(entry['output'], line_num)
                        
                except json.JSONDecodeError as e:
                    print(f"Warning: JSON decode error on line {line_num}: {e}")
                except Exception as e:
                    print(f"Error processing line {line_num}: {e}")
        
        print(f"Successfully parsed {len(self.entries)} entries")
    
    def flatten_nested_structures(self, entry):
        """Flatten nested JSON structures within the output field, even if not valid JSON."""
        max_depth = 5  # Prevent infinite loops
        depth = 0
        
        while 'output' in entry and isinstance(entry['output'], str) and depth < max_depth:
            output = entry['output'].strip()
            if output.startswith('{'):
                # Try to extract the JSON object substring
                brace_count = 0
                start_idx = None
                end_idx = None
                for i, c in enumerate(output):
                    if c == '{':
                        if brace_count == 0:
                            start_idx = i
                        brace_count += 1
                    elif c == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_idx = i
                            break
                if start_idx is not None and end_idx is not None:
                    json_str = output[start_idx:end_idx+1]
                    # Clean up: replace newlines, tabs, and carriage returns with spaces
                    json_str_clean = re.sub(r'[\n\r\t]', ' ', json_str)
                    # Remove multiple spaces
                    json_str_clean = re.sub(r' +', ' ', json_str_clean)
                    try:
                        nested_data = json.loads(json_str_clean)
                        if 'instruction' in nested_data and 'output' in nested_data:
                            entry['instruction'] = nested_data['instruction']
                            entry['output'] = nested_data['output']
                            depth += 1
                            continue
                        else:
                            break
                    except Exception:
                        break
                else:
                    break
            else:
                break
        return entry
    
    def extract_actor_info(self, output_text, line_num):
        """Extract actor type information from code output."""
        # Look for typedef struct patterns
        struct_pattern = r'typedef struct \{\s*/\* 0x0000 \*/ Actor actor;\s*/\* 0x014C \*/ ([^}]+)\} ([^;]+);'
        matches = re.findall(struct_pattern, output_text, re.DOTALL)
        
        for match in matches:
            fields, actor_name = match
            self.actor_types.append({
                'name': actor_name.strip(),
                'fields': fields.strip(),
                'line': line_num
            })
        
        # Look for ActorProfile patterns
        profile_pattern = r'const ActorProfile ([^=]+) = \{[^}]+ACTOR_EN_([^,]+),'
        profile_matches = re.findall(profile_pattern, output_text, re.DOTALL)
        
        for match in profile_matches:
            profile_name, actor_type = match
            self.actor_types.append({
                'name': profile_name.strip(),
                'actor_type': actor_type.strip(),
                'line': line_num
            })
    
    def categorize_features(self):
        """Categorize features based on instruction keywords."""
        categories = {
            'Actor Systems': ['actor', 'creation', 'system'],
            'Animation': ['animation', 'anim', 'skel', 'skeleton'],
            'Physics': ['physics', 'cloth', 'hair', 'bubble', 'water'],
            'AI & Behavior': ['ai', 'behavior', 'npc', 'interaction'],
            'Combat': ['combat', 'enemy', 'attack', 'damage'],
            'Puzzle': ['puzzle', 'door', 'switch', 'mechanism'],
            'Sound': ['sound', 'voice', 'audio'],
            'Memory': ['memory', 'optimization'],
            'Debug': ['debug', 'error', 'handling'],
            'Equipment': ['equipment', 'inventory', 'item']
        }
        
        for entry in self.entries:
            instruction = entry.get('instruction', '').lower()
            
            for category, keywords in categories.items():
                if any(keyword in instruction for keyword in keywords):
                    self.feature_categories[category].append(entry)
                    break
            else:
                # Default category for uncategorized entries
                self.feature_categories['Other'].append(entry)
    
    def extract_code_snippets(self):
        """Extract and analyze code snippets."""
        for entry in self.entries:
            if 'output' in entry:
                output = entry['output']
                
                # Extract function definitions
                func_pattern = r'void ([^(]+)\([^)]*\) \{[^}]*\}'
                functions = re.findall(func_pattern, output, re.DOTALL)
                
                # Extract struct definitions
                struct_pattern = r'typedef struct \{[^}]*\} ([^;]+);'
                structs = re.findall(struct_pattern, output, re.DOTALL)
                
                # Extract enum definitions
                enum_pattern = r'typedef enum \{[^}]*\} ([^;]+);'
                enums = re.findall(enum_pattern, output, re.DOTALL)
                
                self.code_patterns.append({
                    'instruction': entry.get('instruction', ''),
                    'functions': functions,
                    'structs': structs,
                    'enums': enums
                })
    
    def generate_report(self, output_file):
        """Generate a comprehensive report document."""
        print(f"Generating report: {output_file}")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(self.generate_header())
            f.write(self.generate_summary())
            f.write(self.generate_feature_categories())
            f.write(self.generate_actor_analysis())
            f.write(self.generate_code_analysis())
            f.write(self.generate_detailed_entries())
            f.write(self.generate_footer())
        
        print(f"Report generated successfully: {output_file}")
    
    def generate_header(self):
        """Generate report header."""
        return f"""# Zelda OoT Actor System Generation Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Source File:** {self.jsonl_file}  
**Total Entries:** {len(self.entries)}

---

## Executive Summary

This report analyzes {len(self.entries)} generated actor system implementations for The Legend of Zelda: Ocarina of Time. The data contains various actor types, feature implementations, and code patterns following authentic OoT decompilation standards.

---

"""
    
    def generate_summary(self):
        """Generate summary statistics."""
        total_entries = len(self.entries)
        unique_actors = len(set(actor['name'] for actor in self.actor_types if 'name' in actor))
        
        return f"""## Summary Statistics

- **Total Entries:** {total_entries}
- **Unique Actor Types:** {unique_actors}
- **Feature Categories:** {len(self.feature_categories)}
- **Code Patterns Extracted:** {len(self.code_patterns)}

### Entry Distribution by Category

"""
    
    def generate_feature_categories(self):
        """Generate feature category analysis."""
        content = "## Feature Categories\n\n"
        
        for category, entries in self.feature_categories.items():
            content += f"### {category} ({len(entries)} entries)\n\n"
            
            for entry in entries[:3]:  # Show first 3 entries per category
                instruction = entry.get('instruction', 'N/A')
                content += f"- **{instruction[:100]}{'...' if len(instruction) > 100 else ''}**\n"
            
            if len(entries) > 3:
                content += f"- *... and {len(entries) - 3} more entries*\n"
            content += "\n"
        
        return content
    
    def generate_actor_analysis(self):
        """Generate actor type analysis."""
        content = "## Actor Type Analysis\n\n"
        
        if not self.actor_types:
            content += "No actor types extracted from code.\n\n"
            return content
        
        content += "### Extracted Actor Types\n\n"
        
        for actor in self.actor_types:
            name = actor.get('name', 'Unknown')
            actor_type = actor.get('actor_type', 'N/A')
            line = actor.get('line', 'N/A')
            
            content += f"- **{name}**"
            if actor_type != 'N/A':
                content += f" (Type: {actor_type})"
            content += f" (Line: {line})\n"
        
        content += "\n"
        return content
    
    def generate_code_analysis(self):
        """Generate code pattern analysis."""
        content = "## Code Pattern Analysis\n\n"
        
        if not self.code_patterns:
            content += "No code patterns extracted.\n\n"
            return content
        
        # Count function types
        function_types = Counter()
        struct_types = Counter()
        
        for pattern in self.code_patterns:
            for func in pattern['functions']:
                if 'Init' in func:
                    function_types['Init'] += 1
                elif 'Update' in func:
                    function_types['Update'] += 1
                elif 'Draw' in func:
                    function_types['Draw'] += 1
                elif 'Destroy' in func:
                    function_types['Destroy'] += 1
                else:
                    function_types['Other'] += 1
            
            for struct in pattern['structs']:
                struct_types[struct.strip()] += 1
        
        content += "### Function Distribution\n\n"
        for func_type, count in function_types.most_common():
            content += f"- **{func_type}:** {count} occurrences\n"
        
        content += "\n### Struct Types\n\n"
        for struct_type, count in struct_types.most_common(10):
            content += f"- **{struct_type}:** {count} occurrences\n"
        
        content += "\n"
        return content
    
    def generate_detailed_entries(self):
        """Generate detailed entry analysis."""
        content = "## Detailed Entry Analysis\n\n"
        
        for i, entry in enumerate(self.entries, 1):
            instruction = entry.get('instruction', 'N/A')
            output = entry.get('output', '')
            
            content += f"### Entry {i}\n\n"
            content += f"**Instruction:** {instruction}\n\n"
            
            # Extract key information from output
            if output:
                # Look for actor names
                actor_pattern = r'En([A-Z][a-zA-Z]+)'
                actors = re.findall(actor_pattern, output)
                if actors:
                    content += f"**Actors Found:** {', '.join(set(actors))}\n\n"
                
                # Look for function names
                func_pattern = r'void ([A-Za-z_]+)\([^)]*\)'
                functions = re.findall(func_pattern, output)
                if functions:
                    content += f"**Functions:** {', '.join(set(functions))}\n\n"
                
                # Show first 200 characters of output
                output_preview = output[:200].replace('\n', ' ').strip()
                content += f"**Output Preview:** {output_preview}...\n\n"
            
            content += "---\n\n"
        
        return content
    
    def generate_footer(self):
        """Generate report footer."""
        return f"""## Report Footer

**Analysis Complete**  
**Generated by:** JSONL Log Parser v1.0  
**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

*This report was automatically generated from the JSONL log file. All code patterns and actor types were extracted using regex patterns designed to match OoT decompilation standards.*
"""

    def write_conformed_jsonl(self, output_file):
        """Write a new JSONL file with conformed, flat instruction/output pairs."""
        print(f"Writing conformed JSONL to: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            for entry in self.entries:
                # Only keep instruction and output fields
                flat_entry = {
                    'instruction': entry.get('instruction', ''),
                    'output': entry.get('output', '')
                }
                f.write(json.dumps(flat_entry, ensure_ascii=False) + '\n')
        print(f"Conformed JSONL written: {output_file}")

def main():
    """Main execution function."""
    import sys
    input_file = "large_generation_20.jsonl"
    output_file = "zelda_actor_system_report.md"
    conformed_file = "large_generation_20_conformed.jsonl"
    
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found!")
        return
    
    # Create parser and process data
    parser = LogParser(input_file)
    parser.parse_jsonl()
    parser.categorize_features()
    parser.extract_code_snippets()
    
    # CLI option: --conform to write conformed JSONL
    if len(sys.argv) > 1 and sys.argv[1] == '--conform':
        parser.write_conformed_jsonl(conformed_file)
        return
    
    # Generate report
    parser.generate_report(output_file)
    
    # Print summary to console
    print("\n" + "="*50)
    print("PARSING COMPLETE")
    print("="*50)
    print(f"Entries processed: {len(parser.entries)}")
    print(f"Actor types found: {len(parser.actor_types)}")
    print(f"Feature categories: {len(parser.feature_categories)}")
    print(f"Report generated: {output_file}")
    print("="*50)

if __name__ == "__main__":
    main() 
    main() 