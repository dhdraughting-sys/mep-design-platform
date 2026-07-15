"""
Run this BEFORE trying the full app's login feature, to check your
Supabase credentials and connection actually work in isolation. This was
written without the ability to test it against a real Supabase project
(no network access in the sandbox it was built in), so this script exists
specifically to let YOU verify it works, one step at a time, rather than
discovering a problem buried inside the full Streamlit app.

Usage:
    python test_supabase_connection.py

Edit SUPABASE_URL and SUPABASE_ANON_KEY below first (find both in your
Supabase project: Settings -> API).
"""

SUPABASE_URL = "https://YOUR-PROJECT-REF.supabase.co"
SUPABASE_ANON_KEY = "YOUR-ANON-KEY-HERE"

print("Step 1: Importing supabase-py...")
try:
    from supabase import create_client
    print("  OK - library installed correctly.")
except ImportError:
    print("  FAILED - run: pip install supabase")
    exit(1)

print("\nStep 2: Creating client (no network call yet, just local setup)...")
try:
    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    print("  OK - client created.")
except Exception as e:
    print(f"  FAILED - check SUPABASE_URL is correct: {e}")
    exit(1)

print("\nStep 3: Testing the 'projects' table exists and RLS is reachable...")
print("  (This is EXPECTED to return zero rows if you're not logged in - ")
print("   that's Row Level Security working correctly, not a failure.)")
try:
    response = client.table("projects").select("id").limit(1).execute()
    print(f"  OK - table reachable. Rows visible (anonymous): {len(response.data)}")
except Exception as e:
    print(f"  FAILED - did you run supabase_schema.sql in your Supabase SQL Editor yet? Error: {e}")
    exit(1)

print("\nStep 4: Testing email OTP login (sends a real email!)...")
test_email = input("  Enter an email address you can check right now (or press Enter to skip): ").strip()
if test_email:
    try:
        client.auth.sign_in_with_otp({"email": test_email})
        print(f"  OK - request sent. Check {test_email} for a 6-digit code.")
        code = input("  Enter the code you received: ").strip()
        result = client.auth.verify_otp({"email": test_email, "token": code, "type": "email"})
        print(f"  SUCCESS - logged in as {result.user.email} (user id: {result.user.id})")
    except Exception as e:
        print(f"  FAILED at login step: {e}")
        exit(1)
else:
    print("  Skipped.")

print("\nAll checks passed. Your Supabase setup is ready for the full app.")
