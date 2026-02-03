#!/usr/bin/env python3
"""
Phase 4/5 Test Runner
Run complete pipeline test with LangChain chains and callbacks
"""

import asyncio
import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

async def run_test():
    """Run Phase 4/5 test"""
    from context.agent import ContextAgent
    
    # Paths
    config_path = "Agents/context/IMP-10-0-0-00.yaml"
    output_dir = "Agents/test/ContextAgent/IMP-10-0-0-00"
    
    print("="*60)
    print("Phase 4/5 Test: LangChain Chains + Callbacks")
    print("="*60)
    print(f"\nConfig: {config_path}")
    print(f"Output: {output_dir}\n")
    
    # Create agent with debug mode
    agent = ContextAgent(debug_mode=True)
    
    # Run pipeline
    try:
        result = await agent.process({
            "config_path": config_path,
            "output_dir": output_dir
        })
        
        if result.status == "success":
            print("\n" + "="*60)
            print("[SUCCESS] Phase 4/5 Test Completed!")
            print("="*60)
            print(f"\nArtifacts: {result.artifacts}")
            return 0
        else:
            print("\n" + "="*60)
            print("[FAILED] Phase 4/5 Test Failed")
            print("="*60)
            print(f"\nErrors: {result.errors}")
            return 1
            
    except Exception as e:
        print("\n" + "="*60)
        print("[ERROR] Phase 4/5 Test Exception")
        print("="*60)
        print(f"\nException: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(run_test())
    sys.exit(exit_code)
