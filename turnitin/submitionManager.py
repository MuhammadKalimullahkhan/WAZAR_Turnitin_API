import json
import time
from .turnitinAPI import submit, newSession, getAssignmentsInfo, getClasses
from requests import Session

def submitFile(cookies, data: dict):
    # getClasses(cookies)
    s = Session()
    s.cookies.update(cookies)
    s.get(data["class_url"])
    s.get(data['assignment_url'])

    assignmentId: str = data['assignment_id']
    auther: dict = data['auther']
    file_title: str = data['file_title']
    file_name: str = data['file_name']
    file_stream = data['file_stream']
    assignment_url: str = data['assignment_url']
    return submit(
        cookies,
        assignmentId,
        auther,
        file_title,
        file_name,
        file_stream,
        assignment_url
    )


def generatePaperReport(cookies, paper_title, aid):
    ass_info = getAssignmentsInfo(cookies, aid)
    if not ass_info: return
    for info in ass_info:
        if info.get('title') == paper_title:
            if info['overlap'] >= 0:
                return {
                    "plagiarism": [info['overlap']], 
                    "title":info['title'].split('.')[0],
                    "id":info['id']
                }
            
            else:
                print(info['overlap'])
                time.sleep(3)
                return None
            

def getPDFLink(cookies, file_name, slot_id):
    while True:
        paper_info = generatePaperReport(cookies, file_name, slot_id)
        if paper_info != None:
            break    
    if paper_info:
        s = newSession()
        s.cookies.update(cookies)
        paper_id = paper_info['id']

        url = f"https://ev.turnitin.com/paper/{paper_id}/queue_pdf?lang=en_us&cv=1&output=json"
        res = json.loads(s.post(url, json={"as":1,"or_type":"similarity","or_translate_language":0}).text)
        # wating for correct pdf link
        sas = ( res['url'].split("?")[0] ).split("sas:")[1]
        for i in range(100):
            res = json.loads(s.get(f"https://ev.turnitin.com/paper/{paper_id}/queue_pdf/sas:{sas}?lang=en_us&cv=1&output=json").content)
            res['paper_info'] = paper_info
            if res['ready'] == 1:
                print("Downloading Please Wait.")
                return res
            print('Getting file url, please wait')
            time.sleep(3)
        return res
    
    
def downloadFile(cookies, url, file_path):
    s = newSession()
    s.cookies.update(cookies)
    res = s.get(url)
    save_file = open(f'{file_path}.pdf', 'wb')
    save_file.write(res.content)
    save_file.close()


if __name__ =="__main__":
    session_id = "5c503f1e447d402c833ddf12ac4bfa0e"
    cookies = {
        "legacy-session-id": session_id,
        "session-id": session_id,
        "t": session_id,
        "test_cookie": "1",
        "xhfaculty": "0"
    }
    g = getPDFLink(cookies, "my final year thesis - 02497049161101042023", 114235268)
    print(g)