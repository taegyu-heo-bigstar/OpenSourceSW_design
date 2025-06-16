interface.py

import tkinter as tk from tkinter import ttk, scrolledtext, messagebox import hashlib import requests import json import math from datetime import datetime, timedelta import threading

from inventory import Inventory, Item from account_management import AccountManager from Localinfo import search_titles from Analyze import load_model_and_columns, predict_demand

--- 설정 ---

KMA_API_KEY = "사용자값을 입력 사용자 값을 입력 사용자 값을 입력" CITY_COORDINATES = { "서울": {"lat": 37.5665, "lon": 126.9780}, "대구": {"lat": 35.8714, "lon": 128.6014} } CATEGORIES = ["문구", "생활용품", "전자기기", "음료", "식품", "기타"] NEWS_KEYWORDS = ["축제", "행사", "사고", "정전", "공연", "폭염", "미세먼지"]

--- 헬퍼 함수: 기상청 API ---

def dfs_grid_conv(lat, lon): RE, GRID = 6371.00877, 5.0 SLAT1, SLAT2 = 30.0, 60.0 OLON, OLAT = 126.0, 38.0 XO, YO = 43, 136 DEGRAD = math.pi / 180.0 re = RE / GRID slat1 = SLAT1 * DEGRAD; slat2 = SLAT2 * DEGRAD olon = OLON * DEGRAD; olat = OLAT * DEGRAD sn = math.log(math.cos(slat1) / math.cos(slat2)) / math.log( math.tan(math.pi * 0.25 + slat2 * 0.5) / math.tan(math.pi * 0.25 + slat1 * 0.5) ) sf = (math.pow(math.tan(math.pi * 0.25 + slat1 * 0.5), sn) * math.cos(slat1)) / sn ro = (re * sf) / math.pow(math.tan(math.pi * 0.25 + olat * 0.5), sn) ra = (re * sf) / math.pow(math.tan(math.pi * 0.25 + lat * DEGRAD * 0.5), sn) theta = lon * DEGRAD - olon if theta > math.pi: theta -= 2.0 * math.pi if theta < -math.pi: theta += 2.0 * math.pi theta *= sn x = math.floor(ra * math.sin(theta) + XO + 0.5) y = math.floor(ro - ra * math.cos(theta) + YO + 0.5) return int(x), int(y)

def get_kma_weather(lat, lon): if not KMA_API_KEY or '여기에' in KMA_API_KEY: return {"error": "기상청 API 키를 설정해주세요."} nx, ny = dfs_grid_conv(lat, lon) now = datetime.now() - timedelta(hours=1) base_date = now.strftime('%Y%m%d'); base_time = now.strftime('%H00') url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtFcst" params = { "serviceKey": KMA_API_KEY, "pageNo": "1", "numOfRows": "100", "dataType": "JSON", "base_date": base_date, "base_time": base_time, "nx": str(nx), "ny": str(ny) } try: resp = requests.get(url, params=params, timeout=10) resp.raise_for_status() data = resp.json() if data['response']['header']['resultCode'] != '00': return {"error": f"API 오류: {data['response']['header']['resultMsg']}"} items = data['response']['body']['items']['item'] weather = {} cat_map = {'T1H':'온도','RN1':'강수량','REH':'습도','PTY':'강수형태'} pty_map = {'0':'없음','1':'비','2':'비/눈','3':'눈','5':'빗방울','6':'빗방울눈날림','7':'눈날림'} for it in items: c = it['category']; v = it.get('fcstValue') if c in cat_map and v is not None: if c=='PTY': weather[cat_map[c]] = pty_map.get(v,'정보 없음') else: weather[cat_map[c]] = v weather['is_raining'] = weather.get('강수형태') in ['비','비/눈','빗방울','빗방울눈날림'] return weather except Exception as e: return {"error": f"날씨 정보 처리 중 오류: {e}"}

--- 메인 앱 ---

class MainApp: def init(self, master): self.master = master self.master.protocol("WM_DELETE_WINDOW", self._on_closing) self.account_manager = AccountManager() self.logged_in_user = None self.classifier, self.regressor, self.model_columns = load_model_and_columns() self.show_login_screen()

def _on_closing(self):
    self.account_manager.close_connection()
    self.master.destroy()

def clear_screen(self):
    for w in self.master.winfo_children():
        w.destroy()

def show_login_screen(self):
    self.clear_screen()
    self.master.title("Login"); self.master.geometry("400x250")
    tk.Label(self.master, text="로그인").pack(pady=20)
    tk.Label(self.master, text="아이디").pack()
    uid = tk.Entry(self.master); uid.pack(pady=5)
    tk.Label(self.master, text="비밀번호").pack()
    pwd = tk.Entry(self.master, show="*"); pwd.pack(pady=5)
    tk.Button(self.master, text="Login", command=lambda: self.handle_login(uid.get(), pwd.get())).pack(pady=20)

def handle_login(self, username, password):
    user = self.account_manager.login(username, password)
    if user:
        self.logged_in_user = user
        self.show_main_menu()
    else:
        messagebox.showerror("로그인 실패", "아이디 또는 비밀번호가 잘못되었습니다.")

