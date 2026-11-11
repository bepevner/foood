import json
import time
from urllib.parse import quote
import requests
import streamlit as st
# Compatibility is limited to importing the legacy cookie package.
# Its cached encryption-engine factory uses allow_output_mutation=True.
if not hasattr(st, "cache"):
    def _legacy_cache(func=None, **kwargs):
        mutable = kwargs.pop("allow_output_mutation", False)
        kwargs.pop("suppress_st_warning", None)
        kwargs.pop("persist", None)
        decorator = st.cache_resource if mutable else st.cache_data
        return decorator(func, **kwargs) if func is not None else decorator(**kwargs)
    st.cache = _legacy_cache
    try:
        from streamlit_cookies_manager import EncryptedCookieManager
    finally:
        delattr(st, "cache")
else:
    from streamlit_cookies_manager import EncryptedCookieManager

class CloudError(Exception):
    pass

def config():
    try:
        c = st.secrets['firebase']
        return c['api_key'], c['project_id']
    except Exception:
        raise CloudError('Firebase 설정이 없습니다. 설정안내.md에 따라 Secrets를 등록하세요.') from None

def call(method, url, **kwargs):
    try:
        r = requests.request(method, url, timeout=20, **kwargs)
    except requests.RequestException:
        raise CloudError('네트워크 연결 실패. 입력을 유지한 채 다시 시도하세요.') from None
    if not r.ok:
        raise CloudError(f'Firebase 요청 실패 (HTTP {r.status_code}). 계정 정보, Firestore 규칙, 프로젝트 설정을 확인하세요.')
    return r.json() if r.content else {}

def login(email, password, signup=False):
    key, _ = config()
    action = 'signUp' if signup else 'signInWithPassword'
    d = call('POST', f'https://identitytoolkit.googleapis.com/v1/accounts:{action}',
             params={'key':key}, json={'email':email, 'password':password, 'returnSecureToken':True})
    st.session_state.auth = {'uid':d['localId'], 'token':d['idToken'], 'refresh':d['refreshToken'], 'expires':time.time()+int(d['expiresIn']), 'email':email}

def headers():
    a = st.session_state.auth
    if time.time() > a['expires']-60:
        key, _ = config()
        d = call('POST', 'https://securetoken.googleapis.com/v1/token', params={'key':key},
                 data={'grant_type':'refresh_token', 'refresh_token':a['refresh']})
        a.update(token=d['id_token'], refresh=d['refresh_token'], expires=time.time()+int(d['expires_in']))
    return {'Authorization':'Bearer '+a['token']}

def base():
    _, project = config()
    return f'https://firestore.googleapis.com/v1/projects/{quote(project, safe="")}/databases/(default)/documents/users/{quote(st.session_state.auth["uid"], safe="")}/menus'

def load():
    menus, page = {}, None
    while True:
        params = {'pageSize':100}
        if page: params['pageToken'] = page
        data = call('GET', base(), headers=headers(), params=params)
        for doc in data.get('documents', []):
            menus[doc['name'].rsplit('/',1)[-1]] = json.loads(doc['fields']['payload']['stringValue'])
        page = data.get('nextPageToken')
        if not page: return menus

def save(ident, menu):
    # Persist only the current menu; no whole-account overwrite or cross-user cache.
    clean = {k:menu[k] for k in ('name','price','target','extra')}
    clean['rows'] = menu.get('latest_rows',menu['rows'])
    # Pandas missing values are normalized before Firestore JSON serialization.
    for row in clean['rows']:
        for k,v in list(row.items()):
            if isinstance(v,float) and not __import__('math').isfinite(v): row[k]=None
    text=json.dumps(clean,ensure_ascii=False,allow_nan=False)
    call('PATCH',base()+'/'+quote(ident,safe=''),headers=headers(),json={'fields':{'payload':{'stringValue':text}}})

def delete(ident):
    call('DELETE',base()+'/'+quote(ident,safe=''),headers=headers())

def cookie_store():
    try:
        secret = st.secrets['login_cookie']['password']
        if len(secret) < 32:
            raise ValueError
    except Exception:
        st.error('Secrets에 [login_cookie] password를 32자 이상의 임의 문자열로 설정하세요. 로그인 유지 안내를 확인하세요.')
        st.stop()
    jar = EncryptedCookieManager(prefix='menu_cost_v6_', password=secret)
    if not jar.ready():
        st.stop()
    return jar

def forget(jar):
    if jar.get('session'):
        del jar['session']
        jar.save()

def restore(jar):
    raw = jar.get('session')
    if not raw:
        return
    try:
        payload = json.loads(raw)
        if time.time() >= payload['until']:
            forget(jar)
            return
        key, _ = config()
        d = call('POST', 'https://securetoken.googleapis.com/v1/token',
                 params={'key':key}, data={'grant_type':'refresh_token', 'refresh_token':payload['refresh']})
        st.session_state.auth = {
            'uid':d['user_id'], 'token':d['id_token'], 'refresh':d['refresh_token'],
            'expires':time.time()+int(d['expires_in']), 'email':payload.get('email','로그인됨')}
        payload['refresh'] = d['refresh_token']
        jar['session'] = json.dumps(payload)
        jar.save()
    except CloudError:
        st.warning('자동 로그인에 실패했습니다. 다시 로그인하거나 연결을 확인하세요.')
        forget(jar)
    except (ValueError, KeyError, TypeError):
        forget(jar)

def gate():
    jar = cookie_store()
    if 'auth' not in st.session_state and not st.session_state.get('_logged_out', False):
        restore(jar)
    if 'auth' not in st.session_state:
        import auth_ui
        auth_ui.screen(__import__(__name__), jar)
        st.stop()
    with st.sidebar:
        st.caption(st.session_state.auth['email'])
        if st.button('로그아웃', use_container_width=True):
            forget(jar)
            # Keep the cookie component alive long enough to flush deletion.
            for key in list(st.session_state):
                if key in ('auth', 'menus', 'active_menu', 'page') or key.startswith(('name_', 'price_', 'target_', 'extra_', 'ingredients_', 'confirm_delete_')):
                    del st.session_state[key]
            st.session_state['_logged_out'] = True
            import auth_ui
            auth_ui.screen(__import__(__name__), jar)
            st.stop()
    if 'menus' not in st.session_state:
        try:
            menus=load()
        except (CloudError,ValueError,KeyError) as e:
            st.error(str(e) if isinstance(e,CloudError) else '저장 데이터 형식을 확인할 수 없습니다. 관리자에게 문의하세요.')
            st.button('불러오기 다시 시도')
            st.stop()
        st.session_state.menus=menus
        if menus: st.session_state.active_menu=next(iter(menus))
