#!/usr/bin/env python3
"""
Monitor OoT Training Data Generation Progress
"""

import os
import time
import json
from pathlib import Path

def monitor_generation():
    """Monitor the generation progress"""
    
    output_file = "oot_training_100_examples.jsonl"
    analysis_file = "oot_training_100_examples_diversity_analysis.json"
    
    print("🔍 Monitoring OoT Training Data Generation")
    print("=" * 50)
    print(f"📁 Output file: {output_file}")
    print(f"📊 Analysis file: {analysis_file}")
    print()
    
    start_time = time.time()
    last_count = 0
    
    while True:
        # Check if files exist
        output_exists = Path(output_file).exists()
        analysis_exists = Path(analysis_file).exists()
        
        current_count = 0
        if output_exists:
            try:
                with open(output_file, 'r') as f:
                    current_count = sum(1 for line in f if line.strip())
            except:
                current_count = 0
        
        elapsed = time.time() - start_time
        
        # Clear screen and show status
        os.system('clear' if os.name == 'posix' else 'cls')
        
        print("🔍 OoT Training Data Generation Monitor")
        print("=" * 50)
        print(f"⏱️  Elapsed time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
        print(f"📊 Examples generated: {current_count}/100")
        
        if current_count > 0:
            rate = current_count / elapsed * 60  # examples per minute
            estimated_total = 100 / rate if rate > 0 else 0
            remaining = estimated_total - elapsed/60 if estimated_total > elapsed/60 else 0
            
            print(f"📈 Generation rate: {rate:.1f} examples/minute")
            print(f"⏳ Estimated remaining: {remaining:.1f} minutes")
            
            # Progress bar
            progress = current_count / 100
            bar_length = 40
            filled_length = int(bar_length * progress)
            bar = '█' * filled_length + '░' * (bar_length - filled_length)
            print(f"📊 Progress: [{bar}] {progress*100:.1f}%")
        
        print()
        print(f"📁 Output file exists: {'✅' if output_exists else '❌'}")
        print(f"📊 Analysis file exists: {'✅' if analysis_exists else '❌'}")
        
        # Show recent activity
        if current_count > last_count:
            print(f"🆕 New examples: +{current_count - last_count}")
            last_count = current_count
        
        # Check if generation is complete
        if analysis_exists and current_count >= 100:
            print("\n🎉 GENERATION COMPLETE!")
            
            # Show final analysis
            try:
                with open(analysis_file, 'r') as f:
                    analysis = json.load(f)
                    
                print("\n📊 FINAL RESULTS:")
                print(f"✅ Total examples: {analysis.get('total_examples', 0)}")
                print(f"📈 Average quality: {analysis.get('average_quality', 0):.2f}/10")
                print(f"🎯 Average authenticity: {analysis.get('average_authenticity', 0):.2f}/10")
                
                diversity = analysis.get('diversity_metrics', {})
                print(f"🌈 Category coverage: {diversity.get('category_coverage', 0)}/14")
                print(f"🎲 Type coverage: {diversity.get('type_coverage', 0)}/18")
                print(f"💡 Unique scenarios: {diversity.get('unique_scenarios', 0)}")
                
            except Exception as e:
                print(f"⚠️  Could not read analysis: {e}")
            
            break
        
        # Check if process is still running
        try:
            import subprocess
            result = subprocess.run(['pgrep', '-f', 'enhanced_authentic_generator'], 
                                  capture_output=True, text=True)
            if not result.stdout.strip():
                print("\n⚠️  Generation process not found - may have completed or failed")
                break
        except:
            pass
        
        print(f"\n🔄 Updating in 10 seconds... (Ctrl+C to stop monitoring)")
        time.sleep(10)

if __name__ == "__main__":
    try:
        monitor_generation()
    except KeyboardInterrupt:
        print("\n\n👋 Monitoring stopped by user")
    except Exception as e:
        print(f"\n❌ Monitor error: {e}") 