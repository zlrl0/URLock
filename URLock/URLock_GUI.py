import os
import tkinter as tk
from tkinter import messagebox, simpledialog
from tkinter import filedialog
import sqlite3
import webbrowser
import qrcode
from PIL import Image, ImageDraw, ImageFont

# DB FILE
def init_db():
    if not os.path.exists("urls.db"):
        conn = sqlite3.connect("urls.db")
        c = conn.cursor()
        c.execute('''CREATE TABLE groups 
                     (id INTEGER PRIMARY KEY, group_name TEXT UNIQUE)''')
        c.execute('''CREATE TABLE urls 
                     (id INTEGER PRIMARY KEY, url TEXT, title TEXT, tags TEXT, description TEXT, click_count INTEGER DEFAULT 0)''')
        c.execute('''CREATE TABLE url_groups
                     (url_id INTEGER, group_id INTEGER, 
                      FOREIGN KEY(url_id) REFERENCES urls(id), 
                      FOREIGN KEY(group_id) REFERENCES groups(id))''')
        conn.commit()
        conn.close()
    else:
        conn = sqlite3.connect("urls.db")
        c = conn.cursor()
        c.execute("PRAGMA table_info(urls)")
        columns = [info[1] for info in c.fetchall()]
        if 'click_count' not in columns:
            c.execute("ALTER TABLE urls ADD COLUMN click_count INTEGER DEFAULT 0")
            conn.commit()
        conn.close()

# ADD URLS
def add_group_gui():
    group_name = simpledialog.askstring("새로운 그룹", "그룹 이름을 입력하세요:")
    if group_name:
        conn = sqlite3.connect("urls.db")
        c = conn.cursor()
        c.execute("SELECT * FROM groups WHERE group_name=?", (group_name,))
        if c.fetchone():
            messagebox.showwarning("경고", "이미 존재하는 그룹입니다.")
        else:
            c.execute("INSERT INTO groups (group_name) VALUES (?)", (group_name,))
            conn.commit()
            messagebox.showinfo("성공", f"그룹 '{group_name}'이(가) 성공적으로 추가되었습니다.")
        conn.close()


def add_url_gui():
    url = simpledialog.askstring("URL 입력", "URL을 입력하세요:")
    if url is None:  
        return  
    title = simpledialog.askstring("제목 입력", "제목을 입력하세요:")
    if title is None:
        return
    tags = simpledialog.askstring("태그 입력", "태그를 입력하세요:")
    if title is None:
        return
    description = simpledialog.askstring("설명 입력", "설명을 입력하세요:")
    if title is None:
        return
    group_name = simpledialog.askstring("그룹 입력", "URL을 추가할 그룹을 입력하세요 (없으면 빈칸):")
    if title is None:
        return
    
    if url and title and tags and description:
        conn = sqlite3.connect("urls.db")
        c = conn.cursor()

        c.execute("SELECT * FROM urls WHERE url=?", (url,))
        if c.fetchone():
            messagebox.showwarning("경고", "이미 존재하는 URL입니다.")
        else:
            c.execute("INSERT INTO urls (url, title, tags, description) VALUES (?, ?, ?, ?)", 
                      (url, title, tags, description))
            url_id = c.lastrowid

            if group_name:
                c.execute("SELECT id FROM groups WHERE group_name=?", (group_name,))
                group = c.fetchone()
                if group:
                    c.execute("INSERT INTO url_groups (url_id, group_id) VALUES (?, ?)", (url_id, group[0]))
                    messagebox.showinfo("성공", f"그룹 '{group_name}'에 URL이 추가되었습니다.")
                else:
                    messagebox.showwarning("경고", f"그룹 '{group_name}'이 존재하지 않으므로 URL을 그룹 없이 추가했습니다.")
            else:
                messagebox.showinfo("성공", "URL이 그룹 없이 추가되었습니다.")
            conn.commit()
        conn.close()

