import copy
import json
import os
from pathlib import Path
import streamlit as st

DATA = Path(__file__).parent / 'data' / 'menus.json'
class CloudError(Exception):
    pass

def clean_menu(menu):
    clean = {k: menu[k] for k in ('name', 'price', 'target', 'extra')}
    clean['rows'] = copy.deepcopy(menu.get('latest_rows', menu.get('rows', [])))
    for row in clean['rows']:
        for key, value in list(row.items()):
            if isinstance(value, float) and not __import__('math').isfinite(value):
                row[key] = None
    return clean

def write_all(menus):
    try:
        DATA.parent.mkdir(parents=True, exist_ok=True)
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=DATA.parent, delete=False) as f:
            json.dump({k: clean_menu(v) for k,v in menus.items()}, f, ensure_ascii=False, allow_nan=False)
            temp = f.name
        os.replace(temp, DATA)
    except (OSError, ValueError, TypeError) as e:
        raise CloudError('파일 저장 실패: ' + str(e)) from e

def gate():
    if 'menus' not in st.session_state:
        try:
            st.session_state.menus = json.loads(DATA.read_text(encoding='utf-8')) if DATA.exists() else {}
        except (OSError, ValueError) as e:
            st.error('저장 파일을 읽지 못했습니다. 원본 파일을 확인하세요. ' + str(e))
            st.stop()
        if st.session_state.menus:
            st.session_state.active_menu = next(iter(st.session_state.menus))

def delete(ident):
    write_all({k:v for k,v in st.session_state.menus.items() if k != ident})

def autosave(ident, menu):
    payload = json.dumps({k:clean_menu(v) for k,v in st.session_state.menus.items()}, ensure_ascii=False, sort_keys=True)
    if st.session_state.get('_saved_payload') != payload:
        write_all(st.session_state.menus)
        st.session_state['_saved_payload'] = payload

def flush_pending():
    for ident, menu in st.session_state.get('menus', {}).items():
        for field in ('name', 'price', 'target', 'extra'):
            key = field + '_' + ident
            if key in st.session_state:
                menu[field] = st.session_state[key]
        delta = st.session_state.get('ingredients_' + ident)
        bases = st.session_state.get('_ingredient_bases', {})
        if isinstance(delta, dict) and ident in bases:
            rows = copy.deepcopy(bases[ident])
            for index, values in delta.get('edited_rows', {}).items():
                if int(index) < len(rows):
                    rows[int(index)].update(values)
            deleted = set(delta.get('deleted_rows', []))
            rows = [r for i,r in enumerate(rows) if i not in deleted]
            rows.extend(delta.get('added_rows', []))
            menu['latest_rows'] = rows
        autosave(ident, menu)


SETTING_DEFAULTS = {'rent':0, 'labor':0, 'utilities':0, 'other':0, 'monthly_units':0, 'fee_pct':0.0}
SETTINGS_FILE = DATA.parent / 'operating.json'

def get_settings():
    if 'operating_settings' not in st.session_state:
        try:
            values=json.loads(SETTINGS_FILE.read_text(encoding='utf-8')) if SETTINGS_FILE.exists() else {}
            merged={**SETTING_DEFAULTS, **values}
            import math
            for key in SETTING_DEFAULTS:
                if not isinstance(merged[key],(int,float)) or not math.isfinite(merged[key]) or merged[key]<0:
                    raise ValueError('잘못된 운영비 값')
            if merged['fee_pct']>100:raise ValueError('수수료 범위 오류')
            st.session_state.operating_settings=merged
        except (OSError,ValueError,TypeError) as e:
            raise CloudError('운영비 설정을 읽지 못했습니다: '+str(e)) from e
    return st.session_state.operating_settings

def save_settings(values):
    try:
        SETTINGS_FILE.parent.mkdir(parents=True,exist_ok=True)
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=SETTINGS_FILE.parent,delete=False) as f:
            json.dump(values,f,ensure_ascii=False,allow_nan=False)
            temp=f.name
        os.replace(temp,SETTINGS_FILE)
        st.session_state.operating_settings=dict(values)
    except (OSError,ValueError,TypeError) as e:
        raise CloudError('운영비 저장 실패: '+str(e)) from e

def operating_estimate(price, material, extra, settings):
    total=sum(settings[k] for k in ('rent','labor','utilities','other'))
    allocated=total/settings['monthly_units'] if settings['monthly_units']>0 else None
    fee=price*settings['fee_pct']/100
    remainder=price-material-extra-fee-allocated if allocated is not None else None
    return allocated,fee,remainder
