import json
import time
import streamlit as st


def theme():
    from atelier import style
    style()


def remember_login(cloud, jar, remember, email):
    if remember:
        jar['session']=json.dumps({'refresh':st.session_state.auth['refresh'],
                                  'email':email,'until':time.time()+7*86400})
        jar.save()
    else:
        cloud.forget(jar)


def screen(cloud, jar):
    _, main, _ = st.columns([1,5,1])
    with main:
        st.markdown('''<div class="auth-hero"><small>MISE / PRIVATE WORKSPACE</small>
        <h2>좋은 메뉴의 시작,<br>정확한 한 접시.</h2>
        <p>재료비 계산부터 메뉴 관리까지 한곳에서 시작하세요.</p></div>''',unsafe_allow_html=True)
        mode=st.radio('계정 메뉴',['로그인','회원가입','비밀번호 찾기'],horizontal=True,label_visibility='collapsed')
        if mode=='로그인':
            with st.form('sign_in',clear_on_submit=True):
                st.subheader('다시 만나 반가워요')
                email=st.text_input('이메일 아이디',placeholder='you@example.com')
                password=st.text_input('비밀번호',type='password')
                remember=st.checkbox('이 기기에서 7일 동안 로그인 유지')
                submit=st.form_submit_button('로그인',use_container_width=True)
            if submit:
                if not email.strip() or not password:
                    st.error('이메일과 비밀번호를 입력하세요.')
                else:
                    try:
                        cloud.login(email.strip(),password)
                        remember_login(cloud,jar,remember,email.strip())
                        st.rerun()
                    except cloud.CloudError as e:st.error(str(e))
        elif mode=='회원가입':
            with st.form('sign_up',clear_on_submit=True):
                st.subheader('우리 가게의 첫 시작')
                email=st.text_input('이메일 아이디',placeholder='실제로 사용하는 이메일')
                password=st.text_input('비밀번호',type='password',help='6자 이상. 프로젝트의 비밀번호 정책이 추가로 적용됩니다.')
                repeat=st.text_input('비밀번호 확인',type='password')
                remember=st.checkbox('이 기기에서 7일 동안 로그인 유지')
                st.caption('입력한 이메일이 로그인 아이디입니다. 공용 기기에서는 로그인 유지를 선택하지 마세요.')
                submit=st.form_submit_button('회원가입하고 시작하기',use_container_width=True)
            if submit:
                if '@' not in email.strip() or len(password)<6:
                    st.error('올바른 이메일과 6자 이상의 비밀번호를 입력하세요.')
                elif password!=repeat:st.error('비밀번호 확인이 일치하지 않습니다.')
                else:
                    try:
                        cloud.login(email.strip(),password,signup=True)
                        remember_login(cloud,jar,remember,email.strip())
                        st.rerun()
                    except cloud.CloudError as e:st.error(str(e))
        elif mode=='비밀번호 찾기':
            with st.form('reset_password',clear_on_submit=True):
                st.subheader('비밀번호를 잊으셨나요?')
                st.caption('기존 비밀번호를 보여주는 대신, 이메일로 재설정 링크를 보내드립니다.')
                email=st.text_input('가입한 이메일',placeholder='you@example.com')
                submit=st.form_submit_button('재설정 메일 요청',use_container_width=True)
            if submit:
                if '@' not in email.strip():st.error('올바른 이메일 주소를 입력하세요.')
                else:
                    try:
                        key,_=cloud.config()
                        cloud.call('POST','https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode',
                                   params={'key':key},json={'requestType':'PASSWORD_RESET','email':email.strip()})
                        st.success('해당 이메일이 등록되어 있고 발송 가능한 경우 재설정 메일이 전송됩니다. 받은편지함과 스팸함을 확인하세요.')
                    except cloud.CloudError:
                        st.info('메일을 요청할 수 없습니다. 잠시 후 재시도하거나 Firebase 이메일 인증 설정을 확인하세요. 계정 존재 여부는 안내하지 않습니다.')
        st.caption('계정별 메뉴 분리 보관 · 비밀번호 원문 저장 안 함 · 공용 기기 사용 후 로그아웃')