# URLS LIST
def view_urls_gui():
    def open_url(url_id):
        conn = sqlite3.connect("urls.db")
        c = conn.cursor()
        c.execute("SELECT url, click_count FROM urls WHERE id=?", (url_id,))
        url, click_count = c.fetchone()
        webbrowser.open(url)
        c.execute("UPDATE urls SET click_count = ? WHERE id=?", (click_count + 1, url_id))
        conn.commit()
        conn.close()

    def delete_url(result_window):
        selected = listbox.get(listbox.curselection())
        url_id = url_dict[selected]
        confirm = messagebox.askyesno("확인", "정말로 이 URL을 삭제하시겠습니까?")
        if confirm:
            conn = sqlite3.connect("urls.db")
            c = conn.cursor()

            c.execute("DELETE FROM url_groups WHERE url_id=?", (url_id,))

            c.execute("DELETE FROM urls WHERE id=?", (url_id,))
            conn.commit()
            conn.close()
            messagebox.showinfo("성공", "URL이 삭제되었습니다.")
            result_window.destroy()
            view_urls_gui()  

    conn = sqlite3.connect("urls.db")
    c = conn.cursor()
    c.execute('''SELECT u.id, u.url, u.title, u.tags, u.description, g.group_name, u.click_count
                 FROM urls u
                 LEFT JOIN url_groups ug ON u.id = ug.url_id
                 LEFT JOIN groups g ON ug.group_id = g.id
                 ORDER BY u.click_count DESC, u.id ASC''')
    urls = c.fetchall()

    if not urls:
        messagebox.showinfo("알림", "저장된 URL이 없습니다.")
    else:
        result_window = tk.Toplevel()
        result_window.title("URL 목록")
        result_window.geometry("600x400")

        listbox = tk.Listbox(result_window, width=80, height=20)
        listbox.pack(pady=10)

        url_dict = {}
        for url in urls:
            display_text = f"ID: {url[0]} / 제목: {url[2]} / {url[1]} / 그룹: {url[5]} / 클릭 수: {url[6]}"
            listbox.insert(tk.END, display_text)
            url_dict[display_text] = url[0]

        def on_select(event):
            selected = listbox.get(listbox.curselection())
            url_id = url_dict[selected]
            open_url(url_id)

        listbox.bind("<Double-1>", on_select)

        button_frame = tk.Frame(result_window)
        button_frame.pack(pady=10)

        def go_to_url():
            selected = listbox.get(listbox.curselection())
            url_id = url_dict[selected]
            open_url(url_id)

        go_button = tk.Button(button_frame, text="이동", command=go_to_url)
        go_button.pack(side=tk.LEFT, padx=10)

        delete_button = tk.Button(button_frame, text="삭제", command=lambda: delete_url(result_window))
        delete_button.pack(side=tk.RIGHT, padx=10)

    conn.close()


# SEARCH URLS
def search_urls_gui():
    search_term = simpledialog.askstring("검색", "검색어를 입력하세요:")
    if not search_term:
        messagebox.showwarning("경고", "검색어를 입력해야 합니다.")
        return

    conn = sqlite3.connect("urls.db")
    c = conn.cursor()
    c.execute('''
        SELECT u.id, u.url, u.title, u.tags, u.description, g.group_name
        FROM urls u
        LEFT JOIN url_groups ug ON u.id = ug.url_id
        LEFT JOIN groups g ON ug.group_id = g.id
        WHERE u.url LIKE ? OR u.title LIKE ? OR u.tags LIKE ? OR u.description LIKE ? OR g.group_name LIKE ?
    ''', ('%' + search_term + '%', '%' + search_term + '%', '%' + search_term + '%', '%' + search_term + '%', '%' + search_term + '%'))
    results = c.fetchall()
    conn.close()

    if not results:
        messagebox.showinfo("검색 결과", "검색 결과가 없습니다.")
    else:
        result_window = tk.Toplevel()
        result_window.title("검색 결과")
        result_window.geometry("600x400")

        listbox = tk.Listbox(result_window, width=80, height=20)
        listbox.pack(pady=10)

        url_dict = {}
        for url in results:
            display_text = f"ID: {url[0]} 제목: {url[2]} URL: {url[1]} 그룹: {url[5]} 태그: {url[3]} 설명: {url[4]}"
            listbox.insert(tk.END, display_text)
            url_dict[display_text] = url[0]

        def on_select(event):
            selected = listbox.get(listbox.curselection())
            url_id = url_dict[selected]
            conn = sqlite3.connect("urls.db")
            c = conn.cursor()
            c.execute("SELECT url FROM urls WHERE id=?", (url_id,))
            url_data = c.fetchone()
            conn.close()
            if url_data:
                webbrowser.open(url_data[0])

        listbox.bind("<Double-1>", on_select)

