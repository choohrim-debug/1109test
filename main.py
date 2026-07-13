import streamlit as st
import pandas as pd
import os

# 1. 웹앱 페이지 제목 및 소개
st.title("☀️ 서울-양평 기온 분석 및 전력수요 연관성 대시보드")
st.markdown("""
이 웹앱은 서울과 양평의 기온 데이터를 통해 **도시 열섬현상**을 분석하고, 
더 나아가 **서울의 기온 변화가 전력수요에 미치는 영향**을 시각적으로 살펴봅니다.
""")

# 안전하게 CSV 파일을 읽고 상단 주석을 제거하는 헬퍼 함수
def read_csv_with_encoding(path):
    for enc in ["utf-8-sig", "cp949", "utf-8", "euc-kr"]:
        try:
            for skip in range(6):
                try:
                    df = pd.read_csv(path, encoding=enc, skiprows=skip)
                    df.columns = df.columns.str.strip()
                    if any(any(k in str(col) for k in ['일시', '일자', '시간', 'date', 'time']) for col in df.columns):
                        return df
                except:
                    continue
            df = pd.read_csv(path, encoding=enc)
            df.columns = df.columns.str.strip()
            return df
        except:
            continue
    try:
        return pd.read_csv(path)
    except:
        return pd.DataFrame()

# 탭 2개 먼저 생성 (데이터 로드 실패해도 탭은 유지)
tab1, tab2 = st.tabs(["📊 탭1: 도시 열섬 분석", "⚡ 탭2: 기온과 전력 연결"])

current_dir = os.path.dirname(os.path.abspath(__file__))
seoul_path = os.path.join(current_dir, "seoul.csv")
yang_path = os.path.join(current_dir, "yang.csv")
power_path = os.path.join(current_dir, "power.csv")

# =========================================================================
# [탭1: 열섬 분석] - 독립적으로 실행
# =========================================================================
with tab1:
    st.header("도시 열섬현상(Urban Heat Island) 분석")
    try:
        seoul_df = read_csv_with_encoding(seoul_path)
        yang_df = read_csv_with_encoding(yang_path)
        
        seoul_time_col = [c for c in seoul_df.columns if any(k in c for k in ['일시', '시간', 'date'])][0] if any(any(k in c for k in ['일시', '시간', 'date']) for c in seoul_df.columns) else seoul_df.columns[0]
        seoul_temp_col = [c for c in seoul_df.columns if '기온' in c][0] if any('기온' in c for c in seoul_df.columns) else seoul_df.columns[-1]
        
        yp_time_col = [c for c in yang_df.columns if any(k in c for k in ['일시', '시간', 'date'])][0] if any(any(k in c for k in ['일시', '시간', 'date']) for c in yang_df.columns) else yang_df.columns[0]
        yp_temp_col = [c for c in yang_df.columns if '기온' in c][0] if any('기온' in c for c in yang_df.columns) else yang_df.columns[-1]
        
        seoul_df['일시'] = pd.to_datetime(seoul_df[seoul_time_col], errors='coerce').dt.round('h')
        yang_df['일시'] = pd.to_datetime(yang_df[yp_time_col], errors='coerce').dt.round('h')
        
        seoul_df = seoul_df.dropna(subset=['일시'])[['일시', seoul_temp_col]].rename(columns={seoul_temp_col: '서울 기온'})
        yang_df = yang_df.dropna(subset=['일시'])[['일시', yp_temp_col]].rename(columns={yp_temp_col: '양평 기온'})
        
        weather_merged = pd.merge(seoul_df, yang_df, on='일시', how='inner')
        
        if len(weather_merged) == 0:
            st.warning("⚠️ 서울과 양평 데이터의 시간대가 맞지 않습니다.")
        else:
            weather_merged['기온차(서울-양평)'] = weather_merged['서울 기온'] - weather_merged['양평 기온']
            weather_merged['시각'] = weather_merged['일시'].dt.hour
            weather_merged['월'] = weather_merged['일시'].dt.month
            
            st.subheader("① 1년간 두 지역 기온 변화")
            st.line_chart(weather_merged.set_index('일시')[['서울 기온', '양평 기온']])
            
            st.subheader("② 시각(0~23시)별 평균 기온차 (서울 - 양평)")
            st.bar_chart(weather_merged.groupby('시각')['기온차(서울-양평)'].mean())
            
            st.subheader("③ 월(1~12월)별 평균 기온차 (서울 - 양평)")
            st.bar_chart(weather_merged.groupby('월')['기온차(서울-양평)'].mean())
            
    except Exception as e:
        st.error(f"탭1 실행 중 오류 발생: {e}")

# =========================================================================
# [탭2: 전력 연결] - 독립적으로 실행
# =========================================================================
with tab2:
    st.header("서울 기온과 전력수요의 연관성 분석")
    try:
        seoul_df = read_csv_with_encoding(seoul_path)
        power_df = read_csv_with_encoding(power_path)
        
        if len(power_df) == 0 or power_df.empty:
            st.error("⚠️ 현재 power.csv 파일에 데이터가 비어 있거나 정상적으로 읽히지 않았습니다.")
            st.info("💡 파일 저장 상태를 확인하시거나, power.csv 파일 내용에 실제 데이터가 적혀있는지 열어보세요!")
        else:
            seoul_time_col = [c for c in seoul_df.columns if any(k in c for k in ['일시', '시간', 'date'])][0] if any(any(k in c for k in ['일시', '시간', 'date']) for c in seoul_df.columns) else seoul_df.columns[0]
            seoul_temp_col = [c for c in seoul_df.columns if '기온' in c][0] if any('기온' in c for c in seoul_df.columns) else seoul_df.columns[-1]
            
            power_time_col = [c for c in power_df.columns if any(k in c for k in ['일시', '시간', 'date'])][0] if any(any(k in c for k in ['일시', '시간', 'date']) for c in power_df.columns) else power_df.columns[0]
            power_val_col = [c for c in power_df.columns if '전력' in c][0] if any('전력' in c for c in power_df.columns) else power_df.columns[-1]
            
            seoul_df['일시'] = pd.to_datetime(seoul_df[seoul_time_col], errors='coerce').dt.round('h')
            power_df['일시'] = pd.to_datetime(power_df[power_time_col], errors='coerce').dt.round('h')
            
            seoul_df = seoul_df.dropna(subset=['일시'])[['일시', seoul_temp_col]].rename(columns={seoul_temp_col: '서울 기온'})
            power_df = power_df.dropna(subset=['일시'])[['일시', power_val_col]].rename(columns={power_val_col: '전력수요(MWh)'})
            
            power_merged = pd.merge(seoul_df, power_df, on='일시', how='inner')
            
            if len(power_merged) == 0:
                st.warning("⚠️ 서울 기온과 전력 데이터의 매칭되는 시간대가 없습니다.")
            else:
                power_merged['월'] = power_merged['일시'].dt.month
                
                st.subheader("① 기온별 전력수요 분포 (산점도)")
                st.scatter_chart(data=power_merged, x='서울 기온', y='전력수요(MWh)')
                
                st.subheader("② 기온 구간별 평균 전력수요")
                power_merged['기온 구간'] = (power_merged['서울 기온'] // 5) * 5
                st.bar_chart(power_merged.groupby('기온 구간')['전력수요(MWh)'].mean())
                
                st.subheader("③ 월(1~12월)별 평균 전력수요")
                st.bar_chart(power_merged.groupby('월')['전력수요(MWh)'].mean())
                
    except Exception as e:
        st.error(f"탭2 실행 중 오류 발생: {e}")
