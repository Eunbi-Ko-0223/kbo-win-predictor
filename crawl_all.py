# 2015~2025 전체 크롤링
#  (1) TeamRankDaily: 시즌별 스냅샷 (입력 X) — 13개 열 날것 그대로 저장
#  (2) TeamRank.aspx: 연도별 최종승률 (정답 y)
import sys, io, time, csv
from datetime import date, timedelta
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import requests
from bs4 import BeautifulSoup

H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Origin": "https://www.koreabaseball.com",
}
DAILY_URL = "https://www.koreabaseball.com/Record/TeamRank/TeamRankDaily.aspx"
FINAL_URL = "https://www.koreabaseball.com/Record/TeamRank/TeamRank.aspx"
PFX = "ctl00$ctl00$ctl00$cphContents$cphContents$cphContents$"
YEARS = list(range(2015, 2026))   # 2015 ~ 2025

# 행을 dict로 파싱 (날것 보존: 변환 없이 원본 문자열 그대로)
def parse_table_rows(soup, extra):
    tables = soup.find_all("table")
    if not tables:
        return []
    out = []
    for tr in tables[0].find_all("tr")[1:]:
        c = [td.get_text(strip=True) for td in tr.find_all(["th", "td"])]
        if len(c) < 12:
            continue
        row = {
            "rank": c[0], "team": c[1], "games": c[2], "win": c[3],
            "loss": c[4], "draw": c[5], "win_rate": c[6], "gb": c[7],
            "last10": c[8], "streak": c[9], "home": c[10], "away": c[11],
        }
        row.update(extra)
        out.append(row)
    return out

def build_payload(soup):
    form = soup.find("form")
    p = {}
    for inp in form.find_all("input"):
        n = inp.get("name")
        if n:
            p[n] = inp.get("value", "")
    for sel in form.find_all("select"):
        n = sel.get("name")
        o = sel.find("option", selected=True) or sel.find("option")
        p[n] = o.get("value", "") if o else ""
    return p

# ---------- (1) 스냅샷 ----------
def fetch_daily(session, date_str):
    soup = BeautifulSoup(session.get(DAILY_URL, headers={**H, "Referer": DAILY_URL}, timeout=20).text, "html.parser")
    p = build_payload(soup)
    p[PFX + "txtCanlendar"] = date_str
    p[PFX + "hfSearchDate"] = date_str
    p[PFX + "hfSearchYear"] = date_str[:4]
    p[PFX + "hfSearchSeries"] = "0"
    p[PFX + "ddlSeries"] = "0"
    p["__EVENTTARGET"] = PFX + "btnCalendarSelect"
    p["__EVENTARGUMENT"] = ""
    for b in ["btnPreDate", "btnNextDate"]:
        p.pop(PFX + b, None)
    r = session.post(DAILY_URL, headers={**H, "Referer": DAILY_URL}, data=p, timeout=20)
    s2 = BeautifulSoup(r.text, "html.parser")
    cal = s2.find("input", {"name": PFX + "txtCanlendar"})
    got = (cal.get("value") if cal else "").strip()
    rows = parse_table_rows(s2, {"date": date_str, "year": date_str[:4]})
    # 요청 날짜와 응답 날짜가 다르거나 경기수 0이면 무효(시즌 전 등)
    if got != date_str:
        return []
    rows = [x for x in rows if x["games"].isdigit() and int(x["games"]) > 0]
    return rows

# 시즌별 스냅샷 날짜 생성 (4/5 ~ 10/8, 약 13일 간격)
def season_dates(year):
    d, end, out = date(year, 4, 5), date(year, 10, 8), []
    while d <= end:
        out.append(d.strftime("%Y%m%d"))
        d += timedelta(days=13)
    return out

# ---------- (2) 최종승률 ----------
def fetch_final(session, year):
    soup = BeautifulSoup(session.get(FINAL_URL, headers={**H, "Referer": FINAL_URL}, timeout=20).text, "html.parser")
    p = build_payload(soup)
    # ddlYear / ddlSeries 의 실제 name 을 suffix 로 찾아 세팅
    ddl_year = next((s.get("name") for s in soup.find_all("select") if s.get("name", "").endswith("ddlYear")), None)
    ddl_series = next((s.get("name") for s in soup.find_all("select") if s.get("name", "").endswith("ddlSeries")), None)
    if ddl_year:
        p[ddl_year] = str(year)
        p["__EVENTTARGET"] = ddl_year
        p["__EVENTARGUMENT"] = ""
    if ddl_series:
        p[ddl_series] = "0"
    r = session.post(FINAL_URL, headers={**H, "Referer": FINAL_URL}, data=p, timeout=20)
    s2 = BeautifulSoup(r.text, "html.parser")
    return parse_table_rows(s2, {"year": str(year)})

def main():
    cols_daily = ["year", "date", "rank", "team", "games", "win", "loss", "draw",
                  "win_rate", "gb", "last10", "streak", "home", "away"]
    cols_final = ["year", "rank", "team", "games", "win", "loss", "draw",
                  "win_rate", "gb", "last10", "streak", "home", "away"]

    session = requests.Session()

    # (1) 스냅샷
    snap = []
    for y in YEARS:
        cnt = 0
        for ds in season_dates(y):
            try:
                rows = fetch_daily(session, ds)
            except Exception as e:
                print(f"  [에러] {ds}: {e}"); rows = []
            snap.extend(rows); cnt += len(rows)
            time.sleep(0.5)
        print(f"[스냅샷] {y}: {cnt}행")
    with open("all_snapshots.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols_daily); w.writeheader(); w.writerows(snap)
    print(f"=> all_snapshots.csv 저장: 총 {len(snap)}행\n")

    # (2) 최종승률
    finals = []
    for y in YEARS:
        try:
            rows = fetch_final(session, y)
        except Exception as e:
            print(f"  [에러] final {y}: {e}"); rows = []
        finals.extend(rows)
        print(f"[최종] {y}: {len(rows)}팀")
        time.sleep(0.5)
    with open("final_standings.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols_final); w.writeheader(); w.writerows(finals)
    print(f"=> final_standings.csv 저장: 총 {len(finals)}행")

if __name__ == "__main__":
    main()
