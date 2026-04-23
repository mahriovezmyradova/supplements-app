import hashlib
import json
import secrets
import streamlit as st
from typing import Optional, Dict


# ── Hardcoded base users ───────────────────────────────────────────────────────
# Passwords were generated at setup. Admin can override via the admin panel
# (changes saved to Supabase app_settings table).
_BASE_USERS: Dict[str, dict] = {
    "mahri": {
        "name": "Mahri Ovezmyradova",
        "role": "admin",
        "salt": "a982e19316f620eda46992beef4e8196",
        "hash": "4290cbb307eac5df21a01094bd930472af00575225d82cd77bbfb68deee89e28",
    },
    "richter": {
        "name": "Kai-Uwe Richter",
        "role": "doctor",
        "salt": "9543e317e3204e2452e35df9e1e29eab",
        "hash": "78abcbcda074c63cb9f4e79513ebf45d32c5774ce3b1ae9765d9c2188e6f9669",
    },
    "winhold": {
        "name": "Martin Winhold",
        "role": "doctor",
        "salt": "ae809cc08f90b7ca9a4748cadb95a7be",
        "hash": "c3029d9a7639f5087066a5d47d5b91cda1323cfefb7de3762bae078554cf9f54",
    },
    "sonnberg": {
        "name": "Dr. Anna-Maria Sonnberg",
        "role": "doctor",
        "salt": "8fbd082126b2a0ba0bc788fc3257a13d",
        "hash": "9a0a485990d5847e5da1ae7648140aefbbe886eae2309cb40ad8e7e0c94a0a91",
    },
}

_LOGIN_CSS = """
<style>
.auth-wrapper {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 80vh;
}
.auth-card {
    background: white;
    border-radius: 16px;
    padding: 48px 40px 40px;
    box-shadow: 0 4px 32px rgba(0,0,0,0.10);
    max-width: 420px;
    width: 100%;
    margin: 40px auto;
}
.auth-logo-title {
    text-align: center;
    margin-bottom: 8px;
    font-family: 'DM Serif Display', serif;
    font-size: 28px;
    color: rgb(38,96,65);
    font-weight: 700;
    letter-spacing: 0.5px;
}
.auth-subtitle {
    text-align: center;
    color: #888;
    font-size: 14px;
    margin-bottom: 32px;
}
.auth-error {
    background: #fff0f0;
    border: 1px solid #ffcccc;
    border-radius: 8px;
    padding: 10px 16px;
    color: #c0392b;
    font-size: 14px;
    margin-bottom: 16px;
    text-align: center;
}
</style>
"""


# ── Helpers ────────────────────────────────────────────────────────────────────

def _hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260000).hex()


def _verify(password: str, user_record: dict) -> bool:
    computed = _hash_password(password, user_record["salt"])
    return computed == user_record["hash"]


def _get_users(db=None) -> Dict[str, dict]:
    """Base users merged with any admin overrides stored in Supabase."""
    users = {k: dict(v) for k, v in _BASE_USERS.items()}
    if db is not None:
        try:
            raw = db.load_app_setting("users_override")
            if raw:
                overrides = json.loads(raw)
                users.update(overrides)
        except Exception:
            pass
    return users


def _save_users_override(db, users: dict):
    """Persist user overrides (non-base additions/changes) to Supabase."""
    overrides = {k: v for k, v in users.items() if k not in _BASE_USERS or v != _BASE_USERS[k]}
    db.save_app_setting("users_override", json.dumps(overrides))


# ── Public API ─────────────────────────────────────────────────────────────────

def check_auth() -> Optional[dict]:
    """Return the current authenticated user dict, or None."""
    return st.session_state.get("_auth_user")


def logout():
    st.session_state.pop("_auth_user", None)
    st.rerun()


def login_page(db=None) -> Optional[dict]:
    """
    Render the login wall. Returns the logged-in user dict on success,
    or None (and halts rendering via st.stop()) if not authenticated.
    """
    if st.session_state.get("_auth_user"):
        return st.session_state["_auth_user"]

    st.markdown(_LOGIN_CSS, unsafe_allow_html=True)

    _, center, _ = st.columns([1, 1.6, 1])
    with center:
        st.markdown('<div class="auth-logo-title">THERAPIEKONZEPT</div>', unsafe_allow_html=True)
        st.markdown('<div class="auth-subtitle">Revita Clinic · Berlin-Charlottenburg<br>Bitte melden Sie sich an, um fortzufahren.</div>', unsafe_allow_html=True)

        if st.session_state.get("_auth_error"):
            st.markdown(
                f'<div class="auth-error">⚠️ {st.session_state.pop("_auth_error")}</div>',
                unsafe_allow_html=True,
            )

        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Benutzername", placeholder="benutzername")
            password = st.text_input("Passwort", type="password", placeholder="••••••••••••")
            submitted = st.form_submit_button("Anmelden", use_container_width=True)

        if submitted:
            users = _get_users(db)
            key = username.strip().lower()
            if key in users and _verify(password, users[key]):
                st.session_state["_auth_user"] = {"username": key, **users[key]}
                st.rerun()
            else:
                st.session_state["_auth_error"] = "Ungültiger Benutzername oder Passwort."
                st.rerun()

    st.stop()
    return None


