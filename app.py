import streamlit as st
import os
import time
from dotenv import load_dotenv

# --- CONFIGURATION MUST BE FIRST ---
st.set_page_config(
    page_title="Phantom Trax",
    page_icon="👻",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- LOAD ENVIRONMENT VARIABLES ---
load_dotenv()

# --- 🔍 DEBUG SECTION (TEMPORARY) ---
# This prints to the Logs (Streamlit "Manage App" or Render "Logs")
token = os.getenv("REPLICATE_API_TOKEN")
print("--- DEBUGGING API TOKEN ---")
if token:
    print(f"DEBUG: Token found!")
    print(f"DEBUG: Length: {len(token)}")
    print(f"DEBUG: First 4 chars: '{token[:4]}'") # Shows if there are quotes at start
    print(f"DEBUG: Last 4 chars: '{token[-4:]}'") # Shows if there are spaces at end
else:
    print("DEBUG: ❌ NO TOKEN FOUND. The app cannot see the key.")
print("---------------------------")
# ------------------------------------

# Import custom modules
try:
    from remix_engine import start_remix_job, optimize_prompt_text
except ImportError:
    st.error("CRITICAL ERROR: 'remix_engine.py' is missing. Please make sure it is in the same folder.")
    st.stop()

# --- CUSTOM CSS (STYLING) ---
st.markdown("""
<style>
    /* Global Styles */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #bd1e59 !important; /* Phantom Pink */
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 700;
    }

    /* Buttons */
    .stButton>button {
        color: white;
        background-color: #bd1e59;
        border-radius: 8px;
        border: none;
        padding: 10px 24px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #d63372;
        box-shadow: 0 4px 12px rgba(189, 30, 89, 0.4);
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #161B22;
        border-right: 1px solid #30363D;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("👻 Phantom Trax")
    st.caption("AI Audio Remix Engine")
    st.divider()
    
    st.markdown("### 🎛️ Settings")
    model_duration = st.slider("Duration (seconds)", 5, 30, 30)
    creativity = st.slider("Creativity (Temperature)", 0.0, 1.5, 0.8)
    
    use_optimizer = st.toggle("✨ AI Prompt Optimizer", value=True, help="Uses Llama 3 to rewrite your prompt for better quality.")
    
    st.divider()
    st.info("💡 **Tip:** Use headphones for best quality.")
    st.markdown("---")
    st.markdown("Build v2.0 | Powered by Meta MusicGen")

# --- MAIN APP UI ---
st.title("🎚️ Remix Your Reality")
st.markdown("Turn any audio sample into a **Trap, Lo-Fi, or Techno banger** using AI.")

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("1. Upload Source")
    uploaded_file = st.file_uploader("Drop a loop, voice memo, or song snippet", type=["mp3", "wav", "m4a"])
    
    if uploaded_file:
        st.audio(uploaded_file, format='audio/wav')
        # Save temp file
        with open("temp_input.wav", "wb") as f:
            f.write(uploaded_file.getbuffer())

with col2:
    st.subheader("2. Describe the Vibe")
    prompt_text = st.text_area("What should it sound like?", placeholder="e.g., Dark trap beat, 140bpm, heavy 808s, cinematic atmosphere...")
    
    generate_btn = st.button("🚀 Generate Remix", type="primary", use_container_width=True)

# --- GENERATION LOGIC ---
if generate_btn:
    if not uploaded_file:
        st.warning("⚠️ Please upload an audio file first.")
    elif not prompt_text:
        st.warning("⚠️ Please describe the style you want.")
    else:
        status_box = st.status("🎧 Processing Audio...", expanded=True)
        
        try:
            # Step 1: Optimize Prompt (If enabled)
            final_prompt = prompt_text
            if use_optimizer:
                status_box.write("🧠 AI Brain: Optimizing your prompt...")
                final_prompt = optimize_prompt_text(prompt_text)
                st.info(f"✨ **Optimized Prompt:** {final_prompt}")
            
            # Step 2: Send to MusicGen
            status_box.write("📡 Uploading to GPU Cloud...")
            prediction = start_remix_job(
                "temp_input.wav",
                final_prompt,
                model_duration,
                creativity
            )
            
            status_box.write("🎵 Generating Audio (this takes ~30s)...")
            
            # Step 3: Poll for results
            prediction.reload()
            while prediction.status not in ["succeeded", "failed", "canceled"]:
                time.sleep(2)
                prediction.reload()

            if prediction.status == "succeeded":
                status_box.update(label="✅ Remix Complete!", state="complete", expanded=False)
                output_url = prediction.output
                
                st.success("Your remix is ready!")
                st.audio(output_url)
                
                # Download Button
                st.link_button("⬇️ Download Remix", output_url)
                
            else:
                status_box.update(label="❌ Generation Failed", state="error")
                st.error(f"Error from AI: {prediction.error}")
                print(f"DEBUG ERROR DETAILS: {prediction.error}")

        except Exception as e:
            status_box.update(label="❌ System Error", state="error")
            st.error(f"An error occurred: {e}")
            print(f"CRITICAL EXCEPTION: {e}")

# --- AFFILIATE / ADS SECTION ---
st.divider()
col_ads, col_info = st.columns([2, 1])

with col_ads:
    st.markdown("### 🚀 Take Your Music Further")
    st.markdown("Ready to release your tracks to Spotify & Apple Music?")
    # Replace the link below with your actual Affiliate Link
    st.markdown("""
        <a href="https://distrokid.com/vip/seven/phantomtrax" target="_blank">
            <button style='background:#FFD700; color:black; border:none; padding:12px 20px; border-radius:5px; font-weight:bold; cursor:pointer;'>
                Get 7% Off DistroKid
            </button>
        </a>
    """, unsafe_allow_html=True)