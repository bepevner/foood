import math
import uuid
import pandas as pd
import streamlit as st

st.set_page_config(page_title="한 접시 원가 계산기", page_icon="🍽️", layout="wide")
st.title("🍽️ 한 접시 원가 계산기")
st.caption("식재료 구매 비용과 1인분 사용량으로 메뉴의 재료비를 계산하세요.")

UNIT_OPTIONS = ["g", "kg", "mL", "L", "개", "장", "마리", "봉", "팩", "병", "캔", "회분"]

initial = pd.DataFrame([
    {"재료명": "쌀", "단위": "g", "구매 가격(원)": 30000.0, "구매량": 10000.0, "1인분 사용량": 100.0, "수율(%)": 100.0},
    {"재료명": "김치", "단위": "g", "구매 가격(원)": 10000.0, "구매량": 1000.0, "1인분 사용량": 100.0, "수율(%)": 100.0},
    {"재료명": "달걀", "단위": "개", "구매 가격(원)": 9000.0, "구매량": 30.0, "1인분 사용량": 1.0, "수율(%)": 100.0},
    {"재료명": "기름·양념", "단위": "회분", "구매 가격(원)": 900.0, "구매량": 1.0, "1인분 사용량": 1.0, "수율(%)": 100.0},
])
if "menus" not in st.session_state:
    st.session_state.menus = {"sample": {"name": "김치볶음밥", "price": 8000, "target": 30.0, "extra": 0, "rows": initial.to_dict("records")}}
    st.session_state.active_menu = "sample"
def delete_selected_menu():
    ident = st.session_state.get("active_menu")
    if ident not in st.session_state.menus:
        return
    if not st.session_state.get(f"confirm_delete_{ident}", False):
        return
    del st.session_state.menus[ident]
    for prefix in ("name", "price", "target", "extra", "ingredients", "confirm_delete"):
        st.session_state.pop(f"{prefix}_{ident}", None)
    if st.session_state.menus:
        st.session_state.active_menu = next(iter(st.session_state.menus))
    else:
        st.session_state.pop("active_menu", None)
    st.session_state["delete_notice"] = "선택한 메뉴를 삭제했습니다."

with st.sidebar:
    st.header("📋 메뉴 관리")
    if "delete_notice" in st.session_state:
        st.success(st.session_state.pop("delete_notice"))
    with st.form("add_menu", clear_on_submit=True):
        new_name = st.text_input("추가할 메뉴 이름", placeholder="예: 제육덮밥")
        add = st.form_submit_button("＋ 메뉴 추가")
    if add:
        if not new_name.strip():
            st.warning("메뉴 이름을 입력하세요.")
        else:
            ident = uuid.uuid4().hex
            st.session_state.menus[ident] = {"name": new_name.strip(), "price": 8000, "target": 30.0, "extra": 0, "rows": []}
            st.session_state.active_menu = ident
            st.rerun()
    if st.session_state.menus:
        st.selectbox("편집할 메뉴", list(st.session_state.menus), key="active_menu",
                     format_func=lambda k: st.session_state.menus[k]["name"])
        selected = st.session_state.active_menu
        st.divider()
        st.checkbox(
            f"‘{st.session_state.menus[selected]['name']}’ 메뉴와 재료를 삭제합니다 (복구 불가)",
            key=f"confirm_delete_{selected}",
        )
        st.button("🗑️ 선택 메뉴 삭제", on_click=delete_selected_menu,
                  disabled=not st.session_state.get(f"confirm_delete_{selected}", False))
    st.caption("메뉴별 입력은 현재 접속 세션에서 유지됩니다. 새로고침·서버 재시작에 대비해 결과 CSV를 저장하세요.")
if not st.session_state.menus:
    st.info("등록된 메뉴가 없습니다. 왼쪽 메뉴 관리에서 새 메뉴를 추가하세요.")
    st.stop()
