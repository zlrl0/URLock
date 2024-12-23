import sqlite3
import os
import webbrowser
from PIL import Image, ImageDraw, ImageFont
import qrcode

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


def add_group():
    group_name = input("새로운 그룹 이름을 입력하세요: ").strip()

    conn = sqlite3.connect("urls.db")
    c = conn.cursor()
    c.execute("SELECT * FROM groups WHERE group_name=?", (group_name,))
    if c.fetchone():
        print("이미 존재하는 그룹입니다.")
    else:
        c.execute("INSERT INTO groups (group_name) VALUES (?)", (group_name,))
        conn.commit()
        print(f"그룹 '{group_name}'이(가) 성공적으로 추가되었습니다.")
    conn.close()


def add_url():
    url = input("URL을 입력하세요: ").strip()
    title = input("제목을 입력하세요: ").strip()
    tags = input("태그를 입력하세요 (쉼표로 구분): ").strip()
    description = input("설명을 입력하세요: ").strip()

    group_name = input("URL을 추가할 그룹 이름을 입력하세요 (그룹 없이 추가하려면 엔터를 누르세요): ").strip()

    conn = sqlite3.connect("urls.db")
    c = conn.cursor()

    c.execute("SELECT * FROM urls WHERE url=?", (url,))
    if c.fetchone():
        print("이미 존재하는 URL입니다.")
    else:
        c.execute("INSERT INTO urls (url, title, tags, description) VALUES (?, ?, ?, ?)", 
                  (url, title, tags, description))
        url_id = c.lastrowid

        if group_name:
            c.execute("SELECT id FROM groups WHERE group_name=?", (group_name,))
            group = c.fetchone()

            if group:
                c.execute("INSERT INTO url_groups (url_id, group_id) VALUES (?, ?)", 
                          (url_id, group[0]))
                print(f"그룹 '{group_name}'에 URL이 추가되었습니다.")
            else:
                print(f"그룹 '{group_name}'이 존재하지 않으므로 URL을 그룹 없이 추가했습니다.")
                c.execute("INSERT INTO url_groups (url_id, group_id) VALUES (?, ?)", 
                          (url_id, None))  
        else:
            print("그룹 없이 URL이 추가되었습니다.")
            c.execute("INSERT INTO url_groups (url_id, group_id) VALUES (?, ?)", 
                      (url_id, None))  

        conn.commit()
        print("URL이 성공적으로 추가되었습니다.")
    
    conn.close()

# GROUP
def assign_group_to_url(url_id, group_id):
    conn = sqlite3.connect("urls.db")
    c = conn.cursor()

    if group_id is None:
        c.execute("DELETE FROM url_groups WHERE url_id=?", (url_id,))
        print("그룹이 삭제되었습니다.")
    else:
        c.execute("SELECT * FROM url_groups WHERE url_id=?", (url_id,))
        existing_group = c.fetchone()

        if existing_group:
            c.execute("UPDATE url_groups SET group_id=? WHERE url_id=?", (group_id, url_id))
            print("그룹이 변경되었습니다.")
        else:
            c.execute("INSERT INTO url_groups (url_id, group_id) VALUES (?, ?)", (url_id, group_id))
            print("그룹이 추가되었습니다.")

    conn.commit()
    conn.close()



# URLS LIST
def view_urls():
    conn = sqlite3.connect("urls.db")
    c = conn.cursor()

    c.execute('''SELECT u.id, u.url, u.title, u.tags, u.description, g.group_name, u.click_count
                 FROM urls u
                 LEFT JOIN url_groups ug ON u.id = ug.url_id
                 LEFT JOIN groups g ON ug.group_id = g.id
                 ORDER BY u.click_count DESC, u.id ASC''')
    urls = c.fetchall()

    if not urls:
        print("저장된 URL이 없습니다.")
    else:
        print(f"{'ID':<5} {'URL':<30} {'제목':<20} {'태그':<20} {'설명':<30} {'그룹':<15} {'클릭 수'}")
        print("-" * 150)
        for url in urls:
            group_name = url[5] if url[5] else "" 
            print(f"{url[0]:<5} {url[1]:<30} {url[2]:<20} {url[3]:<20} {url[4]:<30} {group_name:<15} {url[6]}")

        print("\n작업을 선택하세요:")
        print("1. URL 이동")
        print("2. 그룹 변경")
        print("q. 취소")
        choice = input("선택: ").strip()

        if choice.lower() == 'q':
            conn.close()
            return

        try:
            url_id = int(input("\n이동할 URL의 ID를 입력하세요: ").strip())

            if choice == "1":
                c.execute("SELECT url, click_count FROM urls WHERE id=?", (url_id,))
                url = c.fetchone()
                if url:
                    new_count = url[1] + 1
                    c.execute("UPDATE urls SET click_count=? WHERE id=?", (new_count, url_id))
                    conn.commit()
                    print(f"{url[0]}로 이동합니다... (클릭 수: {new_count})")
                    webbrowser.open(url[0])
                    conn.close()
                    return 

            elif choice == "2":
                c.execute("SELECT id, group_name FROM groups")
                groups = c.fetchall()
                if groups:
                    print("\n그룹 목록:")
                    for group in groups:
                        print(f"{group[0]}: {group[1]}")
                    print("0: 그룹 없음")

                    group_id = input("\n새 그룹의 번호를 선택하세요 (그룹 없음은 0): ").strip()
                    if group_id.isdigit():
                        group_id = int(group_id)
                        if group_id == 0:
                            assign_group_to_url(url_id, None) 
                        else:
                            assign_group_to_url(url_id, group_id) 
                    else:
                        print("유효한 그룹 번호를 입력해주세요.")
                else:
                    print("저장된 그룹이 없습니다.")
            else:
                print("유효한 선택이 아닙니다.")
        except ValueError:
            print("유효한 숫자 ID를 입력하세요.")

    conn.close()


