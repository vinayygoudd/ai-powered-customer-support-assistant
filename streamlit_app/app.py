import os
import requests
import streamlit as st


# ============================================================
# CONFIGURATION
# ============================================================

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:5000"
).rstrip("/")

st.set_page_config(
    page_title="AI Support Assistant",
    page_icon="🤖",
    layout="wide",
)


# ============================================================
# SESSION STATE
# ============================================================

DEFAULT_SESSION_STATE = {
    "token": None,
    "user": None,
    "last_result": None,
    "ticket_data": None,
}

for key, default in DEFAULT_SESSION_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ============================================================
# API HELPER
# ============================================================

def api(method, path, **kwargs):
    """
    Send a request to the Flask backend.

    Automatically attaches the JWT access token when logged in.
    """

    headers = kwargs.pop("headers", {}).copy()

    if st.session_state.get("token"):
        headers["Authorization"] = (
            f"Bearer {st.session_state.token}"
        )

    url = f"{API_BASE_URL}{path}"

    try:
        response = requests.request(
            method,
            url,
            headers=headers,
            timeout=60,
            **kwargs,
        )

        return response

    except requests.RequestException as exc:
        st.error(
            f"Backend communication failed.\n\n"
            f"Backend: `{API_BASE_URL}`\n\n"
            f"Error: `{exc}`"
        )
        return None


def response_error(response, default_message="Request failed"):
    """
    Safely extract an API error message.
    """

    if response is None:
        return default_message

    try:
        data = response.json()

        if isinstance(data, dict):
            return data.get("error") or data.get("message") or default_message

        return str(data)

    except ValueError:
        if response.text:
            return response.text

        return default_message


# ============================================================
# LOGIN / REGISTER
# ============================================================

if not st.session_state.get("token"):

    st.title("🤖 AI-Powered Customer Support & Operations Assistant")

    st.caption(
        "AI-assisted customer support, ticket classification, "
        "priority prediction and operations management."
    )

    login_tab, register_tab = st.tabs(
        ["🔐 Login", "📝 Register"]
    )

    # --------------------------------------------------------
    # LOGIN
    # --------------------------------------------------------

    with login_tab:

        st.subheader("Login")

        with st.form("login_form"):

            email = st.text_input(
                "Email",
                placeholder="you@example.com",
            )

            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
            )

            submitted = st.form_submit_button(
                "Login",
                type="primary",
                use_container_width=True,
            )

        if submitted:

            if not email.strip():
                st.warning("Please enter your email.")

            elif not password:
                st.warning("Please enter your password.")

            else:

                with st.spinner("Signing you in..."):

                    response = api(
                        "POST",
                        "/api/auth/login",
                        json={
                            "email": email.strip(),
                            "password": password,
                        },
                    )

                if response is not None and response.ok:

                    try:
                        data = response.json()

                        token = data.get("access_token")

                        if not token:
                            st.error(
                                "Login succeeded but the server "
                                "did not return an access token."
                            )
                        else:

                            st.session_state.token = token
                            st.session_state.user = data
                            st.session_state.last_result = None
                            st.session_state.ticket_data = None

                            st.success(
                                "Login successful. Loading dashboard..."
                            )

                            st.rerun()

                    except ValueError:

                        st.error(
                            "The server returned an invalid login response."
                        )

                elif response is not None:

                    st.error(
                        response_error(
                            response,
                            "Login failed."
                        )
                    )

    # --------------------------------------------------------
    # REGISTER
    # --------------------------------------------------------

    with register_tab:

        st.subheader("Create Customer Account")

        with st.form("register_form"):

            name = st.text_input(
                "Name",
                placeholder="Your name",
            )

            registration_email = st.text_input(
                "Registration Email",
                placeholder="you@example.com",
            )

            registration_password = st.text_input(
                "Password (minimum 10 characters)",
                type="password",
                placeholder="At least 10 characters",
            )

            submitted = st.form_submit_button(
                "Register",
                type="primary",
                use_container_width=True,
            )

        if submitted:

            if not name.strip():
                st.warning("Please enter your name.")

            elif not registration_email.strip():
                st.warning("Please enter your email.")

            elif len(registration_password) < 10:
                st.warning(
                    "Password must be at least 10 characters."
                )

            else:

                with st.spinner("Creating your account..."):

                    response = api(
                        "POST",
                        "/api/auth/register",
                        json={
                            "name": name.strip(),
                            "email": registration_email.strip(),
                            "password": registration_password,
                        },
                    )

                if response is not None and response.ok:

                    st.success(
                        "Registration successful! "
                        "Please switch to the Login tab."
                    )

                elif response is not None:

                    st.error(
                        response_error(
                            response,
                            "Registration failed."
                        )
                    )

    st.stop()


# ============================================================
# AUTHENTICATED APPLICATION
# ============================================================

