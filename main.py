import streamlit as st
 
st.title("추혜림의 웹앱")
st.write("안녕하세요! 반갑습니다. ;)")

지역 = st.selectbox("지역을 골라 보세요", ["서울", "양평", "부산"])
st.write("당신이 고른 지역:", 지역)
