import wx
import wx.html2
import requests
import json
import base64
import tempfile
import difflib
from collections import defaultdict



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
        super(MainFrame, self).__init__(parent, title="坏分数", size=(800, 600))

        # 设置图标
        icon = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAAXNSR0IArs4c6QAAAY9JREFUOE+l081LlFEYhvHf66RWk4yFgRRB1NAgYiYuW0QQuCloE9QiCNrYok0EOZt2odQ/4Cb6gCiIPiaCDOwLLCJtUVgWfdAmKFTEpiKx4cT0Srzm6GbO9tz3dR4O1xOFC4IqThQuVgu4lADUNpBKU/rJ7Lf5c6XqqV1N6QezxX93UbicALT30tLD+35GjsShcmnjQTItZLv5eJbhbsLvv9dRuJIAbO1l02GKb3myn50PWLmB8SGWN9G4jTeneXEiMcHVBKCuie23qFtDQy4OzXxl8hnr9hBKPN3H5xsJwLUEIJen9VR5sDgw/ZLnh+g8R6ad0i8KK+b9TRSuJwCbj7IlT1TD1AhjJ5keZe9MXBraxfi9/wA3E4BladJZmneT7WHyERMPaT1DOVaoWWBMFAoVPFh/gI7zcWlqmEwHr4/zqb8C4HYlkVLseMWqHBODhMDYMYqjFQB3FjGxc4C1XXHhQx/v8hWFj8LAEip3za3J4za+L3w9FunuEoD65jkXviy6blEYrHaZ7lcH+ANarILlCstN8wAAAABJRU5ErkJggg==")
        with open(tempfile.gettempdir() + "icon.png", "wb") as f:
            f.write(icon)
        self.SetIcon(wx.Icon(tempfile.gettempdir() + "icon.png"))
        
        self.token = None
        self.roleType = None
        self.res = None
        self.examId = []
        self.selected_examId = None
        self.isListAll = False
        
        self.InitUI()
        self.Centre()
        
    def InitUI(self):
        splitter = wx.SplitterWindow(self)
        
        # --------左面板--------
        self.left_panel = wx.ScrolledCanvas(splitter)
        wx.ScrolledCanvas.SetScrollRate(self.left_panel, 5, 5)
        self.grid_left = wx.GridBagSizer(5, 5)
        
        login_button = wx.Button(self.left_panel, label="登录")
        login_button.Bind(wx.EVT_BUTTON, self.OnLogin)
        self.grid_left.Add(login_button, pos=(0, 0), flag=wx.TOP | wx.LEFT, border=10)
        
        st = wx.StaticText(self.left_panel, label="当前登录账号:")
        self.grid_left.Add(st, pos=(0, 1), flag=wx.TOP | wx.ALIGN_RIGHT, border=15)
        
        self.choiceUser = wx.Choice(self.left_panel, choices=["未选择"] + self.load_student_names())
        self.choiceUser.SetSelection(0)  # 默认选择“未选择”
        self.choiceUser.Bind(wx.EVT_CHOICE, self.OnChoiceUser)
        self.grid_left.Add(self.choiceUser, (0, 2), (1, 2), flag=wx.EXPAND | wx.TOP, border=10)
        
        list_btn = wx.Button(self.left_panel, label="查看考试列表")
        list_btn.Bind(wx.EVT_BUTTON, self.OnGetExamList)
        self.grid_left.Add(list_btn, (0, 4), flag=wx.TOP | wx.LEFT, border=10)
        
        list_all_choice = wx.CheckBox(self.left_panel, label="查看所有", style=wx.ALIGN_RIGHT)
        list_all_choice.Bind(wx.EVT_CHECKBOX, self.OnSwitchListAll)
        self.grid_left.Add(list_all_choice, (0, 5), flag=wx.TOP, border=15)
        
        self.choiceExam = wx.Choice(self.left_panel, choices=["未选择"], size=(108, 30))
        self.choiceExam.SetSelection(0)
        self.choiceExam.Bind(wx.EVT_CHOICE, self.OnChoiceExam)
        self.grid_left.Add(self.choiceExam, (1, 0), (1, 3), flag=wx.EXPAND | wx.LEFT, border=10)
        
        self.rankinfoBtn = wx.Button(self.left_panel, label="查看排名信息")
        self.rankinfoBtn.Bind(wx.EVT_BUTTON, self.OnGetRankInfo)
        self.grid_left.Add(self.rankinfoBtn, (1, 3), flag=wx.LEFT, border=10)
        
        self.overviewBtn = wx.Button(self.left_panel, label="查看成绩概览")
        self.overviewBtn.Bind(wx.EVT_BUTTON, self.OnGetOverview)
        self.grid_left.Add(self.overviewBtn, (1, 4), flag=wx.LEFT, border=10)
        
        # --------信息面板--------
        self.info_panel = wx.Panel(self.left_panel)
        self.grid_left.Add(self.info_panel, (2, 0), (5, 6), flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)
        self.grid_left.AddGrowableRow(2)
        self.grid_left.AddGrowableCol(1)
        self.left_panel.SetSizerAndFit(self.grid_left)
        
        
        # --------右面板--------
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
    def OnSize(self, event):
        self.list_ctrl.SetSize((self.info_panel.GetSize()[0] - 20, self.info_panel.GetSize()[1] - 30 - 5 * 30))
        self.Layout()
    
    def OnWrap(self, event):
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

    def GET(self, url , isShowResbody:bool = False):
        """
        向url发送GET请求
        输入: 请求url, 是否把结果写入文本框
        输出: self.res = response.json()
        """
        headers = {
            "Cookie": f"hfs-session-id={self.token}"
        }

        try:
            response = requests.get(url, headers=headers)
            self.res = response.json()
            if isShowResbody:
                formatted_json = json.dumps(self.res, indent=4, ensure_ascii=False)
                self.tc.SetValue(formatted_json)
        except requests.exceptions.RequestException as e:
            if isShowResbody:
                self.tc.SetValue(f"请求失败：\n{e}")
        
    def GetExamList(self, event):
        self.OnGetExamList(event)
        self.choiceExam.Clear()
        self.examId = []
        select = self.choiceExam.GetSelection()
        if not self.isListAll: # 常规处理
            if not self.res:
                return
            for i in range(len(self.res["data"]["list"])):
                self.examId.append(self.res["data"]["list"][i]["examId"])
                self.choiceExam.AppendItems(str(self.res["data"]["list"][i]["name"]))
            if select != wx.NOT_FOUND:
                self.choiceExam.SetSelection(select)
            else:
                self.choiceExam.SetSelection(0)
                self.OnChoiceExam(event)
        else: # 调用导出错题api（获取学科信息）
            if self.choiceUser.GetStringSelection() == "未选择":
                return
            subject_data = self.res
            exam_dict = defaultdict(list) # 用于存储按考试名称合并的 examId
            for subject in subject_data['data']: # 遍历所有科目，收集 examName 和 examId
                for exam in subject['examList']:
                    exam_dict[exam['examName']].append(exam['examId'])
            sorted_exam_dict = {name: sorted(ids, key=int, reverse=True) # 按照 examId 倒序排序
                for name, ids in sorted(exam_dict.items(), key=lambda x: min(map(int, x[1])), reverse=True)}

            result = list(sorted_exam_dict.items()) # [(examName, [examId, examId, ...]), ...]
            for name, ids in result:
                self.examId.append(ids[0])
                self.choiceExam.AppendItems(name)
            if select != wx.NOT_FOUND:
                self.choiceExam.SetSelection(select)
            else:
                self.choiceExam.SetSelection(0)
                self.OnChoiceExam(event)
                
    def OnGetExamList(self, event):
        if self.choiceUser.GetStringSelection() == "未选择":
            return
        if self.isListAll:
            url = "https://hfs-be.yunxiao.com/v2/wrong-items/overview" # 导出错题api（获取学科信息）
        else:
            url = "https://hfs-be.yunxiao.com/v3/exam/list?start=0&limit=5"
        self.GET(url, True)

    def OnSwitchListAll(self, event):
        self.isListAll = not self.isListAll
        self.GetExamList(event)
        
    def OnChoiceExam(self, event):
        '''选择考试并解析json数据'''
        if self.choiceExam.GetStringSelection() == "未选择":
            return
        self.selected_examId = self.examId[self.choiceExam.GetSelection()]
        examId = self.selected_examId
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
                (f"班名:{rank_class}/{number_class}"),
                (f"级名：{rank_grade}/{number_grade}"),
                (f"总分：{score}/{fullscore}"),
                (f"班|级最高：{highest_class} | {highest_grade}"),
                (f"班|级平均：{avg_class} | {avg_grade}"),
                ("* 右键科目可查看答题卡")
            ]
        
        self.grade_list = []
        subject_order = ["语文", "数学", "英语", "物理", "化学", "生物", "政治", "历史", "地理"]
        for i in range(length_papers): # 各科成绩
            paperId = str(papers[i]["paperId"])
            subject_name = str(papers[i]["subject"])
            subject_score = str(papers[i]["score"])
            subject_fullscore = str(papers[i]["manfen"])
            self.GET(f"https://hfs-be.yunxiao.com/v3/exam/{examId}/papers/{paperId}/rank-info", False)
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
            self.grade_list.append((
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
            
        self.grade_list.sort(key=lambda x: subject_order.index(x[1])) # 按照subject_order排序
        
        for i, text in enumerate(data_list): # 显示信息
            st = wx.StaticText(self.info_panel, -1, text, pos=(10, 10 + i * 30))
            st.SetFont(wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))

        self.list_ctrl = wx.ListCtrl(self.info_panel, style=wx.LC_REPORT, pos=(10, 10 + (i + 1) * 30))
        self.list_ctrl.SetSize((self.info_panel.GetSize()[0] - 20, self.info_panel.GetSize()[1] - 20 - i * 30 - 10))
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnShowSubjectMenu)

        # 添加列
        self.list_ctrl.InsertColumn(0, "科目")
        self.list_ctrl.InsertColumn(1, "分数")
        self.list_ctrl.InsertColumn(2, "班名")
        self.list_ctrl.InsertColumn(3, "级名")
        self.list_ctrl.InsertColumn(4, "班最高")
        self.list_ctrl.InsertColumn(5, "级最高")
        self.list_ctrl.InsertColumn(6, "班平均")
        self.list_ctrl.InsertColumn(7, "级平均")
        
        # 添加行数据
        for _, subject, score, rank_class, rank_grade, highest_class, highest_grade, avg_class, avg_grade in self.grade_list:
            index = self.list_ctrl.InsertItem(self.list_ctrl.GetItemCount(), subject)
            self.list_ctrl.SetItem(index, 1, score)
            self.list_ctrl.SetItem(index, 2, rank_class)
            self.list_ctrl.SetItem(index, 3, rank_grade)
            self.list_ctrl.SetItem(index, 4, highest_class)
            self.list_ctrl.SetItem(index, 5, highest_grade)
            self.list_ctrl.SetItem(index, 6, avg_class)
            self.list_ctrl.SetItem(index, 7, avg_grade)
            self.list_ctrl.SetColumnWidth(index, wx.LIST_AUTOSIZE_USEHEADER)
        self.Bind(wx.EVT_SIZING, self.OnSize)
        self.info_panel.Layout()
        
    def OnGetRankInfo(self, event, IsResbody:bool = True):
        id = self.selected_examId
        url = f"https://hfs-be.yunxiao.com/v3/exam/{id}/rank-info"
        self.GET(url, IsResbody)
        
    def OnGetOverview(self, event, IsResbody:bool = True):
        id = self.selected_examId
        url = f"https://hfs-be.yunxiao.com/v3/exam/{id}/overview"
        self.GET(url, IsResbody)
        
    def OnShowSubjectMenu(self, event):
        menu = wx.Menu()
        item = menu.Append(-1, "查看答题卡")
        self.Bind(wx.EVT_MENU, self.OnShowAnswerSheet, item)
        self.PopupMenu(menu)

    def OnShowAnswerSheet(self, event):
        item_index = self.list_ctrl.GetFirstSelected()
        examId = self.selected_examId
        paperId = self.grade_list[item_index][0]
        token = self.token

        answer_sheet = AnswerSheetFrame(None, examId, paperId, token)
        answer_sheet.Show()
        
    def Clear(self, panel:wx.Panel):
        for child in panel.GetChildren():
            child.Destroy()
        panel.Layout()

