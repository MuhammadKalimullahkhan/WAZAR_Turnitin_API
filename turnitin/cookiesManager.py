import json

def getCookies():
    with open(".auth") as f:
        cookies = f.read()
        return json.loads(cookies)

def saveCookies(cookies:str):
    cookies = cookies.replace("\'", "\"")
    with open(".auth", "w") as f:
        f.write(cookies)