"""
Supabase integration - real login (email one-time-code, not a password)
and cloud-saved projects, replacing the "just type any email" box and
the local-file-only Save/Load Project feature with actual per-user cloud
storage.

IMPORTANT - HONESTY NOTE: this was written without the ability to test it
against a real Supabase project (no network access in the sandbox this
was built in). The supabase-py calls below are written correctly against
the documented v2.x SDK, but this has NOT been verified end-to-end by
actually running it. Run test_supabase_connection.py FIRST, on its own,
before trusting the full login/save/load flow inside the app - that
script checks each step (library import, client creation, table access,
actual login) individually, so if something's wrong, you find out there
rather than somewhere buried in the app.
"""
import streamlit as st
from supabase import create_client, Client


def get_client() -> Client:
    """Creates a fresh Supabase client using this app's URL/key from
    Streamlit secrets. Deliberately NOT cached/shared across users
    (st.cache_resource would leak one user's login session to every
    other visitor - a serious bug for a multi-user app) - creating the
    client object itself is local setup, not a network call, so there's
    no real cost to doing this fresh on every rerun."""
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_ANON_KEY"]
    client = create_client(url, key)
    if st.session_state.get("supabase_access_token") and st.session_state.get("supabase_refresh_token"):
        try:
            client.auth.set_session(
                st.session_state["supabase_access_token"],
                st.session_state["supabase_refresh_token"],
            )
        except Exception:
            # Token likely expired or invalid - clear it so the login
            # screen shows again instead of silently failing later.
            for key_name in ["supabase_access_token", "supabase_refresh_token", "supabase_user"]:
                st.session_state.pop(key_name, None)
    return client


def send_login_code(email: str):
    """Triggers Supabase to email a 6-digit one-time code to this
    address. Using OTP-by-code (not a magic-link URL) deliberately -
    Streamlit apps don't have normal page routing/redirects, so a code
    the user types back in is a much better fit than a clickable link."""
    client = get_client()
    client.auth.sign_in_with_otp({"email": email})


def verify_login_code(email: str, code: str):
    """Verifies the code and stores the resulting session in this
    browser's st.session_state (NOT shared with other users)."""
    client = get_client()
    result = client.auth.verify_otp({"email": email, "token": code, "type": "email"})
    session = result.session
    st.session_state["supabase_access_token"] = session.access_token
    st.session_state["supabase_refresh_token"] = session.refresh_token
    st.session_state["supabase_user"] = {"id": result.user.id, "email": result.user.email}
    return result.user


def is_logged_in() -> bool:
    return "supabase_user" in st.session_state


def current_user_email() -> str:
    return st.session_state.get("supabase_user", {}).get("email", "")


def log_out():
    client = get_client()
    try:
        client.auth.sign_out()
    except Exception:
        pass  # already logged out / expired session - fine either way
    for key_name in ["supabase_access_token", "supabase_refresh_token", "supabase_user"]:
        st.session_state.pop(key_name, None)


def save_project_to_cloud(project_name: str, data: dict):
    """Upserts (insert-or-update) a project under the current user's
    account, keyed by project_name - saving again under the same name
    overwrites that project rather than creating a duplicate, per the
    unique(user_id, project_name) constraint in supabase_schema.sql."""
    client = get_client()
    user_id = st.session_state["supabase_user"]["id"]
    payload = {"user_id": user_id, "project_name": project_name, "data": data}
    client.table("projects").upsert(payload, on_conflict="user_id,project_name").execute()


def list_cloud_projects() -> list:
    """Returns [{"id", "project_name", "updated_at"}, ...] for the
    current user's own saved projects only - Row Level Security on the
    database enforces this even if the query itself didn't filter,
    but filtering explicitly here too is cheap and avoids depending
    solely on RLS for something this visible."""
    client = get_client()
    user_id = st.session_state["supabase_user"]["id"]
    response = (
        client.table("projects")
        .select("id, project_name, updated_at")
        .eq("user_id", user_id)
        .order("updated_at", desc=True)
        .execute()
    )
    return response.data


def load_project_from_cloud(project_id: str) -> dict:
    client = get_client()
    response = client.table("projects").select("data").eq("id", project_id).single().execute()
    return response.data["data"]


def delete_project_from_cloud(project_id: str):
    client = get_client()
    client.table("projects").delete().eq("id", project_id).execute()
