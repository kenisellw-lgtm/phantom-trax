import replicate
import os
from dotenv import load_dotenv

load_dotenv()

# Audio Model
MUSIC_MODEL = "meta/musicgen:671ac645ce5e552cc63a54a2bbff63fcf798043055d2dac5fc9e36a837eedcfb"
# Text Model (Llama 3 8B - Fast & Smart)
TEXT_MODEL = "meta/meta-llama-3-8b-instruct"

def start_remix_job(audio_file_path, prompt, duration, temperature=1.0, seed=None):
    """Starts the audio generation job."""
    print(f"🚀 Starting remix job for {audio_file_path}...")
    
    input_data = {
        "input_audio": open(audio_file_path, "rb"), 
        "prompt": prompt,
        "duration": int(duration),
        "model_version": "stereo-melody-large",
        "normalization_strategy": "loudness",
        "temperature": float(temperature)
    }

    if seed is not None and str(seed).strip() != "":
        input_data["seed"] = int(seed)

    prediction = replicate.predictions.create(
        version=MUSIC_MODEL.split(":")[1],
        input=input_data
    )
    return prediction

def optimize_prompt_text(user_prompt):
    """Uses Llama 3 to rewrite the prompt for better audio results."""
    print(f"🧠 Optimizing prompt: {user_prompt}")
    
    system_instruction = (
        "You are an expert music producer. Rewrite the user's prompt to be descriptive, "
        "using specific musical terms (BPM, instruments, mood, genre) that work well for AI music generators. "
        "Keep it concise (under 30 words). Output ONLY the new prompt, nothing else."
    )
    
    output = replicate.run(
        TEXT_MODEL,
        input={
            "prompt": f"{system_instruction}\n\nUser Input: {user_prompt}\n\nOptimized Prompt:",
            "max_tokens": 100,
            "temperature": 0.7
        }
    )
    
    # Replicate returns a list of strings for text models, we join them.
    return "".join(output).strip()