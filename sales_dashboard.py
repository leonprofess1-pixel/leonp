import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# pandas SettingWithCopyWarning 경고 무시 설정 (Streamlit 환경에서 loc 사용 시 발생하는 경고)
pd.options.mode.chained_assignment = None

# --- 1. 데이터 준비 및 보조 함수 ---

@st.cache_data
def load_data(file_path):
    """데이터를 로드하고 기본 전처리 수행"""
    # 파일 경로 수정 (사용자 환경에 맞게)
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        st.error(f"Error: 파일을 찾을 수 없습니다: {file_path}")
        return pd.DataFrame()
        
    # Attrition을 0/1로 변환
    df['Attrition_Numeric'] = df['Attrition'].apply(lambda x: 1 if x == 'Yes' else 0)
    
    # 연령 그룹화
    bins_age = [18, 30, 40, 50, 60]
    labels_age = ['20s', '30s', '40s', '50s+']
    df['Age_Group'] = pd.cut(df['Age'], bins=bins_age, labels=labels_age, right=False)
    
    # 근속 년수 그룹화
    bins_years = [-1, 2, 5, 10, df['YearsAtCompany'].max() + 1]
    labels_years = ['0-2 Years', '3-5 Years', '6-10 Years', '11+ Years']
    df['YearsAtCompany_Group'] = pd.cut(df['YearsAtCompany'], bins=bins_years, labels=labels_years, right=False)
    
    return df

def calculate_attrition_rate(df):
    """필터링된 데이터프레임의 이직률(%) 계산 (DataFrame 입력용)"""
    if df.empty or len(df) == 0:
        return 0.0
    attrition_rate = (df['Attrition_Numeric'].sum() / len(df)) * 100
    return attrition_rate

def create_rate_bar_chart(df, column, title):
    """특정 컬럼별 이직률 바 차트 생성"""
    if df.empty:
        return None
        
    attrition_summary = df.groupby(column, observed=False)['Attrition_Numeric'].agg(
        total='count',
        attrition_count='sum'
    ).reset_index()
    attrition_summary['Attrition Rate (%)'] = (attrition_summary['attrition_count'] / attrition_summary['total']) * 100

    fig = px.bar(
        attrition_summary.sort_values(by='Attrition Rate (%)', ascending=False),
        x=column,
        y='Attrition Rate (%)',
        color='Attrition Rate (%)',
        text='Attrition Rate (%)',
        color_continuous_scale=px.colors.sequential.Reds,
        title=f'<b>{title}</b>'
    )
    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig.update_layout(xaxis_title=column, yaxis_title="Attrition Rate (%)", uniformtext_minsize=8, uniformtext_mode='hide')
    return fig

# 데이터 로드 (파일 경로는 사용자가 마지막에 제시한 경로를 따름)
df = load_data('HR-employee-attrition/HR-Employee-Attrition.csv')

# 데이터가 비어있으면 Streamlit 실행 중단
if df.empty:
    st.stop()


# --- 2. 사이드바 (Sidebar) 필터 ---
st.set_page_config(layout="wide")
st.sidebar.title("sales 이직률 감소를 위한 분석 대시보드")

# 필터 옵션
all_departments = df['Department'].unique().tolist()
selected_departments = st.sidebar.multiselect(
    "부서 (Department)",
    options=all_departments,
    default=all_departments
)

all_job_roles = df[df['Department'].isin(selected_departments)]['JobRole'].unique().tolist()
selected_job_roles = st.sidebar.multiselect(
    "직무 (JobRole)",
    options=all_job_roles,
    default=all_job_roles
)

selected_gender = st.sidebar.radio(
    "성별 (Gender)",
    options=['All', 'Male', 'Female'],
    index=0
)

min_age, max_age = int(df['Age'].min()), int(df['Age'].max())
selected_age_range = st.sidebar.slider(
    "연령대 (Age Range)",
    min_value=min_age,
    max_value=max_age,
    value=(min_age, max_age)
)

# 데이터 필터링 적용 (전역 필터)
filtered_df = df[
    (df['Department'].isin(selected_departments)) &
    (df['JobRole'].isin(selected_job_roles)) &
    (df['Age'] >= selected_age_range[0]) &
    (df['Age'] <= selected_age_range[1])
]
if selected_gender != 'All':
    filtered_df = filtered_df[filtered_df['Gender'] == selected_gender]


