import json, os
from datetime           import datetime, timedelta
from requests_toolbelt  import MultipartEncoder
from exceptions import ClassNotFound
from turnitinAPI       import getClasses, getAssignments, logOut, login, newSession, parseHTML
from formData          import formData
from cookiesManager    import getCookies, saveCookies
        
# ################################################## #
# ################( ACCOUNT MANAGER )############### # 
# ################################################## #


def getClass(cookies, cid:int):
    for cls in getClasses(cookies):
        if int(cls['cid']) == cid:
            return cls['url'] 
    raise ClassNotFound("class with the provided id not found")


def turnitinFreshLogin(email, password):
    return login(email, password)

def turnitinLogout(cookies):
    url = logOut(cookies)
    if "login_page.asp?lang=en_us" in url:
        return True
    return False
        
def turnitinLogin(email, password):
    loginURL = "https://www.turnitin.com/t_home.asp?login=1&svr=49&lang=en_us"
    if os.path.exists(".auth"):
        cookies = dict()
        try:
            cookies = getCookies()
        except: 
            cookies = dict(null="",null2="")
        s = newSession()
        s.cookies.update(cookies)
        if not (loginURL[:36] in s.get(loginURL).url):
            print("login Again")
            cookies = login(email, password)
            saveCookies(str(cookies))
        return cookies


def userInfo(cookies:dict):
    s = newSession()
    s.cookies.update(cookies)

    info = s.get("https://ev.turnitin.com/user/current?lang=en_us&cv=1&output=json").text
    return json.loads(info)['User'][0]


def getSubmission(cookies:dict, aid:int):
    s = newSession()
    s.cookies.update(cookies)

    # aid (Assignment ID)
    paper_stub =  s.get(
        f"https://ev.turnitin.com/assignment/{aid}/papers?lang=en_us&cv=1&output=json").text
    # print(paper_stub)
    return json.loads(paper_stub)['PaperStub']


def __setAssignmentFormData(formData:dict, assignment_duration=6):
    day = "28"
    now = datetime.now()
    post_date = now + timedelta(30 * assignment_duration)

    # Start Date
    formData["start_day"]   = now.strftime("%d")
    formData["start_month"] = now.strftime("%m")
    formData["start_year"]  = now.strftime("%Y")
    # Due Date
    formData["due_day"]     = str( int(day) - 1)
    formData["due_month"]   = post_date.strftime("%m")
    formData["due_year"]    = post_date.strftime("%Y")
    # Post Date
    formData["post_day"]    = day
    formData["post_month"]  = post_date.strftime("%m")
    formData["post_year"]   = post_date.strftime("%Y")


def createAssignment(cookies:dict, class_index:int, ammount:int, assignment_duration:int, title:str):
    s = newSession()
    s.cookies.update(cookies)

    selected_class = getClasses(cookies)[class_index]
    # title
    formData['title'] = title
    __setAssignmentFormData(formData, assignment_duration)
    s.get(selected_class['url'])

    for i in range(ammount):
        data = MultipartEncoder(
            fields=formData,
            boundary="----WebKitFormBoundaryDB0KCBArgtB6PgfX"
        )
        res = s.post(
            'https://www.turnitin.com/t_modify_assignment.asp?at=1&svr=33&lang=en_us&r=19.9242277331248',
            headers={
                "referer": f"https://www.turnitin.com/t_class_home.asp?r=72.0777068924683&svr=57&lang=en_us&aid=66034&cid={selected_class['cid']}",
                'content-type': data.content_type
            },
            data=data
        )

    if "t_modify_assignment.asp" in res.url and not "The post date for this assignment must occur on or before the class end date" in res.text: return True
    else:
        return {"error":"The post date for this assignment must occur on or before the class end date."}

def deleteAssignment(cookies:dict, class_index:int, start:int):
    s = newSession()
    s.cookies.update(cookies)

    selected_class = getClasses(cookies)[class_index]
    assignments = getAssignments(selected_class['url'], cookies)
    total_assignments = len(assignments)

    if assignments or total_assignments > 0:

        s.get(selected_class['url'])

        for i in range(start, total_assignments):
            r = s.post(
                "https://www.turnitin.com/t_class_home.asp",
                data={
                    # getting assignment id of selected assignemt
                    "victim": assignments[i]['aid'],
                    "session_id": cookies['session-id']
                },
            )
    else:
        pass


