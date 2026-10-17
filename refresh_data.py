import urllib.request
import re
import os
import subprocess
import time
from datetime import datetime

# Configuration
SITE_LIST_FILE = 'site_list.csv'
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1KcmSKb4LWRzQyORWYS1Glnxgm_uLlNZLQG_hhTcYWFs/export?format=csv"
SCHEDULE_FILE = 'fishing_schedule.csv'
AVAILABLE_FILE = 'available_schedules.csv'

def update_site_list():
    try:
        print(f"[{datetime.now()}] Updating site_list.csv from Google Sheet...")
        with urllib.request.urlopen(GOOGLE_SHEET_URL) as response:
            content = response.read().decode('utf-8')
            with open(SITE_LIST_FILE, 'w', encoding='utf-8') as f:
                f.write(content)
        print(f"[{datetime.now()}] site_list.csv updated.")
    except Exception as e:
        print(f"[{datetime.now()}] Error updating site_list: {e}")

def get_site_urls():
    if not os.path.exists(SITE_LIST_FILE):
        return []
    with open(SITE_LIST_FILE, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def fetch_and_parse_all():
    update_site_list() # Update list before parsing
    urls = get_site_urls()
    all_rows = []
    
    header = "날짜,요일,물때,선명,선사위치,대상어종,상태,예약좌석수,총좌석수,잔여석,예약가능여부,링크"
    
    for base_url in urls:
        now = datetime.now()
        months_to_fetch = []
        for i in range(4):
            target_month = now.month + i
            target_year = now.year + (target_month - 1) // 12
            target_month = (target_month - 1) % 12 + 1
            months_to_fetch.append((target_year, target_month))
        
        for year, month in months_to_fetch:
            ym = f"{year}{month:02d}"
            
            if 'eugeneho.kr' in base_url:
                url = f"{base_url}&year={year}&month={month}"
            else:
                url = f"{base_url}/{ym}"
            
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                raw_html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8')
                
                if 'eugeneho.kr' in base_url:
                    divs = re.findall(r'<div id="new-div-(\d{8})".*?</table>\s*</div>', raw_html, re.DOTALL)
                    if not divs:
                        divs = re.findall(r'<div id="new-div-(\d{8})".*?<!--day_end-->', raw_html, re.DOTALL)
                    
                    for day_str in divs:
                        m_block = re.search(r'<div id="new-div-' + day_str + r'".*?</table>\s*</div>', raw_html, re.DOTALL)
                        if not m_block:
                            m_block = re.search(r'<div id="new-div-' + day_str + r'".*?<!--day_end-->', raw_html, re.DOTALL)
                        if not m_block: continue
                        block = m_block.group(0)
                        
                        m_info = re.search(r'data-str="<b>(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일</b>,\s*([^,]+),\s*([^"]+)"', block)
                        if m_info:
                            date_display = f"{int(m_info.group(2))}월 {int(m_info.group(3))}일"
                            day_of_week = m_info.group(4).strip()[0]
                            tide = m_info.group(5).strip()
                        else:
                            continue

                        boat_name = '유진호'
                        location = '오천항'

                        m_fish = re.search(r'낚시종류.*?color:#ff0000">([^<]+)</span>', block, re.DOTALL)
                        if m_fish:
                            target_fish = m_fish.group(1).replace('▶', '').replace('◀', '').strip()
                        else:
                            target_fish = '기타'

                        m_seat = re.search(r'alt="남은자리\s*(\d+)명"', block)
                        if m_seat:
                            remaining = int(m_seat.group(1))
                        else:
                            remaining = 0

                        total = 20
                        reserved = max(0, total - remaining)
                        
                        if '예약하기' in block:
                            status = '예약하기' if remaining > 0 else '예약마감'
                        elif '예약마감' in block:
                            status = '예약마감'
                        else:
                            status = '대기'

                        available = 'N'
                        if status != '예약마감' and remaining > 0:
                            available = 'Y'

                        row = f"{date_display},{day_of_week},{tide},{boat_name},{location},{target_fish},{status},{reserved},{total},{remaining},{available},{base_url}"
                        all_rows.append(row)
                    
                    print(f"Parsed {len(divs)} days for Eugene-ho ({year}-{month})")
                
                else:
                    blocks = re.findall(r'<table id="d(\d{4}-\d{2}-\d{2})"[^>]*>(.*?)</table>', raw_html, re.DOTALL)
                    
                    for date_str, b_html in blocks:
                        parts = date_str.split('-')
                        date_display = f"{int(parts[1])}월 {int(parts[2])}일"
                        
                        m_day = re.search(r'<span class="week">\(([^)]+)\)', b_html)
                        day_of_week = m_day.group(1) if m_day else ""
                        
                        m_tide = re.search(r'class="date_info2"\s*>\s*([^<]+)\s*</td>', b_html)
                        tide = m_tide.group(1).strip() if m_tide else ""
                        
                        m_boat = re.search(r'<div class="title">\s*([^<]+)\s*</div>', b_html)
                        boat_name = m_boat.group(1).strip() if m_boat else "Unknown"
                        
                        m_fish = re.search(r'<div id="fish">([^<]+)</div>', b_html)
                        target_fish = m_fish.group(1).strip() if m_fish else ""
                        
                        m_status = re.search(r'data-status_code="[^"]*"[^>]*>([^<]+)</button>', b_html)
                        if not m_status:
                            m_status = re.search(r'<span class="shipping_status"[^>]*>([^<]+)</span>', b_html)
                        status = m_status.group(1).strip() if m_status else "대기"
                        
                        m_total = re.search(r'예약/\s*<span[^>]*>\s*(\d+)명\s*</span>', b_html)
                        m_remaining = re.search(r'남은자리.*?<span[^>]*>\s*(\d+)명\s*</span>', b_html, re.DOTALL)
                        
                        if m_total and m_remaining:
                            total = int(m_total.group(1))
                            remaining = int(m_remaining.group(1))
                            reserved = total - remaining
                        else:
                            m_all_numbers = re.findall(r'<span[^>]*>\s*(\d+)명\s*</span>', b_html)
                            if len(m_all_numbers) >= 2:
                                vals = [int(n) for n in m_all_numbers[:2]]
                                total = max(vals)
                                remaining = min(vals)
                                reserved = total - remaining
                            elif len(m_all_numbers) == 1:
                                total = int(m_all_numbers[0])
                                remaining = total
                                reserved = 0
                            else:
                                total = 0
                                remaining = 0
                                reserved = 0
                        
                        remaining = max(0, remaining)
                        reserved = max(0, reserved)
                        
                        available = 'N'
                        if status != '예약마감' and remaining > 0:
                            available = 'Y'
                        
                        location = "여수" if "영심이호" in boat_name else "고흥" if "청룡호" in boat_name else "기타"
                        
                        row = f"{date_display},{day_of_week},{tide},{boat_name},{location},{target_fish},{status},{reserved},{total},{remaining},{available},{base_url}"
                        all_rows.append(row)
                    
                    print(f"Parsed {len(blocks)} days for {url}")
            except Exception as e:
                print(f"Error parsing {url}: {e}")
                
    return header, all_rows
def git_push(message):
    """ Push changes if there are any """
    status = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
    if not status.stdout.strip():
        print(f"[{datetime.now()}] No changes to push.")
        return

    try:
        print(f"[{datetime.now()}] Git push started...")
        subprocess.run(['git', 'add', SCHEDULE_FILE, AVAILABLE_FILE], check=True)
        subprocess.run(['git', 'commit', '-m', message], check=True)
        subprocess.run(['git', 'push', 'origin', 'main'], check=True)
        print(f"[{datetime.now()}] Git push completed.")
    except subprocess.CalledProcessError as e:
        print(f"[{datetime.now()}] Git operation failed: {e}")

def update_data():
    print(f"[{datetime.now()}] Data update and deployment started...")
    
    header, rows = fetch_and_parse_all()
    
    # Save fishing_schedule.csv
    with open(SCHEDULE_FILE, 'w', encoding='utf-8') as f:
        f.write(header + "\n")
        f.write("\n".join(rows) + "\n")
    
    # Save available_schedules.csv
    with open(AVAILABLE_FILE, 'w', encoding='utf-8') as f:
        f.write(header + "\n")
        # Check column index 10 (0-indexed) for 'Y'
        filtered_rows = [row for row in rows if row.split(',')[10] == 'Y']
        f.write("\n".join(filtered_rows) + "\n")


    # Push changes
    commit_msg = f"Auto-update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    git_push(commit_msg)

if __name__ == "__main__":
    while True:
        try:
            update_data()
        except Exception as e:
            print(f"[{datetime.now()}] Error in update_data loop: {e}")
        print(f"[{datetime.now()}] Waiting 5 minutes for next update...")
        time.sleep(300)

