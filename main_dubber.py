import asyncio
import edge_tts
from google import genai
from moviepy import VideoFileClip, AudioFileClip
import whisper

# ១. អូសយកសំឡេងពីវីដេអូ
def extract_audio(video_path, output_audio_path):
    print("១. កំពុងទាញយកសំឡេងពីវីដេអូ...")
    video = VideoFileClip(video_path)
    video.audio.write_audiofile(output_audio_path, logger=None)
    print("   -> ទាញយកសំឡេងរួចរាល់!\n")

# ២. បំប្លែងសំឡេងទៅជាអក្សរដើម
def transcribe_audio(audio_path):
    print("២. កំពុងស្ដាប់ និងបំប្លែងសំឡេងទៅជាអក្សរ...")
    model = whisper.load_model("base") 
    result = model.transcribe(audio_path)
    return result['text']

# ៣. បកប្រែអត្ថបទទៅជាភាសាខ្មែរ 
def translate_to_khmer(text, api_key):
    print("៣. កំពុងបកប្រែអត្ថបទទៅភាសាខ្មែរ...")
    client = genai.Client(api_key=api_key)
    prompt = f"Translate the following text to Khmer language. Only provide the translated text:\n\n{text}"
    
    response = client.models.generate_content(
        model='gemini-3.6-flash', 
        contents=prompt,
    )
    return response.text.strip()

# ៤. បំប្លែងអក្សរខ្មែរ ទៅជាសំឡេងនិយាយ
async def generate_khmer_audio(text, output_audio_path):
    print("៤. កំពុងបង្កើតសំឡេងនិយាយភាសាខ្មែរ...")
    voice = "km-KH-SreymomNeural" 
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_audio_path)
    print(f"   -> បង្កើតសំឡេងរួចរាល់! រក្សាទុកនៅ៖ {output_audio_path}\n")

# ៥. បញ្ចូលសំឡេងខ្មែរទៅក្នុងវីដេអូដើមវិញ
def merge_audio_with_video(video_path, new_audio_path, output_video_path):
    print("៥. កំពុងបញ្ចូលសំឡេងខ្មែរទៅក្នុងវីដេអូ (សូមរង់ចាំបន្តិច)...")
    video = VideoFileClip(video_path)
    new_audio = AudioFileClip(new_audio_path)
    
    # ដាក់សំឡេងថ្មីជំនួសសំឡេងចាស់
    final_video = video.with_audio(new_audio)
    
    # បញ្ចេញជាវីដេអូថ្មី
    final_video.write_videofile(output_video_path, codec="libx264", audio_codec="aac", logger=None)
    print(f"   -> រួចរាល់! វីដេអូខ្មែរត្រូវបានរក្សាទុកនៅ៖ {output_video_path}\n")


# --- ដំណើរការកូដមេ (Main Execution) ---
async def main():
    VIDEO_INPUT = "my_video.mp4" 
    TEMP_AUDIO = "temp_original_audio.mp3"
    FINAL_KHMER_AUDIO = "final_khmer_dub.mp3"
    FINAL_VIDEO_OUTPUT = "final_khmer_video.mp4" # ឈ្មោះវីដេអូថ្មី
    
    GEMINI_API_KEY = "AQ.Ab8RN6K6TvEJY7F4tWPCCSQCRZCK_t-by7Nph3U60ff-PSHRVw"

    try:
        extract_audio(VIDEO_INPUT, TEMP_AUDIO)
        original_text = transcribe_audio(TEMP_AUDIO)
        khmer_text = translate_to_khmer(original_text, GEMINI_API_KEY)
        
        if khmer_text:
            await generate_khmer_audio(khmer_text, FINAL_KHMER_AUDIO)
            # ហៅមុខងារទី៥ មកធ្វើការ
            merge_audio_with_video(VIDEO_INPUT, FINAL_KHMER_AUDIO, FINAL_VIDEO_OUTPUT)
            
            print("🎉 អបអរសាទរ! ដំណើរការផលិតវីដេអូ AutoDubber ទទួលបានជោគជ័យ ១០០%!")
            
    except Exception as e:
        print(f"❌ មានបញ្ហាគាំងនៅកន្លែងណាមួយ៖ {e}")

if __name__ == "__main__":
    asyncio.run(main())