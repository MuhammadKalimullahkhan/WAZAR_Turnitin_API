def createCookies(session_id: str) -> dict:
    cookies = {
        "legacy-session-id": session_id,
        "session-id": session_id,
        "t": session_id,
        "test_cookie": "1",
        "xhfaculty": "0"
    }
    return cookies