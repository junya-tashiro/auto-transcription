import os
import threading
import tkinter.scrolledtext
import tkinter.ttk
import pandas as pd
import numpy as np
import tkinter
from tkinter import ttk
from tkinter import filedialog
from openai import OpenAI
from pyannote.audio import Pipeline

class AudioApp():
   def __init__(self):
      self.root = tkinter.Tk()
      self.root.title('auto-transcription')
      self.root.geometry('500x350')
      self.root.resizable(False, False)
      self.font = ('Helvetica', 15)
      self.file_name = ''

      path = os.path.dirname(os.path.abspath(__file__))
      with open(path + '/openai_api.txt', 'r') as f:
         self.openai_api_key = f.read()
      with open(path + '/use_auth_token.txt', 'r') as f:
         self.use_auth_token = f.read()

      self.do_separate_var = tkinter.BooleanVar()
      self.validate_cmd = self.root.register(self.validate)

      self.apikey_label = ttk.Label(self.root, text='API key ', font=self.font)
      self.apikey_entry = ttk.Entry(self.root, width=39, font=self.font)
      self.apikey_entry.insert(0, self.openai_api_key)

      self.do_separate_label = ttk.Label(self.root, text='separate', font=self.font)
      self.do_separate_ckbtn = ttk.Checkbutton(text='', variable=self.do_separate_var, command=self.ckbtn_func)

      self.num_speakers_label = ttk.Label(self.root, text='#spk', font=self.font, state='disable')
      self.num_speakers_spinbox = ttk.Spinbox(self.root, from_=1, to=100, width=10, font=self.font, state='disable', validate="key", validatecommand=(self.validate_cmd, "%P"))

      self.prompt_label = ttk.Label(self.root, text='prompt', font=self.font)
      self.prompt_st = tkinter.scrolledtext.ScrolledText(self.root, width=39, height=10, font=self.font)

      self.file_label = ttk.Label(self.root, text='', font=self.font)
      self.file_frame = ttk.Frame(self.root)
      self.file_btn = tkinter.Button(self.file_frame, text='open', width=2, command=self.get_filename)
      self.file_txt = ttk.Label(self.file_frame, text='sound file')
      self.file_btn.grid(row=0, column=0)
      self.file_txt.grid(row=0, column=1, padx=5)

      self.start_btn = tkinter.Button(self.root, text='start', width=5, height=2, command=self.start_btn_func)
      self.progress_bar = ttk.Progressbar(self.root, mode='indeterminate')
      self.end_txt = ttk.Label(self.root, text='complete!', font=self.font)


      self.apikey_label.grid(row=0, column=0, padx=10, sticky=tkinter.W)
      self.apikey_entry.grid(row=0, column=1, padx=10, sticky=tkinter.W)
      self.do_separate_label.grid(row=1, column=0, padx=10, sticky=tkinter.W)
      self.do_separate_ckbtn.grid(row=1, column=1, padx=10, sticky=tkinter.W)
      self.num_speakers_label.grid(row=2, column=0, padx=10, sticky=tkinter.W)
      self.num_speakers_spinbox.grid(row=2, column=1, padx=10, sticky=tkinter.W)
      self.prompt_label.grid(row=3, column=0, padx=10, sticky=tkinter.W)
      self.prompt_st.grid(row=3, column=1, padx=10, sticky=tkinter.W)
      self.file_label.grid(row=4, column=0, padx=10, sticky=tkinter.W)
      self.file_frame.grid(row=4, column=1, padx=10, sticky=tkinter.W)
      self.start_btn.place(x=200, y=300)

      self.root.mainloop()

   def ckbtn_func(self):
      if self.do_separate_var.get():
         self.num_speakers_label['state'] = 'able'
         self.num_speakers_spinbox['state'] = 'able'
      else:
         self.num_speakers_label['state'] = 'disable'
         self.num_speakers_spinbox['state'] = 'disable'

   def start_btn_func(self):
      self.start_btn['state'] = 'disable'
      self.end_txt.place_forget()
      self.progress_bar.place(x=300, y=313)
      self.progress_bar.start()
      th1 = threading.Thread(target=self.process_data)
      th1.start()

   def validate(self, P):
      if str.isdigit(P) or P == '':
         return True
      else:
         return False
   
   def get_filename(self):
      fTyp = [('WAV', '.wav'), ('MP3', '.mp3')] 
      self.file_name = filedialog.askopenfilename(filetypes=fTyp)
      self.file_txt['text'] = self.file_name
   
   def process_data(self):
      if self.do_separate_var.get():
         num_speakers = int(self.num_speakers_spinbox.get())
      else:
         num_speakers = None
      output_xlsx(
         name=self.file_name, 
         num_speakers=num_speakers, 
         do_separate=self.do_separate_var.get(), 
         prompt=self.prompt_st.get('1.0','end - 1c'), 
         api_key=self.apikey_entry.get(),
         use_auth_token=self.use_auth_token
         )
      self.progress_bar.stop()
      self.progress_bar.place_forget()
      self.start_btn['state'] = 'normal'
      self.end_txt.place(x=300, y=313)

