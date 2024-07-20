import wx
import requests
import json
import base64



class LoginDialog(wx.Dialog):
    def __init__(self, parent, MainFrame):
        super(LoginDialog, self).__init__(parent, title="登录", size=(300, 180))
        self.MainFrame = MainFrame
        self.InitUI()
        self.Centre()
        
    def InitUI(self):
        panel = wx.Panel(self)
        sizer = wx.GridBagSizer(5, 5)
        
        st = wx.StaticText(panel, -1, "用户名")
        self.userName = wx.TextCtrl(panel)
        sizer.Add(st, (0, 0), flag=wx.TOP | wx.LEFT | wx.ALIGN_RIGHT, border=20)
        sizer.Add(self.userName, (0, 1), (1, 2), flag=wx.EXPAND | wx.TOP | wx.RIGHT, border=20)
        
        st = wx.StaticText(panel, -1, "密码")
        self.password = wx.TextCtrl(panel, style=wx.TE_PASSWORD)
        sizer.Add(st, (1, 0), flag=wx.ALIGN_RIGHT, border=20)
        sizer.Add(self.password, (1, 1), (1, 2), flag=wx.EXPAND | wx.RIGHT, border=20)
        
        btn_parent = wx.Button(panel, label="家长版", size=(90, -1))
        btn_student = wx.Button(panel, label="学生版", size=(90, -1))
        sizer.Add(btn_parent, (2, 1), (1, 1), flag=wx.ALIGN_CENTER_HORIZONTAL)
        sizer.Add(btn_student, (2, 2), (1, 1), flag=wx.ALIGN_CENTER_HORIZONTAL | wx.RIGHT, border=20)
        
        sizer.AddGrowableCol(2)
        
        btn_parent.Bind(wx.EVT_BUTTON, self.on_login(2))
        btn_student.Bind(wx.EVT_BUTTON, self.on_login(1))
        
        panel.SetSizer(sizer)
        panel.Layout()
        
    def on_login(self, roleType):
        def handler(event):
            username = self.userName.GetValue()
            password = self.password.GetValue()
            password_b64 = base64.b64encode(password.encode()).decode()
            msg, token = self.get_token(username, password_b64, roleType)
            if token:
                student_name = self.get_student_name(token)
                self.MainFrame.update_token(token, roleType)
                self.MainFrame.update_choiceUser(student_name)
                wx.MessageBox(f"Msg: {msg}\nToken: {token}", "提示", wx.OK | wx.ICON_INFORMATION)
                self.Close()
            else:
                wx.MessageBox(f"登录失败！\nMsg: {msg}", "错误", wx.OK | wx.ICON_ERROR)
                
        return handler
    
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
        msg = response_data.get("msg")
        try:
            token = response_data.get("data").get("token")
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
        student_name = response_data.get("data", {}).get("linkedStudent", {}).get("studentName", "")
        return student_name

    # 存储用户登录Token
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
        
