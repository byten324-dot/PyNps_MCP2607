import warnings
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc
import platform
import re
import streamlit as st


# =========================================================
# 한글 폰트 설정
# =========================================================
try:
    if platform.system() == 'Windows':
        font_name = font_manager.FontProperties(
            fname="c:/Windows/Fonts/malgun.ttf"
        ).get_name()
        rc('font', family=font_name)
    else:
        rc('font', family='AppleGothic')
except:
    pass

matplotlib.rcParams['axes.unicode_minus'] = False


# =========================================================
# 국민연금 데이터 클래스
# =========================================================
class pensionData:

    def __init__(self, filepath):
        warnings.simplefilter(
            action='ignore',
            category=pd.errors.DtypeWarning
        )

        self.df = pd.read_csv(
            filepath,
            encoding='cp949'
        )

        self.pattern1 = r'(\([^)]+\))'
        self.pattern2 = r'(\[[^\]]+\])'
        self.pattern3 = r'[^A-Za-z0-9가-힣]'

        self.preprocess()


    # =====================================================
    # 데이터 전처리
    # =====================================================
    def preprocess(self):

        # 사업장업종코드가 비어있는 행 제거
        mask = (
            self.df['사업장업종코드']
            .replace({r'^\s*$': pd.NA}, regex=True)
            .isna()
        )

        self.df = self.df.loc[~mask].copy()

        # 업종코드를 숫자로 변환
        self.df['사업장업종코드'] = pd.to_numeric(
            self.df['사업장업종코드'],
            errors='coerce'
        )

        self.df = self.df.dropna(
            subset=['사업장업종코드']
        ).copy()

        self.df['사업장업종코드'] = (
            self.df['사업장업종코드']
            .astype('int32')
        )


        # 컬럼명 재정의
        self.df.columns = [
            '자료생성년월',
            '사업장명',
            '사업자등록번호',
            '가입상태',
            '우편번호',
            '사업장지번상세주소',
            '주소',
            '고객법정동주소코드',
            '고객행정동주소코드',
            '시도코드',
            '시군구코드',
            '읍면동코드',
            '사업장형태구분코드 1 법인 2 개인',
            '업종코드',
            '업종코드명',
            '적용일자',
            '재등록일자',
            '탈퇴일자',
            '가입자수',
            '금액',
            '신규',
            '상실'
        ]


        # 불필요한 컬럼 삭제
        df = self.df.drop(
            [
                '자료생성년월',
                '우편번호',
                '사업장지번상세주소',
                '고객법정동주소코드',
                '고객행정동주소코드',
                '사업장형태구분코드 1 법인 2 개인',
                '적용일자',
                '재등록일자'
            ],
            axis=1
        ).copy()


        # 사업장명 정제
        df['사업장명'] = (
            df['사업장명']
            .fillna('')
            .apply(self.preprocessing)
        )


        # 날짜 처리
        탈퇴일자 = pd.to_datetime(
            df['탈퇴일자'],
            errors='coerce'
        )

        df['탈퇴일자_연도'] = 탈퇴일자.dt.year
        df['탈퇴일자_월'] = 탈퇴일자.dt.month


        # 주소에서 시도 추출
        df['시도'] = (
            df['주소']
            .fillna('')
            .str.split()
            .str[0]
        )


        # 현재 가입중인 기업만 남김
        df = (
            df.loc[df['가입상태'] == 1]
            .drop(
                ['가입상태', '탈퇴일자'],
                axis=1
            )
            .reset_index(drop=True)
        )


        # 숫자형 변환
        df['가입자수'] = pd.to_numeric(
            df['가입자수'],
            errors='coerce'
        )

        df['금액'] = pd.to_numeric(
            df['금액'],
            errors='coerce'
        )

        df['신규'] = pd.to_numeric(
            df['신규'],
            errors='coerce'
        ).fillna(0)

        df['상실'] = pd.to_numeric(
            df['상실'],
            errors='coerce'
        ).fillna(0)


        # 가입자수가 0이면 계산하지 않음
        df['인당금액'] = np.where(
            df['가입자수'] > 0,
            df['금액'] / df['가입자수'],
            np.nan
        )


        # 월급여 / 연봉 추정
        df['월급여추정'] = (
            df['인당금액'] / 9 * 100
        )

        df['연간급여추정'] = (
            df['월급여추정'] * 12
        )


        self.df = df


    # =====================================================
    # 사업장명 정제
    # =====================================================
    def preprocessing(self, x):

        x = str(x)

        x = re.sub(
            self.pattern1,
            '',
            x
        )

        x = re.sub(
            self.pattern2,
            '',
            x
        )

        x = re.sub(
            self.pattern3,
            ' ',
            x
        )

        x = re.sub(
            r' +',
            ' ',
            x
        )

        return x.strip()


    # =====================================================
    # 회사 검색
    # =====================================================
    def find_company(self, company_name):

        result = self.df.loc[
            self.df['사업장명'].str.contains(
                company_name,
                case=False,
                na=False,
                regex=False
            ),
            [
                '사업장명',
                '월급여추정',
                '연간급여추정',
                '업종코드',
                '가입자수'
            ]
        ]

        return result.sort_values(
            '가입자수',
            ascending=False
        )


    # =====================================================
    # 회사 상세정보
    # =====================================================
    def company_info(self, company_name):

        result = self.df.loc[
            self.df['사업장명'].str.contains(
                company_name,
                case=False,
                na=False,
                regex=False
            )
        ].sort_values(
            '가입자수',
            ascending=False
        )

        if result.empty:
            return None

        return result.iloc[0]


    # =====================================================
    # 동종업계 비교
    # =====================================================
    def compare_company(self, company_name):

        company = self.find_company(
            company_name
        )

        if company.empty:
            return None

        code = company['업종코드'].iloc[0]

        df1 = self.df.loc[
            self.df['업종코드'] == code,
            [
                '월급여추정',
                '연간급여추정'
            ]
        ].agg(
            [
                'mean',
                'count',
                'min',
                'max'
            ]
        )

        df1.columns = [
            '업종_월급여추정',
            '업종_연간급여추정'
        ]

        df1 = df1.T

        df1.columns = [
            '평균',
            '개수',
            '최소',
            '최대'
        ]

        df1.loc[
            '업종_월급여추정',
            company_name
        ] = company['월급여추정'].iloc[0]

        df1.loc[
            '업종_연간급여추정',
            company_name
        ] = company['연간급여추정'].iloc[0]

        return df1