def admin_panel(db=None):
    """
    Full user management panel — only visible to admin role.
    Call this from within the admin tab in the main app.
    """
    user = check_auth()
    if not user or user.get("role") != "admin":
        st.warning("Kein Zugriff.")
        return

    users = _get_users(db)

    st.markdown("### Benutzerverwaltung")
    st.caption("Passwörter werden sicher gehasht gespeichert. Benutzernamen sind Kleinbuchstaben.")

    # ── User table ─────────────────────────────────────────────────────────────
    st.markdown("#### Aktuelle Benutzer")
    role_labels = {"admin": "🔑 Admin", "doctor": "👨‍⚕️ Arzt"}
    for uname, udata in users.items():
        with st.expander(f"{udata['name']}  ·  {role_labels.get(udata['role'], udata['role'])}  ·  `{uname}`"):
            _render_user_edit(uname, udata, users, db, is_self=(uname == user["username"]))

    st.markdown("---")

    # ── Add new user ───────────────────────────────────────────────────────────
    st.markdown("#### Neuen Benutzer hinzufügen")
    with st.form("add_user_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            new_name = st.text_input("Vollständiger Name")
            new_role = st.selectbox("Rolle", ["doctor", "admin"])
        with col2:
            new_username = st.text_input("Benutzername (Login)")
            new_pw = st.text_input("Passwort", type="password")
            new_pw2 = st.text_input("Passwort bestätigen", type="password")

        if st.form_submit_button("Benutzer hinzufügen", use_container_width=True):
            err = None
            if not new_name or not new_username or not new_pw:
                err = "Alle Felder sind Pflichtfelder."
            elif new_pw != new_pw2:
                err = "Passwörter stimmen nicht überein."
            elif len(new_pw) < 8:
                err = "Passwort muss mindestens 8 Zeichen lang sein."
            elif new_username.lower() in users:
                err = f"Benutzername '{new_username.lower()}' existiert bereits."
            if err:
                st.error(err)
            else:
                salt = secrets.token_hex(16)
                h = _hash_password(new_pw, salt)
                users[new_username.lower()] = {
                    "name": new_name,
                    "role": new_role,
                    "salt": salt,
                    "hash": h,
                }
                _save_users_override(db, users)
                st.success(f"Benutzer '{new_name}' wurde hinzugefügt.")
                st.rerun()


def _render_user_edit(uname: str, udata: dict, all_users: dict, db, is_self: bool):
    """Inline edit form inside an expander for one user."""
    is_base = uname in _BASE_USERS

    # Change password
    st.markdown("**Passwort ändern**")
    with st.form(f"pw_form_{uname}", clear_on_submit=True):
        new_pw = st.text_input("Neues Passwort", type="password", key=f"npw_{uname}")
        new_pw2 = st.text_input("Bestätigen", type="password", key=f"npw2_{uname}")
        if st.form_submit_button("Passwort speichern", use_container_width=True):
            if new_pw != new_pw2:
                st.error("Passwörter stimmen nicht überein.")
            elif len(new_pw) < 8:
                st.error("Mindestens 8 Zeichen erforderlich.")
            else:
                salt = secrets.token_hex(16)
                h = _hash_password(new_pw, salt)
                all_users[uname]["salt"] = salt
                all_users[uname]["hash"] = h
                _save_users_override(db, all_users)
                st.success("Passwort wurde geändert.")

    # Delete (not for base users or self)
    if not is_base and not is_self:
        st.markdown("**Benutzer löschen**")
        if st.button(f"🗑 '{udata['name']}' löschen", key=f"del_{uname}"):
            del all_users[uname]
            _save_users_override(db, all_users)
            st.success(f"Benutzer '{udata['name']}' wurde gelöscht.")
            st.rerun()
    elif is_base and not is_self:
        st.caption("Standardbenutzer können nicht gelöscht, aber ihr Passwort kann geändert werden.")
