# interface.py

import tkinter as tk
from tkinter import ttk, scrolledtext
from tkinter import messagebox
import hashlib
import requests
import json
import math
from datetime import datetime, timedelta
import threading

from inventory import Inventory, Item
from account_management import AccountManager
from Localinfo import search_titles

# *** 수정된 부분 ***: predict_demand와 함께 load_model_and_columns를 임포트
from Analyze import load_model_and_columns, predict_demand

# --- 1. 설정 부분 ---
KMA_API_KEY = "사용자값을 입력 사용자 값을 입력 사용자 값을 입력"
CITY_COORDINATES = {
    "서울": {"lat": 37.5665, "lon": 126.9780},
    "대구": {"lat": 35.8714, "lon": 128.6014}
}

CATEGORIES = ["문구", "생활용품", "전자기기", "음료", "식품", "기타"]
NEWS_KEYWORDS = ["축제", "행사", "사고", "정전", "공연", "폭염", "미세먼지"]


# --- 2. 헬퍼 함수 (날씨 API 관련) ---
def dfs_grid_conv(lat, lon):
    RE = 6371.00877; GRID = 5.0; SLAT1 = 30.0; SLAT2 = 60.0; OLON = 126.0; OLAT = 38.0; XO = 43; YO = 136
    DEGRAD = math.pi / 180.0
    re = RE / GRID; slat1 = SLAT1 * DEGRAD; slat2 = SLAT2 * DEGRAD; olon = OLON * DEGRAD; olat = OLAT * DEGRAD
    sn = math.tan(math.pi * 0.25 + slat2 * 0.5) / math.tan(math.pi * 0.25 + slat1 * 0.5)
    sn = math.log(math.cos(slat1) / math.cos(slat2)) / math.log(sn); sf = math.tan(math.pi * 0.25 + slat1 * 0.5)
    sf = (math.pow(sf, sn) * math.cos(slat1)) / sn; ro = math.tan(math.pi * 0.25 + olat * 0.5)
    ro = (re * sf) / math.pow(ro, sn); ra = math.tan(math.pi * 0.25 + lat * DEGRAD * 0.5)
    ra = (re * sf) / math.pow(ra, sn); theta = lon * DEGRAD - olon
    if theta > math.pi: theta -= 2.0 * math.pi
    if theta < -math.pi: theta += 2.0 * math.pi
    theta *= sn; x = math.floor(ra * math.sin(theta) + XO + 0.5); y = math.floor(ro - ra * math.cos(theta) + YO + 0.5)
    return int(x), int(y)

def get_kma_weather(lat, lon):
    if not KMA_API_KEY or '여기에' in KMA_API_KEY: return {"error": "기상청 API 키를 설정해주세요."}
    nx, ny = dfs_grid_conv(lat, lon)
    now = datetime.now() - timedelta(hours=1)
    base_date = now.strftime('%Y%m%d'); base_time = now.strftime('%H00')
    api_url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtFcst"
    params = {"serviceKey": KMA_API_KEY, "pageNo": "1", "numOfRows": "100", "dataType": "JSON",
              "base_date": base_date, "base_time": base_time, "nx": str(nx), "ny": str(ny)}
    try:
        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status(); data = response.json()
        if data['response']['header']['resultCode'] != '00': return {"error": f"API 오류: {data['response']['header']['resultMsg']}"}
        items = data['response']['body']['items']['item']; weather_info = {}
        category_map = {'T1H': '온도', 'RN1': '강수량', 'REH': '습도', 'PTY': '강수형태'}
        pty_map = {'0': '없음', '1': '비', '2': '비/눈', '3': '눈', '5': '빗방울', '6': '빗방울눈날림', '7': '눈날림'}
        for item in items:
            cat = item['category']; value = item.get('fcstValue')
            if cat in category_map and value is not None:
                if cat == 'PTY': weather_info[category_map[cat]] = pty_map.get(value, '정보 없음')
                else: weather_info[category_map[cat]] = value
        weather_info['is_raining'] = weather_info.get('강수형태', '없음') in ['비', '비/눈', '빗방울', '빗방울눈날림']
        return weather_info
    except Exception as e: return {"error": f"날씨 정보 처리 중 오류: {e}"}

