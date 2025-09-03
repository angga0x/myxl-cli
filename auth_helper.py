import time
from api_request import get_new_token
from util import ensure_api_key
import db_helper

class Auth:
    _instance_ = None
    _initialized_ = False
    
    api_key = "97fe7bb2-e6fd-4415-82d5-3412aeb90ff9"
    
    # This will now store tokens for multiple users, keyed by user_id
    # Format: {user_id: {"number": int, "tokens": {...}, "last_refresh": int}}
    active_sessions = {}
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance_:
            cls._instance_ = super().__new__(cls)
        return cls._instance_
    
    def __init__(self):
        if not self._initialized_:
            self.api_key = ensure_api_key()
            self._initialized_ = True

    def login_user(self, user_id, phone_number, refresh_token):
        """Logs in a user and stores their session."""
        db_helper.add_or_update_user(user_id, phone_number, refresh_token)
        tokens = get_new_token(refresh_token)
        if tokens:
            self.active_sessions[user_id] = {
                "number": int(phone_number),
                "tokens": tokens,
                "last_refresh": int(time.time())
            }
            return self.active_sessions[user_id]
        return None

    def logout_user(self, user_id):
        """Logs out a user and removes their session."""
        db_helper.remove_user(user_id)
        if user_id in self.active_sessions:
            del self.active_sessions[user_id]

    def get_session(self, user_id):
        """Gets a user's session, auto-logging in if necessary."""
        if user_id in self.active_sessions:
            # Check if token needs refreshing
            if (int(time.time()) - self.active_sessions[user_id]["last_refresh"]) > 300:
                self.renew_token(user_id)
            return self.active_sessions[user_id]
        
        # If not in active sessions, try to load from DB
        user_data = db_helper.get_user(user_id)
        if user_data:
            tokens = get_new_token(user_data["refresh_token"])
            if tokens:
                self.active_sessions[user_id] = {
                    "number": int(user_data["phone_number"]),
                    "tokens": tokens,
                    "last_refresh": int(time.time())
                }
                # Update the refresh token in the DB in case it changed
                db_helper.add_or_update_user(user_id, user_data["phone_number"], tokens["refresh_token"])
                return self.active_sessions[user_id]
        
        return None

    def renew_token(self, user_id):
        """Renews the token for a specific user."""
        if user_id in self.active_sessions:
            session = self.active_sessions[user_id]
            new_tokens = get_new_token(session["tokens"]["refresh_token"])
            if new_tokens:
                session["tokens"] = new_tokens
                session["last_refresh"] = int(time.time())
                db_helper.add_or_update_user(user_id, session["number"], new_tokens["refresh_token"])
                print(f"Token renewed for user {user_id}")
                return True
        return False

    def get_tokens(self, user_id):
        """A convenience method to get the tokens for a user."""
        session = self.get_session(user_id)
        return session["tokens"] if session else None

AuthInstance = Auth()