user = st.session_state.get("user") or {}

user_id = user.get("user_id", "Unknown")
user_role = user.get("role", "customer")


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🤖 AI Support Assistant")

st.sidebar.success("Authenticated")

st.sidebar.write(f"**User ID:** {user_id}")
st.sidebar.write(f"**Role:** {user_role}")

st.sidebar.divider()

if st.sidebar.button(
    "🚪 Logout",
    use_container_width=True,
):

    st.session_state.token = None
    st.session_state.user = None
    st.session_state.last_result = None
    st.session_state.ticket_data = None

    st.rerun()


# ============================================================
# MAIN HEADER
# ============================================================

st.title("AI-Powered Customer Support & Operations Assistant")

st.write(
    "Welcome back! Submit a support ticket, search existing tickets, "
    "or view operational analytics."
)


# ============================================================
# TABS
# ============================================================

tab1, tab2, tab3 = st.tabs(
    [
        "🎫 Submit Ticket",
        "🔎 Ticket Search",
        "📊 Analytics",
    ]
)


# ============================================================
# TAB 1 — SUBMIT TICKET
# ============================================================

with tab1:

    st.header("Submit Customer Ticket")

    st.write(
        "Enter a customer support message. "
        "The backend will classify the ticket, predict priority, "
        "determine whether human review is required, and generate "
        "an AI-assisted response."
    )

    with st.form("ticket_form"):

        message = st.text_area(
            "Customer Message",
            height=180,
            placeholder=(
                "Example: I was charged twice for the same order "
                "and need help resolving the duplicate payment."
            ),
        )

        submitted = st.form_submit_button(
            "Analyze Ticket",
            type="primary",
            use_container_width=True,
        )

    if submitted:

        if not message.strip():

            st.warning(
                "Customer message is required."
            )

        else:

            with st.spinner(
                "Processing ticket with the AI support pipeline..."
            ):

                response = api(
                    "POST",
                    "/api/process-ticket",
                    json={
                        "message": message.strip()
                    },
                )

            if response is not None and response.ok:

                try:

                    data = response.json()

                    st.session_state.last_result = data

                    st.success(
                        "Ticket processed successfully."
                    )

                except ValueError:

                    st.error(
                        "The backend returned an invalid response."
                    )

            elif response is not None:

                st.error(
                    response_error(
                        response,
                        "Ticket processing failed."
                    )
                )

    # --------------------------------------------------------
    # DISPLAY RESULT
    # --------------------------------------------------------

    if st.session_state.get("last_result"):

        data = st.session_state.last_result

        st.divider()

        st.subheader("Ticket Result")

        ticket_id = data.get("ticket_id")

        prediction = data.get(
            "prediction",
            {}
        )

        ai_response = data.get(
            "ai_response",
            ""
        )

        category = prediction.get(
            "category",
            "N/A"
        )

        priority = prediction.get(
            "priority",
            "N/A"
        )

        human_review = prediction.get(
            "human_review_required",
            False
        )

        st.success(
            f"Ticket created successfully: #{ticket_id}"
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "Category",
                category,
            )

        with col2:

            st.metric(
                "Priority",
                priority,
            )

        with col3:

            st.metric(
                "Human Review",
                "Yes" if human_review else "No",
            )

        if human_review:

            st.warning(
                "⚠️ This ticket requires human review."
            )

        st.subheader("🤖 AI Response")

        if ai_response:

            st.info(ai_response)

        else:

            st.warning(
                "The ticket was processed, but no AI response "
                "was returned."
            )

        # Optional raw result for debugging
        with st.expander("View API Result"):

            st.json(data)


# ============================================================
# TAB 2 — TICKET SEARCH
# ============================================================