class MainFrame(wx.Frame):
    def __init__(self,parent):
        super(MainFrame, self).__init__(parent, title="好分数PY", size=(800, 600))
        
        self.token = None
        self.roleType = None
        self.response_data = None
        self.examId = []
        self.selectedExamId = None

        self.InitUI()
        self.Centre()
        
    def InitUI(self):
        splitter = wx.SplitterWindow(self)
        
        # 左面板
        self.left_panel = wx.ScrolledCanvas(splitter)
        wx.ScrolledCanvas.SetScrollRate(self.left_panel, 5, 5)
        grid_left = wx.GridBagSizer(5, 5)
        
        login_button = wx.Button(self.left_panel, label="登录")
        login_button.Bind(wx.EVT_BUTTON, self.OnLogin)
        grid_left.Add(login_button, pos=(0, 0), flag=wx.TOP | wx.LEFT, border=10)
        
        st = wx.StaticText(self.left_panel, label="当前登录账号:")
        grid_left.Add(st, pos=(0, 1), flag=wx.TOP | wx.ALIGN_RIGHT, border=15)
        
        self.choiceUser = wx.Choice(self.left_panel, choices=["未选择"] + self.load_student_names())
        self.choiceUser.SetSelection(0)  # 默认选择“未选择”
        self.choiceUser.Bind(wx.EVT_CHOICE, self.OnChoiceUser)
        grid_left.Add(self.choiceUser, (0, 2), (1, 2), flag=wx.EXPAND | wx.TOP, border=10)
        
        list_btn = wx.Button(self.left_panel, label="查看考试列表")
        list_btn.Bind(wx.EVT_BUTTON, self.OnGetExamList)
        grid_left.Add(list_btn, (0, 4), flag=wx.TOP | wx.LEFT, border=10)
        
        self.choiceExam = wx.Choice(self.left_panel, choices=["未选择"])
        self.choiceExam.SetSelection(0)
        self.choiceExam.Bind(wx.EVT_CHOICE, self.OnChoiceExam)
        grid_left.Add(self.choiceExam, (1, 0), (1, 3), flag=wx.EXPAND | wx.LEFT, border=10)
        
        self.rankinfoBtn = wx.Button(self.left_panel, label="查看排名信息")
        self.rankinfoBtn.Bind(wx.EVT_BUTTON, self.OnGetRankInfo)
        grid_left.Add(self.rankinfoBtn, (1, 3), flag=wx.LEFT, border=10)
        
        self.overviewBtn = wx.Button(self.left_panel, label="查看成绩概览")
        self.overviewBtn.Bind(wx.EVT_BUTTON, self.OnGetOverview)
        grid_left.Add(self.overviewBtn, (1, 4), flag=wx.LEFT, border=10)
        
        # 信息面板
        self.info_panel = wx.ScrolledCanvas(self.left_panel)
        grid_left.Add(self.info_panel, (2, 0), (5, 5), flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)
        
        self.left_panel.SetSizerAndFit(grid_left)
        grid_left.AddGrowableRow(2)
        
        # 右面板
        self.right_panel = wx.Panel(splitter)
        self.grid_right = wx.GridBagSizer(5, 5)
        
        response_label = wx.StaticText(self.right_panel, label="响应体：")
        self.grid_right.Add(response_label, (0, 0), flag=wx.TOP, border=10)
        
        self.wrap_checkbox = wx.CheckBox(self.right_panel, label="自动换行", style=wx.ALIGN_RIGHT)
        self.grid_right.Add(self.wrap_checkbox, (0, 1), flag=wx.ALIGN_RIGHT | wx.TOP | wx.RIGHT, border=10)
        self.wrap_checkbox.Bind(wx.EVT_CHECKBOX, self.OnWrap)
        
        self.tc = wx.TextCtrl(self.right_panel, style=wx.TE_MULTILINE | wx.TE_DONTWRAP)
        self.grid_right.Add(self.tc,(1, 0), (1, 2), flag=wx.EXPAND | wx.ALL, border=0)
        self.tc.Bind(wx.EVT_ENTER_WINDOW, self.OnFocus)
        self.tc.Bind(wx.EVT_LEAVE_WINDOW, self.OnUnFocus)
        
        self.grid_right.AddGrowableRow(1)  # 第2行（文本框）可扩展
        self.grid_right.AddGrowableCol(1)  # 第2列可扩展
        
        self.right_panel.SetSizerAndFit(self.grid_right)
        splitter.SplitVertically(self.left_panel, self.right_panel, sashPosition=-300)
        splitter.SetSashGravity(1) # 窗口固定大小
        
        self.Layout()
        
    def OnFocus(self, event):
        self.tc.SetFocus()
    def OnUnFocus(self, event):
        self.left_panel.SetFocus()
    
    def OnWrap(self, event): # 代码复用真的是太方便了口牙！
        value = self.tc.GetValue()
        current_style = self.tc.GetWindowStyleFlag()
        if current_style & wx.TE_DONTWRAP:
            new_style = current_style & ~wx.TE_DONTWRAP
            self.wrap_checkbox.SetValue(True)
        else:
            new_style = current_style | wx.TE_DONTWRAP
            self.wrap_checkbox.SetValue(False)
        self.tc.Destroy()
        self.tc = wx.TextCtrl(self.right_panel, style=new_style | wx.TE_MULTILINE)
        self.grid_right.Add(self.tc, (1, 0), (1, 2), flag=wx.EXPAND | wx.ALL, border=0)
        self.tc.SetValue(value)
        self.tc.Bind(wx.EVT_ENTER_WINDOW, self.OnFocus)
        self.tc.Bind(wx.EVT_LEAVE_WINDOW, self.OnUnFocus)
        self.grid_right.Layout()
    
    def load_student_names(self):
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            student_name = [entry["student_name"] for entry in data]
            return student_name
        except FileNotFoundError:
            return []
    
    def load_config(self, student_name):
        with open('config.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            for entry in data:
                if entry["student_name"] == student_name:
                    return entry["token"], entry["roleType"]
        
    def update_choiceUser(self,student_name=None):
        self.choiceUser.Clear()
        student_names = self.load_student_names()
        self.choiceUser.AppendItems(student_names)
        if student_name:
            index = self.choiceUser.FindString(student_name)
            if index != wx.NOT_FOUND:
                self.choiceUser.SetSelection(index)
                self.OnChoiceUser(None)
        
    def OnChoiceUser(self, event):
        if self.choiceUser.GetStringSelection() != "未选择":
            token, roleType = self.load_config(self.choiceUser.GetStringSelection())
            self.update_token(token, roleType)
            self.GetExamList(event)
        
    
    def OnLogin(self,event):
        dialog = LoginDialog(None, self)
        dialog.ShowModal()
        dialog.Destroy()
        
    def update_token(self, token, roleType):
        self.token = token
        self.roleType = roleType

    def GET(self, url , resbody:bool = False):
        """
        向url发送GET请求
        输入: (请求url,是否把响应体写入文本框)
        输出: self.res = response.json()
        """
        headers = {
            "Cookie": f"hfs-session-id={self.token}"
        }
        try:
            response = requests.get(url, headers=headers)
            self.res = response.json()
            if resbody:
                formatted_json = json.dumps(self.res, indent=4, ensure_ascii=False)
                self.tc.SetValue(formatted_json)
        except requests.exceptions.RequestException as e:
            if resbody:
                self.tc.SetValue(f"请求失败：\n{e}")
        
    def GetExamList(self, event):
        self.OnGetExamList(event)
        self.choiceExam.Clear()
        self.examId = []
        select = self.choiceExam.GetSelection()
        for i in range(len(self.res["data"]["list"])):
            self.examId.append(self.res["data"]["list"][i]["examId"])
            self.choiceExam.AppendItems(str(self.res["data"]["list"][i]["name"]))
        if select != wx.NOT_FOUND:
            self.choiceExam.SetSelection(select)
        else:
            self.choiceExam.SetSelection(0)
        self.OnChoiceExam(event)
    
    def OnGetExamList(self, event):
        if self.choiceUser.GetStringSelection() == "未选择":
            return
        url = "https://hfs-be.yunxiao.com/v3/exam/list?start=0&limit=5"
        self.GET(url, True)

        
    def OnChoiceExam(self, event):
        if self.choiceExam.GetStringSelection() == "未选择":
            return
        self.selectedExamId = self.examId[self.choiceExam.GetSelection()]
        self.Clear(self.info_panel)
        self.OnGetRankInfo(event, False)
        data = self.res["data"]
        highest_class = str(data["highest"]["class"])
        highest_grade = str(data["highest"]["grade"])
        avg_class = str(data["avg"]["class"])
        avg_grade = str(data["avg"]["grade"])
        rank_class = str(data["rank"]["class"])
        rank_grade = str(data["rank"]["grade"])
        number_class = str(data["number"]["class"])
        number_grade = str(data["number"]["grade"])
        self.OnGetOverview(event, False)
        data = self.res["data"]
        score = str(data["score"])
        fullscore = str(data["manfen"])
        papers = self.res["data"]["papers"]
        length_papers = len(papers)
        
        data_list = [
                (f"班级排名:{rank_class}/{number_class}"),
                (f"级部排名：{rank_grade}/{number_grade}"),
                (f"总分：{score}/{fullscore}"),
                (f"最高分：{highest_class} | {highest_grade}"),
                (f"平均分：{avg_class} | {avg_grade}"),
                ("")
            ]
        for i in range(length_papers):
            subject_name = str(papers[i]["subject"])
            paper_score = str(papers[i]["score"])
            paper_fullscore = str(papers[i]["manfen"])
            data_list.append((f"{subject_name}: {paper_score}/{paper_fullscore}"))
        
        for i, text in enumerate(data_list):
            st = wx.StaticText(self.info_panel, -1, text, pos=(10, 10 + i * 30))
            st.SetFont(wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            
    def OnGetRankInfo(self, event, IsResbody:bool = True):
        id = self.selectedExamId
        url = f"https://hfs-be.yunxiao.com/v3/exam/{id}/rank-info"
        self.GET(url, IsResbody)
        
    def OnGetOverview(self, event, IsResbody:bool = True):
        id = self.selectedExamId
        url = f"https://hfs-be.yunxiao.com/v3/exam/{id}/overview"
        self.GET(url, IsResbody)
        
    def Clear(self, panel:wx.Panel):
        for child in panel.GetChildren():
            child.Destroy()
    
        
    
app = wx.App()
frame = MainFrame(None)
frame.Show()
app.MainLoop()