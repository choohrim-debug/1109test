import streamlit as st
import pandas as pd
import os
import glob

# 1. 웹앱 페이지 제목 및 소개
st.title("서울-양평 기온 비교를 통한 도시 열섬현상 분석")
st.markdown("""
이 웹앱은 서울(대도시)과 양평(교외 지역)의 기온 데이터를 비교하여 **도시 열섬현상(Urban Heat Island)**을 시각적으로 분석합니다.
""")

# 데이터 불러오기 함수
@st.cache_data
def load_data():
    # 현재 파일의 폴더 경로 확인
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 한글 파일명 깨짐 방지를 위한 검색 패턴
    seoul_pattern = os.path.join(current_dir, "*서울*기온*.csv")
    yangpyeong_pattern = os.path.join(current_dir, "*양평*기온*.csv")
    
    seoul_files = glob.glob(seoul_pattern)
    yangpyeong_files = glob.glob(yangpyeong_pattern)
    
    # 파일 읽기
    if seoul_files and yangpyeong_files:
        seoul_df = pd.read_csv(seoul_files[0], encoding="cp949")
        yangpyeong_df = pd.read_csv(yangpyeong_files[0], encoding="cp949")
    else:
        seoul_path = os.path.join(current_dir, "서울_기온.csv")
        yangpyeong_path = os.path.join(current_dir, "양평_기온.csv")
        seoul_df = pd.read_csv(seoul_path, encoding="cp949")
        yangpyeong_df = pd.read_csv(yangpyeong_path, encoding="cp949")
    
    # [오류 해결 부위] '일시' 컬럼을 datetime 형식으로 변환 (괄호 명확히 마감)
    seoul_df['일시'] = pd.to_datetime(seoul_df['일시'])
    yangpyeong_df['일시'] = pd.to_datetime(yangpyeong_df['일시'])
    
    # 컬럼명 변경
    seoul_df = seoul_df.rename(columns={'기온(°C)': '서울 기온'})
    yangpyeong_df = yangpyeong_df.rename(columns={'기온(°C)': '양평 기온'})
    
    # 데이터 병합
    merged_df = pd.merge(
        seoul_df[['일시', '서울 기온']], 
        yangpyeong_df[['일시', '양평 기온']], 
        on='일시', 
        how='inner'
    )
    
    # 기온차 컬럼 생성
    merged_df['기온차(서울-양평)'] = merged_df['서울 기온'] - merged_df['양평 기온']
    
    return merged_df

# 메인 실행 로직
try:
    df = load_data()
    
    # 사이드바 정보
    st.sidebar.header("📊 데이터 요약 정보 (2025)")
    st.sidebar.write(f"총 데이터 수: {len(df):,}개")
    st.sidebar.write(f"서울 평균 기온: {df['서울 기온'].mean().round(2)} °C")
    st.sidebar.write(f"양평 평균 기온: {df['양평 기온'].mean().round(2)} °C")
    st.sidebar.write(f"평균 기온차: {df['기온차(서울-양평)'].mean().round(2)} °C")

    # ① 1년간 두 지역의 기온 변화
    st.header("① 1년간 두 지역의 기온 변화")
    st.markdown("서울과 양평의 1년간 전체 기온 추이를 선그래프로 비교합니다.")
    line_chart_data = df.set_index('일시')[['서울 기온', '양평 기온']]
    st.line_chart(line_chart_data)

    # 시간/월 파생변수 생성
    df['시각'] = df['일시'].dt.hour
    df['월'] = df['일시'].dt.month

    # ② 시각별 평균 기온차
    st.header("② 시각(0~23시)별 평균 기온차 (서울 - 양평)")
    st.markdown("하루 중 어느 시간대에 도시 열섬현상(기온차)이 가장 뚜렷하게 나타나는지 확인합니다.")
    hourly_diff = df.groupby('시각')['기온차(서울-양평)'].mean()
    st.bar_chart(hourly_diff)

    # ③ 월별 평균 기온차
    st.header("③ 월(1~12월)별 평균 기온차 (서울 - 양평)")
    st.markdown("계절별(월별)로 도시 열섬현상의 세기가 어떻게 달라지는지 확인합니다.")
    monthly_diff = df.groupby('월')['기온차(서울-양평)'].mean()
    st.bar_chart(monthly_diff)

except Exception as e:
    st.error(f"⚠️ 에러가 발생했습니다: {e}") 
