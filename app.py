import math
import pandas as pd
import streamlit as st

st.set_page_config(page_title="한 접시 원가 계산기", page_icon="🍽️", layout="wide")
st.title("🍽️ 한 접시 원가 계산기")
st.caption("식재료 구매 비용과 1인분 사용량으로 메뉴의 재료비를 계산하세요.")

menu = st.text_input("메뉴 이름", "김치볶음밥")
a, b = st.columns(2)
price = a.number_input("메뉴 판매가 (원)", min_value=0, value=8000, step=100)
target = b.number_input("목표 원가율 (%)", min_value=0.1, max_value=100.0, value=30.0, step=0.5)
st.subheader("1. 재료 입력")
st.info("구매량과 1인분 사용량은 같은 단위로 입력하세요. 예: 쌀 1kg 구매 → 구매량 1,000g. 손질 후 사용 가능 비율은 수율에 입력하세요.")
initial = pd.DataFrame([
    {"재료명": "쌀", "단위": "g", "구매 가격(원)": 30000.0, "구매량": 10000.0, "1인분 사용량": 100.0, "수율(%)": 100.0},
    {"재료명": "김치", "단위": "g", "구매 가격(원)": 10000.0, "구매량": 1000.0, "1인분 사용량": 100.0, "수율(%)": 100.0},
    {"재료명": "달걀", "단위": "개", "구매 가격(원)": 9000.0, "구매량": 30.0, "1인분 사용량": 1.0, "수율(%)": 100.0},
    {"재료명": "기름·양념", "단위": "회분", "구매 가격(원)": 900.0, "구매량": 1.0, "1인분 사용량": 1.0, "수율(%)": 100.0},
])
rows = st.data_editor(initial, num_rows="dynamic", hide_index=True, use_container_width=True,
    column_config={
        "구매 가격(원)": st.column_config.NumberColumn(min_value=0.0),
        "구매량": st.column_config.NumberColumn(min_value=0.001),
        "1인분 사용량": st.column_config.NumberColumn(min_value=0.0),
        "수율(%)": st.column_config.NumberColumn(min_value=0.1, max_value=100.0),
    })
extra = st.number_input("1인분당 추가 직접비 (포장 용기 등, 원)", min_value=0, value=0, step=10)

results, errors = [], []
for i, row in rows.iterrows():
    name = row.get("재료명")
    if pd.isna(name) or not str(name).strip():
        errors.append(f"{i+1}행: 재료명을 입력하거나 빈 행을 삭제하세요.")
        continue
    try:
        purchase, amount, used, yield_pct = [float(row[k]) for k in ["구매 가격(원)", "구매량", "1인분 사용량", "수율(%)"]]
        if not all(math.isfinite(v) for v in [purchase, amount, used, yield_pct]) or purchase < 0 or amount <= 0 or used < 0 or not 0 < yield_pct <= 100:
            raise ValueError
        cost = purchase / (amount * yield_pct / 100) * used
        results.append({"재료명": str(name), "1인분 재료비(원)": cost})
    except (TypeError, ValueError):
        errors.append(f"{i+1}행 ({name}): 가격·사용량은 0 이상, 구매량은 0 초과, 수율은 0 초과 100 이하로 입력하세요.")
if errors:
    for error in errors:
        st.error(error)
    st.stop()
if not results:
    st.warning("재료를 하나 이상 입력하세요.")
    st.stop()
material = sum(r["1인분 재료비(원)"] for r in results)
direct = material + extra
st.subheader("2. 계산 결과")
a, b, c = st.columns(3)
a.metric("1인분 식재료비", f"{material:,.0f}원")
b.metric("식재료 원가율", f"{material / price * 100:.2f}%" if price else "계산 불가")
c.metric("판매가 − 재료비 − 추가 직접비", f"{price - direct:,.0f}원")
st.caption("표시 금액은 반올림하며, 계산에는 반올림 전 값을 사용합니다. 위 차액은 순이익이 아닙니다. 인건비·임대료·공과금·플랫폼 수수료·세금 등은 반영하지 않았습니다.")
if not price:
    st.warning("판매가가 0원이어서 원가율을 계산할 수 없습니다.")
else:
    ratio = material / price * 100
    if ratio > target:
        st.warning(f"현재 식재료 원가율은 목표보다 {ratio-target:.2f}%p 높습니다.")
    else:
        st.success("현재 식재료 원가율이 설정한 목표 이하입니다.")
recommended = math.ceil((material / (target / 100)) / 100) * 100
st.metric("목표 식재료 원가율에 맞춘 판매가 (100원 단위 올림)", f"{recommended:,.0f}원")
st.caption("목표 판매가는 식재료비만을 기준으로 계산합니다. 추가 직접비 및 고정비는 포함하지 않으며, 목표 원가율 달성이 흑자를 보장하지 않습니다.")
st.dataframe(pd.DataFrame(results).round(2), hide_index=True, use_container_width=True)
summary = pd.DataFrame([{"메뉴명": menu, "판매가": price, "식재료비": material, "추가 직접비": extra, "식재료 원가율(%)": material / price * 100 if price else None, "직접비 차감 잔액": price-direct, "목표 원가율(%)": target, "목표 판매가": recommended}])
st.download_button("계산 결과 CSV 저장", summary.to_csv(index=False).encode("utf-8-sig"), "menu_cost.csv", "text/csv")
with st.expander("계산식과 입력 기준"):
    st.markdown("""- **재료별 원가** = 구매 가격 ÷ (구매량 × 수율 ÷ 100) × 1인분 사용량
- **식재료 원가율** = 1인분 식재료비 ÷ 판매가 × 100
- **목표 판매가** = 1인분 식재료비 ÷ (목표 원가율 ÷ 100)
- 사용량은 손질 후 실제 사용하는 양으로 입력합니다. 손실이 없다면 수율 100%를 사용합니다.
- 구매 가격과 판매가는 부가세 포함 여부를 일관되게 입력하세요. 세무용 계산기는 아닙니다.
- 입력값은 서버 파일로 저장하지 않습니다. 새로고침하면 초기화될 수 있으니 CSV를 저장하세요.
""")
