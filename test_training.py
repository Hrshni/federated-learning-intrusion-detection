#!/usr/bin/env python
"""Test the training function directly to get full traceback"""

import sys
import traceback

# Import the training function and dependencies
try:
    from app import run_federated_training
    print("✓ Successfully imported run_federated_training")
    
    # Try to run the training
    print("\n" + "="*60)
    print("Starting training test...")
    print("="*60 + "\n")
    
    run_federated_training()
    
    print("\n" + "="*60)
    print("✓ Training completed successfully!")
    print("="*60)
    
except Exception as e:
    print("\n" + "="*60)
    print("✗ Error occurred during training:")
    print("="*60)
    print(f"\nError Type: {type(e).__name__}")
    print(f"Error Message: {str(e)}\n")
    print("Full Traceback:")
    print("-"*60)
    traceback.print_exc()
    print("-"*60)
    sys.exit(1)
