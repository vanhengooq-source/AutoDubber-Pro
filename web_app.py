import streamlit as st
import asyncio
import edge_tts
from deep_translator import GoogleTranslator
from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip
import whisper
import os
import time
import tempfile

def format_time(seconds):
    hours = int(seconds / 3600)
    minutes = int((seconds % 3600) / 60)
    secs = int(seconds % 60)
    millisecs = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

async def generate_khmer_audio(text, output_filename):
    try:
        communicate = edge_tts.Communicate(text, "km-KH-SreymomNeural")
        await communicate.save(output_filename)
        return True
    except: return False

def apply_start(clip, start_time):
    if hasattr(clip, 'with_start'): return clip.with_start(start_time)
    return clip.set_start(start_time)

def apply_volume(clip, vol):
    try: return clip.with_volume_scaled(vol)
    except AttributeError:
        try: return clip.volumex(vol)
        except AttributeError:
            try:
                from moviepy.audio.fx.multiply_volume import multiply_volume
                return multiply_volume(clip, vol)
            except: return clip

def translate_to_khmer(text, log_placeholder):
    if not text.strip(): return ""
    time.sleep(2.5) 
    try:
        translator = GoogleTranslator(source='auto', target='km')
        result = translator.translate(text)
        error_words = ["Error", "error", "500", "1500", "Server", "server", "try again", "Exception"]
        if any(word in result for word in error_words):
            log_placeholder.warning("⚠️ ប្រព័ន្ធ Google ផ្អាកបកប្រែបណ្ដោះអាសន្ន (រំលង)...")
            return ""
        return result
    except: return ""

st.set_page_config(page_title="AutoDubber Pro Web", page_icon="🎬", layout="centered")

# --- ប្រព័ន្ធលេខសម្ងាត់ ---
SECRET_PASSWORD = "12345"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 ចូលប្រើប្រាស់ប្រព័ន្ធ")
    st.info("សូមបញ្ចូលលេខសម្ងាត់ ដើម្បីចូលប្រើប្រាស់កម្មវិធី AutoDubber Pro")
    password_input = st.text_input("លេខសម្ងាត់ (Password):", type="password")
    
    if st.button("ចូល (Login)", type="primary", use_container_width=True):
        if password_input == SECRET_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ លេខសម្ងាត់មិនត្រឹមត្រូវទេ!")
    st.stop() 

# --- ផ្ទាំងកម្មវិធី ---
st.title("🎬 AutoDubber Pro")
st.markdown("**ប្រព័ន្ធបកប្រែ និងបញ្ចូលសំឡេងខ្មែរស្វ័យប្រវត្តិ (គាំទ្រ Audio Ducking)**")

if st.button("🚪 ចាកចេញ (Logout)", type="secondary"):
    st.session_state.authenticated = False
    st.rerun()
    
st.divider()

uploaded_file = st.file_uploader("📂 ជ្រើសរើស ឬទម្លាក់ File វីដេអូនៅទីនេះ", type=['mp4', 'avi', 'mkv'])

if uploaded_file is not None:
    if st.button("▶️ ចាប់ផ្ដើមបកប្រែវីដេអូ", use_container_width=True, type="primary"):
        
        log_box = st.empty()
        progress_bar = st.progress(0)
        
        with st.spinner('⏳ កំពុងដំណើរការកាត់ត... សូមកុំបិទទំព័រនេះ!'):
            try:
                temp_dir = tempfile.mkdtemp()
                input_video_path = os.path.join(temp_dir, uploaded_file.name)
                with open(input_video_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                    
                TEMP_AUDIO = os.path.join(temp_dir, "temp_audio.wav")
                FINAL_VIDEO = os.path.join(temp_dir, "khmer_dubbed_video.mp4")
                
                log_box.info("១. កំពុងទាញសំឡេង និងស្កេនចាប់ពាក្យ...")
                video = VideoFileClip(input_video_path)
                video_duration = video.duration
                video.audio.write_audiofile(TEMP_AUDIO, logger=None)
                
                model = whisper.load_model("base")
                result = model.transcribe(TEMP_AUDIO)
                segments = result['segments']
                
                log_box.info(f"២. រកឃើញការសន្ទនា {len(segments)} ប្រយោគ! កំពុងរៀបចំ Audio Ducking...")
                audio_clips = []
                
                if video.audio:
                    if video_duration is None:
                        video_duration = segments[-1]['end'] if segments else 0
                    
                    last_end = 0.0
                    for seg in segments:
                        start = seg['start']
                        end = seg['end']
                        if start > last_end:
                            try:
                                bg_normal = video.audio.subclip(last_end, start)
                                bg_normal = apply_start(bg_normal, last_end)
                                audio_clips.append(bg_normal)
                            except: pass
                        try:
                            bg_ducked = video.audio.subclip(start, end)
                            bg_ducked = apply_volume(bg_ducked, 0.03)
                            bg_ducked = apply_start(bg_ducked, start)
                            audio_clips.append(bg_ducked)
                        except: pass
                        last_end = end
                        
                    if last_end < video_duration:
                        try:
                            bg_tail = video.audio.subclip(last_end, video_duration)
                            bg_tail = apply_start(bg_tail, last_end)
                            audio_clips.append(bg_tail)
                        except: pass

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                for i, seg in enumerate(segments):
                    start = seg['start']
                    end = seg['end']
                    text = seg['text']
                    
                    log_box.success(f"៣. កំពុងបកប្រែប្រយោគទី {i+1}/{len(segments)}...")
                    progress_bar.progress((i + 1) / len(segments))
                    
                    khmer_text = translate_to_khmer(text, log_box)
                    
                    if khmer_text:
                        temp_seg_audio = os.path.join(temp_dir, f"seg_{i}.mp3")
                        success = loop.run_until_complete(generate_khmer_audio(khmer_text, temp_seg_audio))
                        if success and os.path.exists(temp_seg_audio):
                            seg_clip = AudioFileClip(temp_seg_audio)
                            seg_clip = apply_volume(seg_clip, 1.5)
                            seg_clip = apply_start(seg_clip, start)
                            audio_clips.append(seg_clip)
                
                loop.close()
                
                log_box.info("៤. កំពុងបញ្ចូលសំឡេង និង Render វីដេអូចុងក្រោយ...")
                final_audio = CompositeAudioClip(audio_clips)
                
                if hasattr(video, 'with_audio'): final_video = video.with_audio(final_audio)
                else: final_video = video.set_audio(final_audio)
                    
                final_video.write_videofile(FINAL_VIDEO, codec="libx264", audio_codec="aac", logger=None)
                
                log_box.success("🎉 ជោគជ័យ! វីដេអូរបស់អ្នករួចរាល់ហើយ។ សូមចុចប៊ូតុងខាងក្រោមដើម្បីទាញយក!")
                
                with open(FINAL_VIDEO, "rb") as file:
                    btn = st.download_button(
                        label="⬇️ ទាញយកវីដេអូខ្មែរ (Download)",
                        data=file,
                        file_name=f"AutoDubber_{uploaded_file.name}",
                        mime="video/mp4",
                        use_container_width=True
                    )
            except Exception as e:
                st.error(f"❌ មានបញ្ហា៖ {e}")