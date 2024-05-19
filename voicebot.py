import streamlit as st
from audiorecorder import audiorecorder
import openai
import os
from datetime import datetime
from gtts import gTTS
import base64


### 기능 구현 함수 ###
def STT(audio, apikey):
    # 파일저장
    filename = "input.mp3"
    audio.export(filename, format="mp3")

    # 음원 파일 열기
    audio_file = open(filename, "rb")
    # whisper 모델을 활용해 텍스트 얻기
    client = openai.OpenAI(api_key=apikey)
    response = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
    audio_file.close()  # 파일 닫기
    # 파일 삭제
    os.remove(filename)
    return response.text


def ask_gpt(prompt, model, apikey):
    client = openai.OpenAI(api_key=apikey)
    response = client.chat.completions.create(model=model, messages=prompt)
    gptResponse = response.choices[0].message.content
    return gptResponse


def TTS(response):
    # gTTS를 활용하여 음성 파일 생성
    filename = "output.mp3"
    tts = gTTS(text=response, lang="ko")
    tts.save(filename)

    # 음원 파일 자동 재생
    with open(filename, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
            <audio autoplay = "True">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        st.markdown(
            md,
            unsafe_allow_html=True,
        )

    os.remove(filename)


## 메인 함수 ##
def main():
    # 기본 설정 , 웹 브라우저 상의 타이틀과 레이아웃 설정
    st.set_page_config(page_title="음성 비서 프로그램", layout="wide")

    # 제목
    st.header("음성 비서 프로그램")

    # 구분선
    st.markdown("---")

    # 기본 설명 , expander는 접고 펴는 ui
    with st.expander("음성비서 프로그램에 관하여", expanded=True):
        st.write(
            """
            - 음성 비서 프로그램의 UI는 스트림릿을 활용했습니다. 
            - STT(Speech-To-Text)는 OpenAI의 Whisper AI를 활용했습니다.
            - 답변은 OpenAI의 GPT 모델을 활용했습니다.
            - TTS(Text-To-Speech)는 구글의 Google Translate TTS를 활용했습니다.  
            """
        )
        st.markdown("")

    # session state 초기화
    if "chat" not in st.session_state:
        st.session_state["chat"] = []

    if "OPENAI_API" not in st.session_state:
        st.session_state["OPENAI_API"] = ""

    if "messages" not in st.session_state:
        st.session_state["messages"] = [
            {
                "role": "system",
                "content": "You are a thoughtful assistant. Respond to all input in 25 words and answer in korea",
            }
        ]

    if "check_reset" not in st.session_state:
        st.session_state["check_reset"] = False

    # 사이드 바 생성
    with st.sidebar:
        # Open AI API 키 받기
        st.session_state["OPENAI_API"] = st.text_input(
            label="OPENAI API 키",
            placeholder="Enter your API key",
            value="",
            type="password",
        )

        st.markdown("---")

        # GPT 모델을 선택하기 위한 라디오 버튼 생성
        model = st.radio(label="GPT 모델", options=["gpt-4", "gpt-3.5-turbo"])

        st.markdown("---")

        # 리셋 버튼 생성
        if st.button(label="초기화"):
            # 리셋코드
            st.session_state["chat"] = []
            st.session_state["messages"] = [
                {
                    "role": "system",
                    "content": "You are a thoughtful assistant. Respond to all input in 25 words and answer in korea",
                }
            ]
            st.session_state["check_reset"] = True

    # 기능 구현
    col1, col2 = st.columns(2)
    with col1:
        # 왼쪽 영역
        st.subheader("질문하기")
        # 음성 녹음 아이콘 추가
        audio = audiorecorder("클릭하여 녹음하기", "녹음 중...")
        if (audio.duration_seconds > 0) and (st.session_state["check_reset"] == False):
            st.audio(audio.export().read())  # 녹음한 파일 들을 수 있도록 구현
            # 음원파일에서 텍스트 추출
            question = STT(audio, st.session_state["OPENAI_API"])

            # 채팅을 시각화하기 위해 질문 내용 저장
            now = datetime.now().strftime("%H:%M")
            st.session_state["chat"] = st.session_state["chat"] + [
                ("user", now, question)
            ]
            # GPT 모델에 넣을 프롬프트를 위해 질문 내용 저장
            st.session_state["messages"] = st.session_state["messages"] + [
                {"role": "user", "content": question}
            ]

    with col2:
        # 오른쪽 영역
        st.subheader("질문/답변")
        if (audio.duration_seconds > 0) and (st.session_state["check_reset"] == False):
            # chatGPT에게 답변 얻기
            response = ask_gpt(
                st.session_state["messages"], model, st.session_state["OPENAI_API"]
            )

            # GPT 모델에 넣을 프롬프트를 위해 답변 내용 저장
            st.session_state["messages"] = st.session_state["messages"] + [
                {"role": "system", "content": response}
            ]

            # 채팅 시각화를 위한 답변 내용 저장
            now = datetime.now().strftime("%H:%M")
            st.session_state["chat"] = st.session_state["chat"] + [
                ("bot", now, response)
            ]

            # 채팅 형식으로 시각화하기
            for sender, time, message in st.session_state["chat"]:
                if sender == "user":
                    st.write(
                        f'<div style="display:flex;align-items:center;">\
                        <div style="background-color:#007AFF;color:white;border-radius:12px;padding:8px 12px;margin-right:8px;">{message}</div>\
                        <div style="font-size:0.8rem;color:gray;"){time}</div></div>',
                        unsafe_allow_html=True,
                    )
                    st.write("")
                else:

                    st.write(
                        f'<div style="display:flex;align-items:center;justify-content:flex-end">\
                        <div style="background-color:lightgray;color:black;border-radius:12px;padding:8px 12px;margin-right:8px;">{message}</div>\
                        <div style="font-size:0.8rem;color:gray;"){time}</div></div>',
                        unsafe_allow_html=True,
                    )
                    st.write("")

            # gTTS를 활용하여 음성 파일 생성 및 재생
            TTS(response)


if __name__ == "__main__":
    main()
