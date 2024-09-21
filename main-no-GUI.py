import requests
import json
import base64
import difflib
from collections import defaultdict
from prettytable import PrettyTable




class CommandLineApp:
    def __init__(self):
        self.token = None
        self.roleType = None
        self.student_names = []
        self.selected_user = None # 当前选择的学生
        self.selected_examId = None
        self.isListAll = False
    
    def Login(self):
        roleType = input("请选择身份(0: 退出, 1: 学生, 2: 家长): ")
        if roleType == "0":
            return
        username = input("请输入用户名: ")
        password = input("请输入密码: ")
        password_b64 = base64.b64encode(password.encode()).decode()
        msg, token = self.get_token(username, password_b64, roleType)
        if token:
            student_name = self.get_student_name(token)
            self.token = token
            self.roleType = roleType
            self.selected_user = student_name
            print(f"Msg: {msg}\nToken: {token}\n学生: {student_name}")
        else:
            print(f"登录失败！\nMsg: {msg}")

    def get_token(self, username, password_b64, roleType):
        url = "http://hfs-be.yunxiao.com/v2/users/sessions"
        headers = {
            "Content-Type": "application/json;charset=UTF-8"
        }
        data = json.dumps({
            "loginName": username,
            "password": password_b64,
            "roleType": roleType, # 1:学生, 2: 家长
            "loginType": 1,
            "rememberMe": 2
        })
        response = requests.post(url, headers=headers, data=data)
        response_data = response.json()
        msg = response_data["msg"]
        try:
            token = response_data["data"]["token"]
        except AttributeError:
            token = None
        if token:
            student_name = self.get_student_name(token)
            self.save_config(student_name, token, roleType)
        return msg, token

    def get_student_name(self, token):
        url = "https://hfs-be.yunxiao.com/v2/user-center/user-snapshot"
        headers = {
            "Cookie": f"hfs-session-id={token}"
        }
        response = requests.get(url, headers=headers)
        response_data = response.json()
        student_name = response_data["data"]["linkedStudent"]["studentName"]
        return student_name

    def save_config(self, student_name, token, roleType):
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            data = []
        student_names = [student["student_name"] for student in data]
        if student_name not in student_names and student_name != "": # 不记录重复和空值的Token
            data.append({"student_name": student_name, "token": token, "roleType": roleType})
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

    def load_student_names(self):
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            student_names = [entry["student_name"] for entry in data]
            return student_names
        except FileNotFoundError:
            return []

    def load_config(self, student_name):
        with open('config.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            for entry in data:
                if entry["student_name"] == student_name:
                    return entry["token"], entry["roleType"]
    
    def ChoiceUser(self):
        if not self.student_names:
            input("没有找到任何学生信息，请先登录。")
            return
        print("可选的学生名称：")
        print("0. 退出")
        for idx, name in enumerate(self.student_names, 1):
            print(f"{idx}. {name}")
        # 提示用户输入选择
        choice = input("请输入要选择的学生编号: ")
        try:
            choice = int(choice) - 1  # 转换为索引
        except ValueError:
            input("请输入有效的数字。")
        if not -1 <= choice < len(self.student_names):
            input("无效的选择。")
        elif choice == -1:
            return
        else:
            self.selected_user = self.student_names[choice]  # 选择学生
            print(f"已选择学生: {self.selected_user}")
            self.token, self.roleType = self.load_config(self.selected_user)

    def GET(self, url):
        """
        向url发送GET请求
        输入: 请求url
        输出: self.res = response.json()
        """
        headers = {
            "Cookie": f"hfs-session-id={self.token}"
        }

        try:
            response = requests.get(url, headers=headers)
            self.res = response.json()
        except requests.exceptions.RequestException as e:
            print(f"请求失败：\n{e}")

    def GetExamList(self):
        self.CheckIfListAll()
        self.examId = []
        if not self.res:
            return
        
        if not self.isListAll: # 常规处理
            for i in range(len(self.res["data"]["list"])):
                self.examId.append(self.res["data"]["list"][i]["examId"])
                name = str(self.res["data"]["list"][i]["name"])
                print(f"{i + 1}. {name}")
            
        else: # 调用导出错题api（获取学科信息）
            subject_data = self.res
            exam_dict = defaultdict(list) # 用于存储按考试名称合并的 examId
            for subject in subject_data['data']: # 遍历所有科目，收集 examName 和 examId
                for exam in subject['examList']:
                    exam_dict[exam['examName']].append(exam['examId'])
            sorted_exam_dict = {name: sorted(ids, key=int, reverse=True) # 按照 examId 倒序排序
                for name, ids in sorted(exam_dict.items(), key=lambda x: min(map(int, x[1])), reverse=True)}
            result = list(sorted_exam_dict.items()) # [(examName, [examId, examId, ...]), ...]
            i = 1
            for name, ids in result:
                self.examId.append(ids[0])
                print(f"{i}. {name}")
                i += 1
        
        choice = input("请输入要选择的考试编号: ")
        try:
            choice = int(choice) - 1  # 转换为索引
        except ValueError:
            input("请输入有效的数字。")
        if not 0 <= choice < len(self.examId):
            input("无效的选择。")
        else:
            self.selected_examId = self.examId[choice]  # 选择考试
            self.OnChoiceExam()
                
    def CheckIfListAll(self):
        if not self.selected_user:
            return
        if self.isListAll:
            url = "https://hfs-be.yunxiao.com/v2/wrong-items/overview" # 导出错题api（获取学科信息）
        else:
            url = "https://hfs-be.yunxiao.com/v3/exam/list?start=0&limit=5"
        self.GET(url)
        
    def OnChoiceExam(self):
        '''选择考试并解析json数据'''
        if not self.selected_examId:
            return
        examId = self.selected_examId
        self.OnGetRankInfo()
        data = self.res["data"]
        highest_class = str(data["highest"]["class"])
        highest_grade = str(data["highest"]["grade"])
        avg_class = str(data["avg"]["class"])
        avg_grade = str(data["avg"]["grade"])
        rank_class = str(data["rank"]["class"])
        rank_grade = str(data["rank"]["grade"])
        number_class = str(data["number"]["class"])
        number_grade = str(data["number"]["grade"])
        self.OnGetOverview()
        data = self.res["data"]
        name = data["name"]
        score = str(data["score"])
        fullscore = str(data["manfen"])
        papers = self.res["data"]["papers"]
        length_papers = len(papers)
        
        table = PrettyTable()
        table.field_names = ["科目", "分数", "班名", "级名", "班最高", "级最高", "班平均", "级平均"]
        data_list = [
                "全部",
                f"{score}/{fullscore}",
                f"{rank_class}/{number_class}",
                f"{rank_grade}/{number_grade}",
                f"{highest_class}",
                f"{highest_grade}",
                f"{avg_class}",
                f"{avg_grade}"
            ]

        grade_list = []
        subject_order = ["语文", "数学", "英语", "物理", "化学", "生物", "政治", "历史", "地理"]
        for i in range(length_papers): # 各科成绩
            paperId = str(papers[i]["paperId"])
            subject_name = str(papers[i]["subject"])
            subject_score = str(papers[i]["score"])
            subject_fullscore = str(papers[i]["manfen"])
            self.GET(f"https://hfs-be.yunxiao.com/v3/exam/{examId}/papers/{paperId}/rank-info")
            subject_highest_class = str(self.res["data"]["highest"]["class"])
            subject_highest_grade = str(self.res["data"]["highest"]["grade"])
            subject_avg_class = str(self.res["data"]["avg"]["class"])
            subject_avg_grade = str(self.res["data"]["avg"]["grade"])
            subject_rank_class = str(self.res["data"]["rank"]["class"])
            subject_rank_grade = str(self.res["data"]["rank"]["grade"])
            subject_number_class = str(self.res["data"]["number"]["class"])
            subject_number_grade = str(self.res["data"]["number"]["grade"])
            
            # 使用模糊匹配找到最接近的学科名（如果学科名异常的话）
            closest_match = difflib.get_close_matches(subject_name, subject_order, n=1, cutoff=0.6)
            match_name = closest_match[0] if closest_match else subject_name 
            grade_list.append((
                paperId,
                match_name, 
                f"{subject_score}/{subject_fullscore}",
                f"{subject_rank_class}/{subject_number_class}",
                f"{subject_rank_grade}/{subject_number_grade}",
                f"{subject_highest_class}",
                f"{subject_highest_grade}",
                f"{subject_avg_class}",
                f"{subject_avg_grade}"
                )) # (ID,科目,分数,班名,级名,班最高,级最高,班平均,级平均)
            
        grade_list.sort(key=lambda x: subject_order.index(x[1])) # 按照subject_order排序
        
        table.add_row(data_list)
        for _, subject, score, rank_class, rank_grade, highest_class, highest_grade, avg_class, avg_grade in grade_list:
            table.add_row([subject, score, rank_class, rank_grade, highest_class, highest_grade, avg_class, avg_grade])
        
        print(table)
        if input("(输入0导出结果至文件) 按回车键继续... ") == "0":
            with open(f"{name}.txt", "w", encoding="utf-8") as f:
                f.write(table.get_string())
                print("结果已导出至", f.name)
        
    def OnGetRankInfo(self):
        id = self.selected_examId
        url = f"https://hfs-be.yunxiao.com/v3/exam/{id}/rank-info"
        self.GET(url)
        
    def OnGetOverview(self):
        id = self.selected_examId
        url = f"https://hfs-be.yunxiao.com/v3/exam/{id}/overview"
        self.GET(url)

    def run(self):
        self.student_names = self.load_student_names()
        self.ChoiceUser()
        while True:
            print("\n当前学生:", self.selected_user if self.selected_user else "未登录")
            print("1. 登录")
            print("2. 选择学生")
            print("3. 查看考试")
            print("4. 查看所有 当前: " + ("开" if self.isListAll else "关"))
            print("0. 退出")
            choice = input("请选择操作: ")
            if choice == "1":
                self.Login()
            elif choice == "2":
                self.ChoiceUser()
            elif choice == "3":
                self.GetExamList()
            elif choice == "4":
                self.isListAll = not self.isListAll
                print("已切换查看考试列表状态: " + ("开" if self.isListAll else "关"))
            elif choice == "0":
                break
            else:
                print("无效选项，请重新选择！")

if __name__ == "__main__":
    app = CommandLineApp()
    app.run()
