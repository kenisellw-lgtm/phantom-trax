import streamlit as st
import os
import time
import librosa
import requests
import matplotlib.pyplot as plt
import numpy as np
from remix_engine import start_remix_job, optimize_prompt_text

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Phantom Trax", 
    page_icon="👻", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CUSTOM CSS (THE PROFESSIONAL LOOK) ---
st.markdown("""
<style>
    /* Main Background adjustments */
    .stApp {
        background-color: #0E1117;
    }
    
    /* Metrics Styling */
    [data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
        color: #8A2BE2; /* Ghost Purple */
    }
    
    /* Custom Button Styling */
    div.stButton > button:first-child {
        background: linear-gradient(90deg, #8A2BE2 0%, #4B0082 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: bold;
        transition: 0.3s;
    }
    div.stButton > button:first-child:hover {
        background: linear-gradient(90deg, #9B30FF 0%, #7B00FF 100%);
        box-shadow: 0px 4px 15px rgba(138, 43, 226, 0.4);
    }
    
    /* Ad Container Styling */
    .ad-box {
        background-color: #1e1e1e;
        border: 1px solid #333;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        margin-bottom: 20px;
        color: #888;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'history' not in st.session_state:
    st.session_state.history = []
if 'optimized_prompt' not in st.session_state:
    st.session_state.optimized_prompt = ""
if 'run_remix' not in st.session_state:
    st.session_state.run_remix = False 

# --- HELPERS ---
def estimate_key(y, sr):
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    chroma_sum = np.sum(chroma, axis=1)
    major_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
    minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
    keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    max_corr = -1
    best_key = "Unknown"
    chroma_sum /= np.max(chroma_sum)
    for i in range(12):
        if np.corrcoef(chroma_sum, np.roll(major_profile, i))[0, 1] > max_corr:
            max_corr = np.corrcoef(chroma_sum, np.roll(major_profile, i))[0, 1]
            best_key = f"{keys[i]} Major"
    for i in range(12):
        if np.corrcoef(chroma_sum, np.roll(minor_profile, i))[0, 1] > max_corr:
            max_corr = np.corrcoef(chroma_sum, np.roll(minor_profile, i))[0, 1]
            best_key = f"{keys[i]} Minor"
    return best_key

# --- POP-UP ---
@st.dialog("✨ AI Prompt Optimizer")
def open_optimizer_modal(original_text):
    st.markdown("The AI suggests this improved prompt:")
    if not st.session_state.optimized_prompt:
        with st.spinner("Analyzing style..."):
            st.session_state.optimized_prompt = optimize_prompt_text(original_text)
    
    new_prompt = st.text_area("Optimized Prompt", value=st.session_state.optimized_prompt, height=120)
    st.session_state.optimized_prompt = new_prompt 
    
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        if st.button("✅ Accept", type="primary", use_container_width=True):
            st.session_state.run_remix = True
            st.rerun()
    with c2:
        if st.button("🎲 Retry", use_container_width=True):
            st.session_state.optimized_prompt = "" 
            st.rerun()
    with c3:
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state.run_remix = False
            st.session_state.optimized_prompt = ""
            st.rerun()

# --- SIDEBAR ---
with st.sidebar:
    st.title("👻 Phantom Trax")
    with st.expander("📊 Analysis Settings", expanded=True):
        enable_bpm = st.toggle("Detect BPM", value=True)
        enable_key = st.toggle("Detect Key", value=True)
    
    with st.expander("🎛️ AI Settings", expanded=True):
        use_optimizer = st.toggle("AI Prompt Optimizer", value=True)
        temperature = st.slider("Creativity", 0.1, 2.0, 1.0)
        seed = st.text_input("Seed Number (Optional)")

# --- MAIN LAYOUT (SPLIT 75% Content / 25% Ads) ---
col_main, col_ads = st.columns([3, 1])

# --- RIGHT COLUMN: PARTNERS/ADS ---
with col_ads:
    st.markdown("### 📢 Partners")
    
    # AD SLOT 1: DISTROKID (Placeholder)
    st.markdown("""
    <div class="ad-box">
        <h4>☁️ DistroKid</h4>
        <p>Upload your remixes to Spotify & Apple Music.</p>
        <button style='background:#444; border:none; padding:5px; color:white; border-radius:4px;'>Get 7% Off</button>
    </div>
    """, unsafe_allow_html=True)
    
    # AD SLOT 2: SPLICE (Placeholder)
    st.markdown("""
    <div class="ad-box">
        <h4>🎹 Splice Sounds</h4>
        <p>Millions of royalty-free samples & loops.</p>
        <button style='background:#444; border:none; padding:5px; color:white; border-radius:4px;'>Try Free</button>
    </div>
    """, unsafe_allow_html=True)
    
    st.info("💡 Want to advertise here? Contact us!")

# --- LEFT COLUMN: MAIN APP ---
with col_main:
    st.title("👻 Phantom Trax")
    st.caption("Professional AI Audio Remix Engine")

    # File Upload Area
    uploaded_file = st.file_uploader("Drop your MP3 here", type=["mp3", "wav"])

    if uploaded_file is not None:
        temp_filename = "temp_input.mp3"
        with open(temp_filename, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Dashboard Grid for Stats
        st.markdown("### 📊 Track Analysis")
        with st.container(border=True):
            col_stats, col_player = st.columns([2, 1])
            
            with col_stats:
                with st.spinner("Processing audio..."):
                    try:
                        y, sr = librosa.load(temp_filename, duration=60)
                        clean_duration = int(librosa.get_duration(y=y, sr=sr))
                        mins, secs = clean_duration // 60, clean_duration % 60
                        
                        bpm_text, key_text = "", ""
                        bpm_val = int(librosa.beat.beat_track(y=y, sr=sr)[0]) if enable_bpm else "---"
                        if enable_bpm: bpm_text = f"at {bpm_val} BPM"

                        detected_key = estimate_key(y, sr) if enable_key else "---"
                        if enable_key: key_text = f"in {detected_key}"
                        
                        m1, m2, m3 = st.columns(3)
                        m1.metric("Duration", f"{mins}:{secs:02d}")
                        m2.metric("BPM", f"{bpm_val}")
                        m3.metric("Key", detected_key)
                        
                    except Exception as e:
                        st.error(f"Analysis failed: {e}")
                        clean_duration = 30
            
            with col_player:
                st.write("**Preview Input:**")
                st.audio(uploaded_file, format='audio/mp3')

        # Prompt Input
        st.write("---")
        default_text = f"Remix {bpm_text} {key_text}, trap style, heavy 808"
        default_text = " ".join(default_text.split())
        style_prompt = st.text_input("Describe the new style", default_text)

        # Generate Button (Full Width)
        generate_clicked = st.button("✨ Generate Remix", type="primary", use_container_width=True)

        # Logic
        if generate_clicked:
            if use_optimizer:
                st.session_state.optimized_prompt = "" 
                open_optimizer_modal(style_prompt)
            else:
                st.session_state.run_remix = True
                st.session_state.optimized_prompt = style_prompt 

        if st.session_state.run_remix:
            final_prompt = st.session_state.optimized_prompt if st.session_state.optimized_prompt else style_prompt
            st.session_state.run_remix = False 
            
            try:
                st.toast(f"Starting Remix...", icon="🔥")
                prediction = start_remix_job(temp_filename, final_prompt, clean_duration, temperature, seed)
                
                est_time = int((clean_duration * 1.3) + 20)
                status_text = st.empty()
                progress_bar = st.progress(0)
                start_time = time.time()
                
                while prediction.status not in ["succeeded", "failed", "canceled"]:
                    elapsed = int(time.time() - start_time)
                    remaining = max(0, est_time - elapsed)
                    r_m, r_s = remaining // 60, remaining % 60
                    
                    status_text.markdown(f"### ⏳ Time Remaining: **{r_m}:{r_s:02d}**")
                    progress_bar.progress(min(int((elapsed / est_time) * 100), 95))
                    time.sleep(1)
                    prediction.reload()

                if prediction.status == "succeeded":
                    status_text.success("✅ Remix Complete!")
                    progress_bar.progress(100)
                    remix_url = str(prediction.output)
                    
                    st.session_state.history.insert(0, {
                        "prompt": final_prompt,
                        "url": remix_url,
                        "time": time.strftime("%H:%M"),
                        "seed": seed if seed else "Random"
                    })
                    st.rerun()
                else:
                    st.error(f"❌ Failed: {prediction.status}")

            except Exception as e:
                st.error(f"Error: {e}")

    # History List
    if st.session_state.history:
        st.write("### 📜 Session History")
        for item in st.session_state.history:
            with st.container(border=True):
                h_col1, h_col2 = st.columns([3, 1])
                with h_col1:
                    st.markdown(f"**{item['prompt']}**")
                    st.caption(f"🕒 {item['time']} | 🌱 Seed: {item['seed']}")
                    st.audio(item['url'])
                with h_col2:
                    st.markdown("<br>", unsafe_allow_html=True) # Spacer
                    st.markdown(f"[⬇️ Download WAV]({item['url']})")