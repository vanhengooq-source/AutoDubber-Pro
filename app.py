import asyncio
import edge_tts
from deep_translator import GoogleTranslator
from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip
import whisper
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import os
import time

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
    except:
        return False

class AutoDubberApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AutoDubber Pro - កម្មវិធីបកប្រែវីដេអូ")
        self.root.geometry("750x550")
        self.root.configure(bg="#f0f0f0")
        
        # ប្តូរពី File មួយ ទៅជាការផ្ទុក File ជាច្រើន (List)
        self.video_paths = []

        tk.Label(root, text="កម្មវិធីបកប្រែវីដេអូជំនាន់ថ្មី (Pro - Audio Ducking)", font=("Khmer OS Muol Light", 14), bg="#f0f0f0").pack(pady=15)

        self.btn_select = tk.Button(root, text="📂 ជ្រើសរើស File វីដេអូ (ច្រើនបញ្ចូលគ្នា)", command=self.select_file, font=("Arial", 11), width=35)
        self.btn_select.pack(pady=5)

        self.lbl_file = tk.Label(root, text="មិនទាន់មានវីដេអូត្រូវបានជ្រើសរើសទេ", fg="gray", bg="#f0f0f0")
        self.lbl_file.pack(pady=5)

        self.btn_start = tk.Button(root, text="▶️ ចាប់ផ្ដើមបកប្រែ", command=self.start_process, font=("Arial", 11, "bold"), state=tk.DISABLED, bg="#4CAF50", fg="white", width=35)
        self.btn_start.pack(pady=15)

        self.log_box = tk.Text(root, height=15, width=85, state=tk.DISABLED, bg="black", fg="white", font=("Courier", 10))
        self.log_box.pack(pady=10)

    def log(self, message):
        self.log_box.config(state=tk.NORMAL)
        self.log_box.insert(tk.END, message + "\n")
        self.log_box.see(tk.END)
        self.log_box.config(state=tk.DISABLED)
        self.root.update()

    def translate_to_khmer(self, text):
        if not text.strip(): return ""
        time.sleep(2.5) 
        try:
            translator = GoogleTranslator(source='auto', target='km')
            result = translator.translate(text)
            
            error_words = ["Error", "error", "500", "1500", "Server", "server", "try again", "Exception"]
            if any(word in result for word in error_words):
                self.log("      [ជាប់ Limit]: ប្រព័ន្ធ Google ផ្អាកបកប្រែបណ្ដោះអាសន្ន...")
                return "" 
                
            return result
        except Exception as e:
            self.log(f"      [Error បកប្រែ]: បរាជ័យក្នុងការទាក់ទង Google")
            return ""

    def select_file(self):
        # អនុញ្ញាតឱ្យជ្រើសរើសវីដេអូច្រើន (askopenfilenames)
        filepaths = filedialog.askopenfilenames(filetypes=[("Video files", "*.mp4 *.avi *.mkv")])
        if filepaths:
            self.video_paths = filepaths
            self.lbl_file.config(text=f"បានជ្រើសរើសវីដេអូចំនួន៖ {len(filepaths)} File", fg="blue")
            self.btn_start.config(state=tk.NORMAL)

    def start_process(self):
        self.btn_start.config(state=tk.DISABLED)
        self.btn_select.config(state=tk.DISABLED)
        self.log_box.config(state=tk.NORMAL)
        self.log_box.delete('1.0', tk.END)
        self.log_box.config(state=tk.DISABLED)
        threading.Thread(target=self.run_logic, daemon=True).start()

    def apply_start(self, clip, start_time):
        if hasattr(clip, 'with_start'):
            return clip.with_start(start_time)
        return clip.set_start(start_time)

    def apply_volume(self, clip, vol):
        try:
            return clip.with_volume_scaled(vol)
        except AttributeError:
            try:
                return clip.volumex(vol)
            except AttributeError:
                try:
                    from moviepy.audio.fx.multiply_volume import multiply_volume
                    return multiply_volume(clip, vol)
                except:
                    return clip

    def run_logic(self):
        total_videos = len(self.video_paths)
        
        for index, video_path in enumerate(self.video_paths):
            self.log(f"\n==================================================")
            self.log(f"🎬 កំពុងដំណើរការវីដេអូទី {index + 1}/{total_videos} ៖ {os.path.basename(video_path)}")
            self.log(f"==================================================")
            
            TEMP_AUDIO = f"temp_audio_extract_{index}.wav"
            base_name = os.path.basename(video_path)
            name_only, ext = os.path.splitext(base_name)
            FINAL_VIDEO = f"{name_only}_khmer_pro{ext}"
            SRT_FILE = f"{name_only}_khmer_subtitle.srt"

            try:
                self.log("១. កំពុងទាញសំឡេងពីវីដេអូដើម...")
                video = VideoFileClip(video_path)
                video_duration = video.duration
                video.audio.write_audiofile(TEMP_AUDIO, logger=None)

                self.log("២. កំពុងស្កេនចាប់ទីតាំងសំឡេង (Timestamp)...")
                model = whisper.load_model("base")
                result = model.transcribe(TEMP_AUDIO)
                segments = result['segments']

                self.log(f"   -> រកឃើញការសន្ទនាចំនួន {len(segments)} ប្រយោគ។")

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
                                bg_normal = self.apply_start(bg_normal, last_end)
                                audio_clips.append(bg_normal)
                            except: pass

                        try:
                            bg_ducked = video.audio.subclip(start, end)
                            # កែប្រែកម្រិតសំឡេងដើមពី 0.03 មក 0.90 (90%) តាមការស្នើសុំ
                            bg_ducked = self.apply_volume(bg_ducked, 0.90)
                            bg_ducked = self.apply_start(bg_ducked, start)
                            audio_clips.append(bg_ducked)
                        except: pass
                            
                        last_end = end

                    if last_end < video_duration:
                        try:
                            bg_tail = video.audio.subclip(last_end, video_duration)
                            bg_tail = self.apply_start(bg_tail, last_end)
                            audio_clips.append(bg_tail)
                        except: pass

                srt_content = ""
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                self.log("៣. កំពុងបកប្រែ និងបញ្ចូលសំឡេង AI...")

                for i, seg in enumerate(segments):
                    start = seg['start']
                    end = seg['end']
                    text = seg['text']

                    self.log(f"\n   -> ដំណើរការទី {i+1}/{len(segments)}...")
                    khmer_text = self.translate_to_khmer(text)

                    if khmer_text:
                        self.log(f"      [ខ្មែរ]: {khmer_text}")
                        srt_content += f"{i+1}\n{format_time(start)} --> {format_time(end)}\n{khmer_text}\n\n"

                        temp_seg_audio = f"temp_seg_{index}_{i}.mp3"
                        success = loop.run_until_complete(generate_khmer_audio(khmer_text, temp_seg_audio))

                        if success and os.path.exists(temp_seg_audio):
                            seg_clip = AudioFileClip(temp_seg_audio)
                            seg_clip = self.apply_volume(seg_clip, 1.5)
                            seg_clip = self.apply_start(seg_clip, start)
                            audio_clips.append(seg_clip)
                    else:
                        self.log(f"      [រំលង]: គ្មានការបកប្រែទេ")

                loop.close()

                self.log("៤. កំពុងរក្សាទុក File អក្សររត់ (Subtitle)...")
                with open(SRT_FILE, "w", encoding="utf-8") as f:
                    f.write(srt_content)

                self.log("៥. កំពុងបញ្ចូលសំឡេងទាំងអស់ចូលវីដេអូថ្មី (សូមរង់ចាំបន្តិច)...")
                final_audio = CompositeAudioClip(audio_clips)

                if hasattr(video, 'with_audio'):
                    final_video = video.with_audio(final_audio)
                else:
                    final_video = video.set_audio(final_audio)

                final_video.write_videofile(FINAL_VIDEO, codec="libx264", audio_codec="aac", logger=None)

                if os.path.exists(TEMP_AUDIO): os.remove(TEMP_AUDIO)
                for i in range(len(segments)):
                    if os.path.exists(f"temp_seg_{index}_{i}.mp3"): os.remove(f"temp_seg_{index}_{i}.mp3")

                self.log(f"✅ ជោគជ័យសម្រាប់វីដេអូទី {index + 1}!")
                
            except Exception as e:
                self.log(f"❌ មានបញ្ហាលើវីដេអូនេះ៖ {e}")

        # បន្ទាប់ពីដំណើរការវីដេអូទាំងអស់ចប់
        self.log("\n🎉 ប្រតិបត្តិការទាំងមូលត្រូវបានបញ្ចប់សព្វគ្រប់!")
        messagebox.showinfo("ជោគជ័យ", "វីដេអូទាំងអស់ត្រូវបានកាត់តចប់សព្វគ្រប់! សូមឆែកមើល File ថ្មីរបស់អ្នក។")
        self.btn_start.config(state=tk.NORMAL)
        self.btn_select.config(state=tk.NORMAL)
        self.lbl_file.config(text="មិនទាន់មានវីដេអូត្រូវបានជ្រើសរើសទេ", fg="gray")
        self.video_paths = []

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoDubberApp(root)
    root.mainloop()