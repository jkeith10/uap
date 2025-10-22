#!/usr/bin/env python3
"""Test script to verify all imports work correctly"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test all critical imports"""
    try:
        print("Testing UAP imports...")
        
        # Test main app
        from uap.main import app
        print("✅ Main app imported successfully")
        
        # Test core components
        from uap.core.kernel import WorldStateManager
        from uap.core.events import EventSystem
        from uap.core.versioning import SemanticVersion
        print("✅ Core components imported successfully")
        
        # Test models
        from uap.models.intent import IntentPacket
        from uap.models.action_graph import ActionGraph
        from uap.models.memory_stream import MemoryStream
        print("✅ Models imported successfully")
        
        # Test AML components
        from uap.aml.packets import UAPContextPacket
        from uap.aml.mediator import ProtocolMediator
        print("✅ AML components imported successfully")
        
        # Test storage
        from uap.storage.redis_client import RedisClient
        from uap.storage.postgres_client import PostgreSQLClient
        print("✅ Storage components imported successfully")
        
        # Test client
        from uap.client.async_client import AsyncUAPClient
        from uap.client.sync_client import UAPClient
        print("✅ Client components imported successfully")
        
        print("\n🎉 All imports successful!")
        return True
        
    except ImportError as e:
        print(f"\n❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
