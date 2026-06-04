# 데이터 수집기 (스케줄 실행용)
#  현재 KBO 순위표를 1회 크롤링 → 입력변수 계산 → data/latest_standings.csv 저장
#  ※ 사이트(app.py)는 이 파일만 읽음. KBO에는 이 스크립트만 (하루 1번) 접속.
import os, re, csv
from datetime import datetime
import requests
from bs4 import BeautifulSoup

HERE = os.path.dirname(os.path.abspath(__file__))
DAILY_URL = "https://www.koreabaseball.com/Record/TeamRank/TeamRankDaily.aspx"
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0 Safari/537.36"}
GAMES = 144
TEAM_FIX = {"SK": "SSG", "넥센": "키움"}

def parse_record(s):
    n = list(map(int, re.findall(r"\d+", s)))
    if len(n) < 3: return None
    w, l = n[0], n[2]
    return round(w / (w + l), 4) if (w + l) else None

def parse_streak(s):
    m = re.match(r"(\d+)(승|패|무)", s.strip())
    if not m: return 0
    v, k = int(m.group(1)), m.group(2)
    return v if k == "승" else (-v if k == "패" else 0)

def main():
    html = requests.get(DAILY_URL, headers=H, timeout=20).text
    soup = BeautifulSoup(html, "html.parser")
    cal = soup.find("input", {"id": "cphContents_cphContents_cphContents_txtCanlendar"})
    asof = (cal.get("value").strip() if cal else "")
    fetched_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    rows = []
    for tr in soup.find_all("table")[0].find_all("tr")[1:]:
        c = [td.get_text(strip=True) for td in tr.find_all(["th", "td"])]
        if len(c) < 12:
            continue
        games = int(c[2]); wr = float(c[6])
        team = TEAM_FIX.get(c[1], c[1])
        rows.append({
            "team": team, "games": games, "cur_wr": wr,
            "progress": round(games / GAMES, 4),
            "win_rate": wr,
            "recent10_wr": parse_record(c[8]) or wr,
            "streak_num": parse_streak(c[9]),
            "home_wr": parse_record(c[10]) or wr,
            "away_wr": parse_record(c[11]) or wr,
            "asof": asof,
            "fetched_at": fetched_at,
        })

    if not rows:
        raise SystemExit("크롤링 실패: 표를 찾지 못함 (KBO 사이트 구조 변경 가능)")

    out = os.path.join(HERE, "data", "latest_standings.csv")
    cols = ["team", "games", "cur_wr", "progress", "win_rate", "recent10_wr",
            "streak_num", "home_wr", "away_wr", "asof", "fetched_at"]
    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
    print(f"갱신 완료: {len(rows)}팀, 기준일 {asof}, 시각 {fetched_at}")
    print(f"저장 → {out}")

if __name__ == "__main__":
    main()
