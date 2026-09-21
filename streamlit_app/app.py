import os
import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:5000").rstrip("/")
st.set_page_config(page_title="AI Support Assistant", page_icon="🤖", layout="wide")

for key, default in {"token": None, "user": None, "last_result": None, "ticket_data": None}.items():
    st.session_state.setdefault(key, default)

def api(method, path, **kwargs):
    headers = kwargs.pop("headers", {})
    if st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    try:
        return requests.request(method, f"{API_BASE_URL}{path}", headers=headers, timeout=30, **kwargs)
    except requests.RequestException as exc:
        st.error(f"Backend communication failed: {exc}")
        return None

st.title("AI-Powered Customer Support & Operations Assistant")

if not st.session_state.token:
    login_tab, register_tab = st.tabs(["Login", "Register"])
    with login_tab:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
        if submitted:
            response = api("POST", "/api/auth/login", json={"email": email, "password": password})
            if response and response.ok:
                data = response.json()
                st.session_state.token = data["access_token"]
                st.session_state.user = data
                st.rerun()
            elif response:
                st.error(response.json().get("error", "Login failed"))
    with register_tab:
        with st.form("register_form"):
            name = st.text_input("Name")
            email = st.text_input("Registration Email")
            password = st.text_input("Password (10+ characters)", type="password")
            submitted = st.form_submit_button("Register")
        if submitted:
            response = api("POST", "/api/auth/register", json={"name": name, "email": email, "password": password})
            if response and response.ok:
                st.success("Registration successful. Log in above.")
            elif response:
                st.error(response.json().get("error", "Registration failed"))
    st.stop()

if st.sidebar.button("Logout"):
    st.session_state.token = None
    st.session_state.user = None
    st.session_state.last_result = None
    st.rerun()

st.sidebar.write(f"User ID: {st.session_state.user['user_id']}")
st.sidebar.write(f"Role: {st.session_state.user['role']}")

tab1, tab2, tab3 = st.tabs(["Submit Ticket", "Ticket Search", "Analytics"])

with tab1:
    with st.form("ticket_form"):
        message = st.text_area("Customer Message", height=180)
        submitted = st.form_submit_button("Analyze Ticket", type="primary")
    if submitted:
        if not message.strip():
            st.warning("Message is required.")
        else:
            response = api("POST", "/api/process-ticket", json={"message": message})
            if response and response.ok:
                st.session_state.last_result = response.json()
            elif response:
                st.error(response.json().get("error", "Request failed"))
    if st.session_state.last_result:
        data = st.session_state.last_result
        st.success(f"Ticket created: #{data['ticket_id']}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Category", data["prediction"]["category"])
        c2.metric("Priority", data["prediction"]["priority"])
        c3.metric("Human Review", "Yes" if data["prediction"]["human_review_required"] else "No")
        st.subheader("AI Response")
        st.write(data["ai_response"])

with tab2:
    with st.form("search_form"):
        ticket_id_text = st.text_input("Ticket ID")
        submitted = st.form_submit_button("Search Ticket")
    if submitted:
        if not ticket_id_text.isdigit():
            st.warning("Ticket ID must be an integer.")
        else:
            response = api("GET", f"/api/tickets/{int(ticket_id_text)}")
            if response and response.ok:
                st.session_state.ticket_data = response.json()
            elif response:
                st.error(response.json().get("error", "Ticket not found"))
    if st.session_state.ticket_data:
        data = st.session_state.ticket_data
        st.json(data)
        with st.form("feedback_form"):
            rating = st.slider("Rating", 1, 5, 5)
            comments = st.text_area("Comments")
            submitted = st.form_submit_button("Submit Feedback")
        if submitted:
            fb = api("POST", "/api/feedback", json={
                "ticket_id": data["ticket_id"], "rating": rating, "comments": comments
            })
            if fb and fb.ok:
                st.success("Feedback stored.")
            elif fb:
                st.error(fb.json().get("error", "Feedback failed"))

with tab3:
    if st.session_state.user["role"] != "admin":
        st.info("Analytics and the review queue are available to administrators.")
    else:
        if st.button("Refresh Analytics"):
            response = api("GET", "/api/analytics")
            if response and response.ok:
                data = response.json()
                cols = st.columns(5)
                cols[0].metric("Total Tickets", data["total_tickets"])
                cols[1].metric("Open", data["open_tickets"])
                cols[2].metric("Resolved", data["resolved_tickets"])
                cols[3].metric("Critical", data["critical_tickets"])
                cols[4].metric("AI Interactions", data["ai_interaction_count"])
                st.metric("Avg Feedback", data["average_feedback_rating"] if data["average_feedback_rating"] is not None else "N/A")
                st.bar_chart(data["tickets_by_category"])
                st.bar_chart(data["tickets_by_priority"])
        if st.button("Refresh Review Queue"):
            response = api("GET", "/api/review-queue")
            if response and response.ok:
                st.subheader("Human Review Queue")
                st.dataframe(response.json()["tickets"], use_container_width=True)