ident = st.session_state.active_menu
current = st.session_state.menus[ident]
menu = st.text_input("메뉴 이름", current["name"], key=f"name_{ident}")
a, b = st.columns(2)
price = a.number_input("메뉴 판매가 (원)", min_value=0, value=current["price"], step=100, key=f"price_{ident}")
target = b.number_input("목표 원가율 (%)", min_value=0.1, max_value=100.0, value=current["target"], step=0.5, key=f"target_{ident}")
st.subheader("1. 재료 입력")
st.info("단위 칸을 클릭하면 목록에서 선택할 수 있습니다. 구매량과 1인분 사용량은 선택한 동일 단위로 입력하세요. 예: kg 선택 시 구매량 1, 사용량 0.1. 단위 변경 시 숫자는 자동 환산되지 않습니다. 손질 후 사용 가능 비율은 수율에 입력하세요.")
# Each editor has a stable baseline and a separate key per menu.
editor_initial = pd.DataFrame(current["rows"], columns=initial.columns)
rows = st.data_editor(editor_initial, key=f"ingredients_{ident}", num_rows="dynamic", hide_index=True, use_container_width=True,
    column_config={
        "단위": st.column_config.SelectboxColumn(
            "단위", options=UNIT_OPTIONS, required=True, default="g",
            help="구매량과 1인분 사용량 모두 선택한 단위로 입력하세요. 단위를 바꿔도 숫자는 자동 환산되지 않습니다.",
        ),
        "구매 가격(원)":  st.column_config.NumberColumn(min_value=0.0),
        "구매량": st.column_config.NumberColumn(min_value=0.001),
        "1인분 사용량": st.column_config.NumberColumn(min_value=0.0),
        "수율(%)": st.column_config.NumberColumn(min_value=0.1, max_value=100.0),
    })
extra = st.number_input("1인분당 추가 직접비 (포장 용기 등, 원)", min_value=0, value=current["extra"], step=10, key=f"extra_{ident}")

current.update(name=menu.strip() or "이름 없는 메뉴", price=price, target=target, extra=extra)
current["latest_rows"] = rows.to_dict("records")
current.pop("summary", None)
results, errors = [], []
for i, row in rows.iterrows():
    name = row.get("재료명")
    if pd.isna(name) or not str(name).strip():
        errors.append(f"{i+1}행: 재료명을 입력하거나 빈 행을 삭제하세요.")
        continue
    if row.get("단위") not in UNIT_OPTIONS:
        errors.append(f"{i+1}행 ({name}): 목록에서 단위를 선택하세요.")
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
current["summary"] = summary.iloc[0].to_dict()
st.subheader("3. 등록 메뉴 비교")
all_summaries = [m["summary"] for m in st.session_state.menus.values() if "summary" in m]
comparison = pd.DataFrame(all_summaries)
st.dataframe(comparison.round(2), hide_index=True, use_container_width=True)
st.caption("유효한 재료 입력이 완료된 메뉴만 표시됩니다. 새 메뉴는 재료를 입력하면 비교표에 나타납니다.")
st.download_button("전체 메뉴 비교 CSV 저장", comparison.to_csv(index=False).encode("utf-8-sig"), "all_menu_costs.csv", "text/csv")
st.download_button("계산 결과 CSV 저장", summary.to_csv(index=False).encode("utf-8-sig"), "menu_cost.csv", "text/csv")
with st.expander("계산식과 입력 기준"):
    st.markdown("""- **재료별 원가** = 구매 가격 ÷ (구매량 × 수율 ÷ 100) × 1인분 사용량
- **식재료 원가율** = 1인분 식재료비 ÷ 판매가 × 100
- **목표 판매가** = 1인분 식재료비 ÷ (목표 원가율 ÷ 100)
- 사용량은 손질 후 실제 사용하는 양으로 입력합니다. 손실이 없다면 수율 100%를 사용합니다.
- 구매 가격과 판매가는 부가세 포함 여부를 일관되게 입력하세요. 세무용 계산기는 아닙니다.
- 입력값은 서버 파일로 저장하지 않습니다. 새로고침하면 초기화될 수 있으니 CSV를 저장하세요.
""")
