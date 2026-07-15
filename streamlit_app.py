import streamlit as st
import pandas as pd
from supabase import create_client, Client

# ==========================================================
# 1. DATABASE & CREDENTIALS CONNECTION
# ==========================================================
# Ensure your Streamlit secrets are saved as SUPABASE_URL and SUPABASE_ANON_KEY
@st.cache_resource
def get_supabase_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_ANON_KEY"]
    return create_client(url, key)

try:
    supabase = get_supabase_client()
except Exception as e:
    st.error("Could not connect to Supabase. Check your Streamlit Secrets.")

# ==========================================================
# 2. RESOLVE RERUN GLITCH (INITIALIZE SESSION STATE)
# ==========================================================
if "active_project" not in st.session_state:
    st.session_state.active_project = "Project Alpha"

if "engineer_name" not in st.session_state:
    st.session_state.engineer_name = ""

# ==========================================================
# 3. SIDEBAR - CONTROL PANEL
# ==========================================================
st.sidebar.title("🛠️ MEP-Design Platform")

# Instead of complex magic links, users simply type who they are
st.sidebar.text_input("Your Name / Email:", key="engineer_name", placeholder="e.g. John Thomas")
st.sidebar.text_input("Active Project Title:", key="active_project")

if not st.session_state.engineer_name:
    st.info("👈 Please enter your Name or Email in the sidebar to begin using the platform.")
    st.stop()

# ==========================================================
# 4. TABBED INTERFACE LAYOUT
# ==========================================================
tab1, tab2 = st.tabs(["📊 Calculations Panel", "📂 Drawing Hub & Uploads"])

# --- TAB 1: YOUR CALCULATIONS PANEL ---
with tab1:
    st.header(f"Calculations: {st.session_state.active_project}")
    st.write("Your existing MEP layout formulas and calculations go here...")
    
    # Placeholders for your existing calculations
    flow_rate = st.number_input("Design Flow Rate (L/s)", value=1.5, key="flow_rate")
    pipe_material = st.selectbox("Pipe Material Selection", ["Copper", "Steel", "PVC"], key="pipe_material")
    
    st.info("Your calculation tools run normally inside this tab.")

# --- TAB 2: THE DRAWING HUB (THE NEW EDITION) ---
with tab2:
    st.header(f"Drawing Hub - {st.session_state.active_project}")
    st.subheader("Upload PDF Layouts or Sketches")

    # Drag & drop file upload widget
    uploaded_file = st.file_uploader("Drag and drop your engineering PDF drawings here", type=["pdf", "png", "jpg"])

    if uploaded_file is not None:
        file_name = uploaded_file.name
        
        # Build a safe unique path inside the Supabase bucket
        # Example: "Project Alpha/John Thomas_Layout_RevA.pdf"
        storage_path = f"{st.session_state.active_project}/{st.session_state.engineer_name}_{file_name}"

        # Upload action button
        if st.button("📤 Upload Drawing to Project Hub"):
            try:
                # 1. Read file bytes
                file_bytes = uploaded_file.getvalue()

                # 2. Push to Supabase Storage Bucket
                supabase.storage.from_("mep-drawings").upload(
                    path=storage_path,
                    file=file_bytes,
                    file_options={"content-type": uploaded_file.type}
                )

                # 3. Generate the public URL link
                file_url = supabase.storage.from_("mep-drawings").get_public_url(storage_path)

                # 4. Write record/metadata to database table
                payload = {
                    "project_name": st.session_state.active_project,
                    "uploaded_by": st.session_state.engineer_name,
                    "file_name": file_name,
                    "file_url": file_url
                }
                supabase.table("drawings_registry").insert(payload).execute()

                st.success(f"🎉 Successfully uploaded and linked: {file_name}!")
                st.rerun()

            except Exception as e:
                st.error(f"Upload failed: {e}. Ensure you ran the SQL tables script in Supabase.")

    # ==========================================================
    # 5. DISPLAY PROJECT DRAWINGS REGISTER
    # ==========================================================
    st.write("---")
    st.subheader("📁 Active Project Drawing Register")

    try:
        # Fetch drawings uploaded for this specific active project
        response = supabase.table("drawings_registry").select("*").eq("project_name", st.session_state.active_project).execute()
        drawings = response.data

        if drawings:
            # Convert query results to a neat pandas table
            df = pd.DataFrame(drawings)
            
            # Format columns for display
            df_display = df[["file_name", "uploaded_by", "created_at", "file_url"]].copy()
            df_display.columns = ["Drawing / File Name", "Uploaded By", "Date Added", "Download/View Link"]
            
            # Display drawing links as clickable markdown
            for index, row in df_display.iterrows():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"📄 **{row['Drawing / File Name']}**")
                with col2:
                    st.write(f"👤 {row['Uploaded By']}")
                with col3:
                    st.markdown(f"[🔗 Open File]({row['Download/View Link']})")
        else:
            st.info("No drawings uploaded to this project yet. Use the uploader above to add files.")

    except Exception as e:
        st.write("Ready to list files once the 'drawings_registry' database table is live.")