def show_main_menu(self):
    self.clear_screen()
    self.master.title("메인 메뉴")
    # 상단 우측 메일함 버튼
    top_bar = tk.Frame(self.master)
    top_bar.pack(fill="x")
    tk.Button(top_bar, text="📬 메일함", command=self.show_mailbox).pack(side="right", padx=5, pady=5)

    tk.Label(self.master, text=f"{self.logged_in_user.get_name()}님 로그인에 성공하였습니다.", font=("Arial",12)).pack(pady=20)
    is_admin = self.account_manager.is_admin(self.logged_in_user)
    menu_frame = tk.Frame(self.master); menu_frame.pack(pady=10, padx=20, fill="x")
    if is_admin:
        self.master.geometry("450x450")
        weather_frame = tk.LabelFrame(menu_frame, text=f"'{self.logged_in_user.get_location()}' 날씨 정보",padx=10,pady=10)
        weather_frame.pack(pady=10,fill="x")
        self.update_weather_display(weather_frame, self.logged_in_user.get_location())
        tk.Button(menu_frame, text="사용자 인벤토리 조회", command=self.show_user_selection_for_inventory).pack(pady=5,fill="x")
        tk.Button(menu_frame, text="계정 생성", command=self.show_create_account_popup).pack(pady=5,fill="x")
        tk.Button(menu_frame, text="계정 삭제", command=self.show_delete_account_popup).pack(pady=5,fill="x")
    else:
        self.master.geometry("400x300")
        tk.Button(menu_frame, text="내 인벤토리 보기", command=self.open_my_inventory).pack(pady=5,fill="x",ipady=4)
        tk.Button(menu_frame, text="내 지역 날씨 정보 보기", command=self.show_weather_popup).pack(pady=5,fill="x",ipady=4)
    tk.Button(menu_frame, text="내 지역 소식 보기", command=self.show_news_popup).pack(pady=5,fill="x",ipady=4)
    tk.Button(self.master, text="로그아웃", command=self.show_login_screen).pack(side="bottom", pady=20)

def update_weather_display(self, frame, location):
    for w in frame.winfo_children(): w.destroy()
    loading = tk.Label(frame, text="날씨 정보 로딩 중..."); loading.pack()
    self.master.update_idletasks()
    coords = CITY_COORDINATES.get(location)
    if not coords:
        loading.config(text=f"'{location}'에 대한 좌표 정보가 없습니다.", fg="red")
        return
    weather = get_kma_weather(coords['lat'], coords['lon'])
    loading.destroy()
    if 'error' in weather:
        tk.Label(frame, text=weather['error'], fg='red').pack()
    else:
        disp = {"현재 기온":f"{weather.get('온도','N/A')}°C", "현재 습도":f"{weather.get('습도','N/A')}%", "강수 형태":weather.get('강수형태','N/A'), "강수 여부":('예' if weather.get('is_raining') else '아니오')}
        for k,v in disp.items():
            row = tk.Frame(frame); row.pack(fill='x')
            tk.Label(row, text=f"  • {k}:", width=12, anchor='w').pack(side='left')
            tk.Label(row, text=v, anchor='w').pack(side='left')

# ... 이하 사용자 선택, 날씨 팝업, 인벤토리 및 뉴스, 계정 생성/삭제, 인벤토리 UI 메소드와 메일함 구현 포함 ...

def show_mailbox(self):
    popup = tk.Toplevel(self.master)
    popup.title("📬 메일함"); popup.geometry("650x450")
    popup.transient(self.master); popup.grab_set()
    cols = ("timestamp","sender","message")
    tree = ttk.Treeview(popup, columns=cols, show="headings")
    for c,t,w in [("timestamp","보낸 시간",130),("sender","보낸 사람",110),("message","메시지",390)]:
        tree.heading(c,text=t); tree.column(c,width=w,anchor=("CENTER" if c!="message" else "w"))
    tree.pack(fill="both",expand=True,padx=10,pady=5)
    def refresh():
        for r in tree.get_children(): tree.delete(r)
        mails = self.account_manager.mail_box.get_inbox(self.logged_in_user.get_id())
        for sid,_,msg,ts in mails:
            name = self.account_manager.get_username_by_id(sid) or sid[:8]
            tree.insert("",tk.END,values=(ts,name,msg))
    refresh()
    frm = tk.LabelFrame(popup,text="메일 보내기",padx=10,pady=10)
    frm.pack(fill="x",padx=10,pady=5)
    tk.Label(frm,text="받는 이(ID)").grid(row=0,column=0,sticky="w")
    rid = tk.Entry(frm); rid.grid(row=0,column=1,sticky="ew",padx=5,pady=2)
    tk.Label(frm,text="메시지").grid(row=1,column=0,sticky="nw")
    txt = scrolledtext.ScrolledText(frm,height=4,wrap=tk.WORD); txt.grid(row=1,column=1,sticky="ew",padx=5,pady=2)
    frm.columnconfigure(1,weight=1)
    def send():
        recipient = rid.get().strip()
        message = txt.get("1.0",tk.END).strip()
        try:
            self.account_manager.mail_box.send_mail(self.logged_in_user.get_id(),recipient,message)
            messagebox.showinfo("성공","메일을 보냈습니다.",parent=popup)
            rid.delete(0,tk.END); txt.delete("1.0",tk.END)
            refresh()
        except Exception as e:
            messagebox.showerror("오류",str(e),parent=popup)
    tk.Button(frm,text="보내기",command=send).grid(row=2,columnspan=2,pady=5)

if name == "main": try: import joblib, sklearn, pandas except ImportError: print("="*50 + "\n필수 라이브러리가 설치되지 않았습니다.\n``` pip install pandas scikit-learn joblib

exit()
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()