# DELETE URLS
def delete_url():
    conn = sqlite3.connect("urls.db")
    c = conn.cursor()


    c.execute('''SELECT u.id, u.url, u.title, u.tags, u.description, g.group_name
                 FROM urls u
                 LEFT JOIN url_groups ug ON u.id = ug.url_id
                 LEFT JOIN groups g ON ug.group_id = g.id''')
    urls = c.fetchall()

    if not urls:
        print("저장된 URL이 없습니다.")
    else:
        print(f"{'ID':<5} {'URL':<30} {'제목':<20} {'태그':<20} {'설명':<30} {'그룹'}")
        print("-" * 120)
        for url in urls:
            group_name = url[5] if url[5] else ""  
            print(f"{url[0]:<5} {url[1]:<30} {url[2]:<20} {url[3]:<20} {url[4]:<30} {group_name}")

        try:
            url_id = int(input("\n삭제할 URL의 ID를 입력하세요: ").strip())
            c.execute("DELETE FROM urls WHERE id=?", (url_id,))
            if conn.total_changes > 0:
                print("URL이 삭제되었습니다.")
            else:
                print("해당 ID의 URL이 존재하지 않습니다.")
            conn.commit()
        except ValueError:
            print("유효한 숫자를 입력하세요.")
    
    conn.close()


def search_urls():
    search_term = input("검색어를 입력하세요: ").strip()
    if not search_term:
        print("검색어를 입력해야 합니다.")
        return

    conn = sqlite3.connect("urls.db")
    c = conn.cursor()
    c.execute("SELECT * FROM urls WHERE url LIKE ? OR title LIKE ? OR tags LIKE ? OR description LIKE ?",
              ('%' + search_term + '%', '%' + search_term + '%', '%' + search_term + '%', '%' + search_term + '%'))
    results = c.fetchall()
    conn.close()

    if not results:
        print("검색 결과가 없습니다.")
    else:
        print("\n검색 결과:")
        print(f"{'ID':<5} {'URL':<30} {'제목':<20} {'태그':<20} {'설명'}")
        print("-" * 80)
        for url in results:
            print(f"{url[0]:<5} {url[1]:<30} {url[2]:<20} {url[3]:<20} {url[4]}")


# URLS QR CODE
def generate_qr_code():
    conn = sqlite3.connect("urls.db")
    c = conn.cursor()
    c.execute('''SELECT id, url, title FROM urls''')
    urls = c.fetchall()
    conn.close()

    if not urls:
        print("저장된 URL이 없습니다.")
        return

    print("URL 목록:")
    for url in urls:
        print(f"{url[0]}: {url[1]} (제목: {url[2]})") 

    try:
        url_id = int(input("\nQR 코드를 생성할 URL의 ID를 선택하세요: ").strip())

        conn = sqlite3.connect("urls.db")
        c = conn.cursor()
        c.execute("SELECT url, title FROM urls WHERE id=?", (url_id,))
        url_data = c.fetchone()
        conn.close()

        if url_data:
            url, title = url_data
            filename = input("QR 코드를 저장할 파일 이름을 입력하세요 (확장자는 .png): ").strip()
            if not filename.endswith(".png"):
                filename += ".png"  


            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")


            draw = ImageDraw.Draw(img)
            font = ImageFont.load_default()


            text = title
            text_width, text_height = draw.textbbox((0, 0), text, font=font)[2:]
            text_position = (img.width // 2 - text_width // 2, img.height - text_height - 10)  

  
            draw.text(text_position, text, font=font, fill="black")

       
            img.save(filename)
            print(f"QR 코드가 '{filename}'로 저장되었습니다.")
        else:
            print("해당 ID의 URL이 존재하지 않습니다.")
    except ValueError:
        print("유효한 숫자를 입력해주세요.")


def main_menu():
    init_db()
    while True:
        print("\nURL 정리기")
        print("1. URL 추가")
        print("2. URL 목록 보기")
        print("3. URL 검색")
        print("4. URL 삭제")
        print("5. 그룹 추가")
        print("6. QR 코드 생성")
        print("7. 종료")
        choice = input("메뉴를 선택하세요 (1-7): ").strip()

        if choice == "1":
            add_url()
        elif choice == "2":
            view_urls()
        elif choice == "3":
            search_urls()
        elif choice == "4":
            delete_url()
        elif choice == "5":
            add_group()
        elif choice == "6":
            generate_qr_code()  
        elif choice == "7":
            print("프로그램을 종료합니다.")
            break
        else:
            print("올바른 옵션을 선택해주세요.")


if __name__ == "__main__":
    main_menu()