# URLS QR CODE
def generate_qr_code_gui():
    conn = sqlite3.connect("urls.db")
    c = conn.cursor()
    c.execute('''SELECT id, url, title FROM urls''')
    urls = c.fetchall()
    conn.close()

    if not urls:
        messagebox.showinfo("알림", "저장된 URL이 없습니다.")
        return

    result_window = tk.Toplevel()
    result_window.title("QR 코드 생성")
    result_window.geometry("400x300")

    listbox = tk.Listbox(result_window, width=60, height=10)
    listbox.pack(pady=10)

    url_dict = {}
    for url in urls:
        display_text = f"ID: {url[0]} / 제목: {url[2]} / URL: {url[1]}"
        listbox.insert(tk.END, display_text)
        url_dict[display_text] = url[0]

    def on_select(event):
        selected = listbox.get(listbox.curselection())
        url_id = url_dict[selected]

        conn = sqlite3.connect("urls.db")
        c = conn.cursor()
        c.execute("SELECT url, title FROM urls WHERE id=?", (url_id,))
        url_data = c.fetchone()
        conn.close()

        if url_data:
            url, title = url_data
            filename = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])

            if filename:
                qr = qrcode.QRCode(version=1, box_size=10, border=4)
                qr.add_data(url)
                qr.make(fit=True)
                img = qr.make_image(fill="black", back_color="white")

                draw = ImageDraw.Draw(img)
                font = ImageFont.load_default()

                text_width, text_height = draw.textbbox((0, 0), title, font=font)[2:]
                text_position = (img.width // 2 - text_width // 2, img.height - text_height - 10)

                draw.text(text_position, title, font=font, fill="black")

                img.save(filename)
                messagebox.showinfo("성공", f"QR 코드가 '{filename}'로 저장되었습니다.")

            result_window.destroy() 
        else:
            messagebox.showwarning("경고", "선택된 URL에 대한 정보가 존재하지 않습니다.")

    listbox.bind("<Double-1>", on_select)  




# GUI WINDOW
def create_gui():
    init_db()
    window = tk.Tk()
    window.title("URLock")
    window.geometry("400x300")

    # BUTTONS
    add_url_button = tk.Button(window, text="URL 추가", command=add_url_gui)
    add_url_button.pack(pady=10)

    view_urls_button = tk.Button(window, text="URL 목록 보기", command=view_urls_gui)
    view_urls_button.pack(pady=10)

    search_urls_button = tk.Button(window, text="URL 검색", command=search_urls_gui)
    search_urls_button.pack(pady=10)

    add_group_button = tk.Button(window, text="그룹 추가", command=add_group_gui)
    add_group_button.pack(pady=10)

    generate_qr_button = tk.Button(window, text="QR 코드 생성", command=generate_qr_code_gui)
    generate_qr_button.pack(pady=10)

    exit_button = tk.Button(window, text="종료", command=window.quit)
    exit_button.pack(pady=20)

    window.focus_set()

    window.mainloop()

if __name__ == "__main__":
    create_gui()
