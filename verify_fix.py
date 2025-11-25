import sys
import os
import asyncio

# Add project root to path
sys.path.append("/mnt/data1/work/sm-ai-v2/sm-ai-v2-backend")

async def verify_imports():
    print("Verifying imports...")
    try:
        from src.systems.calling_tools import get_rag_tools, get_internal_tools, get_external_tools
        print("✅ calling_tools imported successfully")
        
        from src.systems.agent.rag_agent import call_model as rag_call_model
        print("✅ rag_agent imported successfully")
        
        from src.systems.agent.internal_agent import call_model as internal_call_model
        print("✅ internal_agent imported successfully")
        
        from src.systems.agent.external_agent import call_model as external_call_model
        print("✅ external_agent imported successfully")
        
        from src.systems.build_graph import build_graph
        print("✅ build_graph imported successfully")
        
        print("All imports successful!")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_imports())
