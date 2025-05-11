import streamlit as st
import datetime
import pytz
import os

# 한국 시간 기준
kst = pytz.timezone("Asia/Seoul")
now_kst = datetime.datetime.now(kst)
today_kst = now_kst.date()
time_kst = now_kst.strftime("%H:%M")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.session_state.room_code = ""
    st.session_state.rooms = {}

if not st.session_state.logged_in:
    st.title("🔐 Toolbox Talk 로그인")
    role = st.radio("역할", ["관리자", "팀원"])
    name = st.text_input("이름")

    if role == "관리자":
        st.subheader("📁 회의방 생성")
        new_room_code = st.text_input("회의 코드 입력 (예: A팀-0511)")
        team_list = st.text_area("팀원 이름 입력 (쉼표로 구분)", "김강윤,이민우,박지현")
        if st.button("회의방 생성") and new_room_code and team_list:
            st.session_state.rooms[new_room_code] = {
                "admin": name,
                "members": [n.strip() for n in team_list.split(",")],
                "attendees": [],
                "confirmations": [],
                "discussion": [],
                "tasks": [],
                "info": {},
                "additional": ""
            }
            st.session_state.room_code = new_room_code
            st.session_state.username = name
            st.session_state.role = role
            st.session_state.logged_in = True
    else:
        st.subheader("🧑‍🤝‍🧑 회의방 입장")
        room_code = st.text_input("참여할 회의 코드 입력")
        if st.button("입장") and name and room_code:
            if room_code in st.session_state.rooms:
                if name in st.session_state.rooms[room_code]["members"]:
                    st.session_state.room_code = room_code
                    st.session_state.username = name
                    st.session_state.role = role
                    st.session_state.logged_in = True
                else:
                    st.warning("등록되지 않은 팀원입니다.")
            else:
                st.error("해당 회의 코드가 존재하지 않습니다.")
    st.stop()

# 회의방 메인
room_code = st.session_state.room_code
room = st.session_state.rooms[room_code]
user = st.session_state.username
is_admin = st.session_state.role == "관리자"

if user not in room["attendees"]:
    room["attendees"].append(user)

st.title(f"📋 Toolbox Talk 회의록 - [{room_code}]")

st.header("1️⃣ 회의 정보")
if is_admin:
    col1, col2 = st.columns(2)
    with col1:
        date = st.date_input("날짜", today_kst)
        place = st.text_input("장소", "현장 A")
    with col2:
        time = st.text_input("시간", time_kst)
        task = st.text_input("작업 내용", "고소작업")
    st.session_state.rooms[room_code]["info"] = {
        "date": str(date), "place": place, "time": time, "task": task
    }
else:
    info = room.get("info", {})
    st.markdown(f"- 날짜: {info.get('date', '')}")
    st.markdown(f"- 시간: {info.get('time', '')}")
    st.markdown(f"- 장소: {info.get('place', '')}")
    st.markdown(f"- 작업내용: {info.get('task', '')}")

st.header("2️⃣ 참석자 명단")
for name in room["attendees"]:
    st.markdown(f"- {name}")

st.header("3️⃣ 논의 내용")
if is_admin:
    risk = st.text_input("위험요소", key="risk_input")
    measure = st.text_input("안전대책", key="measure_input")
    if st.button("논의 내용 추가"):
        if risk and measure:
            st.session_state.rooms[room_code]["discussion"].append((risk, measure))
else:
    for idx, (r, m) in enumerate(room["discussion"]):
        st.markdown(f"**{idx+1}. 위험요소:** {r}  \\n➡️ **안전대책:** {m}")

st.header("4️⃣ 추가 논의 사항")
if is_admin:
    additional = st.text_area("추가 논의 사항", value=room.get("additional", ""))
    st.session_state.rooms[room_code]["additional"] = additional
else:
    st.markdown(room.get("additional", ""))

st.header("5️⃣ 결정사항 및 조치")
if is_admin:
    col1, col2, col3 = st.columns(3)
    person = col1.text_input("담당자", key="p_input")
    role = col2.text_input("업무/역할", key="r_input")
    due = col3.date_input("완료예정일", today_kst)
    if st.button("조치 추가"):
        if person and role:
            st.session_state.rooms[room_code]["tasks"].append((person, role, due))
else:
    for p, r, d in room["tasks"]:
        st.markdown(f"- **{p}**: {r} (완료일: {d})")

st.header("6️⃣ 회의록 확인 및 서명")
if user not in room["confirmations"]:
    if st.button("📥 회의 내용 확인"):
        st.session_state.rooms[room_code]["confirmations"].append(user)
        st.success(f"{user}님의 확인이 저장되었습니다.")
else:
    st.success(f"{user}님은 이미 확인하셨습니다.")

if is_admin:
    st.markdown(f"### ✅ 서명 현황: {len(room['confirmations'])} / {len(room['members'])}")
    for name in room["members"]:
        st.markdown(f"- {name} {'✅' if name in room['confirmations'] else '❌'}")

# Markdown 다운로드 대체
if is_admin:
    if st.button("📄 회의요약 Markdown 다운로드"):
        info = room.get("info", {})
        lines = [
            f"# 📋 Toolbox Talk 회의록 [{room_code}]",
            f"**날짜:** {info.get('date')}  |  **시간:** {info.get('time')}",
            f"**장소:** {info.get('place')}  |  **작업내용:** {info.get('task')}",
            f"**리더:** {room.get('admin')}",
            "",
            "## 참석자",
            ", ".join(room["attendees"]),
            "",
            "## 논의 내용"
        ]
        for idx, (r, m) in enumerate(room["discussion"]):
            lines.append(f"{idx+1}. 위험요소: {r} / 안전대책: {m}")
        lines += ["", "## 추가 논의 사항", room.get("additional", ""), "", "## 결정사항 및 조치"]
        for p, r, d in room["tasks"]:
            lines.append(f"- {p}: {r} (완료예정일: {d})")
        lines.append("")
        lines.append("## 확인자")
        for n in room["confirmations"]:
            lines.append(f"- {n} (확인 완료)")

        markdown_content = "\n".join(lines)
        st.download_button("📥 Markdown 저장", data=markdown_content, file_name=f"{room_code}_회의록.md")