class AnswerSheetFrame(wx.Frame):
    def __init__(self, parent, examId, paperId, token):
        super(AnswerSheetFrame, self).__init__(parent, title="查看答题卡", size=(1024, 768))
        self.SetIcon(wx.Icon(tempfile.gettempdir() + "icon.png"))
        
        # 创建 WebView 来显示网页
        self.url = f"https://www.haofenshu.com/answer-sheet?examId={examId}&paperId={paperId}"
        self.token = token
        self.browser:wx.html2.WebView = wx.html2.WebView.New(self)
        self.Maximize()
        self.browser.LoadURL(self.url)
        self.browser.Bind(wx.html2.EVT_WEBVIEW_LOADED, self.OnPageLoaded)
        
    def OnPageLoaded(self, event):
        # JavaScript 注入代码，将 token 保存到 localStorage (本地存储) 实现登录
        self.browser.RunScript(f"""
        localStorage.setItem('hfs-session-id', '{self.token}');
        location.reload();  // 刷新页面以使 localStorage 生效
        """)
        self.fix_the_fricking_shit_bug() # 凸_(^v^ +)/*
        
    def fix_the_fricking_shit_bug(self):
        # 关闭报错窗口
        import win32gui, win32con, os
        program_name = os.path.splitext(os.path.basename(__file__))[0]
        error_window_name = f"{program_name} Error".lower()
        def enum_windows_callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if error_window_name == title.lower():
                    win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
        # 枚举所有窗口
        win32gui.EnumWindows(enum_windows_callback, None)
        
app = wx.App()
frame = MainFrame(None)
frame.Show()
app.MainLoop()