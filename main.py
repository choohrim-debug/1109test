import streamlit as st
import pandas as pd
import os
import glob

# 1. 웹앱 페이지 제목 및 소개
st.title("서울-양평 기온 비교를 통한 도시 열섬현상 분석")
st.markdown("""
이 웹앱은 서울(대도시)과 양평(교외 지역)의 기온 데이터를 비교하여 **도시 열섬현상(Urban Heat Island)**을 시각적으로 분석합니다.
""")

# 데이터 불러오기 함수 (한글 자모 분리 및 경로 문제 해결 버전)
@st.cache_data
def load_data():
    # 현재 main.py 파일이 실행되는 폴더의 절대 경로 확인
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 한글 깨짐/자모 분리 현상을 방지하기 위해 와일드카드(*) 패턴으로 파일 검색
    seoul_pattern = os.path.join(current_dir, "*서울*기온*.csv")
    yangpyeong_pattern = os.path.join(current_dir, "*양평*기온*.csv")
    
    seoul_files = glob.glob(seoul_pattern)
    yangpyeong_files = glob.glob(yangpyeong_pattern)
    
    # 안전하게 파일 매칭 여부를 확인 후 데이터 읽기 (encoding="cp949" 필수 적용)
    if seoul_files and yangpyeong_files:
        seoul_df = pd.read_csv(seoul_files[0], encoding="cp949")
        yangpyeong_df = pd.read_csv(yangpyeong_files[0], encoding="cp949")
    else:
        # 패턴 매칭 실패 시 기본 파일명으로 직접 지정 시도
        seoul_path = os.path.join(current_dir, "서울_기온.csv")
        yangpyeong_path = os.path.join(current_dir, "양평_기온.csv")
        seoul_df = pd.read_csv(seoul_path, encoding="cp949")
        yangpyeong_df = pd.read_csv(yangpyeong_path, encoding="cp949")
    
    # '일시' 컬럼을 날짜/시간(datetime) 형식으로 변환
    seoul_df['일시'] = pd.to_datetime(seoul_
