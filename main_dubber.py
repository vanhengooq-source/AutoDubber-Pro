import asyncio
import edge_tts
from google import genai
from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip
import whisper
import os

def extract_audio(video_path, output_audio_path):
    print("១. កំពុងទាញយកសំឡេង...")
    video = VideoFileClip(video_path)
    video.audio.write_audiofile(output_audio_path, logger=None)

def transcribe_audio(audio_path):
    print("២. ស្ដាប់ និងចាប់ម៉ោងនិយាយ (ល្បឿនលឿន)...")
    # ប្ដូរទៅ tiny ដើម្បីលឿនបំផុត និង fp16=False សម្រាប់ Cloud
    model = whisper.load_model("tiny") 
    result = model.transcribe(audio_path, fp16=False)
    return result['segments'] # យកជាកង់ៗមាននាទីច្បាស់លាស់

def translate_to_khmer(text, api_key):
    if not text.strip(): return ""
    client = genai.Client(api_key=api_key)
    prompt = f"Translate to Khmer. Only output the translation:\n{text}"
    response = client.models.generate_content(
        model='gemini-3.6-flash', 
        contents=prompt,
    )
    return response.text.strip()

async def generate_khmer_audio(text, output_audio_path):
    voice = "km-KH-SreymomNeural" 
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_audio_path)

async def main():
    VIDEO_INPUT = "my_video.mp4" 
    TEMP_AUDIO = "temp_original_audio.mp3"
    FINAL_VIDEO_OUTPUT = "final_khmer_video.mp4"
    
    # API Key របស់បងត្រូវបានដាក់បញ្ចូលរួចរាល់នៅទីនេះ
    GEMINI_API_KEY = "AQ.Ab8RN6K6TvEJY7F4tWPCCSQCRZCK_t-by7Nph3U60ff-PSHRVw"

    try:
        extract_audio(VIDEO_INPUT, TEMP_AUDIO)
        segments = transcribe_audio(TEMP_AUDIO)
        
        print("៣ & ៤. កំពុងបកប្រែ និងតម្រៀបសំឡេងខ្មែរតាមម៉ោងដើមពិតៗ...")
        video = VideoFileClip(VIDEO_INPUT)
        
        # បន្ថយសំឡេងដើមឱ្យនៅតិចៗ (10%) កុំឱ្យបាត់ជាតិវីដេអូដើម
        original_audio = AudioFileClip(TEMP_AUDIO).with_volume_scaled(0.1)
        audio_clips = [original_audio]

        for i, seg in enumerate(segments):
            start_time = seg['start']
            khmer_text = translate_to_khmer(seg['text'], GEMINI_API_KEY)
            
            if khmer_text:
                temp_tts_path = f"temp_tts_{i}.mp3"
                await generate_khmer_audio(khmer_text, temp_tts_path)
                # ដាក់សំឡេងខ្មែរឱ្យចំវិនាទីដែលតួអង្គនិយាយ
                tts_clip = AudioFileClip(temp_tts_path).with_start(start_time)
                audio_clips.append(tts_clip)

        print("៥. កំពុងកាត់តសំឡេងទាំងអស់ចូលវីដេអូ...")
        final_audio = CompositeAudioClip(audio_clips)
        final_video = video.with_audio(final_audio)
        final_video.write_videofile(FINAL_VIDEO_OUTPUT, codec="libx264", audio_codec="aac", logger=None)
        
        # សម្អាត File កម្ទេចកំទីចោល ដើម្បីសន្សំទំហំ Cloud
        for i in range(len(segments)):
            if os.path.exists(f"temp_tts_{i}.mp3"): os.remove(f"temp_tts_{i}.mp3")
        if os.path.exists(TEMP_AUDIO): os.remove(TEMP_AUDIO)
            
        print("🎉 ជោគជ័យ! សំឡេងខ្មែរដើរត្រូវម៉ោង ១០០% ហើយ!")
            
    except Exception as e:
        print(f"❌ មានបញ្ហា៖ {e}")

if __name__ == "__main__":
    asyncio.run(main())