# --- 3. 메인 애플리케이션 클래스 ---
class MainApp:
    def __init__(self, master):
        self.master = master
        self.master.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.account_manager = AccountManager()
        self.logged_in_user = None
        
        # *** 수정된 부분 ***: 반환되는 3개의 값을 각각 올바른 속성에 저장합니다.
        self.classifier, self.regressor, self.model_columns = load_model_and_columns()
        
        self.show_login_screen()

    def _on_closing(self): self.account_manager.close_connection(); self.master.destroy()
    def clear_screen(self):
        for widget in self.master.winfo_children(): widget.destroy()
    def show_login_screen(self):
        self.clear_screen(); self.logged_in_user = None
        self.master.title("Login"); self.master.geometry("400x250")
        tk.Label(self.master, text="로그인").pack(pady=20)
        tk.Label(self.master, text="아이디").pack()
        username_entry = tk.Entry(self.master); username_entry.pack(pady=5)
        tk.Label(self.master, text="비밀번호").pack()
        password_entry = tk.Entry(self.master, show="*"); password_entry.pack(pady=5)
        tk.Button(self.master, text="Login", command=lambda: self.handle_login(username_entry.get(), password_entry.get())).pack(pady=20)
    def handle_login(self, username, password):
        user = self.account_manager.login(username, password)
        if user: self.logged_in_user = user; self.show_main_menu()
        else: messagebox.showerror("로그인 실패", "아이디 또는 비밀번호가 잘못되었습니다.")
    def show_main_menu(self):
        self.clear_screen(); self.master.title("메인 메뉴")
        tk.Label(self.master, text=f"{self.logged_in_user.get_name()}님 로그인에 성공하였습니다.", font=("Arial", 12)).pack(pady=20)
        is_admin = self.account_manager.is_admin(self.logged_in_user)
        menu_frame = tk.Frame(self.master); menu_frame.pack(pady=10, padx=20, fill="x")
        if is_admin:
            self.master.geometry("450x450")
            weather_frame = tk.LabelFrame(menu_frame, text=f"'{self.logged_in_user.get_location()}' 날씨 정보", padx=10, pady=10); weather_frame.pack(pady=10, fill="x")
            self.update_weather_display(weather_frame, self.logged_in_user.get_location())
            tk.Button(menu_frame, text="사용자 인벤토리 조회", command=self.show_user_selection_for_inventory).pack(pady=5, fill="x")
            tk.Button(menu_frame, text="계정 생성", command=self.show_create_account_popup).pack(pady=5, fill="x")
            tk.Button(menu_frame, text="계정 삭제", command=self.show_delete_account_popup).pack(pady=5, fill="x")
        else:
            self.master.geometry("400x300")
            tk.Button(menu_frame, text="내 인벤토리 보기", command=self.open_my_inventory).pack(pady=5, fill="x", ipady=4)
            tk.Button(menu_frame, text="내 지역 날씨 정보 보기", command=self.show_weather_popup).pack(pady=5, fill="x", ipady=4)
        tk.Button(menu_frame, text="내 지역 소식 보기", command=self.show_news_popup).pack(pady=5, fill="x", ipady=4)
        tk.Button(self.master, text="로그아웃", command=self.show_login_screen).pack(side="bottom", pady=20)
    def update_weather_display(self, frame, location):
        for widget in frame.winfo_children(): widget.destroy()
        loading_label = tk.Label(frame, text="날씨 정보 로딩 중..."); loading_label.pack()
        self.master.update_idletasks()
        coords = CITY_COORDINATES.get(location)
        if not coords: loading_label.config(text=f"'{location}'에 대한 좌표 정보가 없습니다.", fg="red"); return
        weather = get_kma_weather(coords['lat'], coords['lon'])
        loading_label.destroy()
        if 'error' in weather: tk.Label(frame, text=weather['error'], fg="red").pack()
        else:
            display_data = {"현재 기온": f"{weather.get('온도', 'N/A')}°C", "현재 습도": f"{weather.get('습도', 'N/A')}%", "강수 형태": weather.get('강수형태', 'N/A'), "강수 여부": '예' if weather.get('is_raining') else '아니오'}
            for key, value in display_data.items():
                row_frame = tk.Frame(frame); row_frame.pack(fill="x")
                tk.Label(row_frame, text=f"  • {key}:", width=12, anchor='w').pack(side="left")
                tk.Label(row_frame, text=value, anchor='w').pack(side="left")
    def show_weather_popup(self):
        location = self.logged_in_user.get_location()
        popup = tk.Toplevel(self.master); popup.title(f"'{location}' 날씨 정보"); popup.geometry("350x220"); popup.transient(self.master); popup.grab_set()
        frame = tk.Frame(popup, padx=15, pady=15); frame.pack(fill=tk.BOTH, expand=True)
        loading_label = tk.Label(frame, text="날씨 정보 로딩 중..."); loading_label.pack(pady=20)
        self.master.update_idletasks()
        coords = CITY_COORDINATES.get(location)
        if not coords: loading_label.config(text=f"'{location}'에 대한 좌표 정보가 없습니다.", fg="red"); return
        weather = get_kma_weather(coords['lat'], coords['lon']); loading_label.destroy()
        if 'error' in weather: tk.Label(frame, text=weather['error'], fg="red").pack(pady=20)
        else:
            display_data = {"현재 기온": f"{weather.get('온도', 'N/A')}°C", "현재 습도": f"{weather.get('습도', 'N/A')}%", "강수 형태": weather.get('강수형태', 'N/A'), "강수 여부": '예' if weather.get('is_raining') else '아니오'}
            for key, value in display_data.items():
                row_frame = tk.Frame(frame); row_frame.pack(fill="x", pady=3)
                tk.Label(row_frame, text=f"  • {key}:", width=12, anchor='w').pack(side="left")
                tk.Label(row_frame, text=value, anchor='w').pack(side="left")
        tk.Button(frame, text="닫기", command=popup.destroy, width=10).pack(side="bottom", pady=20)
    def open_my_inventory(self): self.open_inventory_window(self.logged_in_user.get_id(), self.logged_in_user.get_name(), self, read_only=False)
    def open_inventory_window(self, user_id, user_name, main_app, read_only=False):
        inv = Inventory(); inventory_window = tk.Toplevel(self.master); inventory_window.title("인벤토리 관리"); inventory_window.geometry("800x500")
        InventoryUI(inventory_window, inv, user_id, user_name, main_app, read_only=read_only)
    def show_user_selection_for_inventory(self):
        view_window = tk.Toplevel(self.master); view_window.title("사용자 선택"); view_window.geometry("300x400")
        tk.Label(view_window, text="인벤토리를 조회할 사용자를 선택하세요.").pack(pady=10)
        listbox = tk.Listbox(view_window); listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        all_users = self.account_manager.get_all_users(exclude_admin=True); user_map = {f"{name} ({username})": (user_id, name) for user_id, name, username, location in all_users}
        for display_text in user_map.keys(): listbox.insert(tk.END, display_text)
        def on_view():
            try:
                selected_text = listbox.get(listbox.curselection())
                user_id, user_name = user_map[selected_text]
                self.open_inventory_window(user_id, user_name, self, True); view_window.destroy()
            except tk.TclError: messagebox.showwarning("선택 없음", "조회할 사용자를 선택하세요.", parent=view_window)
        tk.Button(view_window, text="선택한 사용자 인벤토리 조회", command=on_view).pack(pady=10)
    def show_news_popup(self):
        location = self.logged_in_user.get_location()
        popup = tk.Toplevel(self.master); popup.title(f"'{location}' 관련 최신 소식"); popup.geometry("600x400"); popup.transient(self.master); popup.grab_set()
        text_area = scrolledtext.ScrolledText(popup, wrap=tk.WORD, font=("Arial", 10)); text_area.pack(expand=True, fill='both', padx=10, pady=5)
        text_area.insert(tk.END, "최신 소식을 불러오는 중입니다..."); text_area.config(state='disabled')
        text_area.tag_config('bold', font=('Arial', 12, 'bold'))
        thread = threading.Thread(target=self.scrape_and_display_news, args=(location, text_area)); thread.daemon = True; thread.start()
    def scrape_and_display_news(self, location, text_area):
        results = search_titles(location, NEWS_KEYWORDS)
        text_area.config(state='normal'); text_area.delete('1.0', tk.END)
        for keyword, titles in results.items():
            text_area.insert(tk.END, f"\n📌 {location} + {keyword} 관련 소식\n", 'bold')
            if titles:
                for i, title in enumerate(titles, 1): text_area.insert(tk.END, f"  {i}. {title}\n")
            else: text_area.insert(tk.END, "  - 관련 소식을 찾을 수 없습니다.\n")
        text_area.config(state='disabled')
    def show_create_account_popup(self):
        popup = tk.Toplevel(self.master); popup.title("새 계정 생성")
        fields = {"아이디": tk.Entry(popup), "이름": tk.Entry(popup), "비밀번호": tk.Entry(popup, show="*")}
        for i, (text, entry) in enumerate(fields.items()):
            tk.Label(popup, text=text).grid(row=i, column=0, padx=10, pady=5, sticky="w"); entry.grid(row=i, column=1, padx=10, pady=5)
        tk.Label(popup, text="지역").grid(row=len(fields), column=0, padx=10, pady=5, sticky="w")
        location_combobox = ttk.Combobox(popup, values=list(CITY_COORDINATES.keys()), state="readonly"); location_combobox.grid(row=len(fields), column=1, padx=10, pady=5)
        if location_combobox['values']: location_combobox.current(0)
        def on_submit():
            try:
                location = location_combobox.get()
                if not location: messagebox.showerror("오류", "지역을 선택해주세요.", parent=popup); return
                self.account_manager.create_user(fields["아이디"].get(), fields["이름"].get(), fields["비밀번호"].get(), location)
                messagebox.showinfo("성공", "계정이 성공적으로 생성되었습니다.", parent=popup); popup.destroy()
            except ValueError as e: messagebox.showerror("오류", str(e), parent=popup)
        tk.Button(popup, text="생성", command=on_submit).grid(row=len(fields) + 1, columnspan=2, pady=10)
    def show_delete_account_popup(self):
        popup = tk.Toplevel(self.master); popup.title("계정 삭제"); listbox = tk.Listbox(popup); listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        users = self.account_manager.get_all_users(exclude_admin=True)
        for _, name, username, location in users: listbox.insert(tk.END, f"{name} ({username})")
        def on_delete():
            try:
                selected = listbox.get(listbox.curselection())
                username = selected[selected.rfind("(") + 1:-1]
                if messagebox.askyesno("확인", f"'{username}' 계정을 정말 삭제하시겠습니까?", parent=popup):
                    self.account_manager.delete_user(username)
                    messagebox.showinfo("성공", "계정이 삭제되었습니다.", parent=popup); popup.destroy()
            except tk.TclError: messagebox.showwarning("선택 없음", "삭제할 계정을 선택하세요.", parent=popup)
            except ValueError as e: messagebox.showerror("오류", str(e), parent=popup)
        tk.Button(popup, text="선택한 계정 삭제", command=on_delete).pack(pady=5)

