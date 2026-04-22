```python
import streamlit as st

# ===============================
# CHECK LOGIN STATUS
# ===============================
def is_user_logged_in():
    return st.session_state.get("logged_in", False)

# ===============================
# LOGIN PAGE
# ===============================
def show_auth_page():
    st.title("🔐 Login - JSS Pro Suite")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login", use_container_width=True):
        if email and password:
            # Simple session login (replace later with Firebase)
            user_id = email.replace("@", "_").replace(".", "_")

            st.session_state.logged_in = True
            st.session_state.user = {
                "user_id": user_id,
                "email": email
            }

            st.success("Login successful")
            st.rerun()
        else:
            st.error("Please enter both email and password")

# ===============================
# LOGOUT
# ===============================
def logout_user():
    st.session_state.clear()
    st.rerun()

# ===============================
# GET CURRENT USER
# ===============================
def get_current_user():
    return st.session_state.get("user", {
        "user_id": "demo_user",
        "email": "demo@example.com"
    })
```
