import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

@st.cache_data
def load_data():
    try:
        url = 'https://github.com/seungmin956/toilet_project_lfs/raw/master/data/data.csv'
        df = pd.read_csv(url, encoding='utf-8')
        return df
    except Exception as e:
        st.error(f"데이터 로드 오류: {str(e)}")
        return pd.DataFrame()

merged_df1 = load_data()

def page1_hourly_analysis():
    """1페이지: 시간대별 화장실 대란 분석"""

    @st.cache_data
    def load_data():
        try:
            url = 'https://github.com/seungmin956/toilet_project_lfs/raw/master/data/data.csv'
            df = pd.read_csv(url, encoding='utf-8')
            return df
        except Exception as e:
            st.error(f"데이터 로드 오류: {str(e)}")
            return pd.DataFrame()
    
    merged_df1 = load_data()
    
    if merged_df1.empty:
        st.error("데이터를 불러올 수 없습니다.")
        return
    
    st.info("시간대/성별에 따른 화장실 수급 분석을 진행합니다.")
    
    # 사이드바에서 선택된 값들 가져오기
    if 'selected_regions' not in st.session_state:
        st.session_state.selected_regions = []
    if 'use_weights' not in st.session_state:
        st.session_state.use_weights = True

    selected_regions = st.session_state.selected_regions
    use_weights = st.session_state.use_weights
    
    # 데이터 필터링
    if selected_regions:
        filtered_data = merged_df1[merged_df1['행정동_동'].isin(selected_regions)]
        region_text = f" ({len(selected_regions)}개 선택 지역: {', '.join(selected_regions[:3])}{'...' if len(selected_regions) > 3 else ''})"
    else:
        filtered_data = merged_df1
        region_text = " (전체 지역)"
    
    # 시간대별 집계 계산
    @st.cache_data(ttl=300) 
    def calculate_hourly_summary(data, apply_weights=True):
        """시간대별 요약 통계 계산"""
        data_hash = str(data.shape) + str(data.columns.tolist())

        # 시간대별 가중치 정의
        demand_weights = {
            0: 0.3, 1: 0.2, 2: 0.2, 3: 0.2, 4: 0.3, 5: 0.5,
            6: 0.8, 7: 1.5, 8: 1.8, 9: 1.5, 10: 1.0, 11: 1.1,
            12: 1.4, 13: 1.3, 14: 1.1, 15: 1.0, 16: 1.1, 17: 1.3,
            18: 1.6, 19: 1.4, 20: 1.2, 21: 1.0, 22: 0.8, 23: 0.5
        }
        
        hourly_summary = data.groupby('시간대구분').agg({
            '총인구수': 'sum',
            '남성인구수': 'sum', 
            '여성인구수': 'sum',
            '전체_총칸수': 'sum',
            '남성_총칸수': 'sum',
            '여성_총칸수': 'sum',
            '번호': 'count'
        }).reset_index()
        
        # 기본 수급 비율
        hourly_summary['기본_수급비율'] = (hourly_summary['전체_총칸수'] / hourly_summary['총인구수'] * 1000).round(3)
        hourly_summary['기본_남성비율'] = (hourly_summary['남성_총칸수'] / hourly_summary['남성인구수'] * 1000).round(3)
        hourly_summary['기본_여성비율'] = (hourly_summary['여성_총칸수'] / hourly_summary['여성인구수'] * 1000).round(3)
        
        if apply_weights:
            # 가중치 적용 수급 비율
            hourly_summary['수요_가중치'] = hourly_summary['시간대구분'].map(demand_weights)
            hourly_summary['가중_수급비율'] = (hourly_summary['전체_총칸수'] / 
                                          (hourly_summary['총인구수'] * hourly_summary['수요_가중치']) * 1000).round(3)
            hourly_summary['가중_남성비율'] = (hourly_summary['남성_총칸수'] / 
                                          (hourly_summary['남성인구수'] * hourly_summary['수요_가중치']) * 1000).round(3)
            hourly_summary['가중_여성비율'] = (hourly_summary['여성_총칸수'] / 
                                          (hourly_summary['여성인구수'] * hourly_summary['수요_가중치']) * 1000).round(3)
        
        # 위기 지수 계산
        if apply_weights:
            hourly_summary['위기지수'] = ((hourly_summary['총인구수'] * hourly_summary['수요_가중치'] - hourly_summary['전체_총칸수']) / 
                                     hourly_summary['전체_총칸수'] * 100).clip(lower=0).round(1)
        else:
            hourly_summary['위기지수'] = 0
        
        # 성별 격차
        if apply_weights:
            hourly_summary['성별_격차'] = (hourly_summary['가중_남성비율'] - hourly_summary['가중_여성비율']).round(3)
        else:
            hourly_summary['성별_격차'] = (hourly_summary['기본_남성비율'] - hourly_summary['기본_여성비율']).round(3)
        
        return hourly_summary
    
    # 데이터 계산
    hourly_data = calculate_hourly_summary(filtered_data, use_weights)
    
    # 상단 지표 카드들
    col1, col2, col3= st.columns(3)
    
    with col1:
        if use_weights:
            worst_hour = hourly_data.loc[hourly_data['가중_수급비율'].idxmin()]
            st.metric(
                "🚨 최악 수급 시간",
                f"{int(worst_hour['시간대구분'])}시",
                f"{worst_hour['가중_수급비율']:.2f}칸/1000명"
            )
        else:
            worst_hour = hourly_data.loc[hourly_data['기본_수급비율'].idxmin()]
            st.metric(
                "🚨 최악 수급 시간",
                f"{int(worst_hour['시간대구분'])}시",
                f"{worst_hour['기본_수급비율']:.2f}칸/1000명"
            )
    
    with col2:
        max_population = hourly_data.loc[hourly_data['총인구수'].idxmax()]
        st.metric(
            "🔥 최대 인구 집중",
            f"{int(max_population['시간대구분'])}시",
            f"{int(max_population['총인구수']):,}명"
        )
    
    with col3:
        if use_weights:
            avg_supply = hourly_data['가중_수급비율'].mean()
        else:
            avg_supply = hourly_data['기본_수급비율'].mean()
        st.metric(
            "📊 평균 수급 비율",
            f"{avg_supply:.2f}",
            "칸/1000명"
        )
    
    # 메인 차트 영역
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        # 기본 vs 가중치 비교 차트
        fig_supply = go.Figure()
        
        # 기본 수급 비율
        fig_supply.add_trace(go.Scatter(
            x=hourly_data['시간대구분'],
            y=hourly_data['기본_수급비율'],
            mode='lines+markers',
            name='기본 수급 비율',
            line=dict(color='lightblue', width=2),
            marker=dict(size=6)
        ))
        
        if use_weights:
            # 가중치 적용 수급 비율
            fig_supply.add_trace(go.Scatter(
                x=hourly_data['시간대구분'],
                y=hourly_data['가중_수급비율'],
                mode='lines+markers',
                name='가중치 적용 수급 비율',
                line=dict(color='red', width=3),
                marker=dict(size=8)
            ))
        
        fig_supply.update_layout(
            title="시간대별 화장실 수급 비율 변화",
            xaxis_title="시간대",
            yaxis_title="1000명당 화장실 칸수",
            hovermode='x unified',
            height=400
        )
        
        st.plotly_chart(fig_supply, use_container_width=True)
        
    
    # 우측 컬럼: 위기 시간대 및 통계
    with col_right:
        # 성별 수급 비교 차트
        fig_gender = go.Figure()
        
        if use_weights:
            male_data = hourly_data['가중_남성비율']
            female_data = hourly_data['가중_여성비율']
            title_suffix = "(가중치 적용)"
        else:
            male_data = hourly_data['기본_남성비율']
            female_data = hourly_data['기본_여성비율']
            title_suffix = "(기본)"
        
        fig_gender.add_trace(go.Scatter(
            x=hourly_data['시간대구분'],
            y=male_data,
            mode='lines+markers',
            name='남성',
            line=dict(color='blue', width=2),
            marker=dict(size=6)
        ))
        
        fig_gender.add_trace(go.Scatter(
            x=hourly_data['시간대구분'],
            y=female_data,
            mode='lines+markers',
            name='여성',
            line=dict(color='pink', width=2),
            marker=dict(size=6)
        ))
        
        fig_gender.update_layout(
            title=f"성별 화장실 수급 비교 {title_suffix}",
            xaxis_title="시간대",
            yaxis_title="1000명당 화장실 칸수",
            hovermode='x unified',
            height=400
        )
        
        st.plotly_chart(fig_gender, use_container_width=True)

    
    # 인사이트 요약
    st.subheader("💡 주요 인사이트")

    # 컨테이너로 박스 효과 생성
    with st.container():
        # CSS 스타일 적용
        st.markdown("""
        <style>
        .insight-box {
            background-color: #f0f2f6;
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #1f77b4;
            margin: 10px 0;
        }
        .pattern-box {
            background-color: #fff3cd;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #ffc107;
            margin-bottom: 15px;
        }
        .suggestion-box {
            background-color: #d1ecf1;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #17a2b8;
            margin-bottom: 15px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 발견된 패턴 박스
            st.markdown('<div class="pattern-box">', unsafe_allow_html=True)
            st.markdown("**🔍 발견된 패턴**")
            
            # 동적 인사이트 생성
            if use_weights:
                peak_hours = hourly_data[hourly_data['가중_수급비율'] < 1.0]['시간대구분'].tolist()
                crisis_hours = hourly_data[hourly_data['위기지수'] > 20]['시간대구분'].tolist()
            else:
                peak_hours = hourly_data[hourly_data['기본_수급비율'] < 1.0]['시간대구분'].tolist()
                crisis_hours = []
            
            insights = []
            
            if peak_hours:
                if any(h in [7, 8, 9] for h in peak_hours):
                    insights.append(" 출근 시간대(7-9시)에 화장실 부족 심각")
                if any(h in [18, 19, 20] for h in peak_hours):
                    insights.append(" 퇴근 시간대(18-20시)에 화장실 수급 문제")
                if any(h in [12, 13] for h in peak_hours):
                    insights.append(" 점심 시간대(12-13시) 화장실 대기 예상")
            
            if crisis_hours:
                insights.append(f" {len(crisis_hours)}개 시간대에서 위기 상황 발생")
            
            if not insights:
                insights.append("✅ 전체적으로 안정적인 화장실 수급 상태")
            
            for insight in insights:
                st.markdown(f"• {insight}")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            # 개선 제안 박스
            st.markdown('<div class="suggestion-box">', unsafe_allow_html=True)
            st.markdown("**🎯 개선 제안**")
            
            suggestions = []
            
            max_gap = hourly_data['성별_격차'].max()
            if max_gap > 0.5:
                gap_hour = int(hourly_data.loc[hourly_data['성별_격차'].idxmax(), '시간대구분'])
                suggestions.append(f" {gap_hour}시 여성 화장실 확충 우선")
            
            if len(peak_hours) > 5:
                suggestions.append(" 시간대별 차등 화장실 운영 고려")
                suggestions.append(" 임시 화장실 설치 검토")
            
            if not suggestions:
                suggestions.append(" 현재 수급 상태 유지 관리")
                suggestions.append(" 정기적 모니터링 지속")
            
            for suggestion in suggestions:
                st.markdown(f"• {suggestion}")
            
            st.markdown('</div>', unsafe_allow_html=True)