# --- 4. 인벤토리 UI 클래스 ---
class InventoryUI:
    def __init__(self, master, db_inventory, user_id, user_name, main_app, read_only=False):
        self.master = master; self.inventory = db_inventory; self.user_id = user_id
        self.user_name = user_name; self.read_only = read_only
        self.main_app = main_app 
        self.frame = tk.Frame(master); self.frame.pack(fill=tk.BOTH, expand=True)
        self.draw_user_inventory()

    def draw_user_inventory(self):
        for widget in self.frame.winfo_children(): widget.destroy()
        label_text = f"'{self.user_name}'님의 인벤토리"
        if self.read_only: label_text += " (읽기 전용)"
        tk.Label(self.frame, text=label_text).pack(pady=10)
        btn_frame = tk.Frame(self.frame)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        tk.Frame(btn_frame).pack(side=tk.LEFT, expand=True) 
        if not self.read_only:
            tk.Button(btn_frame, text="➕ 추가", command=self.add_item_popup).pack(side=tk.LEFT, padx=5)
            tk.Button(btn_frame, text="✏️ 수정", command=self.edit_item_popup).pack(side=tk.LEFT, padx=5)
            tk.Button(btn_frame, text="❌ 삭제", command=self.delete_item).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="📈 수요 예측", command=self.run_demand_prediction).pack(side=tk.LEFT, padx=10)
        tk.Frame(btn_frame).pack(side=tk.LEFT, expand=True)
        columns = ("name", "item_id", "quantity", "price", "cost", "category")
        self.tree = ttk.Treeview(self.frame, columns=columns, show="headings")
        headings = {"name":"이름", "item_id":"자동 ID", "quantity":"수량", "price":"가격", "cost":"원가", "category":"카테고리"}
        for col, text in headings.items(): self.tree.heading(col, text=text)
        self.tree.column("name", width=120, anchor=tk.W); self.tree.column("item_id", width=130, anchor=tk.W)
        self.tree.column("quantity", width=60, anchor=tk.E); self.tree.column("price", width=90, anchor=tk.E)
        self.tree.column("cost", width=90, anchor=tk.E); self.tree.column("category", width=100, anchor=tk.W)
        self.tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.refresh_inventory()

    def run_demand_prediction(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("선택 없음", "수요를 예측할 항목을 선택하세요.", parent=self.master)
            return
        thread = threading.Thread(target=self._demand_prediction_thread, args=(selected[0],))
        thread.daemon = True
        thread.start()
        messagebox.showinfo("알림", "수요 예측을 시작합니다.\n날씨와 지역 소식 정보를 수집하는 데 시간이 걸릴 수 있습니다.", parent=self.master)
        
    def _demand_prediction_thread(self, selected_item):
        try:
            item_values = self.tree.item(selected_item)['values']
            item_name = item_values[0]
            category = item_values[5]
            user_location = self.main_app.logged_in_user.get_location()
            coords = CITY_COORDINATES.get(user_location, {})
            weather_data = get_kma_weather(coords.get('lat', 0), coords.get('lon', 0))
            event_data = search_titles(user_location, ["축제", "공연"]) 

            if "error" in weather_data:
                messagebox.showerror("오류", f"날씨 정보 수집 실패: {weather_data['error']}", parent=self.master)
                return

            # *** 수정된 부분 ***: predict_demand 함수에 올바른 인자(분류기, 회귀 모델)를 전달합니다.
            result = predict_demand(
                category, 
                weather_data, 
                event_data, 
                self.main_app.classifier, 
                self.main_app.regressor, 
                self.main_app.model_columns
            )
            
            messagebox.showinfo("수요 예측 결과", f"선택한 항목: {item_name}\n카테고리: {category}\n\n예측 결과: {result}", parent=self.master)
        except Exception as e:
            messagebox.showerror("예측 오류", f"수요 예측 중 오류가 발생했습니다: {e}", parent=self.master)

    def refresh_inventory(self):
        for row in self.tree.get_children(): self.tree.delete(row)
        items = self.inventory.list_items(self.user_id)
        for item in items: self.tree.insert("", "end", values=item.to_tuple())
    def add_item_popup(self): self._item_popup(mode="add")
    def edit_item_popup(self):
        selected = self.tree.selection()
        if not selected: messagebox.showwarning("경고", "수정할 항목을 선택하세요."); return
        self._item_popup(mode="edit", values=self.tree.item(selected[0])['values'])
    def delete_item(self):
        selected = self.tree.selection()
        if not selected: messagebox.showwarning("경고", "삭제할 항목을 선택하세요."); return
        item_id = self.tree.item(selected[0])['values'][1]; item_name = self.tree.item(selected[0])['values'][0]
        if messagebox.askyesno("확인", f"'{item_name}'({item_id}) 항목을 정말 삭제하시겠습니까?"):
            self.inventory.delete_item(self.user_id, item_id); self.refresh_inventory()
    def _item_popup(self, mode="add", values=None):
        popup = tk.Toplevel(self.master); popup.title("항목 추가" if mode == "add" else "항목 수정")
        fields = ["이름", "수량", "가격", "원가"]; entries = {}
        value_map = {"이름": values[0], "수량": values[2], "가격": values[3], "원가": values[4]} if values else {}
        if mode == "edit": original_item_id = values[1]
        for i, field in enumerate(fields):
            tk.Label(popup, text=field).grid(row=i, column=0, padx=5, pady=5, sticky='w')
            entry = tk.Entry(popup); entry.grid(row=i, column=1, padx=5, pady=5)
            if values: entry.insert(0, value_map.get(field, ""))
            entries[field] = entry
        tk.Label(popup, text="카테고리").grid(row=len(fields), column=0, padx=5, pady=5, sticky='w')
        category_combobox = ttk.Combobox(popup, values=CATEGORIES, state="readonly")
        category_combobox.grid(row=len(fields), column=1, padx=5, pady=5)
        if values and values[5] in CATEGORIES: category_combobox.set(values[5])
        else: category_combobox.current(0)
        def on_submit():
            try:
                name = entries["이름"].get(); quantity = int(entries["수량"].get())
                price = int(entries["가격"].get()); cost = int(entries["원가"].get())
                category = category_combobox.get()
                if not category: messagebox.showerror("오류", "카테고리를 선택하세요.", parent=popup); return
                if mode == "add":
                    item = Item(name=name, quantity=quantity, price=price, cost=cost, category=category)
                    self.inventory.add_item(self.user_id, item)
                else: 
                    new_item_id = hashlib.sha256(name.encode('utf-8')).hexdigest()[:16]
                    self.inventory.update_item(self.user_id, original_item_id, item_id=new_item_id, name=name, quantity=quantity, price=price, cost=cost, category=category)
                popup.destroy(); self.refresh_inventory()
            except ValueError as e: messagebox.showerror("오류", "수량, 가격, 원가는 숫자로 입력해야 합니다." if "invalid literal" in str(e) else str(e), parent=popup)
            except Exception as e: messagebox.showerror("오류", str(e), parent=popup)
        tk.Button(popup, text="확인", command=on_submit).grid(row=len(fields) + 1, columnspan=2, pady=10)

if __name__ == "__main__":
    try:
        import joblib, sklearn, pandas
    except ImportError:
        print("="*50 + "\n필수 라이브러리가 설치되지 않았습니다.\n터미널에 아래 명령어를 입력하여 설치해주세요.\npip install pandas scikit-learn joblib\n" + "="*50)
        exit()
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()