def clearAssignment(cookies:dict, class_index:int):
    data = {
        'perform_delete': '1',
        'do_zip_download': '0',
        'use_pdfs': '0',
        'folder': '0',
        'object_checkbox': [],
    }
    s = newSession()
    s.cookies.update(cookies)

    selected_class = getClasses(cookies)[class_index]
    assignments = getAssignments(selected_class['url'], cookies)

    for asg in assignments:
        if not "0" == asg['info'].split(" / ")[0].strip():
            aid = asg['aid']
            data['object_checkbox'] = [x['id'] for x in getSubmission(cookies, aid)]
            s.get(f"https://www.turnitin.com/t_inbox.asp?r=29.1840658298803&svr=39&lang=en_us&aid={aid}")
            s.post(f"https://www.turnitin.com/t_inbox.asp?r=44.6284535913726&svr=35&lang=en_us&aid={aid}",data=data)
    


def enrollStudent(cookies:dict, class_index:int, std_data:dict):
    s = newSession()
    s.cookies.update(cookies)

    url = "https://www.turnitin.com/t_add_student.asp?r=18.9487876550427&svr=45&lang=en_us&"
    selected_class = getClasses(cookies)[class_index]
    s.get(selected_class['url'])
    content = s.get(url).content
    srandom = parseHTML(content).find('input', {'name': 'srandom'})['value']
    std_data['srandom'] = srandom
    res = s.post(url, data=std_data)
    if "/t_students.asp?" in res.url: 
        return True


def enrollStudentList(cookies:dict, class_index:int, file):
    s = newSession()
    s.cookies.update(cookies)

    url = "https://www.turnitin.com/t_upload_student_list.asp?lang=en_us"
    selected_class = getClasses(cookies)[class_index]
    s.get(selected_class['url'])
    file = {"userfile": file}

    res = s.post(url, files=file)
    
    try:
        if "t_confirm_student_list.asp" in res.url:
            res = s.post(res.url, data={"confirm": True})
            return True
        else: print("Failed to confirm")
    except Exception as e:
        print(e)


def getEnrolledStudents(cookies:dict, class_index:int):
    pages = None
    s = newSession()
    s.cookies.update(cookies)

    url = "https://www.turnitin.com/t_students.asp?lang=en_us&tdan=1&sort=2"
    selected_class = getClasses(cookies)[class_index]
    s.get(selected_class['url'])
    content = s.get(url).content
    try:
        pages = len(parseHTML(content).find_all("a", {'class': 'VD9_darkG'}))
    except:
        pages = 1
        
    if pages < 1:
        pages = 1
        
    std_pages = [None]*pages
    for i in range(pages):
        content=""
        if pages > 1:
            content = s.get(f"{url}&pg={i + 1}")
        else:
            content = s.get("https://www.turnitin.com/t_students.asp?lang=en_us")
        content = content.content

        trs = parseHTML(content).find_all("tr")[1:]
        
        if "Welcome!" in trs[0].text.strip(): return

        for j in range(len(trs) ):
            id = trs[j].find("td", {'class': 'student-id'}).text
            enrolled_date = trs[j].find("td", {'class': 'date-enrolled'}).text
            name = trs[j].find("td", {'class': 'student-name'}).text
            email = trs[j].find("td", {'class': 'student-email'}).find('a')['href'].split('mailto:')[-1]
            is_locked = trs[j].find("td", {'class': 'locked'})
            is_locked = True if is_locked else False
            
            trs[j] = { 
                "id": id.strip(),
                "enrolled_date": enrolled_date.strip(),
                "name": name.strip(),
                "email": email.strip(),
                "is_locked": is_locked,
            }
        std_pages[i] = trs
    return std_pages


def noOfEnrolledStudents(cookies:dict, class_index:int):
    stds = getEnrolledStudents(cookies, class_index)
    m = 0
    if stds:
        for std in stds:
            for i in std:
                m += 1
    return m
    

def studentAction(cookies:dict, class_index:int, std_id:str, action:str):
    s = newSession()
    s.cookies.update(cookies)

    url = "https://www.turnitin.com/t_students.asp?lang=en_us"
    selected_class = getClasses(cookies)[class_index]
    s.get(selected_class['url'])
    data = {
        "target": std_id,
        "unlock": "",
        "lock": "",
        "del": "",
        "csrf_token": "",
        "victim": "0",
    }
    if action == 'del': 
        data["del"] = "1"
    elif action == 'unlock': 
        data["unlock"] = "1"
    else: 
        data["lock"] = "1"

    content = s.get(url).content
    csrf_token = parseHTML(content).find('input', {'name': 'csrf_token'})['value']
    data['csrf_token'] = csrf_token
    res = s.post(url, data=data)
    return True if "/t_students.asp" in res.url else False