with tab2:

    st.header("Ticket Search")

    with st.form("search_form"):

        ticket_id_text = st.text_input(
            "Ticket ID",
            placeholder="Example: 1",
        )

        submitted = st.form_submit_button(
            "Search Ticket",
            type="primary",
        )

    if submitted:

        if not ticket_id_text.strip():

            st.warning(
                "Please enter a ticket ID."
            )

        elif not ticket_id_text.strip().isdigit():

            st.warning(
                "Ticket ID must be an integer."
            )

        else:

            ticket_id = int(
                ticket_id_text.strip()
            )

            with st.spinner(
                "Searching ticket..."
            ):

                response = api(
                    "GET",
                    f"/api/tickets/{ticket_id}",
                )

            if response is not None and response.ok:

                try:

                    data = response.json()

                    st.session_state.ticket_data = data

                    st.success(
                        f"Ticket #{ticket_id} found."
                    )

                except ValueError:

                    st.error(
                        "The backend returned an invalid ticket response."
                    )

            elif response is not None:

                st.error(
                    response_error(
                        response,
                        "Ticket not found."
                    )
                )

    # --------------------------------------------------------
    # DISPLAY TICKET
    # --------------------------------------------------------

    if st.session_state.get("ticket_data"):

        data = st.session_state.ticket_data

        st.divider()

        st.subheader(
            f"Ticket #{data.get('ticket_id', 'N/A')}"
        )

        st.json(data)

        st.divider()

        st.subheader("Customer Feedback")

        with st.form("feedback_form"):

            rating = st.slider(
                "Rating",
                min_value=1,
                max_value=5,
                value=5,
            )

            comments = st.text_area(
                "Comments",
                placeholder="Optional feedback...",
            )

            submitted = st.form_submit_button(
                "Submit Feedback"
            )

        if submitted:

            feedback_ticket_id = data.get(
                "ticket_id"
            )

            with st.spinner(
                "Saving feedback..."
            ):

                feedback_response = api(
                    "POST",
                    "/api/feedback",
                    json={
                        "ticket_id": feedback_ticket_id,
                        "rating": rating,
                        "comments": comments,
                    },
                )

            if (
                feedback_response is not None
                and feedback_response.ok
            ):

                st.success(
                    "Feedback submitted successfully."
                )

            elif feedback_response is not None:

                st.error(
                    response_error(
                        feedback_response,
                        "Feedback submission failed."
                    )
                )


# ============================================================
# TAB 3 — ANALYTICS
# ============================================================

with tab3:

    st.header("Analytics")

    if user_role != "admin":

        st.info(
            "Analytics and the human review queue are "
            "available to administrators."
        )

    else:

        st.subheader("Operational Analytics")

        if st.button(
            "🔄 Refresh Analytics",
            type="primary",
        ):

            with st.spinner(
                "Loading analytics..."
            ):

                response = api(
                    "GET",
                    "/api/analytics",
                )

            if response is not None and response.ok:

                try:

                    data = response.json()

                    total_tickets = data.get(
                        "total_tickets",
                        0
                    )

                    open_tickets = data.get(
                        "open_tickets",
                        0
                    )

                    resolved_tickets = data.get(
                        "resolved_tickets",
                        0
                    )

                    critical_tickets = data.get(
                        "critical_tickets",
                        0
                    )

                    ai_interactions = data.get(
                        "ai_interaction_count",
                        0
                    )

                    average_feedback = data.get(
                        "average_feedback_rating"
                    )

                    cols = st.columns(5)

                    cols[0].metric(
                        "Total Tickets",
                        total_tickets,
                    )

                    cols[1].metric(
                        "Open",
                        open_tickets,
                    )

                    cols[2].metric(
                        "Resolved",
                        resolved_tickets,
                    )

                    cols[3].metric(
                        "Critical",
                        critical_tickets,
                    )

                    cols[4].metric(
                        "AI Interactions",
                        ai_interactions,
                    )

                    st.metric(
                        "Average Feedback",
                        (
                            average_feedback
                            if average_feedback is not None
                            else "N/A"
                        ),
                    )

                    tickets_by_category = data.get(
                        "tickets_by_category"
                    )

                    if tickets_by_category:

                        st.subheader(
                            "Tickets by Category"
                        )

                        st.bar_chart(
                            tickets_by_category
                        )

                    tickets_by_priority = data.get(
                        "tickets_by_priority"
                    )

                    if tickets_by_priority:

                        st.subheader(
                            "Tickets by Priority"
                        )

                        st.bar_chart(
                            tickets_by_priority
                        )

                    with st.expander(
                        "View Analytics API Response"
                    ):

                        st.json(data)

                except ValueError:

                    st.error(
                        "The backend returned an invalid analytics response."
                    )

            elif response is not None:

                st.error(
                    response_error(
                        response,
                        "Unable to load analytics."
                    )
                )

        st.divider()

        # ----------------------------------------------------
        # HUMAN REVIEW QUEUE
        # ----------------------------------------------------

        st.subheader("Human Review Queue")

        if st.button(
            "🔄 Refresh Review Queue"
        ):

            with st.spinner(
                "Loading human review queue..."
            ):

                response = api(
                    "GET",
                    "/api/review-queue",
                )

            if response is not None and response.ok:

                try:

                    queue_data = response.json()

                    tickets = queue_data.get(
                        "tickets",
                        []
                    )

                    if tickets:

                        st.dataframe(
                            tickets,
                            use_container_width=True,
                        )

                    else:

                        st.success(
                            "No tickets are currently waiting "
                            "for human review."
                        )

                except ValueError:

                    st.error(
                        "The backend returned an invalid review queue response."
                    )

            elif response is not None:

                st.error(
                    response_error(
                        response,
                        "Unable to load review queue."
                    )
                )


# ============================================================
# FOOTER / DEBUG INFORMATION
# ============================================================

st.divider()

st.caption(
    "AI-Powered Customer Support & Operations Assistant"
)
