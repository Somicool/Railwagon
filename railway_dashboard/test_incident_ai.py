"""
Test Script for AI Incident Response Agent
===========================================
Run this to verify the AI agent is working correctly
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

def test_incident_ai():
    """Test the incident AI agent"""
    print("=" * 60)
    print("  AI INCIDENT RESPONSE AGENT - TEST SCRIPT")
    print("=" * 60)
    print()
    
    # Test 1: Import modules
    print("[TEST 1] Importing modules...")
    try:
        from incident_manager import (
            IncidentAIAgent, 
            Incident, 
            create_incident_from_damage_detection
        )
        print("  ✓ Modules imported successfully")
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False
    
    # Test 2: Initialize AI agent
    print("\n[TEST 2] Initializing AI agent...")
    try:
        agent = IncidentAIAgent(db_path="incidents_db_test")
        print(f"  ✓ AI agent initialized")
        print(f"  ✓ Loaded {len(agent.incidents)} historical incidents")
    except Exception as e:
        print(f"  ✗ Initialization failed: {e}")
        return False
    
    # Test 3: Create a test incident
    print("\n[TEST 3] Creating test incident...")
    try:
        from datetime import datetime
        
        test_damage = {
            'damage_type': 'structural',
            'confidence': 0.89,
            'damage_count': 7,
            'has_damage': True
        }
        
        incident = create_incident_from_damage_detection(
            damage_result=test_damage,
            session_id='test_session_123',
            frame_number=42,
            wagon_number='TEST-999'
        )
        
        incident_id = agent.add_incident(incident)
        print(f"  ✓ Created incident: {incident_id}")
        print(f"  ✓ Title: {incident.title}")
        print(f"  ✓ Severity: {incident.severity}")
    except Exception as e:
        print(f"  ✗ Incident creation failed: {e}")
        return False
    
    # Test 4: Find similar incidents
    print("\n[TEST 4] Finding similar incidents...")
    try:
        similar = agent.find_similar_incidents(incident, top_k=3)
        print(f"  ✓ Found {len(similar)} similar incidents")
        
        if similar:
            for i, item in enumerate(similar[:3], 1):
                sim_inc = item['incident']
                score = item['similarity_score']
                print(f"    {i}. {sim_inc['title']} (similarity: {score:.2f})")
    except Exception as e:
        print(f"  ✗ Similarity search failed: {e}")
        return False
    
    # Test 5: Get AI recommendations
    print("\n[TEST 5] Getting AI recommendations...")
    try:
        recommendations = agent.recommend_actions(incident)
        print(f"  ✓ Generated {len(recommendations)} recommendations")
        
        print("\n  📋 Recommended Actions:")
        for i, action in enumerate(recommendations[:5], 1):
            print(f"    {i}. {action}")
    except Exception as e:
        print(f"  ✗ Recommendations failed: {e}")
        return False
    
    # Test 6: Update incident
    print("\n[TEST 6] Updating incident status...")
    try:
        from datetime import datetime, timedelta
        
        agent.update_incident(incident_id, {
            'status': 'resolved',
            'resolved_at': datetime.now().isoformat(),
            'resolution_steps': recommendations[:3],
            'assigned_to': 'Test Operator'
        })
        
        updated = agent.get_incident_by_id(incident_id)
        print(f"  ✓ Incident updated to: {updated.status}")
        print(f"  ✓ Response time: {updated.response_time_minutes:.1f} minutes")
    except Exception as e:
        print(f"  ✗ Update failed: {e}")
        return False
    
    # Test 7: Get statistics
    print("\n[TEST 7] Calculating response time statistics...")
    try:
        stats = agent.get_response_time_stats()
        print(f"  ✓ Statistics calculated for {len(stats)} incident types")
        
        for inc_type, data in stats.items():
            print(f"\n  {inc_type.replace('_', ' ').title()}:")
            print(f"    • Average: {data['avg_response_time']:.1f} minutes")
            print(f"    • Count: {data['count']} incidents")
    except Exception as e:
        print(f"  ✗ Statistics failed: {e}")
        return False
    
    # Clean up test database
    print("\n[CLEANUP] Removing test database...")
    import shutil
    try:
        test_db = Path("incidents_db_test")
        if test_db.exists():
            shutil.rmtree(test_db)
            print("  ✓ Test database removed")
    except Exception as e:
        print(f"  ⚠ Cleanup warning: {e}")
    
    print("\n" + "=" * 60)
    print("  ALL TESTS PASSED! ✓")
    print("=" * 60)
    print("\nYour AI Incident Response Agent is ready! 🚀")
    print("\nNext steps:")
    print("  1. Review INCIDENT_AI_README.md for integration guide")
    print("  2. Add API endpoints to backend/app.py")
    print("  3. Create dashboard UI for incident monitoring")
    print()
    
    return True

if __name__ == '__main__':
    try:
        success = test_incident_ai()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