# =========================================================
# CSV 주소
# =========================================================
file_path = r'https://www.dropbox.com/scl/fi/q05nabk8r0822dy8q1kew/_-_20251124.csv?rlkey=x3z852i71fwm60kc69rijiwno&st=cxcnw7rz&dl=1'


# =========================================================
# 데이터 불러오기
# =========================================================
@st.cache_resource
def read_pensionData():
    return pensionData(file_path)


data = read_pensionData()


# =========================================================
# Streamlit 화면
# =========================================================
st.title("국민연금 데이터 분석")

st.write(
    "회사명을 검색하면 국민연금 데이터를 기반으로 "
    "추정 급여와 사업장 정보를 확인할 수 있습니다."
)


company_name = st.text_input(
    "회사명을 입력해 주세요",
    placeholder="예: 삼성전자"
)


# =========================================================
# 검색 실행
# =========================================================
if company_name:

    output = data.find_company(
        company_name=company_name
    )


    # 검색 결과가 없을 때
    if output.empty:

        st.warning(
            "검색된 회사가 없습니다."
        )


    # 검색 결과가 있을 때
    else:

        # 가장 가입자수가 많은 회사
        selected = output.iloc[0]


        # 회사명
        st.subheader(
            selected['사업장명']
        )


        # 상세 정보 가져오기
        info = data.company_info(
            company_name=company_name
        )


        # 회사 기본정보
        st.markdown(
            f"""
            - 주소 : `{info['주소']}`
            - 업종코드명 : `{info['업종코드명']}`
            - 총 근무자 : `{int(info['가입자수']):,}` 명
            - 신규 입사자 : `{int(info['신규']):,}` 명
            - 퇴사자 : `{int(info['상실']):,}` 명
            """
        )


        # =================================================
        # 주요 지표
        # =================================================
        col1, col2, col3 = st.columns(3)


        col1.metric(
            "월급여 추정",
            f"{int(selected['월급여추정']):,} 원"
        )


        col2.metric(
            "연봉 추정",
            f"{int(selected['연간급여추정']):,} 원"
        )


        col3.metric(
            "가입자수",
            f"{int(selected['가입자수']):,} 명"
        )


        # =================================================
        # 검색 결과 전체
        # =================================================
        st.subheader(
            "검색 결과"
        )

        display_output = output.copy()

        display_output['월급여추정'] = (
            display_output['월급여추정']
            .round(0)
        )

        display_output['연간급여추정'] = (
            display_output['연간급여추정']
            .round(0)
        )

        st.dataframe(
            display_output,
            use_container_width=True
        )


        # =================================================
        # 동종업계 비교
        # =================================================
        st.subheader(
            "동종업계 급여 비교"
        )

        compare_result = data.compare_company(
            company_name
        )

        if compare_result is not None:

            compare_display = (
                compare_result.copy()
            )

            st.dataframe(
                compare_display,
                use_container_width=True
            )
        comp_output = data.compare_company(company_name=company_name)
        st.dataframe(comp_output.round(0), use_container_width=True)

        st.markdown(f'### 업종 평균 VS {company_name} 비교')
        # 검색은 회사의 '월급여추정'액과 업종평균을 비교
        percent_value = info['월급여추정'] / comp_output.iloc[0, 0] * 100 - 100
        diff_month = abs(comp_output.iloc[0, 0] - info['월급여추정'])  # 월급여추정 액의 차이
        diff_year = abs(comp_output.iloc[1, 0] - info['연간급여추정'])  # 연간급여추정 액의 차이
        upordown = '높은' if percent_value > 0 else '낮은'  # %값이 높은지 낮은지에 따른 문구 선택 
        # 위 결과로 아래에 markdown 으로 출력
        st.markdown(f"""
        - 업종 **평균 월급여**는 `{int(comp_output.iloc[0, 0]):,}` 원, **평균 연봉**은 `{int(comp_output.iloc[1, 0]):,}` 원 입니다.
        - `{company_name}`는 평균 보다 `{int(diff_month):,}` 원, :red[약 {percent_value:.2f} %] `{upordown}` `{int(info['월급여추정']):,}` 원을 **월 평균 급여**를 받는 것으로 추정합니다.
        - `{company_name}`는 평균 보다 `{int(diff_year):,}` 원 `{upordown}` `{int(info['연간급여추정']):,}` 원을 **연봉**을 받는 것으로 추정합니다.
        """)   


        fig, ax = plt.subplots(1, 2)

        p1 = ax[0].bar(x=["Average", "Your Company"], height=(comp_output.iloc[0, 0], info['월급여추정']), width=0.7)
        ax[0].bar_label(p1, fmt='%d')
        p1[0].set_color('black')
        p1[1].set_color('red')
        ax[0].set_title('Monthly Salary')

        p2 = ax[1].bar(x=["Average", "Your Company"], height=(comp_output.iloc[1, 0], info['연간급여추정']), width=0.7)
        p2[0].set_color('black')
        p2[1].set_color('red')
        ax[1].bar_label(p2, fmt='%d')
        ax[1].set_title('Yearly Salary')

        ax[0].tick_params(axis='both', which='major', labelsize=8, rotation=0)
        ax[0].tick_params(axis='both', which='minor', labelsize=6)
        ax[1].tick_params(axis='both', which='major', labelsize=8)
        ax[1].tick_params(axis='both', which='minor', labelsize=6)


        st.pyplot(fig)

        st.markdown('### 동종업계')
        df = data.get_data()
        st.dataframe(df.loc[df['업종코드'] == info['업종코드'], ['사업장명', '월급여추정', '연간급여추정', '가입자수']]\
            .sort_values('연간급여추정', ascending=False).head(10).round(0), 
            use_container_width=True
        )

        else:
        st.subheader('검색결과가 없습니다')











