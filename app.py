import json
import tempfile
from chatbot import *
import streamlit as st
from st_audiorec import st_audiorec
from faster_whisper import WhisperModel

from gtts import gTTS 
import subprocess
import base64
import time
import librosa

from dotenv import load_dotenv
load_dotenv()


# def set_bg_hack(main_bg):
#     '''
#     A function to unpack an image from root folder and set as bg.

#     Returns
#     -------
#     The background.
#     '''
#     # set bg name
#     main_bg_ext = "png"
        
#     st.markdown(
#         f"""
#         <style>
#         .stApp {{
#             background: url(data:image/{main_bg_ext};base64,{base64.b64encode(open(main_bg, "rb").read()).decode()});
#             background-size: 1540px 740px;
#         }}
#         </style>
#         """,
#         unsafe_allow_html=True
#     )

# # #to set custom background image
# set_bg_hack('WhatsApp Image 2024-04-27 at 12.54.02 PM.jpeg')


st.title('LearnFlow')

row1_col1, row1_col2 = st.columns(2)
row2_col1, row2_col2 = st.columns(2)
row3_col1, row3_col2 = st.columns(2)
row4_col1, _ = st.columns(2)


# ========== yazan ==================

def stream_data(response:str, duration):
    for word in response.split(" "):
        yield word + " "
        time.sleep(duration/len(response.split(" ")))

def autoplay_audio(file_path: str, control, gif_holder, response):
    
    with open(file_path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
            <audio controls autoplay="true">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        control.markdown(
            md,
            unsafe_allow_html=True,
        )
        duration=librosa.get_duration(filename=file_path)
        text_area.write_stream(stream_data(response, duration))
        gif_holder.image('spongy_waiting.png')
        

def tts(response: str, gif_holder):
    language = 'ar'
    myobj = gTTS(text=response, lang=language, slow=False) 
    myobj.save("output.wav")
    return voice_cloning('output.wav', response, gif_holder)

def voice_cloning(audio_path: str, response:str, gif_holder):
    command = ["python", "-m", "rvc_python", "-i", f"{audio_path}", "-mp", "./rvc_spongebob/model.pth"]
    try:
        subprocess.run(command, check=True)
        with row3_col2:
            control = st.empty()
        gif_holder.image('spongy_talking.gif')
        #st.write(response)
        autoplay_audio("out.wav", control, gif_holder, response)
        # st.write_stream(stream_data(response))      
                
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")



# ========= belal ==================

with row1_col1:
    with st.popover("معلومات الطالب 🪼"):
        # st.markdown("Tell Us About Yourself 👋")
        name = st.text_input("ما اسمك؟")
        age = st.text_input("كم عمرك؟")

        uploaded_file = st.file_uploader("اختر الدرس 📄", type="pdf")

with row2_col1:
    text_area = st.empty()

with row2_col2:
    #gif_holder = st.image('spongy_waiting.png')
    gif_holder = st.empty()







# Initialize session state variables if not already done
st.session_state.setdefault('explanation', None)
st.session_state.setdefault('mcq_questions', None)
st.session_state.setdefault('voice_file', None)
st.session_state.setdefault('text_question', '')
st.session_state.setdefault('user_question', '')
st.session_state.setdefault('current_question', 0)
st.session_state.setdefault('score', 0)
st.session_state.setdefault('uploaded_file_name', None)





use_case = None

if age and name and uploaded_file:
    age = int(age)
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = tmp.name

    # Check if a new file has been uploaded
    if st.session_state.uploaded_file_name != uploaded_file.name:
        # Reset session state variables
        st.session_state.explanation = None
        st.session_state.mcq_questions = None
        st.session_state.voice_file = None
        st.session_state.text_question = ''
        st.session_state.user_question = ''
        st.session_state.current_question = 0
        st.session_state.score = 0
        st.session_state.uploaded_file_name = uploaded_file.name

    # Generate responses if not already done
    #if st.session_state.explanation is None and st.session_state.mcq_questions is None:                         yazan replaced or with and
    if st.session_state.explanation is None and st.session_state.mcq_questions is None:
        gif_holder.image('loading-loading-forever.gif')

        use_case = "explain"
        st.session_state.explanation =tts(generate_response(age, name, use_case, tmp_path, use_case),gif_holder)
        use_case = "test"
        st.session_state.mcq_questions = generate_response(age, name, use_case, tmp_path, use_case)
        use_case = None

        #gif_holder.empty()

    # Display spongy gif and explanation
    #gif_holder.image('spongy_talking.gif')
    #text_area.write(st.session_state.explanation)





    # Display MCQ questions
    if st.session_state.mcq_questions:
        with row1_col2:
            with st.popover("اختبرني 💡"):
                st.markdown("هل انت مستعد للاختبار؟ 🧠")
                json_start = st.session_state.mcq_questions.find('[')
                json_end = st.session_state.mcq_questions.rfind(']')
                json_content = st.session_state.mcq_questions[json_start:json_end + 1]
                parsed_mcq = json.loads(json_content)

                # If the quiz is not over, display the current question and answer options
                if st.session_state.current_question < len(parsed_mcq):
                    question = parsed_mcq[st.session_state.current_question]['question']
                    options = parsed_mcq[st.session_state.current_question]['options']
                    correct_answer = parsed_mcq[st.session_state.current_question]['correct_answer']
                    user_answer = st.selectbox(question, options)

                    # Check user's answer and update score
                    if st.button('السؤال التالي'):
                        if user_answer == correct_answer:
                            st.session_state.score += 1
                        st.session_state.current_question += 1
                else:
                    # If the quiz is over, display the score
                    st.write(f'💯 تقييمك: {st.session_state.score}/{len(parsed_mcq)}')

                    # Add a reset quiz button
                    if st.button('اعادة الاختبار'):
                        st.session_state.current_question = 0
                        st.session_state.score = 0





    # Audio and text input for user question

    with row4_col1:
        st.session_state.voice_file = st_audiorec()
        if st.session_state.voice_file is not None:
            st.audio(st.session_state.voice_file, format='audio/wav')
            #gif_holder.image('loading.gif')

    with row3_col1:
        st.session_state.user_question = st.text_input("Enter or Record your question:", value=st.session_state.user_question)
        #gif_holder.image('loading.gif')


    # Process voice file if text input is empty
    if st.session_state.user_question == '':
        if st.session_state.voice_file:
            model = WhisperModel("base", device="cpu", compute_type="int8")
            # Write the bytes object to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_wav:
                temp_wav.write(st.session_state.voice_file)
                temp_wav_path = temp_wav.name
            # Read the temporary file when calling transcribe
            with open(temp_wav_path, 'rb') as f:
                segments, _ = model.transcribe(f, beam_size=5)
                st.session_state.user_question = " ".join(segment.text for segment in segments)
                print(st.session_state.user_question)





    # Generate and display response to user question
    if age and name and st.session_state.user_question and tmp_path:
        gif_holder.image('loading-loading-forever.gif')
        response = generate_response(age, name, st.session_state.user_question, tmp_path, use_case)
        #gif_holder2.empty()
        #text_area.write(response)

        tts(response,gif_holder)

        #gif_holder.image('spongy_waiting.png')
        # Reset voice file and text
        st.session_state.voice_file = None
        st.session_state.user_question = ''