def transcript(input, prompt):
   client = OpenAI()
   transcription = client.audio.transcriptions.create(
      model='whisper-1', 
      language='ja',
      file=open(input, 'rb'), 
      prompt=prompt,
      response_format='srt'
   )
   transcript_list = str(transcription).split('\n')

   data = {}
   length = 0
   for i in range(len(transcript_list)//4):
      id = int(transcript_list[4*i])
      times = transcript_list[4*i+1].split(' ')
      start_txt = times[0].split(',')[0]
      end_txt = times[2].split(',')[0]
      times_s = start_txt.split(':')
      times_e = end_txt.split(':')
      txt = transcript_list[4*i+2]
      data[id] = {'start': int(times_s[0])*360+int(times_s[1])*60+int(times_s[2]), 
                  'end': int(times_e[0])*360+int(times_e[1])*60+int(times_e[2]), 
                  'start_txt': start_txt,
                  'end_txt': end_txt,
                  'txt': txt}
      length = int(times_e[0])*360+int(times_e[1])*60+int(times_e[2])
   return {'data': data, 'len': length}


def detect_speaker(input, time_len, num_speakers, use_auth_token):
   p = Pipeline.from_pretrained(
      'pyannote/speaker-diarization-3.1', 
      use_auth_token=use_auth_token
   )
   diarization = p(input, num_speakers=num_speakers)

   data = np.zeros(time_len*10)

   for segment, _, speaker in diarization.itertracks(yield_label=True):
      if segment.start > time_len:
         break
      elif segment.end > time_len:
         data[round(segment.start*10):time_len*10-1] = int(speaker[8:]) + 1
      else:
         data[round(segment.start*10):round(segment.end*10)] = int(speaker[8:]) + 1
   
   return np.identity(num_speakers+1)[data.astype(int)]
   
def separating(data, detect):
   labeled_data = {}
   for key, value in data.items():
      speaker_id = np.argmax(np.sum(detect[value['start']*10:value['end']*10], axis=0)[1:])
      labeled_data[key] = {'speaker': speaker_id,
                           'start': data[key]['start_txt'], 
                           'end': data[key]['end_txt'], 
                           'txt': data[key]['txt']}
   return labeled_data

def no_separating(data):
   labeled_data = {}
   for key, value in data.items():
      speaker_id = 0
      labeled_data[key] = {'speaker': speaker_id,
                           'start': data[key]['start_txt'], 
                           'end': data[key]['end_txt'], 
                           'txt': data[key]['txt']}
   return labeled_data

def output_xlsx(name, num_speakers, do_separate, prompt, api_key, use_auth_token):
   os.environ['OPENAI_API_KEY'] = api_key
   transcripts = transcript(name, prompt)
   if do_separate:
      detect = detect_speaker(name, transcripts['len'], num_speakers, use_auth_token)
      labeled_transcripts = separating(transcripts['data'], detect)
   else:
      labeled_transcripts = no_separating(transcripts['data'])

   df = pd.DataFrame.from_dict(labeled_transcripts, orient='index')
   df.to_excel(name.split('.')[0] + '.xlsx')


if __name__ == '__main__':
   AudioApp()