# --- 3. 메인 화면 - 탭 구조 ---
tab1, tab2, tab3, tab4 = st.tabs(
    ["대시보드 요약", "상세 이직률 분석 (복합)", "이직 핵심 요인 분석 (히트맵)", "🎯 Sales팀 심층 분석 (15가지)"]
)

# --- Tab 1: 대시보드 요약 (Dashboard Summary) ---
with tab1:
    st.header("핵심 지표")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_employees = len(filtered_df)
    total_attrition_rate = calculate_attrition_rate(filtered_df)
    avg_job_satisfaction = filtered_df['JobSatisfaction'].mean() if not filtered_df.empty else 0
    avg_monthly_income = filtered_df['MonthlyIncome'].mean() if not filtered_df.empty else 0
    
    col1.metric("총 직원 수", f"{total_employees:,}")
    col2.metric("전체 이직률 (%)", f"{total_attrition_rate:.2f}%")
    col3.metric("평균 직무 만족도 (1-4)", f"{avg_job_satisfaction:.2f}")
    col4.metric("평균 월소득", f"${avg_monthly_income:,.0f}")
    
    st.markdown("---")
    
    st.header("전체 이직 현황")
    
    col_l, col_r = st.columns(2)
    
    with col_l:
        st.subheader("이직자/잔류자 비율")
        if not filtered_df.empty:
            fig_pie = px.pie(
                filtered_df, 
                names='Attrition', 
                title='<b>전체 이직자(Yes)/잔류자(No) 비율</b>',
                color_discrete_sequence=px.colors.sequential.RdBu
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.warning("필터링된 데이터가 없습니다.")

    with col_r:
        st.subheader("부서별 이직률")
        fig_dept_rate = create_rate_bar_chart(filtered_df, 'Department', '부서별 이직률')
        if fig_dept_rate:
            st.plotly_chart(fig_dept_rate, use_container_width=True)
        else:
            st.warning("필터링된 데이터가 없습니다.")

# --- Tab 2: 상세 이직률 분석 (Detailed Attrition Rate Analysis) - 복합 차트 강화 ---
with tab2:
    st.header("인구통계 및 직무 복합 분석")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("연봉-근속년수-직무만족도 복합 분석")
        if not filtered_df.empty:
            # 3가지 요소 복합: MonthlyIncome(Y), YearsAtCompany(X), JobSatisfaction(Color), Attrition(Symbol)
            
            # --- 수정된 부분: Attrition 기호 변경 ---
            symbol_map = {'Yes': 'x', 'No': 'circle'} # Yes는 x, No는 o(circle)로 표시
            # ------------------------------------
            
            fig_scatter = px.scatter(
                filtered_df,
                x='YearsAtCompany',
                y='MonthlyIncome',
                color='JobSatisfaction',  # 색상: 직무 만족도 (연속형)
                symbol='Attrition',      # 기호: 이직 여부
                symbol_map=symbol_map,   # 기호 매핑 적용
                hover_data=['Age', 'Department', 'JobRole'],
                title='<b>월소득, 근속년수, 직무만족도에 따른 이직 현황</b>',
                color_continuous_scale=px.colors.sequential.Viridis
            )
            fig_scatter.update_layout(height=500)
            st.plotly_chart(fig_scatter, use_container_width=True)
            st.caption("🔍 **저소득(Y축 하단), 단기 근속(X축 좌측), 낮은 직무 만족도(짙은 색상) 영역**에 'x' 기호(이직)가 집중되어 있습니다.")
        else:
            st.warning("필터링된 데이터가 없습니다.")
    
    with col_b:
        st.subheader("직무 등급 및 만족도별 이직률 (Treemap)")
        if not filtered_df.empty:
            # Treemap: JobLevel -> JobSatisfaction (색상: 이직률)
            df_treemap = filtered_df.groupby(['JobLevel', 'JobSatisfaction'], observed=False)['Attrition_Numeric'].agg(
                total='count',
                attrition_rate=lambda s: (s.sum() / len(s)) * 100 if len(s) > 0 else 0 
            ).reset_index()
            
            fig_treemap = px.treemap(
                df_treemap,
                path=['JobLevel', 'JobSatisfaction'],
                values='total',
                color='attrition_rate',
                color_continuous_scale='Reds', # 이직률이 높을수록 빨갛게
                title='<b>직무 등급(JobLevel) 및 만족도별 직원 수 (색상: 이직률)</b>'
            )
            st.plotly_chart(fig_treemap, use_container_width=True)
            st.caption("JobLevel 1이면서 JobSatisfaction이 1인 영역에서 이직률(색상)이 가장 높게 나타납니다.")
        else:
            st.warning("필터링된 데이터가 없습니다.")


# --- Tab 3: 이직 핵심 요인 분석 (Key Driver Analysis) - 히트맵 강화 ---
with tab3:
    st.header("주요 이직 유발 요인 상호작용 분석")
    
    # 1. 초과 근무 & 직무 만족도 히트맵
    st.subheader("1. 초과 근무(OverTime)와 직무 만족도(JobSatisfaction)의 이직률 히트맵")
    if not filtered_df.empty:
        # 3가지 요소 복합: OverTime(X), JobSatisfaction(Y), Attrition Rate(Color)
        
        # 1. 그룹별 이직률 계산
        df_heatmap = filtered_df.groupby(['OverTime', 'JobSatisfaction'], observed=False)['Attrition_Numeric'].agg(
            Attrition_Rate=lambda s: (s.sum() / len(s)) * 100 if len(s) > 0 else 0
        ).reset_index()
        
        # 2. 히트맵 생성
        fig_ot_js_heatmap = px.density_heatmap(
            df_heatmap,
            x='OverTime',
            y='JobSatisfaction',
            z='Attrition_Rate',
            histfunc='avg', # 실제로 Attrition_Rate 값을 색상으로 사용
            color_continuous_scale="Viridis",
            text_auto=True,
            title="<b>초과 근무(OT) 및 직무 만족도(JS)에 따른 평균 이직률 (%)</b>"
        )
        fig_ot_js_heatmap.update_layout(xaxis_title="OverTime", yaxis_title="JobSatisfaction")
        st.plotly_chart(fig_ot_js_heatmap, use_container_width=True)
        st.info("🚨 **초과 근무 'Yes' 그룹**은 직무 만족도와 관계없이 **전반적으로 이직률이 높습니다.** (특히 JS=1일 때 가장 위험)")
    else:
        st.warning("필터링된 데이터가 없습니다.")

    st.markdown("---")
    
    # 2. 월 소득과 이직의 관계 (Box Plot 유지)
    st.header("소득과 이직의 관계")
    if not filtered_df.empty:
        fig_income = px.box(
            filtered_df,
            x="Attrition",
            y="MonthlyIncome",
            color="Attrition",
            title="<b>이직 그룹(Yes/No)별 월소득 분포</b>",
            color_discrete_map={'Yes': 'red', 'No': 'green'}
        )
        st.plotly_chart(fig_income, use_container_width=True)
        st.caption("이직자 그룹(Yes)의 월소득 분포가 잔류자 그룹(No)보다 낮게 형성되어, 저소득층의 이직 경향이 뚜렷합니다.")
    else:
        st.warning("필터링된 데이터가 없습니다.")


# --- Tab 4: 🎯 Sales팀 심층 분석 (Sales Attrition Deep Dive) - 15가지 복합 요소 ---
with tab4:
    st.title("🎯 Sales팀 이직률 심층 분석: 15가지 핵심 요인")
    
    # Sales팀 데이터만 필터링 (필터링된 데이터 기준: filtered_df 사용)
    df_sales = filtered_df[filtered_df['Department'] == 'Sales']
    
    if df_sales.empty:
        # Sales 부서가 필터링되었거나, 필터링된 데이터가 없는 경우
        if 'Sales' not in selected_departments:
             st.error("사이드바에서 'Sales' 부서를 선택해야만 이 탭의 데이터가 표시됩니다.")
        else:
             st.error("현재 선택된 필터 조건(연령, 성별, 직무 등)에 해당하는 Sales 부서 데이터가 없습니다.")
    else:
        # A. Sales팀 핵심 지표 및 현황
        st.header("Sales팀 핵심 성과 지표")
        
        col1, col2, col3, col4 = st.columns(4)
        
        sales_total = len(df_sales)
        sales_attrition_rate = calculate_attrition_rate(df_sales)
        sales_avg_income = df_sales['MonthlyIncome'].mean()
        sales_avg_years = df_sales['YearsAtCompany'].mean()
        
        col1.metric("Sales팀 총 직원 수", f"{sales_total:,}")
        col2.metric("Sales팀 이직률 (%)", f"{sales_attrition_rate:.2f}%")
        col3.metric("평균 월소득", f"${sales_avg_income:,.0f}")
        col4.metric("평균 잔류 년수", f"{sales_avg_years:.1f}년")
        
        st.markdown("---")
        
        # B. Sales팀 이직에 영향을 미치는 15가지 핵심 요인 분석
        st.header("Sales팀 이직률에 영향을 미치는 15가지 복합 요인 분석")

        # 1. JobRole별 MonthlyIncome vs Attrition (산점도 + 3개 요소)
        st.subheader("1. JobRole, MonthlyIncome, Attrition 복합 분석")
        fig_scatter_sales = px.scatter(
            df_sales,
            x='MonthlyIncome',
            y='JobRole',
            color='Attrition', # 이직 여부
            symbol='JobLevel', # 직무 레벨 (기호)
            title='<b>Sales팀 JobRole별 Monthly Income 분포 및 이직 현황</b>',
            color_discrete_map={'Yes': 'red', 'No': 'blue'}
        )
        st.plotly_chart(fig_scatter_sales, use_container_width=True)
        st.caption("Sales Executive는 소득이 낮을수록 이직 위험이 높으며, 특히 Job Level 1 직무에서 이직이 집중됩니다.")

        # 2. 근속년수(YAC) vs 초과근무(OT) vs 이직률 (히트맵 + 3개 요소)
        st.subheader("2. 근속년수(YAC)와 초과근무(OT)에 따른 이직률 히트맵")
        df_yac_ot = df_sales.groupby(['YearsAtCompany_Group', 'OverTime'], observed=False)['Attrition_Numeric'].agg(
            Attrition_Rate=lambda s: (s.sum() / len(s)) * 100 if len(s) > 0 else 0
        ).reset_index()
        
        fig_yac_ot_heatmap = px.density_heatmap(
            df_yac_ot,
            x='YearsAtCompany_Group',
            y='OverTime',
            z='Attrition_Rate',
            histfunc='avg',
            color_continuous_scale="Reds",
            text_auto=True,
            title="<b>Sales팀 근속년수 그룹(YAC) 및 OverTime별 평균 이직률 (%)</b>"
        )
        st.plotly_chart(fig_yac_ot_heatmap, use_container_width=True)
        st.info("🚨 **0-2 Years & OverTime=Yes** 그룹이 가장 높은 이직률을 보입니다.")

        # 3. BusinessTravel vs WorkLifeBalance (WLB) vs 이직률 (히트맵 + 3개 요소)
        st.subheader("3. 출장 빈도(BT)와 WorkLifeBalance(WLB)에 따른 이직률 히트맵")
        df_bt_wlb = df_sales.groupby(['BusinessTravel', 'WorkLifeBalance'], observed=False)['Attrition_Numeric'].agg(
            Attrition_Rate=lambda s: (s.sum() / len(s)) * 100 if len(s) > 0 else 0
        ).reset_index()

        fig_bt_wlb_heatmap = px.density_heatmap(
            df_bt_wlb,
            x='BusinessTravel',
            y='WorkLifeBalance',
            z='Attrition_Rate',
            histfunc='avg',
            color_continuous_scale="Cividis",
            text_auto=True,
            title="<b>Sales팀 BusinessTravel 및 WorkLifeBalance별 평균 이직률 (%)</b>"
        )
        st.plotly_chart(fig_bt_wlb_heatmap, use_container_width=True)
        st.caption("출장이 잦고 WLB 점수가 낮은 (1 또는 2) 그룹의 이직률이 높습니다.")
        
        # 4. EnvironmentSatisfaction vs JobSatisfaction vs Attrition (산점도 + 3개 요소)
        st.subheader("4. 환경 만족도(ES) vs 직무 만족도(JS)에 따른 이직 현황")
        fig_es_js_scatter = px.scatter(
            df_sales,
            x='EnvironmentSatisfaction',
            y='JobSatisfaction',
            color='Attrition',
            size='MonthlyIncome', # 월 소득을 크기로 표시 (4가지 요소)
            hover_data=['Age', 'JobLevel'],
            title='<b>Sales팀 환경/직무 만족도 및 월소득에 따른 이직 현황</b>',
            color_discrete_map={'Yes': 'red', 'No': 'blue'}
        )
        st.plotly_chart(fig_es_js_scatter, use_container_width=True)
        st.caption("만족도 지수가 모두 낮은 (좌측 하단) 영역에 월소득(크기)이 작은 이직자(빨간색)가 집중되어 있습니다.")
        
        # 5. DistanceFromHome vs YearsSinceLastPromotion vs Attrition (버블 차트 + 3개 요소)
        st.subheader("5. 재택 거리(DFH)와 승진 후 년수(YSLP)에 따른 이직 현황")
        fig_dfh_yslp_bubble = px.scatter(
            df_sales,
            x='YearsSinceLastPromotion',
            y='DistanceFromHome',
            color='Attrition',
            size='YearsAtCompany', # 근속년수를 버블 크기로 표시 (4가지 요소)
            hover_data=['Age', 'MonthlyIncome'],
            title='<b>Sales팀 재택 거리, 승진 후 년수 및 근속년수에 따른 이직 현황</b>',
            color_discrete_map={'Yes': 'red', 'No': 'blue'}
        )
        st.plotly_chart(fig_dfh_yslp_bubble, use_container_width=True)
        st.caption("승진이 오래되었거나(X축 우측) 집이 먼(Y축 상단) 직원이 단기 근속(작은 버블)일 때 이직 위험이 높습니다.")


        # 6. ~ 15. 나머지 10가지 요소는 Bar Chart 형태로 제공 

        st.markdown("---")
        st.subheader("Sales팀 상세 단일 요인 분석 (이직률 바 차트 10가지)")

        factors = [
            'OverTime', 'BusinessTravel', 'JobSatisfaction', 'YearsAtCompany_Group', 
            'WorkLifeBalance', 'JobLevel', 'EducationField', 'RelationshipSatisfaction',
            'PerformanceRating', 'MaritalStatus'
        ]
        
        for i, factor in enumerate(factors):
            if i % 2 == 0:
                col_l, col_r = st.columns(2)
                current_col = col_l
            else:
                current_col = col_r
            
            with current_col:
                st.markdown(f"**{i+6}. {factor}별 이직률**")
                fig = create_rate_bar_chart(df_sales, factor, f'{factor} 그룹별 이직률')
                st.plotly_chart(fig, use_container_width=True)

        
        st.markdown("---")
        
        # C. Sales팀 맞춤형 분석 결론 및 제언
        st.header("🔑 Sales팀 맞춤형 분석 결론 및 제언")
        
        st.markdown(
            """
            ### **결론: Sales팀 이직의 주된 교차점 (복합 요약)**
            Sales 부서의 이직은 단순히 하나의 요인이 아닌, **다양한 만족도 지표(직무/환경)가 낮고, 초과 근무가 잦으며, 낮은 직무 등급(JobLevel 1, 2)에 속하는 저소득 직원**에게서 위험이 폭발적으로 증가하는 것으로 확인됩니다. 특히 **입사 2년 미만의 주니어 직원**은 워크로드와 보상의 불만족으로 인해 이탈 위험이 가장 높습니다.
            """
        )
        
        st.warning("### Sales팀 이직률 감소를 위한 특화된 3가지 제언")
        st.markdown(
            """
            1.  **💰 보상 경쟁력 확보 및 만족도 연계:** 월 소득 및 인센티브 구조를 재검토하고, 특히 **Job Level 1의 직원**과 **직무 만족도가 1 또는 2인 직원**에 대한 **즉각적인 보상 상향 조정 플랜**을 실행해야 합니다.
            2.  **📈 주니어 Fast-Track 경력 개발:** **'0-2 Years' 근속 그룹**을 위한 멘토링 프로그램 및 **Job Level Up 로드맵**을 의무화하고, 승진이 오래된 직원들을 위한 **'경력 전환' 기회**를 적극적으로 제공해야 합니다.
            3.  **⚖️ 초과 근무/출장/환경 개선:** **초과 근무(OverTime=Yes)**와 **잦은 출장(Travel_Frequently)** 그룹에 대해 **자동 휴식일 할당 시스템**을 도입하고, **EnvironmentSatisfaction**이 낮은 그룹을 대상으로 사무실 환경 개선(조명, 좌석 등) 설문조사를 실시해야 합니다.
            """
        )
