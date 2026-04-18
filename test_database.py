#!/usr/bin/env python3
"""
Test database connection for anonymous tracking
"""

import psycopg2
import os

def test_database_connection():
    """Test PostgreSQL database connection"""
    # Local connection string
    conn_string = "postgresql://reginaldrice@localhost:5432/leafengines_tracking"
    
    print("🔍 Testing PostgreSQL database connection...")
    print(f"Connection string: {conn_string}")
    
    try:
        # Test connection
        conn = psycopg2.connect(conn_string)
        print("✅ Database connection successful!")
        
        # Test tables exist
        with conn.cursor() as cur:
            # Check tables
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            tables = cur.fetchall()
            print(f"\n📊 Tables found ({len(tables)}):")
            for table in tables:
                print(f"  - {table[0]}")
            
            # Check row counts (should be 0 for new database)
            print("\n📈 Initial row counts:")
            for table in ['anonymous_sessions', 'api_usage_log', 'platform_correlation']:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                print(f"  - {table}: {count} rows")
            
            # Test functions
            print("\n⚙️ Testing database functions...")
            
            # Test create_anonymous_session function
            cur.execute("""
                SELECT create_anonymous_session(
                    'qgis',
                    'US',
                    'test_user_agent_hash',
                    'test_ip_hash'
                )
            """)
            session_id = cur.fetchone()[0]
            print(f"✅ Created test session: {session_id[:16]}...")
            
            # Verify session was created
            cur.execute("SELECT COUNT(*) FROM anonymous_sessions WHERE session_id = %s", (session_id,))
            session_count = cur.fetchone()[0]
            print(f"✅ Session verified in database: {session_count} session(s)")
            
            # Test update_session_activity function
            cur.execute("SELECT update_session_activity(%s)", (session_id,))
            print("✅ Session activity update function works")
            
            # Verify update worked
            cur.execute("SELECT total_calls FROM anonymous_sessions WHERE session_id = %s", (session_id,))
            total_calls = cur.fetchone()[0]
            print(f"✅ Session now has {total_calls} total calls")
            
            # Test views
            print("\n📊 Testing database views...")
            views = ['daily_usage_summary', 'platform_adoption', 'geographic_usage']
            for view in views:
                cur.execute(f"SELECT COUNT(*) FROM {view}")
                view_count = cur.fetchone()[0]
                print(f"  - {view}: {view_count} rows")
            
            # Clean up test data
            cur.execute("DELETE FROM anonymous_sessions WHERE session_id = %s", (session_id,))
            conn.commit()
            print(f"\n🧹 Cleaned up test session")
            
        conn.close()
        print("\n🎉 All database tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_anonymous_tracker_module():
    """Test the AnonymousTracker Python module"""
    print("\n🔍 Testing AnonymousTracker module...")
    
    try:
        # Import the module
        from anonymous_tracker import AnonymousTracker
        
        # Initialize tracker
        tracker = AnonymousTracker("postgresql://reginaldrice@localhost:5432/leafengines_tracking")
        
        if tracker.enabled:
            print("✅ AnonymousTracker initialized successfully")
            
            # Test platform detection
            test_agents = [
                ("QGIS/3.28.0", "qgis"),
                ("python-requests/2.28.0", "python"),
                ("node-fetch/1.0", "node"),
                ("curl/7.88.0", "curl"),
                ("Mozilla/5.0", "browser"),
                ("OpenClaw/1.0", "clawhub"),
                ("Unknown/1.0", "unknown")
            ]
            
            print("\n🔧 Testing platform detection:")
            for agent, expected in test_agents:
                detected = tracker.detect_platform(agent)
                status = "✅" if detected == expected else "❌"
                print(f"  {status} {agent[:30]:30} → {detected:10} (expected: {expected})")
            
            # Test hashing function
            print("\n🔒 Testing privacy hashing:")
            test_string = "test@example.com"
            hashed = tracker._hash_string(test_string)
            print(f"  Original: {test_string}")
            print(f"  Hashed:   {hashed[:32]}...")
            print(f"  Length:   {len(hashed)} characters")
            
            # Test session ID generation (simulated)
            print("\n🆔 Testing session ID generation:")
            class MockRequest:
                def __init__(self):
                    self.user_agent = type('obj', (object,), {'string': 'QGIS/3.28.0'})
                    self.remote_addr = "192.168.1.100"
                    self.headers = {
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept': 'application/json'
                    }
            
            mock_request = MockRequest()
            session_id = tracker.create_session_id(mock_request)
            print(f"  Generated session ID: {session_id[:32]}...")
            print(f"  Session ID length: {len(session_id)} characters")
            
            print("\n🎉 AnonymousTracker module tests passed!")
            return True
        else:
            print("❌ AnonymousTracker not enabled")
            return False
            
    except Exception as e:
        print(f"❌ AnonymousTracker test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Anonymous Tracking Database Test Suite")
    print("=" * 60)
    
    # Run tests
    db_test = test_database_connection()
    module_test = test_anonymous_tracker_module()
    
    print("\n" + "=" * 60)
    print("Test Summary:")
    print(f"  Database Connection: {'✅ PASS' if db_test else '❌ FAIL'}")
    print(f"  Python Module:       {'✅ PASS' if module_test else '❌ FAIL'}")
    
    if db_test and module_test:
        print("\n🎉 ALL TESTS PASSED! Database is ready for anonymous tracking.")
        print("\nNext steps:")
        print("1. Update Render environment with DATABASE_URL")
        print("2. Deploy updated API code")
        print("3. Test with actual API requests")
    else:
        print("\n⚠️ Some tests failed. Check the errors above.")
    print("=" * 60)