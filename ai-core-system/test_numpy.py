#!/usr/bin/env python3
"""
Test script to verify NumPy and PyTorch installation.
"""

import sys

def test_imports():
    """Test basic imports."""
    print("🔍 Testing imports...")
    
    try:
        import numpy as np
        print(f"✅ NumPy version: {np.__version__}")
    except ImportError as e:
        print(f"❌ NumPy import failed: {e}")
        return False
    
    try:
        import torch
        print(f"✅ PyTorch version: {torch.__version__}")
        print(f"   CUDA available: {torch.cuda.is_available()}")
        print(f"   Device: {torch.device('cuda' if torch.cuda.is_available() else 'cpu')}")
    except ImportError as e:
        print(f"❌ PyTorch import failed: {e}")
        return False
    
    try:
        import transformers
        print(f"✅ Transformers version: {transformers.__version__}")
    except ImportError as e:
        print(f"❌ Transformers import failed: {e}")
        return False
    
    return True

def test_numpy_operations():
    """Test basic NumPy operations."""
    print("\n🔍 Testing NumPy operations...")
    
    try:
        import numpy as np
        
        # Test basic array creation
        arr = np.array([1, 2, 3, 4, 5])
        print(f"✅ Array creation: {arr}")
        
        # Test basic operations
        result = np.sum(arr)
        print(f"✅ Array sum: {result}")
        
        # Test random operations
        random_arr = np.random.rand(3, 3)
        print(f"✅ Random array shape: {random_arr.shape}")
        
        return True
    except Exception as e:
        print(f"❌ NumPy operations failed: {e}")
        return False

def test_torch_operations():
    """Test basic PyTorch operations."""
    print("\n🔍 Testing PyTorch operations...")
    
    try:
        import torch
        
        # Test tensor creation
        tensor = torch.tensor([1, 2, 3, 4, 5])
        print(f"✅ Tensor creation: {tensor}")
        
        # Test basic operations
        result = torch.sum(tensor)
        print(f"✅ Tensor sum: {result}")
        
        # Test random operations
        random_tensor = torch.rand(3, 3)
        print(f"✅ Random tensor shape: {random_tensor.shape}")
        
        return True
    except Exception as e:
        print(f"❌ PyTorch operations failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Testing NumPy and PyTorch Installation")
    print("=" * 50)
    
    # Test imports
    if not test_imports():
        print("❌ Import tests failed")
        sys.exit(1)
    
    # Test NumPy operations
    if not test_numpy_operations():
        print("❌ NumPy operations failed")
        sys.exit(1)
    
    # Test PyTorch operations
    if not test_torch_operations():
        print("❌ PyTorch operations failed")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("✅ All tests passed! NumPy and PyTorch are working correctly.")

if __name__ == "__main__":
    main() 