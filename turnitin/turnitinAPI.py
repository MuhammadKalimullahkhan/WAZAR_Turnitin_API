import json
import requests
import time
import re
from datetime import datetime
from bs4 import BeautifulSoup

__LOGIN_URL = "https://www.turnitin.com/login_page.asp?lang=en_us"
__LOGOUT_URL = "https://www.turnitin.com/logout.asp?lang=en_us"
__HOMEPAGE = "https://www.turnitin.com/t_home.asp?login=1&svr=49&lang=en_us&r=16.3309135841924"
__DOWNLOAD_URL = "https://www.turnitin.com//newreport.asp"
__SUBMIT_URL = "https://www.turnitin.com/t_submit.asp"
__CONFIRM_URL = "https://www.turnitin.com/submit_confirm.asp"
__HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "sec-ch-ua": '"Chromium";v="85", "\\\\Not;A\\"Brand";v="99", "Microsoft Edge";v="85"',
    "content-type": "application/x-www-form-urlencoded",
    "referer": __LOGIN_URL,
    "referrer": __LOGIN_URL,
    "referrerPolicy": "no-referrer-when-downgrade",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
}


def login(email, password):
    s = newSession()
    token = __getToken()
    payload = f"javascript_enabled=0&email={email}&user_password={password}&login_id={token[0]}&login_token={token[1]}&submit=Log+in".encode(
        "utf-8"
    )
    cookies = __getCookies(s, __LOGIN_URL)
    __setCookies(s, cookies)
    url = __post(s, __LOGIN_URL, payload).url

    if "t_home.asp" in url:
        return cookies.get_dict()
    else:
        print("Invalid Email or Password")
        return None


def logOut(cookies):
    s = newSession()
    __setCookies(s, cookies)
    return s.get(__LOGOUT_URL).url


def getClasses(cookies):
    s = newSession()
    __setCookies(s, cookies)
    source = __get(s, __HOMEPAGE)
    classes = __parseDashboard(source)
    return classes


def getAssignments(url, cookies):
    s = newSession()
    __setCookies(s, cookies)
    source = __get(s, url)
    table = __getAssignmentTable(source)
    return [
        {
            "title": __getAssignmentTitle(assignment),
            "info": __getAssignmentInfo(assignment),
            "dates": __getAssignmentDate(assignment),
            "submission": __getSubmissionLink(assignment),
            "aid": __getAid(assignment),
            "oid": __getOid(__getMenu(assignment)),
            "file": __getFileName(__getMenu(assignment)),
        }
        for assignment in table
    ]


# def getDownload(cookies, oid, filename, pdf):
def getDownload(cookies, oid):
    s = newSession()
    __setCookies(s, cookies)
    query = {
        'lang': 'en_us',
        'oid': oid,
        'pbd': 2,
        'ft': 1,
        'ro': ''
    }
    # query = {"oid": "1854201996", "fn": filename, "type": "paper", "p": int(pdf)}
    # print(f"[DEBUG] Ah shit, here we go again")
    r = s.get(__DOWNLOAD_URL, params=query)
    # print(f"[DEBUG] Status code of {r.status_code}")
    return r.content


def submit(
    cookies,
    aid,
    auther_info,
    submission_title,
    filename,
    userfile,
    referrer,
):
    s = newSession()
    __setCookies(s, cookies)

    r = s.get(referrer)
    # author_first, author_last = __getAuthorName(r.text)
    author_first = auther_info['fname']
    author_last = auther_info['lname']

    file_to_mime = {
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "pdf": "application/pdf",
        "csv": "text/csv",
        "xls": "application/vnd.ms-excel",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "ppt": "application/vnd.ms-powerpoint",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "html": "text/html",
        "txt": "text/plain",
        "rtf": "application/rtf",
        "odt": "application/vnd.oasis.opendocument.text"
    }

    try:
        fileending = re.findall(r"\.(.+)$", filename)[0]
    except IndexError:
        return "Please submit a valid filename with filetype"

    mimetype = file_to_mime.get(fileending, "application/octet-stream")

    query = {"aid": aid, "session-id": cookies["session-id"], "lang": "en_us"}
    form_data = dict(
        async_request=1,
        author_first=author_first,
        author_last=author_last,
        title=submission_title,
        filename=filename
    )
    files = {
        "userfile": (filename, userfile, mimetype),
        "Content-Disposition":  f"form-data; name=\"file\"; filename=\"{filename}\"",
        "Content-Type": mimetype
    }

    r = s.post(
        __SUBMIT_URL,
        data=form_data,
        files=files,
        headers={"accept": "application/json"},
        params=query,
        cookies=cookies
    )

    # Request didn't return json
    if not (r.headers["content-type"] == "application/json" and r.json()["errors"] is None):
        return "Something went wrong during your submission"

    uuid = r.json()["uuid"]
    r = None

    # Keep asking for metadata until the document is processed
    while r is None or time.sleep(1) or not r.json()["status"]:
        r = s.post(
            "https://www.turnitin.com/panda/get_submission_metadata.asp",
            params={
                "session-id": cookies["session-id"],
                "lang": "en_us",
                "skip_ready_check": 0,
                "uuid": uuid,
            },
        )

    metadata = r.json()
    session = cookies["session-id"]

    # Send the confirmation request
    r = s.post(
        (
            f"{__CONFIRM_URL}?lang=en_us&sessionid={session}&"
            f"data-state=confirm&uuid={uuid}"
        )
    )

    if r.text == "null":
        return "Something went wrong with confirmation"

    return metadata


def getAssignmentsInfo(cookies, aid):
    print("\n\n\n")
    print(aid)
    print("\n\n\n")
    s = newSession()
    __setCookies(s, cookies)
    url = f"https://ev.turnitin.com/assignment/{aid}/papers?lang=en_us&cv=1&output=json"
    r = s.get(url)
    return r.json()['PaperStub']


def newSession():
    return requests.Session()


def parseHTML(content):
    return BeautifulSoup(content, "html.parser")


def __getToken():
    response = requests.get(__LOGIN_URL)

    c = response.text.split(
        '''<input name="login_id" type="hidden" value="''')[1]
    login_id = c.split('" />\');')[0].strip()

    login_token = c.split('" />\');')[1].replace(
        '$("form[name=\'FormName\']").append(\'<input name="login_token" type="hidden" value="', "").strip()
    return [login_id, login_token]


def __parseDashboard(source):
    soup = parseHTML(source)
    classes_row = soup.find_all("tr", {"class": "class"})
    classes = soup.find_all("td", {"class": "class_name"})

    for i in range(len(classes)):
        e = classes[i].find("a")
        cid = classes_row[i].find("td", {'class': "class_id"})
        sd = classes_row[i].find("td", {'class': "class_start_date"})
        ed = classes_row[i].find("td", {'class': "class_end_date"})
        classes[i] = {
            "cid": cid.text,
            "title": e.text,
            "url": f"https://www.turnitin.com/{e['href']}",
            "start_date": sd.text,
            "end_date": ed.text,
        }
    return classes


def __resetHeaders(s):
    s.headers.update(__HEADERS)


def __post(s, url, payload):
    __resetHeaders(s)
    return s.post(url, data=payload)


def __get(s, url):
    __resetHeaders(s)
    return s.get(url).content.decode("utf-8")


def __getCookies(s, url):
    s.get(url)
    cookies = s.cookies
    return cookies


def __setCookies(s, cookies):
    s.cookies.update(cookies)


def __getAssignmentTitle(e):
    if e:
        return e['title']
    return None


def __getAssignmentInfo(e):
    info = e.find("td", {"class": "assgn-status"}
                  ).find("div", {"class": "primary"}).text.strip()
    # info = re.sub(r"\s\s+", " ", info)
    # info = info.replace("\n", " ")
    # info = info.replace(" Assignment Instructions ", "", 1)
    # info = info[:-1]
    return info


def __convertDate(raw):
    date = raw.find("div", {"class": "primary"}).text
    time = raw.find("div", {"class": "secondary"}).text

    if date.strip() == "N/A" or time.strip() == "N/A":
        return None
    dateObject = datetime.strptime(date + " " + time, "%d-%b-%Y %H:%M%p")
    return dateObject.strftime("%m/%d/%Y %I:%M:%S")


def __getAssignmentDate(e):
    raw_dates = e.find_all("td", {'class': 'assgn-date'})
    return {
        "start": __convertDate(raw_dates[0]),
        "due": __convertDate(raw_dates[1]),
        "post": __convertDate(raw_dates[2]),
    }


def __getSubmissionLink(e):
    domain = "https://www.turnitin.com/"
    return domain + e.find("td", {"class": "assgn-inbox"}).find("a")["href"]


# def __getAid(e):
#     return re.search("(\d+)", e["id"]).group(1)

def __getAid(e):
    return e.find('td', {"class": "assgn-inbox"}).find('a')['href'].split("&aid=")[-1]


def __getOid(e):
    try:
        pattern = re.compile("(\d+)")
        # print(f"[DEBUG] Searching {e.find('a')['id']} for {pattern}")
        return re.search(pattern, e.find("a")["id"]).group(1)
    except KeyError:
        return "void"
    except AttributeError:
        # print(f"[DEBUG] {e} of type {type(e)} does not seem to have a .find()")
        return "void"


def __getFileName(e):
    pattern = re.compile("fn=(.+)\\&.+\\&")
    try:
        # print(f"[DEBUG] Searching {e} for {pattern}")
        return re.search(pattern, str(e)).group(1)
    except KeyError:
        # uin = ''
        # QUIT = 0
        # while uin != "QUIT":
        #     try:
        #         uin = input(">>> ")
        #         eval(uin)
        #     except:
        #         pass
        # print(f"[DEBUG] Fuck you bich (from __getFileName(e))")
        return "void"
    except AttributeError:
        # print(f"[DEBUG] {e} of type {type(e)} does not seem to have a .find()")
        return "void"


def __getMenu(e):
    return e.find("ul", {"class": "dropdown-menu"})


def __getAssignmentTable(html):
    soup = BeautifulSoup(html, "html.parser")
    # return soup.find_all("tr", {"class": ("Paper", "Revision")})
    return soup.find_all("tr", {"class": "assgn-row"})


def __getAuthorName(html):
    soup = BeautifulSoup(html, "html.parser")
    return (
        soup.find_all("div", {"class": "form-group"}
                      )[0].find("input")["value"],
        soup.find_all("div", {"class": "form-group"})[1].find("input")["value"]
    )
