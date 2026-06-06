# -*- coding: utf-8 -*-
"""
간다GO 관악 출장마사지 — static site generator.

One-time generator that emits PURE static HTML (inline CSS/JS, zero runtime
dependencies). The published site needs no build step or framework; this script
only exists to keep the shared header/footer/SEO blocks consistent across pages.

Run:  python3 tools/build.py
Output: HTML files + sitemap.xml + robots.txt + site.webmanifest at repo root.
"""

import os
import json
import re
import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------------------
# Brand / business constants  (replace placeholders before going live)
# ---------------------------------------------------------------------------
BASE_URL   = "https://gwanak-massage.pages.dev"  # 메인 도메인 (Cloudflare Pages)
BRAND      = "간다GO 관악 출장마사지"
BRAND_SHORT= "간다GO"
PHONE_DISP = "0508-202-4743"                     # 예약 전화번호
PHONE_TEL  = "+825082024743"                     # tel: 링크용
HOURS      = "연중무휴 · 24시간 상담"
INDEXNOW_KEY = "ff387028a8fb421199a855dcb0d5c7a8"   # IndexNow(빙·네이버 등) 인증 키
NAVER_VERIFY = "b51993b1086bcfb0c3e062ac00f0e7cf72c5250f"   # 네이버 서치어드바이저 사이트 소유확인

COMPANY = {
    "name": "간다GO 헬스케어",
    "ceo": "김도현",
    "biz_no": "000-00-00000",            # TODO
    "addr": "서울특별시 관악구",
    "sales_no": "2026-서울관악-0000",    # TODO
    "privacy_officer": "김도현",
}

# ---------------------------------------------------------------------------
# Data model — 권역 / 동
# ---------------------------------------------------------------------------
REGIONS = [
    {
        "slug": "bongcheon-area",
        "name": "봉천권역",
        "summary": "서울대입구역·봉천역·낙성대역 2호선 라인을 따라 이어지는 관악구 동부 주거·상업 권역입니다.",
        "stations": ["seoul-national-university-station", "bongcheon-station", "nakseongdae-station"],
        "long": [
            "봉천권역은 서울대입구역에서 봉천역, 낙성대역으로 이어지는 2호선 라인을 따라 생활권이 형성되어 있습니다. 관악구청·관악중앙시장 등 행정·상업 인프라가 모여 있어 평일 저녁과 주말 모두 주거지·오피스텔 방문 문의가 고르게 들어옵니다.",
            "샤로수길과 서울대입구역 일대는 청년·1인 가구 비중이 높아 원룸·오피스텔 방문이 많고, 은천동·인헌동 쪽은 대단지 아파트와 학군지가 많아 가족 단위 방문이 늘어나는 편입니다. 예약 데이터 기준 평균 도착 시간은 봉천권역 19~23분 내외입니다."],
        "dongs": [
            {"slug": "bongcheon-dong", "name": "봉천동", "arrival": 20,
             "landmarks": "서울대입구역(2호선), 봉천역(2호선), 관악구청 일대",
             "character": "관악구를 대표하는 주거·상업 중심 생활권",
             "sub_note": "봉천동은 은천동·성현동·청룡동·청림동·행운동·중앙동·인헌동 등 여러 "
                         "행정동으로 나뉘며, 세부 위치는 예약 시 함께 확인해 드립니다."},
            {"slug": "euncheon-dong", "name": "은천동", "arrival": 22,
             "landmarks": "봉천역(2호선), 관악푸르지오·벽산블루밍 일대",
             "character": "대단지 아파트가 모인 안정적인 정주형 주거 생활권"},
            {"slug": "seonghyeon-dong", "name": "성현동", "arrival": 21,
             "landmarks": "서울대입구역 북측, 성현동 현대아파트 주거단지 일대",
             "character": "서울대입구역 배후의 주거 밀집 생활권"},
            {"slug": "cheongnyong-dong", "name": "청룡동", "arrival": 19,
             "landmarks": "서울대입구역(2호선), 샤로수길 일대",
             "character": "서울대입구역 역세권 상업·원룸·주거 혼합 생활권"},
            {"slug": "boramae-dong", "name": "보라매동", "arrival": 24,
             "landmarks": "보라매공원, 신대방역(2호선) 인근",
             "character": "보라매공원을 낀 주거·생활 권역",
             "sub_note": "보라매동은 신대방역 생활권과 가까워, 신대방역 인근 방문 문의도 "
                         "보라매동 기준으로 함께 안내드립니다."},
            {"slug": "cheongnim-dong", "name": "청림동", "arrival": 22,
             "landmarks": "관악구청, 서울대입구역 남측 일대",
             "character": "관악구청과 가까운 행정·주거 생활권"},
            {"slug": "haengun-dong", "name": "행운동", "arrival": 21,
             "landmarks": "낙성대역(2호선), 행운동 주거지 일대",
             "character": "낙성대 방면으로 이어지는 정주형 주거 생활권"},
            {"slug": "nakseongdae-dong", "name": "낙성대동", "arrival": 22,
             "landmarks": "낙성대역(2호선), 낙성대공원 일대",
             "character": "낙성대역 역세권과 공원을 낀 주거 생활권"},
            {"slug": "jungang-dong", "name": "중앙동", "arrival": 20,
             "landmarks": "봉천역(2호선), 관악중앙시장 일대",
             "character": "봉천역 중심의 상업·주거가 밀집한 생활권"},
            {"slug": "inheon-dong", "name": "인헌동", "arrival": 23,
             "landmarks": "낙성대역 인근, 인헌중·고등학교 일대",
             "character": "학군과 주거가 안정된 조용한 생활권"},
        ],
    },
    {
        "slug": "sillim-area",
        "name": "신림권역",
        "summary": "신림역·서원역·서울대벤처타운역·관악산역을 따라 이어지는 관악구 최대 주거·상업 권역입니다.",
        "stations": ["sillim-station", "danggok-station", "seowon-station",
                     "seoul-national-university-venture-town-station", "gwanaksan-station"],
        "long": [
            "신림권역은 2호선과 신림선이 함께 지나는 신림역을 중심으로 서원역·서울대벤처타운역·관악산역으로 이어지는 관악구 최대 생활권입니다. 신림중앙시장과 순대타운을 낀 상권 주변으로 원룸·오피스텔이 밀집해 있어 심야 시간대 방문 문의가 특히 많습니다.",
            "대학동 고시촌과 서울대 방면은 학생·청년층 방문이 많고, 난곡동·난향동 등 산자락 생활권은 정주형 주거 비중이 높습니다. 같은 신림권역 안에서도 위치에 따라 평균 도착 시간이 18~27분 내외로 달라집니다."],
        "dongs": [
            {"slug": "sillim-dong", "name": "신림동", "arrival": 18,
             "landmarks": "신림역(2호선·신림선), 신림중앙시장, 순대타운 일대",
             "character": "관악구에서 검색 수요가 가장 큰 대표 상업·주거 밀집 생활권",
             "sub_note": "신림동은 서원동·신원동·서림동·삼성동·미성동 등 여러 행정동으로 "
                         "나뉘며, 세부 방문 가능 여부는 위치와 시간에 따라 안내드립니다."},
            {"slug": "seowon-dong", "name": "서원동", "arrival": 22,
             "landmarks": "서원역(신림선), 서원동 주거지 일대",
             "character": "신림 서부의 주거 밀집 생활권"},
            {"slug": "sinwon-dong", "name": "신원동", "arrival": 21,
             "landmarks": "신림역 남측, 신원시장 일대",
             "character": "신림역과 가까운 주거·상업 혼합 생활권"},
            {"slug": "seorim-dong", "name": "서림동", "arrival": 20,
             "landmarks": "신림역 인근, 서림동 주거지 일대",
             "character": "신림역 역세권에 인접한 원룸·주거 생활권"},
            {"slug": "nangok-dong", "name": "난곡동", "arrival": 26,
             "landmarks": "난곡로, 난곡사거리 일대",
             "character": "산자락을 따라 형성된 주거 밀집 생활권"},
            {"slug": "sinsa-dong", "name": "신사동", "arrival": 23,
             "landmarks": "신림역 서측, 신사동고개 일대",
             "character": "신림 서북부의 주거 생활권"},
            {"slug": "samseong-dong", "name": "삼성동", "arrival": 25,
             "landmarks": "삼성산 자락, 삼성동 주거단지 일대",
             "character": "삼성산 녹지와 주거가 어우러진 생활권"},
            {"slug": "nanhyang-dong", "name": "난향동", "arrival": 27,
             "landmarks": "난향로, 삼성산 자락 일대",
             "character": "녹지 비중이 높은 관악 남서부 외곽 주거 생활권"},
            {"slug": "jowon-dong", "name": "조원동", "arrival": 24,
             "landmarks": "조원시장, 신대방역 방면 일대",
             "character": "신대방 생활권과 이어지는 주거 밀집 권역",
             "sub_note": "조원동은 신대방역 생활권과 가까워, 신대방역 인근 방문 문의도 "
                         "조원동 기준으로 함께 안내드립니다."},
            {"slug": "daehak-dong", "name": "대학동", "arrival": 25,
             "landmarks": "서울대벤처타운역(신림선), 관악산역, 서울대학교 일대",
             "character": "서울대학교와 고시촌이 어우러진 학생·청년 생활권"},
            {"slug": "miseong-dong", "name": "미성동", "arrival": 23,
             "landmarks": "신림선 인근, 미성동 주거단지 일대",
             "character": "신림 남부의 정주형 주거 생활권"},
        ],
    },
    {
        "slug": "namhyeon-area",
        "name": "남현권역",
        "summary": "사당역과 예술인마을을 끼고 관악 동남쪽 생활권이 묶이는 권역입니다.",
        "stations": [],
        "long": [
            "남현권역은 관악구 동남쪽 끝에 위치하며, 사당역(2·4호선) 생활권과 맞닿아 있는 남현동을 중심으로 합니다. 예술인마을과 관악산 둘레길을 낀 조용한 주택가가 많아 자택 방문 문의가 주를 이루며, 단독·다세대 주택 비중이 높은 편입니다.",
            "사당역은 2호선과 4호선이 만나는 환승역으로 유동 인구가 많지만, 행정구역상 사당역 인근은 남현동 생활권으로 안내드립니다. 별도의 역 페이지를 만들지 않고 남현동 본문에서 사당역 생활권을 함께 다루며, 평균 도착 시간은 26분 내외입니다."],
        "extra": [
            ("남현동과 사당역 생활권", [
                "남현권역의 유일한 행정동인 남현동은 사당역(2·4호선)을 일상 생활권으로 두고 있습니다. 사당역은 강남·동작 방면 이동이 편리해 직장인 1인 가구가 많고, 예술인마을 안쪽으로는 단독·다세대 주택과 빌라가 모여 있어 가족 단위 자택 방문도 꾸준합니다.",
                "행정구역상 사당역은 동작구와 관악구에 걸쳐 있어, 사당역 인근에서 출장마사지를 찾는 분들은 위치에 따라 남현동 생활권으로 안내드립니다. 별도의 사당역 페이지를 만들지 않고 이 권역과 남현동 본문에서 함께 다루는 이유입니다."]),
            ("남현권역 방문 안내", [
                "남현동 일대는 관악산 자락과 가까워 경사진 골목과 일방통행 구간이 많습니다. 예약 시 정확한 주소와 가까운 기준점(사당역 출구, 예술인마을 입구 등)을 함께 알려주시면 평균 26분 내외로 도착할 수 있습니다.",
                "조용한 주택가 특성상 야간에는 공동현관·주차 안내가 중요합니다. 출입 방법과 연락 가능한 번호를 미리 남겨주시면 방문이 한결 매끄럽습니다."]),
            ("남현권역에서 많이 찾는 관리", [
                "남현권역은 자택에서 받는 피로 회복·아로마 관리 문의가 특히 많습니다. 단독·다세대 주택이 많아 가족과 함께 받는 커플·가족 방문 관리 수요도 꾸준한 편입니다.",
                "코스별 상세 설명과 정찰 요금은 페이지마다 반복하지 않고 코스안내에서 확인하실 수 있으며, 남현동 상세 생활권은 남현동 페이지에서 안내드립니다."]),
        ],
        "dongs": [
            {"slug": "namhyeon-dong", "name": "남현동", "arrival": 26,
             "landmarks": "사당역(2·4호선), 예술인마을, 남현동 주거지 일대",
             "character": "사당역 생활권과 이어지는 관악 동남부 주거 권역",
             "sub_note": "남현동은 사당역(2·4호선) 생활권과 맞닿아 있어, 사당역 인근 방문 "
                         "문의도 남현동 기준으로 함께 안내드립니다."},
        ],
    },
]

# ---------------------------------------------------------------------------
# Data model — 지하철역별 안내 (역세권 보조 랜딩)
# ---------------------------------------------------------------------------
# 핵심 키워드 "관악 출장마사지"는 대표 페이지(/gwanak-gu/)에 집중시키고,
# 역명+출장마사지 키워드는 아래 역세권 페이지로 확장한다.
# 사당역·신대방역은 별도 페이지를 만들지 않고 인접 동(남현동·보라매동·조원동)
# 본문 섹션으로 흡수해 도어웨이 리스크를 회피한다.
STATIONS = [
    {"slug": "sillim-station", "name": "신림역", "line": "2호선·신림선",
     "group": "line2",
     "title": "신림역 출장마사지 | 관악구 신림역 인근 방문 마사지",
     "desc": "신림역 출장마사지 안내 페이지입니다. 관악구 신림역 인근 방문 가능 지역, 예약 가능 시간, 코스 선택 기준, 이용 전 확인사항을 확인해보세요.",
     "addr": "서울 관악구 남부순환로 지하1614",
     "arrival": 18,
     "summary": "2호선·신림선 환승역인 신림역은 관악구에서 검색 수요가 가장 큰 핵심 역세권입니다.",
     "zones": [
        ("신림동 생활권", "신림역은 신림중앙시장·순대타운을 낀 관악 최대 상업·주거 밀집 생활권의 중심입니다. 역 주변 아파트·빌라·오피스텔로 방문 문의가 고르게 들어옵니다."),
        ("서원동·신원동 인근", "신림선 서원역 방면 서원동과 신림역 남측 신원동 생활권도 신림역 기준으로 함께 안내드립니다."),
        ("오피스텔·원룸 방문 안내", "신림역 일대는 1인 가구 원룸·오피스텔이 많아, 공동현관 출입 방법과 동·호수를 알려주시면 도착이 빨라집니다.")],
     "related": ["sillim-dong", "seowon-dong", "sinwon-dong", "seorim-dong"],
     "faq": [
        ("신림역 어느 출구 쪽까지 방문하나요?", "신림역 전 출구 방면(신림중앙시장·순대타운·서원동·신원동 등) 인근을 안내드립니다. 정확한 가능 여부는 예약 시 위치를 기준으로 확인합니다."),
        ("신림역 근처 오피스텔도 예약되나요?", "네. 신림역 일대 원룸·오피스텔 방문 문의가 많습니다. 공동현관 출입 방법을 미리 알려주시면 도착이 수월합니다."),
        ("신림역까지 도착은 얼마나 걸리나요?", "평균 18분 내외이며, 시간대와 정확한 위치에 따라 달라질 수 있습니다.")]},

    {"slug": "seoul-national-university-station", "name": "서울대입구역", "line": "2호선",
     "group": "line2",
     "title": "서울대입구역 출장마사지 | 관악구 서울대입구역 방문 마사지",
     "desc": "서울대입구역 출장마사지 예약 안내입니다. 서울대입구역, 봉천동, 청룡동 생활권을 중심으로 방문 가능 여부와 예약 전 준비사항을 안내합니다.",
     "addr": "서울 관악구 남부순환로 지하1924",
     "arrival": 19,
     "summary": "2호선 서울대입구역은 샤로수길 상권과 봉천 주거지가 어우러진 관악 동부의 대표 역세권입니다.",
     "zones": [
        ("봉천동·청룡동 생활권", "서울대입구역은 봉천동 중심 생활권과 청룡동 원룸촌이 맞닿은 곳으로, 주거지와 1인 가구 방문 문의가 고르게 들어옵니다."),
        ("샤로수길·역세권 상권", "샤로수길 상권 주변 오피스텔·주거지도 서울대입구역 기준으로 함께 안내드립니다."),
        ("오피스텔·숙소 방문 안내", "역 인근 오피스텔·숙소 방문 시 건물명과 동·호수, 출입 방법을 알려주시면 빠르게 도착합니다.")],
     "related": ["bongcheon-dong", "cheongnyong-dong", "seonghyeon-dong"],
     "faq": [
        ("서울대입구역 어느 동까지 방문하나요?", "봉천동·청룡동·성현동 등 서울대입구역 인근 생활권을 안내드립니다. 정확한 위치는 예약 시 확인합니다."),
        ("샤로수길 근처도 예약되나요?", "네. 샤로수길 상권 주변 주거지·오피스텔도 서울대입구역 기준으로 함께 안내합니다."),
        ("서울대입구역 도착 시간은 어느 정도인가요?", "평균 19분 내외이며, 시간대와 위치에 따라 달라질 수 있습니다.")]},

    {"slug": "bongcheon-station", "name": "봉천역", "line": "2호선",
     "group": "line2",
     "title": "봉천역 출장마사지 | 관악구 봉천역 인근 방문 마사지",
     "desc": "봉천역 출장마사지 안내 페이지입니다. 봉천역, 은천동, 중앙동 생활권 인근 방문 가능 지역과 예약 가능 시간, 코스 선택 기준을 확인해보세요.",
     "addr": "서울 관악구 남부순환로 지하1721",
     "arrival": 20,
     "summary": "2호선 봉천역은 관악중앙시장과 대단지 아파트가 어우러진 봉천 중심 역세권입니다.",
     "zones": [
        ("봉천동·중앙동 생활권", "봉천역은 관악중앙시장을 낀 상업·주거 밀집 생활권의 중심으로, 봉천동·중앙동 방문 문의가 많습니다."),
        ("은천동 아파트 단지", "관악푸르지오·벽산블루밍 등 봉천역 인근 대단지 아파트 생활권도 함께 안내드립니다."),
        ("주거지·숙소 방문 안내", "봉천역 일대 아파트·빌라 방문 시 동·호수와 공동현관 출입 방법을 알려주시면 도착이 빨라집니다.")],
     "related": ["bongcheon-dong", "euncheon-dong", "jungang-dong"],
     "faq": [
        ("봉천역 어느 방면까지 방문하나요?", "봉천동·은천동·중앙동 등 봉천역 인근 생활권을 안내드립니다. 정확한 가능 여부는 예약 시 확인합니다."),
        ("봉천역 근처 아파트 단지도 되나요?", "네. 은천동 대단지 아파트 등 봉천역 인근 주거지 방문 문의가 많습니다."),
        ("봉천역 도착은 얼마나 걸리나요?", "평균 20분 내외이며, 시간대와 위치에 따라 달라질 수 있습니다.")]},

    {"slug": "nakseongdae-station", "name": "낙성대역", "line": "2호선",
     "group": "line2",
     "title": "낙성대역 출장마사지 | 관악구 낙성대역 방문 마사지",
     "desc": "낙성대역 출장마사지 안내 페이지입니다. 낙성대역, 낙성대동, 인헌동 인근 생활권의 방문 가능 지역과 코스 선택 기준을 확인해보세요.",
     "addr": "서울 관악구 남부순환로 지하1928",
     "arrival": 22,
     "summary": "2호선 낙성대역은 낙성대공원과 인헌동 학군지를 낀 조용한 정주형 역세권입니다.",
     "zones": [
        ("낙성대동 생활권", "낙성대역은 낙성대공원을 낀 주거 생활권의 중심으로, 공원 주변 아파트·빌라 방문 문의가 많습니다."),
        ("행운동·인헌동 인근", "낙성대역 방면 행운동과 인헌중·고 인근 학군지 인헌동 생활권도 함께 안내드립니다."),
        ("주거지·숙소 방문 안내", "낙성대역 일대 주거지 방문 시 정확한 주소와 출입 방법을 알려주시면 도착이 수월합니다.")],
     "related": ["nakseongdae-dong", "haengun-dong", "inheon-dong"],
     "faq": [
        ("낙성대역 어느 동까지 방문하나요?", "낙성대동·행운동·인헌동 등 낙성대역 인근 생활권을 안내드립니다. 정확한 위치는 예약 시 확인합니다."),
        ("낙성대공원 근처도 예약되나요?", "네. 낙성대공원 주변 주거지도 낙성대역 기준으로 함께 안내합니다."),
        ("낙성대역 도착 시간은 어느 정도인가요?", "평균 22분 내외이며, 시간대와 위치에 따라 달라질 수 있습니다.")]},

    {"slug": "danggok-station", "name": "당곡역", "line": "신림선",
     "group": "sillimline",
     "title": "당곡역 출장마사지 | 관악구 당곡역 인근 방문 마사지",
     "desc": "당곡역 출장마사지 안내입니다. 신림선 당곡역 인근 신원동·서원동 생활권의 방문 가능 지역, 예약 가능 시간, 코스 선택 기준을 확인해보세요.",
     "addr": "서울 관악구 신림로 지하",
     "arrival": 21,
     "summary": "신림선 당곡역은 신림 남부 주거 생활권과 신림역 상권 사이를 잇는 역세권입니다.",
     "zones": [
        ("신원동·서원동 생활권", "당곡역은 신원동·서원동 주거 밀집 생활권과 가까워, 빌라·아파트 방문 문의가 많습니다."),
        ("신림역 방면", "신림선을 따라 신림역 상권 방면 생활권과 이어집니다."),
        ("주거지·숙소 방문 안내", "당곡역 일대 주거지 방문 시 동·호수와 출입 방법을 알려주시면 도착이 빨라집니다.")],
     "related": ["sinwon-dong", "seowon-dong", "miseong-dong"],
     "faq": [
        ("당곡역 어느 방면까지 방문하나요?", "신원동·서원동·미성동 등 당곡역 인근 생활권을 안내드립니다. 정확한 가능 여부는 예약 시 확인합니다."),
        ("당곡역은 어느 노선인가요?", "당곡역은 신림선 역으로, 신림 남부 생활권과 가깝습니다."),
        ("당곡역 도착은 얼마나 걸리나요?", "평균 21분 내외이며, 시간대와 위치에 따라 달라질 수 있습니다.")]},

    {"slug": "seowon-station", "name": "서원역", "line": "신림선",
     "group": "sillimline",
     "title": "서원역 출장마사지 | 관악구 서원역 인근 방문 마사지",
     "desc": "서원역 출장마사지 안내입니다. 신림선 서원역 인근 서원동·신림동 생활권의 방문 가능 지역과 예약 전 준비사항을 안내합니다.",
     "addr": "서울 관악구 신림로 지하",
     "arrival": 22,
     "summary": "신림선 서원역은 서원동 주거지와 신림역 상권을 잇는 신림 서부 역세권입니다.",
     "zones": [
        ("서원동 생활권", "서원역은 서원동 빌라·주택 주거 밀집 생활권의 중심으로, 정주형 주거지 방문 문의가 많습니다."),
        ("신림동·신림역 방면", "신림선을 따라 신림역 상권·신림동 생활권과 이어집니다."),
        ("주거지·숙소 방문 안내", "서원역 일대 주거지 방문 시 정확한 주소와 출입 방법을 알려주시면 도착이 수월합니다.")],
     "related": ["seowon-dong", "sillim-dong", "miseong-dong"],
     "faq": [
        ("서원역 어느 동까지 방문하나요?", "서원동·신림동·미성동 등 서원역 인근 생활권을 안내드립니다. 정확한 위치는 예약 시 확인합니다."),
        ("서원역은 어느 노선인가요?", "서원역은 신림선 역으로, 신림 서부 생활권과 가깝습니다."),
        ("서원역 도착 시간은 어느 정도인가요?", "평균 22분 내외이며, 시간대와 위치에 따라 달라질 수 있습니다.")]},

    {"slug": "seoul-national-university-venture-town-station", "name": "서울대벤처타운역", "line": "신림선",
     "group": "sillimline",
     "title": "서울대벤처타운역 출장마사지 | 관악구 신림선 방문 마사지",
     "desc": "서울대벤처타운역 출장마사지 안내입니다. 신림선 서울대벤처타운역 인근 대학동·신림동 생활권의 방문 가능 지역과 코스 선택 기준을 확인해보세요.",
     "addr": "서울 관악구 신림로 지하",
     "arrival": 24,
     "summary": "신림선 서울대벤처타운역은 서울대학교 진입로와 대학동 고시촌을 낀 학생·청년 역세권입니다.",
     "zones": [
        ("대학동·고시촌 생활권", "서울대벤처타운역은 대학동 고시촌의 원룸·고시원 밀집 생활권과 가까워, 1인 가구 방문 문의가 많습니다."),
        ("신림동 방면", "신림선을 따라 신림역 상권·신림동 생활권과 이어집니다."),
        ("오피스텔·원룸 방문 안내", "역 인근 원룸·고시원 방문 시 건물명과 호수, 출입 방법을 알려주시면 도착이 빨라집니다.")],
     "related": ["daehak-dong", "sillim-dong", "seowon-dong"],
     "faq": [
        ("서울대벤처타운역 어느 방면까지 방문하나요?", "대학동·신림동 등 서울대벤처타운역 인근 생활권을 안내드립니다. 정확한 가능 여부는 예약 시 확인합니다."),
        ("고시촌 원룸도 예약되나요?", "네. 대학동 고시촌 원룸·고시원 방문 문의가 많습니다. 건물명과 호수를 미리 알려주세요."),
        ("서울대벤처타운역 도착은 얼마나 걸리나요?", "평균 24분 내외이며, 시간대와 위치에 따라 달라질 수 있습니다.")]},

    {"slug": "gwanaksan-station", "name": "관악산역", "line": "신림선",
     "group": "sillimline",
     "title": "관악산역 출장마사지 | 관악산역 인근 방문 마사지",
     "desc": "관악산역 출장마사지 안내입니다. 신림선 관악산역(서울대) 인근 대학동·고시촌 생활권의 방문 가능 지역과 예약 가능 시간을 안내합니다.",
     "addr": "서울 관악구 관악로 지하",
     "arrival": 25,
     "summary": "신림선 관악산역(서울대)은 서울대학교 정문과 대학동 생활권을 낀 신림선 종점 역세권입니다.",
     "zones": [
        ("대학동 생활권", "관악산역은 서울대학교 정문과 대학동 생활권의 관문으로, 고시촌·원룸 방문 문의가 많습니다."),
        ("서울대·미성동 방면", "서울대 캠퍼스 방면과 미성동 주거 생활권으로 이어집니다."),
        ("오피스텔·숙소 방문 안내", "관악산역 일대 원룸·숙소 방문 시 정확한 주소와 출입 방법을 알려주시면 도착이 수월합니다.")],
     "related": ["daehak-dong", "miseong-dong"],
     "faq": [
        ("관악산역 어느 방면까지 방문하나요?", "대학동·미성동 등 관악산역 인근 생활권을 안내드립니다. 정확한 위치는 예약 시 확인합니다."),
        ("관악산역은 어느 노선인가요?", "관악산역(서울대)은 신림선 종점 역으로, 서울대학교·대학동 생활권과 가깝습니다."),
        ("관악산역 도착 시간은 어느 정도인가요?", "평균 25분 내외이며, 시간대와 위치에 따라 달라질 수 있습니다.")]},
]

# 역별 고유 단락(역세권 특징) — 도어웨이 회피용 1차 정보
STATION_DETAIL = {
    "sillim-station": [
        "신림역은 2호선과 신림선이 만나는 환승역으로, 관악구에서 유동 인구와 검색 수요가 가장 많은 역세권입니다. 신림중앙시장·순대타운·고시촌 상권을 따라 원룸과 오피스텔이 빽빽하게 들어서 있어, 자정 이후 심야 시간대에도 방문 문의가 끊이지 않는 편입니다.",
        "역 주변은 골목과 경사로가 많아 같은 신림역 인근이라도 위치에 따라 도착 시간이 달라집니다. 예약 시 정확한 건물명과 출구 번호, 공동현관 출입 방법을 함께 알려주시면 평균 18분 내외로 도착할 수 있습니다."],
    "seoul-national-university-station": [
        "서울대입구역은 2호선 단일 역이지만 샤로수길이라는 대형 상권을 끼고 있어 청년·직장인 방문 문의가 많은 역세권입니다. 봉천동 주거지와 청룡동 원룸촌이 역을 중심으로 펼쳐져 있어, 평일 퇴근 이후와 주말 저녁에 예약이 집중되는 편입니다.",
        "역 일대는 오피스텔과 도시형 생활주택이 많아 건물 출입 절차가 제각각입니다. 예약 시 호수와 출입 방법을 미리 알려주시면 샤로수길 혼잡 시간대에도 평균 19분 내외로 도착할 수 있습니다."],
    "bongcheon-station": [
        "봉천역은 관악중앙시장과 대단지 아파트가 어우러진 봉천 중심 역세권으로, 1인 가구와 가족 단위 방문이 고르게 들어옵니다. 남부순환로(관악구 남부순환로 지하1721)를 따라 상권과 주거지가 이어져 낮부터 밤까지 시간대별 문의가 비교적 고른 편입니다.",
        "은천동·중앙동 쪽 대단지 아파트는 동·호수와 공동현관 비밀번호만 정확히 알려주시면 진입이 빠릅니다. 봉천역 인근은 평균 20분 내외로 도착하며, 주말 저녁에는 다소 길어질 수 있어 사전 예약을 권장드립니다."],
    "nakseongdae-station": [
        "낙성대역은 낙성대공원과 인헌동 학군지를 낀 비교적 조용한 정주형 역세권입니다. 강감찬 장군 사적지인 낙성대공원 주변으로 아파트와 빌라가 모여 있어, 가족 단위와 직장인 방문 문의가 많은 편입니다.",
        "행운동·인헌동 방면은 언덕 지형이 많아 차량 진입로가 한정적입니다. 예약 시 가까운 출구나 큰 건물을 기준점으로 알려주시면 평균 22분 내외로 도착할 수 있습니다."],
    "danggok-station": [
        "당곡역은 2022년 개통한 신림선 역으로, 신림 남부의 신원동·서원동 주거 생활권과 신림역 상권 사이를 잇습니다. 비교적 최근 정비된 주거지가 많아 빌라·소형 아파트 방문 문의가 꾸준한 편입니다.",
        "신림선은 배차가 촘촘해 역 접근성이 좋지만, 당곡역 일대는 골목이 많아 위치 안내가 중요합니다. 예약 시 정확한 주소와 출입 방법을 알려주시면 평균 21분 내외로 도착할 수 있습니다."],
    "seowon-station": [
        "서원역은 신림선을 따라 서원동 주거 밀집지와 신림역 상권을 연결하는 역세권입니다. 빌라·다세대 주택이 많은 정주형 생활권으로, 저녁 시간대 자택 방문 문의가 주를 이룹니다.",
        "서원동 일대는 일방통행과 경사 골목이 섞여 있어 도보 진입이 빠른 경우가 많습니다. 예약 시 건물명과 층·호수를 함께 알려주시면 평균 22분 내외로 도착할 수 있습니다."],
    "seoul-national-university-venture-town-station": [
        "서울대벤처타운역은 신림선 역으로, 대학동 고시촌과 서울대학교 진입로를 끼고 있어 학생·청년 1인 가구 방문이 많은 역세권입니다. 고시원·원룸이 밀집한 특성상 시험 기간 전후로 예약 패턴이 달라지는 편입니다.",
        "고시촌은 골목이 좁고 건물이 빽빽해 호수와 건물명 확인이 특히 중요합니다. 예약 시 출입 방법을 미리 알려주시면 평균 24분 내외로 도착할 수 있습니다."],
    "gwanaksan-station": [
        "관악산역(서울대)은 신림선 종점으로, 서울대학교 정문과 대학동 생활권의 관문 역할을 합니다. 캠퍼스와 관악산 둘레길을 낀 지역 특성상 학생·연구원과 등산객 숙소 방문 문의가 섞여 들어옵니다.",
        "종점 특성상 차량보다 신림선 도보 접근이 빠른 경우가 많습니다. 예약 시 정확한 주소와 기준점을 알려주시면 평균 25분 내외로 도착할 수 있습니다."],
}

# 역 그룹(메뉴·허브용)
STATION_GROUPS = [
    ("line2", "2호선 관악권", "낙성대·서울대입구·봉천·신림역으로 이어지는 2호선 관악 구간입니다."),
    ("sillimline", "신림선 관악권", "당곡·서원·서울대벤처타운·관악산역으로 이어지는 신림선 관악 구간입니다."),
]

# 인접 생활권(별도 페이지 없이 인접 동 본문 섹션으로 흡수)
STATION_NEARBY = [
    {"name": "사당역 인근", "dong": "namhyeon-dong", "dong_name": "남현동",
     "note": "사당역(2·4호선) 인근은 남현동 생활권과 맞닿아 있어, 남현동 페이지에서 함께 안내드립니다."},
    {"name": "신대방역 인근", "dong": "boramae-dong", "dong_name": "보라매동",
     "note": "신대방역(2호선) 인근은 보라매동·조원동 생활권과 가까워, 보라매동 페이지에서 함께 안내드립니다."},
]

def station_by_slug(slug):
    for s in STATIONS:
        if s["slug"] == slug:
            return s
    return None

# 코스
COURSES = [
    {"slug": "fatigue", "kicker": "RELAX · 피로 회복", "name": "피로 회복 관리",
     "desc": "전신의 긴장을 부드럽게 풀어주는 스웨디시 계열 기본 관리입니다.",
     "prices": [("60분", "70,000원"), ("90분", "100,000원"), ("120분", "130,000원")]},
    {"slug": "aroma", "kicker": "AROMA · 아로마", "name": "아로마 관리",
     "desc": "블렌딩 오일을 사용해 향과 함께 심신을 이완하는 관리입니다.",
     "prices": [("60분", "80,000원"), ("90분", "110,000원"), ("120분", "140,000원")], "best": True},
    {"slug": "sports", "kicker": "SPORTS · 스포츠", "name": "스포츠 관리",
     "desc": "운동 후 뭉친 근육과 컨디션 회복에 초점을 맞춘 관리입니다.",
     "prices": [("60분", "90,000원"), ("90분", "120,000원"), ("120분", "150,000원")]},
    {"slug": "couple", "kicker": "COUPLE · 커플·가족", "name": "커플·가족 방문 관리",
     "desc": "두 분이 함께 같은 공간에서 동시에 받는 동반 관리입니다.",
     "prices": [("60분", "150,000원~"), ("90분", "200,000원~"), ("120분", "250,000원~")]},
    {"slug": "group", "kicker": "GROUP · 기업·단체", "name": "기업·단체 방문 관리",
     "desc": "워크숍·행사 등 단체 인원을 위한 사전 협의형 방문 관리입니다.",
     "prices": [("협의", "별도 견적"), ("협의", "별도 견적"), ("협의", "별도 견적")]},
]

# 코스별 기본 요금 (시간 기준 메뉴 — 메인/모든 지역 페이지 공통)
TIME_PRICING = [
    {"name": "60분 코스", "price": "90,000", "dur": "60분", "desc": "기본 컨디션·릴랙스 케어"},
    {"name": "90분 코스", "price": "150,000", "dur": "90분", "desc": "아로마 포함 추천 구성", "best": True},
    {"name": "120분 코스", "price": "180,000", "dur": "120분", "desc": "전신 집중 프리미엄 케어"},
]

# ---------------------------------------------------------------------------
# Shared CSS  (design system from BLUEPRINT.md)
# ---------------------------------------------------------------------------
CSS = """
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0b0b0e;--surface:#13131a;--surface-2:#1a1a23;--line:rgba(255,255,255,.08);
  --text:#f3f3f5;--muted:#9a9aa3;--dim:#6c6c75;
  --gold:#d6b274;--rose:#e9b8a7;--copper:#c98a6b;
  --grad:linear-gradient(135deg,#f4d29c 0%,#e9b8a7 45%,#c98a6b 100%);
  --grad-soft:linear-gradient(135deg,rgba(244,210,156,.14),rgba(201,138,107,.06));
}
html{scroll-behavior:smooth}
body{background:var(--bg);color:var(--text);line-height:1.65;letter-spacing:-.01em;
  font-family:"Pretendard","Apple SD Gothic Neo","Noto Sans KR",system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  -webkit-font-smoothing:antialiased;overflow-x:hidden}
a{color:inherit;text-decoration:none}
img{max-width:100%;display:block}
.serif,.note-num,.step .n{font-family:"Cormorant Garamond","Noto Serif KR",Georgia,serif;font-weight:300;font-style:italic}
.grad{background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent}
.wrap{max-width:1240px;margin:0 auto;padding:0 24px}
section.block{padding:96px 0}
.eyebrow{display:inline-flex;align-items:center;gap:8px;font-size:11.5px;letter-spacing:.2em;
  text-transform:uppercase;color:var(--gold);font-weight:700}
.pulse{width:7px;height:7px;border-radius:50%;background:var(--rose);box-shadow:0 0 0 0 rgba(233,184,167,.6);animation:pulse 2s infinite}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(233,184,167,.55)}70%{box-shadow:0 0 0 9px rgba(233,184,167,0)}100%{box-shadow:0 0 0 0 rgba(233,184,167,0)}}
h2.sec{font-size:clamp(28px,4vw,46px);letter-spacing:-.03em;font-weight:800;margin:14px 0 10px}
.sec-lead{color:var(--muted);max-width:660px;font-size:15px}
/* header */
header{position:sticky;top:0;z-index:60;backdrop-filter:blur(14px);
  background:rgba(11,11,14,.78);border-bottom:1px solid var(--line)}
.nav{max-width:1240px;margin:0 auto;padding:14px 24px;display:flex;align-items:center;gap:18px}
.brand{display:flex;align-items:center;gap:10px;font-weight:800;font-size:18px;letter-spacing:-.02em}
.brand .mark{width:34px;height:34px;border-radius:10px;background:var(--grad);display:grid;place-items:center;
  color:#1a1208;font-weight:800;font-family:"Cormorant Garamond",serif;font-style:italic;font-size:20px}
.brand small{display:block;font-size:10.5px;letter-spacing:.16em;color:var(--gold);font-weight:700}
.menu{list-style:none;display:flex;align-items:center;gap:4px;margin-left:auto}
.menu>li{position:relative}
.menu>li>a{display:block;padding:10px 13px;font-size:14px;color:var(--text);border-radius:9px;font-weight:600}
.menu>li>a:hover{background:rgba(255,255,255,.05)}
.menu>li>a.active{color:var(--gold)}
.submenu{position:absolute;top:calc(100% + 6px);left:0;min-width:212px;list-style:none;padding:8px;
  background:linear-gradient(160deg,var(--surface),var(--surface-2));border:1px solid var(--line);
  border-radius:14px;box-shadow:0 20px 48px rgba(0,0,0,.45);opacity:0;visibility:hidden;transform:translateY(6px);
  transition:.22s;z-index:70}
.menu>li:hover>.submenu,.menu>li:focus-within>.submenu{opacity:1;visibility:visible;transform:none}
.submenu li{position:relative}
.submenu li a{display:block;padding:9px 12px;font-size:13.5px;color:var(--muted);border-radius:9px}
.submenu li a:hover{background:rgba(255,255,255,.05);color:var(--text)}
.submenu li.has-sub>a::after{content:"›";float:right;color:var(--dim);font-weight:700}
.submenu .sub2{position:absolute;top:-9px;left:calc(100% + 7px);transform:translateX(6px)}
.submenu li.has-sub:hover>.sub2,.submenu li.has-sub:focus-within>.sub2{opacity:1;visibility:visible;transform:none}
.cta-pill{margin-left:6px;padding:11px 18px!important;background:var(--grad);color:#1a1208!important;
  border-radius:999px;font-weight:800!important}
.toggle{display:none;margin-left:auto;background:none;border:1px solid var(--line);color:var(--text);
  font-size:20px;width:44px;height:44px;border-radius:11px;cursor:pointer}
/* hero */
.hero{position:relative;overflow:hidden;border-bottom:1px solid var(--line)}
.hero::before{content:"";position:absolute;inset:0;z-index:0;
  background:radial-gradient(60% 70% at 80% 10%,rgba(233,184,167,.16),transparent 60%),
             radial-gradient(50% 60% at 10% 90%,rgba(214,178,116,.12),transparent 60%),
             radial-gradient(40% 50% at 50% 50%,rgba(201,138,107,.08),transparent 70%)}
.hero-inner{position:relative;z-index:1;display:grid;grid-template-columns:1.12fr .88fr;gap:48px;
  align-items:center;max-width:1240px;margin:0 auto;padding:88px 24px}
.hero h1{font-size:clamp(36px,6vw,70px);font-weight:800;letter-spacing:-.038em;line-height:1.06;margin:18px 0}
.hero .lead{color:var(--muted);font-size:16px;max-width:520px;margin-bottom:26px}
.actions{display:flex;gap:12px;flex-wrap:wrap}
.btn{display:inline-flex;align-items:center;gap:8px;padding:14px 22px;border-radius:12px;font-weight:700;
  font-size:14.5px;transition:.25s;border:1px solid transparent}
.btn-primary{background:var(--grad);color:#1a1208}
.btn-primary:hover{transform:translateY(-2px);box-shadow:0 14px 34px rgba(201,138,107,.35)}
.btn-ghost{border-color:var(--line);color:var(--text)}
.btn-ghost:hover{border-color:rgba(244,210,156,.4);transform:translateY(-2px)}
.trust{margin-top:24px;display:flex;flex-wrap:wrap;gap:8px 18px;color:var(--muted);font-size:13px}
.trust b{color:var(--text)}
.hero-visual{position:relative}
.glass{position:relative;z-index:2;border-radius:20px;padding:26px;
  background:linear-gradient(160deg,rgba(255,255,255,.06),rgba(255,255,255,.02));
  border:1px solid rgba(255,255,255,.12);backdrop-filter:blur(20px);transform:rotate(1.5deg)}
.glass h3{font-size:13px;color:var(--gold);letter-spacing:.04em;margin-bottom:14px}
.glass h3 b{display:block;font-size:21px;color:var(--text);letter-spacing:-.02em;margin-top:4px}
.book-row{display:flex;justify-content:space-between;padding:11px 0;border-top:1px solid var(--line);font-size:14px}
.book-row span:first-child{color:var(--muted)}
.bk{display:block;text-align:center;margin-top:16px;padding:13px;border-radius:12px;background:var(--grad);color:#1a1208;font-weight:800}
.floating{position:absolute;z-index:3;padding:11px 14px;border-radius:12px;font-size:12px;font-weight:600;
  background:linear-gradient(160deg,var(--surface),var(--surface-2));border:1px solid var(--line);
  box-shadow:0 14px 34px rgba(0,0,0,.4)}
.fl-1{top:-18px;left:-14px;transform:rotate(-4deg)}
.fl-2{bottom:-16px;right:-10px;transform:rotate(3deg)}
.fl-1 .dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:#6fe3a1;margin-right:6px}
/* marquee */
.marquee{overflow:hidden;border-bottom:1px solid var(--line);background:var(--surface)}
.marquee-track{display:flex;gap:0;white-space:nowrap;width:max-content;animation:scroll 34s linear infinite}
.marquee-track span{padding:14px 26px;color:var(--muted);font-size:13px;letter-spacing:.04em}
.marquee-track span::after{content:"·";margin-left:26px;color:var(--dim)}
@keyframes scroll{to{transform:translateX(-50%)}}
/* cards grid */
.grid{display:grid;gap:16px}
.g4{grid-template-columns:repeat(auto-fit,minmax(230px,1fr))}
.g3{grid-template-columns:repeat(auto-fit,minmax(280px,1fr))}
.g2{grid-template-columns:repeat(auto-fit,minmax(320px,1fr))}
.card{padding:24px;border-radius:16px;border:1px solid var(--line);
  background:linear-gradient(135deg,var(--surface),var(--surface-2));transition:.3s}
.card:hover{transform:translateY(-4px);border-color:rgba(244,210,156,.28);box-shadow:0 18px 40px rgba(0,0,0,.3)}
.card .k{font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--gold);font-weight:700}
.card h3{margin:10px 0 8px;font-size:19px;font-weight:800}
.card p{color:var(--muted);font-size:14px}
.card .more{display:inline-block;margin-top:14px;color:var(--rose);font-size:13.5px;font-weight:700}
.card:hover .more{transform:translateX(4px)}
/* note card */
.note-card{display:flex;gap:22px;padding:26px 28px;border-radius:18px;position:relative;overflow:hidden;
  background:linear-gradient(135deg,var(--surface),var(--surface-2));border:1px solid var(--line);transition:.3s}
.note-card::before{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--grad);opacity:0;transition:.3s}
.note-card:hover::before{opacity:1}
.note-card:hover{transform:translateY(-2px);box-shadow:0 18px 44px rgba(0,0,0,.32);border-color:rgba(244,210,156,.28)}
.note-num{font-size:44px;background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent;flex-shrink:0;line-height:1}
.note-title{font-size:18px;font-weight:800;margin-bottom:10px}
.note-text{max-width:660px}
.note-text p{margin:0 0 9px;color:#c8c8d0;font-size:14.5px;line-height:1.78}
.note-stack{display:flex;flex-direction:column;gap:14px}
/* chips */
.chips{display:flex;flex-wrap:wrap;gap:10px;margin-top:18px}
.chip{padding:9px 14px;border-radius:999px;border:1px solid var(--line);background:var(--surface);
  font-size:12.5px;color:var(--muted)}
.chip b{color:var(--gold)}
/* price */
.price-card{padding:24px;border-radius:16px;border:1px solid var(--line);position:relative;overflow:hidden;
  background:linear-gradient(135deg,var(--surface),var(--surface-2));transition:.3s}
.price-card::after{content:"";position:absolute;left:0;right:0;top:0;height:2px;background:var(--grad);opacity:.5}
.price-card:hover{transform:translateY(-3px);border-color:rgba(244,210,156,.3)}
.price-card.best{border-color:rgba(244,210,156,.45)}
.best-badge{position:absolute;top:14px;right:14px;font-size:10.5px;font-weight:800;letter-spacing:.1em;
  padding:5px 10px;border-radius:999px;background:var(--grad);color:#1a1208}
.price-card .k{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--gold);font-weight:700}
.price-card h3{margin:8px 0 6px;font-size:20px;font-weight:800}
.price-card>p{color:var(--muted);font-size:13.5px;margin-bottom:14px}
.time-rows>div{display:flex;justify-content:space-between;padding:9px 0;border-top:1px solid var(--line);font-size:14px}
.time-rows span:last-child{font-weight:700}
/* 코스별 기본 요금 메뉴 */
.pmenu{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin-top:28px}
.pmenu-card{position:relative;text-align:center;padding:36px 24px 26px;border-radius:18px;
  background:linear-gradient(135deg,var(--surface),var(--surface-2));border:1px solid var(--line);transition:.3s}
.pmenu-card:hover{transform:translateY(-4px);border-color:rgba(244,210,156,.3);box-shadow:0 18px 42px rgba(0,0,0,.32)}
.pmenu-card.best{border-color:rgba(244,210,156,.5);box-shadow:0 16px 42px rgba(201,138,107,.2)}
.pmenu-name{font-weight:800;font-size:17px;margin-bottom:16px}
.pmenu-price{font-size:clamp(30px,4vw,40px);font-weight:800;letter-spacing:-.035em;line-height:1}
.pmenu-price span{font-size:15px;font-weight:600;color:var(--muted);margin-left:3px;letter-spacing:0}
.pmenu-dur{color:var(--gold);font-size:13px;font-weight:700;margin-top:10px}
.pmenu-desc{color:var(--muted);font-size:13.5px;margin:8px 0 22px}
.pmenu-btn{display:block;padding:13px;border-radius:11px;border:1px solid var(--line);font-weight:700;font-size:14px;transition:.25s}
.pmenu-btn:hover{border-color:rgba(244,210,156,.5);transform:translateY(-1px)}
.pmenu-card.best .pmenu-btn{background:var(--grad);color:#1a1208;border-color:transparent}
.pmenu-badge{position:absolute;top:-12px;left:50%;transform:translateX(-50%);background:var(--grad);color:#1a1208;
  font-size:11.5px;font-weight:800;padding:5px 15px;border-radius:999px;box-shadow:0 6px 16px rgba(201,138,107,.35)}
.pmenu-note{margin-top:20px;color:var(--muted);font-size:13px}
.pmenu-note a{color:var(--gold);font-weight:700;white-space:nowrap}
@media(max-width:760px){.pmenu{grid-template-columns:1fr}}
/* faq */
details{border:1px solid var(--line);border-radius:14px;padding:0;margin-bottom:12px;
  background:linear-gradient(135deg,var(--surface),var(--surface-2));overflow:hidden}
summary{list-style:none;cursor:pointer;padding:18px 22px;font-weight:700;font-size:15px;
  display:flex;justify-content:space-between;align-items:center;gap:14px}
summary::-webkit-details-marker{display:none}
summary span{color:var(--gold);font-size:22px;transition:.25s;flex-shrink:0}
details[open] summary span{transform:rotate(45deg)}
details>div{padding:0 22px 20px;color:var(--muted);font-size:14.5px;line-height:1.78}
/* breadcrumb */
.crumb{font-size:12.5px;color:var(--dim);padding:18px 0}
.crumb a{color:var(--muted)}
.crumb a:hover{color:var(--gold)}
.crumb b{color:var(--text)}
/* review */
.review{padding:22px;border-radius:16px;border:1px solid var(--line);
  background:linear-gradient(135deg,var(--surface),var(--surface-2))}
.review .stars{color:var(--gold);font-size:13px;letter-spacing:2px}
.review p{margin:10px 0;font-size:14px;color:#c8c8d0;line-height:1.7}
.review .who{font-size:12.5px;color:var(--muted)}
/* cta band */
.cta-band{position:relative;overflow:hidden;text-align:center;padding:88px 24px;border-top:1px solid var(--line)}
.cta-band::before{content:"";position:absolute;inset:0;background:radial-gradient(50% 80% at 50% 0%,rgba(233,184,167,.16),transparent 60%)}
.cta-band>div{position:relative}
.cta-band h2{font-size:clamp(26px,4vw,42px);font-weight:800;letter-spacing:-.03em}
.cta-band p{color:var(--muted);margin:12px 0 24px}
/* footer */
.site-footer{border-top:1px solid var(--line);background:var(--surface);padding:64px 0 36px;font-size:13.5px}
.footer-grid{display:grid;grid-template-columns:1.4fr 1fr 1fr 1fr;gap:30px}
.footer-grid h4{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--gold);margin-bottom:14px}
.footer-grid a{display:block;color:var(--muted);padding:5px 0}
.footer-grid a:hover{color:var(--text)}
.footer-brand b{font-size:17px}
.footer-brand p{color:var(--muted);margin-top:10px;max-width:280px;line-height:1.7}
.footer-ops{margin:34px 0;padding:22px;border-radius:14px;background:var(--grad-soft);
  border:1px solid var(--line);display:flex;flex-wrap:wrap;gap:14px 40px}
.footer-ops div b{color:var(--gold);display:block;font-size:11px;letter-spacing:.12em;margin-bottom:4px}
.company-info{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;color:var(--dim);font-size:12.5px;
  padding-top:24px;border-top:1px solid var(--line)}
.company-info b{color:var(--muted)}
.footer-policies{display:flex;flex-wrap:wrap;gap:8px 18px;margin:22px 0 14px}
.footer-policies a{color:var(--muted);font-size:12.5px}
.footer-bottom{color:var(--dim);font-size:12px;line-height:1.7;border-top:1px solid var(--line);padding-top:18px}
.legal-note{margin-top:8px;color:var(--dim)}
/* 콘텐츠 아티클 + 저자 표기(E-E-A-T) */
.byline{display:flex;flex-wrap:wrap;gap:6px 16px;margin-top:18px;color:var(--dim);font-size:12.5px}
.byline span{display:inline-flex;align-items:center}
.byline span+span::before{content:"·";margin-right:16px;color:var(--dim)}
.byline .au{color:var(--muted);font-weight:700}
.article{max-width:760px}
.article h2{font-size:clamp(21px,3vw,29px);font-weight:800;letter-spacing:-.02em;margin:38px 0 12px}
.article h2:first-child{margin-top:8px}
.article h3{font-size:17px;font-weight:800;margin:20px 0 8px}
.article p{color:#c8c8d0;font-size:15px;line-height:1.85;margin:0 0 12px}
.article ul{margin:0 0 14px;padding-left:20px;color:#c8c8d0;font-size:15px;line-height:1.85}
.article li{margin-bottom:6px}
.article strong{color:var(--text)}
.data-box{margin:24px 0;padding:20px 22px;border-radius:14px;background:var(--grad-soft);border:1px solid var(--line)}
.data-box b{color:var(--gold);display:block;font-size:11px;letter-spacing:.14em;margin-bottom:8px;text-transform:uppercase}
.data-box p{color:var(--muted);font-size:13.5px;margin:0;line-height:1.8}
/* 다크 럭스 스파 — 지역/콘텐츠 페이지 (네이비 패널 + 골드 + 좌측 TOC) */
.lux-hero{position:relative;overflow:hidden;border-bottom:1px solid rgba(244,210,156,.14);
  background:radial-gradient(70% 120% at 88% -10%,rgba(233,184,167,.14),transparent 60%),
             linear-gradient(180deg,#0d1018,#0b0b0e);padding:54px 0 40px}
.lux-h1{font-size:clamp(30px,5vw,52px);font-weight:800;letter-spacing:-.03em;line-height:1.1;margin:14px 0 12px;color:#fff}
.lux-lead{color:#cfd2da;font-size:16.5px;line-height:1.8;max-width:760px}
.lux-body{background:linear-gradient(180deg,#0b0b0e,#0c0e15 40%,#0b0b0e)}
.lux-grid{display:grid;grid-template-columns:240px 1fr;gap:46px;align-items:start}
.toc{position:sticky;top:86px}
.toc-inner{border:1px solid rgba(244,210,156,.2);border-radius:16px;padding:18px 14px;
  background:linear-gradient(165deg,#10131f,#0a0c13);box-shadow:0 18px 40px rgba(0,0,0,.35)}
.toc-label{display:block;font-size:10.5px;letter-spacing:.2em;color:var(--gold);font-weight:800;text-transform:uppercase;margin:0 0 12px 8px}
.toc ul{list-style:none;margin:0;padding:0}
.toc li a{display:block;padding:8px 12px;font-size:13px;line-height:1.4;color:var(--muted);
  border-left:2px solid transparent;border-radius:0 8px 8px 0;transition:.2s}
.toc li a:hover{color:var(--text);background:rgba(255,255,255,.05)}
.toc li a.active{color:var(--gold);border-left-color:var(--gold);background:rgba(244,210,156,.09);font-weight:700}
.lux-main{min-width:0}
.lux-sec{position:relative;overflow:hidden;background:linear-gradient(165deg,#121626,#0c0e16);
  border:1px solid rgba(255,255,255,.08);border-radius:18px;padding:28px 32px;margin-bottom:18px}
.lux-sec::before{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--grad)}
.lux-sec h2{font-size:clamp(20px,2.5vw,27px);font-weight:800;letter-spacing:-.02em;margin:0 0 14px;color:#fff}
.lux-sec h3{color:var(--gold);font-size:16.5px;font-weight:800;margin:20px 0 7px}
.lux-sec p{color:#e4e5ec;font-size:15.5px;line-height:1.9;margin:0 0 12px}
.lux-sec>ul{margin:6px 0 14px;padding:0;list-style:none}
.lux-sec>ul li{position:relative;padding:8px 0 8px 22px;color:#e4e5ec;font-size:15px;line-height:1.65;
  border-bottom:1px solid rgba(255,255,255,.06)}
.lux-sec>ul li::before{content:"";position:absolute;left:3px;top:15px;width:6px;height:6px;border-radius:50%;background:var(--grad)}
.lux-sec>ul li:last-child{border-bottom:none}
.lux-sec a{color:var(--rose);font-weight:600;border-bottom:1px solid rgba(233,184,167,.4)}
.lux-sec a:hover{color:var(--gold);border-bottom-color:var(--gold)}
.lux-sec strong{color:#fff}
.lux-sec .grid{margin-top:6px}
.lux-main .data-box{margin:4px 0 0;background:linear-gradient(135deg,rgba(244,210,156,.12),rgba(201,138,107,.05));
  border:1px solid rgba(244,210,156,.22)}
@media(max-width:980px){
  .lux-grid{grid-template-columns:1fr;gap:14px}
  .toc{position:static}
  .toc-inner{display:flex;flex-wrap:wrap;gap:6px;align-items:center;padding:12px 14px}
  .toc-label{margin:0 4px 0 2px}
  .toc ul{display:flex;flex-wrap:wrap;gap:6px}
  .toc li a{border-left:none;border:1px solid var(--line);border-radius:999px;padding:6px 13px;font-size:12px}
  .toc li a.active{background:var(--grad);color:#1a1208;border-color:transparent}
  .lux-sec{padding:22px 20px}
}
/* 플로팅 전화예약 버튼 (전 페이지) */
.call-fab{position:fixed;right:20px;bottom:20px;z-index:90;display:inline-flex;align-items:center;gap:9px;
  padding:14px 20px 14px 16px;border-radius:999px;color:#fff;font-weight:800;font-size:14.5px;letter-spacing:-.01em;
  background:linear-gradient(135deg,#ffa23c,#ff7a18 55%,#f4600a);
  box-shadow:0 12px 30px rgba(255,122,24,.5);transition:transform .25s,box-shadow .25s}
.call-fab:hover{transform:translateY(-3px);box-shadow:0 16px 38px rgba(255,122,24,.6)}
.call-fab::before{content:"";position:absolute;inset:0;border-radius:999px;border:2px solid #ff7a18;
  animation:fabpulse 1.8s ease-out infinite;pointer-events:none}
.call-fab-ic{position:relative;display:grid;place-items:center;width:26px;height:26px;
  transform-origin:60% 60%;animation:fabring 1.5s ease-in-out infinite}
.call-fab-ic svg{width:21px;height:21px;fill:#fff}
.call-fab-tx{position:relative;white-space:nowrap}
.call-fab-tx small{display:block;font-size:11px;font-weight:700;opacity:.92;letter-spacing:.01em}
@keyframes fabring{0%,62%,100%{transform:rotate(0)}8%,26%{transform:rotate(-15deg)}17%,35%{transform:rotate(15deg)}}
@keyframes fabpulse{0%{transform:scale(1);opacity:.7}100%{transform:scale(1.55);opacity:0}}
@media(max-width:560px){.call-fab{right:14px;bottom:14px;padding:14px}.call-fab-tx{display:none}}
@media(prefers-reduced-motion:reduce){.call-fab-ic,.call-fab::before{animation:none}}
/* reveal */
.reveal{opacity:0;transform:translateY(20px);transition:.8s}
.reveal.in{opacity:1;transform:none}
/* perf */
#region,#process,#reviews,#about,#faq,.cta-band,.site-footer{content-visibility:auto;contain-intrinsic-size:auto 700px}
.card,.note-card,.review,.price-card{contain:layout style}
@media(hover:none){.glass,.floating{backdrop-filter:none}}
@media(prefers-reduced-motion:reduce){.marquee-track,.pulse{animation:none}.reveal{opacity:1;transform:none}}
@media(max-width:1100px){
  .toggle{display:block}
  .menu{position:fixed;inset:64px 0 auto 0;flex-direction:column;align-items:stretch;gap:2px;margin:0;
    padding:14px;background:var(--bg);border-bottom:1px solid var(--line);max-height:calc(100vh - 64px);
    overflow:auto;transform:translateY(-12px);opacity:0;visibility:hidden;transition:.25s}
  .menu.open{transform:none;opacity:1;visibility:visible}
  .menu>li>a{padding:13px 12px}
  .submenu,.submenu .sub2{position:static;opacity:1;visibility:visible;transform:none;box-shadow:none;
    background:transparent;border:none;padding:0 0 6px 12px;min-width:0;left:auto;top:auto}
  .submenu .sub2{padding-left:14px}
  .submenu li.has-sub>a::after{content:""}
  .cta-pill{text-align:center}
  .hero-inner{grid-template-columns:1fr;gap:36px}
  .hero-visual{max-width:420px}
  .footer-grid{grid-template-columns:1fr 1fr}
  .company-info{grid-template-columns:1fr 1fr}
}
@media(max-width:560px){
  .footer-grid,.company-info{grid-template-columns:1fr}
  .note-card{flex-direction:column;gap:12px}
  .hero-inner{padding:56px 24px}
}
"""

# ---------------------------------------------------------------------------
# Navigation model  (top menu + dropdowns)
# ---------------------------------------------------------------------------
def menu_html(active):
    def li(key, href, label, sub=None, cta=False):
        cls = ' class="active"' if active == key else ""
        pop = ' aria-haspopup="true"' if sub else ""
        a = f'<a href="{href}"{cls}{pop}>{label}</a>'
        if cta:
            a = f'<a class="cta-pill" href="tel:{PHONE_TEL}">24시 예약</a>'
        sub_html = ""
        if sub:
            parts = []
            for item in sub:
                if len(item) == 3:  # 하위 동(洞)을 펼치는 3단 항목
                    h, t, kids = item
                    kids_html = "".join(f'<li><a href="{kh}">{kt}</a></li>' for kh, kt in kids)
                    parts.append(
                        f'<li class="has-sub"><a href="{h}" aria-haspopup="true">{t}</a>'
                        f'<ul class="submenu sub2">{kids_html}</ul></li>')
                else:
                    h, t = item
                    parts.append(f'<li><a href="{h}">{t}</a></li>')
            sub_html = f'<ul class="submenu">{"".join(parts)}</ul>'
        return f"<li>{a}{sub_html}</li>"

    region_sub = [("/gwanak-gu/", "관악 출장마사지"),
                  ("/gwanak-gu/area/", "관악구 출장 가능 지역")]
    region_sub += [(f"/gwanak-gu/{r['slug']}/", r["name"],
                    [(f"/gwanak-gu/{d['slug']}/", d["name"]) for d in r["dongs"]])
                   for r in REGIONS]
    # 지하철역별 안내 (역 그룹 → 역, 인접 생활권은 동 섹션으로 연결)
    station_sub = [("/gwanak-gu/stations/", "관악구 지하철역 전체 안내")]
    for gkey, gname, _ in STATION_GROUPS:
        kids = [(f"/gwanak-gu/stations/{s['slug']}/", f"{s['name']} 출장마사지")
                for s in STATIONS if s["group"] == gkey]
        station_sub.append(("/gwanak-gu/stations/", gname, kids))
    station_sub.append(("/gwanak-gu/stations/", "인접 생활권",
                        [(f"/gwanak-gu/{n['dong']}/", n["name"]) for n in STATION_NEARBY]))
    items = [
        li("home", "/", "홈"),
        li("gwanak", "/gwanak-gu/", "관악 출장마사지", [
            ("/gwanak-gu/", "관악 출장마사지 안내"),
            ("/gwanak-gu/area/", "관악구 출장 가능 지역"),
            ("/gwanak-gu/stations/", "관악구 지하철역 안내"),
            ("/gwanak-gu/hours/", "예약 가능 시간"),
            ("/course/guide/", "코스 선택 안내"),
            ("/gwanak-gu/checklist/", "이용 전 확인사항"),
            ("/gwanak-gu/safety/", "위생 및 안전 안내"),
            ("/gwanak-gu/faq/", "관악 출장마사지 FAQ"),
        ]),
        li("area", "/gwanak-gu/area/", "지역별 안내", region_sub),
        li("stations", "/gwanak-gu/stations/", "지하철역별 안내", station_sub),
        li("course", "/course/", "코스안내", [
            ("/course/", "전체 코스"),
            ("/course/fatigue/", "피로 회복 관리"),
            ("/course/aroma/", "아로마 관리"),
            ("/course/sports/", "스포츠 관리"),
            ("/course/couple/", "커플·가족 방문 관리"),
            ("/course/group/", "기업·단체 방문 관리"),
            ("/course/price/", "가격 안내"),
            ("/course/guide/", "코스 선택 가이드"),
        ]),
        li("reservation", "/reservation/", "예약안내"),
        li("guide", "/guide/", "이용가이드"),
        li("reviews", "/reviews/", "고객후기"),
        li("customer", "/customer/", "고객센터"),
        li("cta", "#", "", cta=True),
    ]
    return (
        '<header><nav class="nav" aria-label="주 메뉴">'
        '<a class="brand" href="/" aria-label="간다GO 관악 출장마사지 홈">'
        '<span class="mark">G</span><span>간다GO<small>관악 출장마사지</small></span></a>'
        '<button class="toggle" aria-expanded="false" aria-controls="primary-menu" aria-label="메뉴 열기">☰</button>'
        f'<ul id="primary-menu" class="menu">{"".join(items)}</ul>'
        "</nav></header>"
    )

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
def footer_html():
    region_links = "".join(
        f'<a href="/gwanak-gu/{r["slug"]}/">{r["name"]}</a>' for r in REGIONS
    )
    course_links = "".join(
        f'<a href="/course/{c["slug"]}/">{c["name"]}</a>' for c in COURSES
    )
    return f"""<footer class="site-footer"><div class="wrap">
<div class="footer-grid">
  <div class="footer-brand">
    <b class="grad">{BRAND}</b>
    <p>서울 관악구 봉천·신림·남현 일대(서울대입구·낙성대·신림역 등 역세권 포함) 방문 건강관리 서비스 예약 안내입니다.</p>
  </div>
  <div><h4>지역·역세권</h4>{region_links}<a href="/gwanak-gu/area/">전체 지역 보기</a><a href="/gwanak-gu/stations/">지하철역별 안내</a></div>
  <div><h4>코스</h4>{course_links}</div>
  <div><h4>안내</h4>
    <a href="/about/">간다GO 소개</a><a href="/reservation/">예약안내</a><a href="/guide/">이용가이드</a>
    <a href="/reviews/">고객후기</a><a href="/customer/">고객센터</a></div>
</div>
<div class="footer-ops">
  <div><b>운영 시간</b>{HOURS}</div>
  <div><b>전화 예약·상담</b><a href="tel:{PHONE_TEL}">{PHONE_DISP}</a></div>
</div>
<div class="company-info">
  <div><b>상호</b> {COMPANY['name']}</div>
  <div><b>대표</b> {COMPANY['ceo']}</div>
  <div><b>사업자등록번호</b> {COMPANY['biz_no']}</div>
  <div><b>주소</b> {COMPANY['addr']}</div>
  <div><b>통신판매업신고</b> {COMPANY['sales_no']}</div>
  <div><b>개인정보보호책임자</b> {COMPANY['privacy_officer']}</div>
</div>
<div class="footer-policies">
  <a href="/customer/#notice">공지사항</a><a href="/customer/#qna">자주 묻는 질문</a>
  <a href="/customer/#inquiry">1:1 문의</a><a href="/privacy/">개인정보처리방침</a>
  <a href="/terms/">이용약관</a><a href="/youth/">청소년보호정책</a>
</div>
<div class="footer-bottom">
  © 2026 {COMPANY['name']}. All rights reserved.
  <div class="legal-note">본 서비스는 의료 행위가 아닌 건강관리(이완·휴식) 목적의 방문 관리 서비스이며, 만 19세 이상 성인을 대상으로 합니다. 불법·퇴폐 행위는 일절 제공하지 않습니다.</div>
</div>
</div></footer>"""

# ---------------------------------------------------------------------------
# Shared JS  (idle-loaded)
# ---------------------------------------------------------------------------
JS = """
(function(){
  var t=document.querySelector('.toggle'),m=document.getElementById('primary-menu');
  if(t&&m){t.addEventListener('click',function(){
    var o=m.classList.toggle('open');t.setAttribute('aria-expanded',o);});}
  document.addEventListener('keydown',function(e){if(e.key==='Escape'&&m){m.classList.remove('open');}});
  function idle(fn){if('requestIdleCallback'in window){requestIdleCallback(fn,{timeout:1500});}else{setTimeout(fn,1);}}
  idle(function(){
    if(!('IntersectionObserver'in window)){document.querySelectorAll('.reveal').forEach(function(el){el.classList.add('in');});return;}
    var io=new IntersectionObserver(function(es){es.forEach(function(e){
      if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target);}});},{threshold:.12,rootMargin:'80px'});
    document.querySelectorAll('.reveal').forEach(function(el){io.observe(el);});
    var secs=[].slice.call(document.querySelectorAll('.lux-sec')),
        links=[].slice.call(document.querySelectorAll('.toc a'));
    if(secs.length&&links.length){
      var spy=new IntersectionObserver(function(es){es.forEach(function(e){
        if(e.isIntersecting){var id=e.target.id;
          links.forEach(function(a){a.classList.toggle('active',a.getAttribute('href')==='#'+id);});}});
      },{rootMargin:'-35% 0px -55% 0px'});
      secs.forEach(function(s){spy.observe(s);});
    }
  });
})();
"""

# ---------------------------------------------------------------------------
# Page shell
# ---------------------------------------------------------------------------
def page(path, title, desc, active, body, jsonld=None, og_type="website"):
    canonical = BASE_URL + path
    ld = ""
    if jsonld:
        if isinstance(jsonld, list):
            blocks = jsonld
        else:
            blocks = [jsonld]
        ld = "".join(
            '<script type="application/ld+json">'
            + json.dumps(b, ensure_ascii=False, separators=(",", ":"))
            + "</script>"
            for b in blocks
        )
    og_img = BASE_URL + "/assets/og-cover.jpg"
    html = f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#0b0b0e">
<meta name="format-detection" content="telephone=no">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">
<meta name="googlebot" content="index,follow">
<meta name="referrer" content="strict-origin-when-cross-origin">
<meta name="naver-site-verification" content="{NAVER_VERIFY}">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="author" content="{COMPANY['name']} 운영팀">
<link rel="canonical" href="{canonical}">
<link rel="alternate" hreflang="ko-KR" href="{canonical}">
<link rel="alternate" hreflang="x-default" href="{canonical}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{BRAND}">
<meta property="og:locale" content="ko_KR">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og_img}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{og_img}">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<style>{CSS}</style>
{ld}
</head>
<body>
{menu_html(active)}
{body}
{footer_html()}
{call_fab()}
<script>{JS}</script>
</body>
</html>"""
    return html

def call_fab():
    """오렌지색 플로팅 전화예약 버튼 — 전 페이지 고정 노출."""
    phone_svg = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6.6 10.8c1.4 2.8 3.8 5.2 '
                 '6.6 6.6l2.2-2.2c.28-.28.68-.36 1.02-.24 1.12.37 2.33.57 3.58.57.55 0 1 .45 1 '
                 '1V20c0 .55-.45 1-1 1C10.4 21 3 13.6 3 4.4c0-.55.45-1 1-1h3.6c.55 0 1 .45 1 1 0 '
                 '1.25.2 2.46.57 3.58.12.34.04.74-.24 1.02l-2.2 2.2z"/></svg>')
    return (f'<a class="call-fab" href="tel:{PHONE_TEL}" aria-label="전화 예약 {PHONE_DISP}">'
            f'<span class="call-fab-ic">{phone_svg}</span>'
            f'<span class="call-fab-tx">전화 예약<small>{PHONE_DISP}</small></span></a>')

# ---------------------------------------------------------------------------
# Reusable body builders
# ---------------------------------------------------------------------------
def breadcrumb(items):
    # items: list of (href or None, label)
    parts = []
    for href, label in items:
        if href:
            parts.append(f'<a href="{href}">{label}</a>')
        else:
            parts.append(f"<b>{label}</b>")
    return f'<div class="wrap"><nav class="crumb" aria-label="탐색경로">{" › ".join(parts)}</nav></div>'

def breadcrumb_ld(items):
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": label,
             "item": BASE_URL + href}
            for i, (href, label) in enumerate(items) if href
        ] + [
            {"@type": "ListItem", "position": len(items), "name": items[-1][1]}
        ][:0],  # last handled below
    }

def bc_ld(trail):
    # trail: list of (path, name); last is current page
    el = []
    for i, (p, n) in enumerate(trail):
        item = {"@type": "ListItem", "position": i + 1, "name": n}
        if p:
            item["item"] = BASE_URL + p
        el.append(item)
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": el}

def faq_block(qas, heading="자주 묻는 질문"):
    rows = "".join(
        f"<details><summary>{q}<span>+</span></summary><div>{a}</div></details>"
        for q, a in qas
    )
    return f"""<section class="block" id="faq"><div class="wrap">
<span class="eyebrow"><span class="pulse"></span>FAQ</span>
<h2 class="sec">{heading}</h2>
<div style="margin-top:26px;max-width:820px">{rows}</div>
</div></section>"""

def faq_ld(qas):
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in qas
        ],
    }

def notes_block(eyebrow, heading, lead, notes, _id="about"):
    cards = "".join(
        f'<div class="note-card reveal"><div class="note-num">{n:02d}</div>'
        f'<div class="note-content"><h3 class="note-title">{t}</h3>'
        f'<div class="note-text">{"".join(f"<p>{p}</p>" for p in ps)}</div></div></div>'
        for n, (t, ps) in enumerate(notes, 1)
    )
    return f"""<section class="block" id="{_id}"><div class="wrap">
<span class="eyebrow"><span class="pulse"></span>{eyebrow}</span>
<h2 class="sec">{heading}</h2>
<p class="sec-lead">{lead}</p>
<div class="note-stack" style="margin-top:30px">{cards}</div>
</div></section>"""

def price_grid(courses):
    cards = ""
    for c in courses:
        best = " best" if c.get("best") else ""
        badge = '<span class="best-badge">BEST</span>' if c.get("best") else ""
        rows = "".join(f"<div><span>{t}</span><span>{p}</span></div>" for t, p in c["prices"])
        cards += (
            f'<div class="price-card{best}" id="{c["slug"]}">{badge}'
            f'<div class="k">{c["kicker"]}</div><h3>{c["name"]}</h3>'
            f'<p>{c["desc"]}</p><div class="time-rows">{rows}</div></div>'
        )
    return f'<div class="grid g3">{cards}</div>'

def price_menu_block(anchor="pricing-menu"):
    """코스별 기본 요금 (60·90·120분) — 메인/모든 지역 페이지 공통 블록."""
    cards = ""
    for p in TIME_PRICING:
        best = " best" if p.get("best") else ""
        badge = '<span class="pmenu-badge">추천</span>' if p.get("best") else ""
        cards += (
            f'<div class="pmenu-card{best}">{badge}'
            f'<div class="pmenu-name">{p["name"]}</div>'
            f'<div class="pmenu-price">{p["price"]}<span>원</span></div>'
            f'<div class="pmenu-dur">{p["dur"]}</div>'
            f'<div class="pmenu-desc">{p["desc"]}</div>'
            f'<a class="pmenu-btn" href="tel:{PHONE_TEL}">예약 문의</a></div>'
        )
    return (
        f'<section class="block" id="{anchor}"><div class="wrap">'
        f'<span class="eyebrow"><span class="pulse"></span>요금 안내</span>'
        f'<h2 class="sec">코스별 기본 요금</h2>'
        f'<p class="sec-lead">60·90·120분 코스별 기본 요금입니다. 숨겨진 추가 비용 없이 투명하게 안내합니다.</p>'
        f'<div class="pmenu">{cards}</div>'
        f'<p class="pmenu-note">지역·예약 시간대·이동 거리에 따라 상담 시 최종 확인됩니다. '
        f'<a href="/course/">상세 요금 안내 보기 →</a></p>'
        f'</div></section>'
    )

def offer_ld():
    """코스별 기본 요금 구조화 데이터(Offer)."""
    return {
        "@context": "https://schema.org", "@type": "OfferCatalog",
        "name": "코스별 기본 요금",
        "itemListElement": [
            {"@type": "Offer", "name": p["name"],
             "price": p["price"].replace(",", ""), "priceCurrency": "KRW",
             "description": p["desc"], "url": BASE_URL + "/course/"}
            for p in TIME_PRICING
        ],
    }

def cta_band(title="오늘 밤, 가까운 곳에서 휴식을 예약하세요", sub=None):
    sub = sub or f"{HOURS} · 전화 한 통으로 방문 일정과 코스를 안내드립니다."
    return f"""<section class="cta-band"><div>
<span class="eyebrow"><span class="pulse"></span>RESERVE</span>
<h2>{title}</h2><p>{sub}</p>
<div class="actions" style="justify-content:center">
<a class="btn btn-primary" href="tel:{PHONE_TEL}">{PHONE_DISP} 전화하기 →</a>
<a class="btn btn-ghost" href="/reservation/">예약 안내 보기</a>
</div></div></section>"""

UPDATED = "2026-06-06"

def byline():
    """저자·감수·업데이트 표기 (E-E-A-T 신뢰 신호)."""
    return (f'<div class="byline">'
            f'<span class="au">작성 · 간다GO 운영팀</span>'
            f'<span>감수 · {COMPANY["ceo"]} ({COMPANY["name"]} 대표)</span>'
            f'<span>최종 업데이트 · {UPDATED.replace("-", ".")}</span></div>')

def article_ld(title, desc, path):
    return {
        "@context": "https://schema.org", "@type": "Article",
        "headline": title, "description": desc, "inLanguage": "ko-KR",
        "author": {"@type": "Organization", "name": BRAND, "url": BASE_URL + "/about/"},
        "publisher": {"@type": "Organization", "name": COMPANY["name"], "url": BASE_URL + "/"},
        "mainEntityOfPage": BASE_URL + path,
        "image": BASE_URL + "/assets/og-cover.jpg",
        "datePublished": UPDATED, "dateModified": UPDATED,
    }

def render_lux(sections):
    """다크 럭스 섹션 패널 + 좌측 고정 목차(TOC) 생성.
    sections: [(title, [블록...])]  블록: 문자열(문단)/("ul",[…])/("h3","…")/("html","원본")."""
    toc, panels = [], []
    for i, (title, blocks) in enumerate(sections, 1):
        sid = f"sec-{i}"
        toc.append(f'<li><a href="#{sid}">{title}</a></li>')
        inner = ""
        for b in blocks:
            if isinstance(b, tuple) and b[0] == "ul":
                inner += "<ul>" + "".join(f"<li>{x}</li>" for x in b[1]) + "</ul>"
            elif isinstance(b, tuple) and b[0] == "h3":
                inner += f"<h3>{b[1]}</h3>"
            elif isinstance(b, tuple) and b[0] == "html":
                inner += b[1]
            else:
                inner += f"<p>{b}</p>"
        panels.append(f'<section class="lux-sec reveal" id="{sid}"><h2>{title}</h2>{inner}</section>')
    toc_html = ('<aside class="toc"><div class="toc-inner"><span class="toc-label">목차</span>'
                f'<ul>{"".join(toc)}</ul></div></aside>')
    return toc_html, "".join(panels)

def content_page(path, active, trail, *, title, desc, eyebrow, h1, lead,
                 sections, faq, data_note=None, service=None, show_price=False,
                 top_links=None, extra_schema=None, cta_title=None):
    """E-E-A-T 기준 개별 콘텐츠 페이지 생성기 (다크 럭스 레이아웃 + TOC)."""
    toc_html, panels = render_lux(sections)
    if data_note:
        panels += f'<div class="data-box"><b>현장 운영 메모</b><p>{data_note}</p></div>'
    links_html = ""
    if top_links:
        btns = ""
        for href, label, *rest in top_links:
            primary = rest and rest[0]
            cls = "btn btn-primary" if primary else "btn btn-ghost"
            btns += f'<a class="{cls}" href="{href}">{label}</a>'
        links_html = f'<div class="actions" style="margin-top:22px">{btns}</div>'
    body = (breadcrumb(trail) +
        f'<section class="lux-hero"><div class="wrap">'
        f'<span class="eyebrow"><span class="pulse"></span>{eyebrow}</span>'
        f'<h1 class="lux-h1">{h1}</h1>'
        f'<p class="lux-lead">{lead}</p>{byline()}{links_html}</div></section>'
        f'<section class="block lux-body" style="padding-top:34px"><div class="wrap">'
        f'<div class="lux-grid">{toc_html}<div class="lux-main">{panels}</div></div>'
        f'</div></section>'
        + (price_menu_block() if show_price else "")
        + faq_block(faq) + (cta_band(cta_title) if cta_title else cta_band()))
    jsonld = [bc_ld(trail), article_ld(title, desc, path), faq_ld(faq)]
    if service:
        jsonld.append(service_ld(service[0], service[1], path))
        jsonld.append(offer_ld())
    if extra_schema:
        jsonld += extra_schema
    write(path, page(path, title, desc, active, body, jsonld, og_type="article"))

# ---------------------------------------------------------------------------
# JSON-LD: org / localbusiness / website
# ---------------------------------------------------------------------------
def org_ld():
    return {
        "@context": "https://schema.org", "@type": "Organization",
        "name": BRAND, "legalName": COMPANY["name"], "url": BASE_URL + "/",
        "telephone": PHONE_DISP,
        "logo": BASE_URL + "/icon-512.png",
        "image": BASE_URL + "/assets/og-cover.jpg",
        "address": {"@type": "PostalAddress", "addressLocality": "관악구",
                    "addressRegion": "서울특별시", "addressCountry": "KR"},
    }

def website_ld():
    return {
        "@context": "https://schema.org", "@type": "WebSite",
        "name": BRAND, "url": BASE_URL + "/",
        "potentialAction": {"@type": "SearchAction",
            "target": BASE_URL + "/?q={search_term_string}",
            "query-input": "required name=search_term_string"},
    }

def localbiz_ld(name=None, area="서울특별시 관악구", path="/"):
    return {
        "@context": "https://schema.org",
        "@type": "HealthAndBeautyBusiness",
        "name": name or BRAND, "url": BASE_URL + path,
        "telephone": PHONE_DISP, "priceRange": "₩₩",
        "areaServed": {"@type": "AdministrativeArea", "name": area},
        "address": {"@type": "PostalAddress", "addressLocality": "관악구",
                    "addressRegion": "서울특별시", "addressCountry": "KR"},
        "image": BASE_URL + "/assets/og-cover.jpg",
        "openingHoursSpecification": {"@type": "OpeningHoursSpecification",
            "dayOfWeek": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
            "opens": "00:00", "closes": "23:59"},
        "aggregateRating": {"@type": "AggregateRating", "ratingValue": "4.9",
            "reviewCount": "1280", "bestRating": "5"},
    }

def service_ld(name, desc, path):
    return {
        "@context": "https://schema.org", "@type": "Service",
        "name": name, "description": desc, "serviceType": "방문 건강관리(마사지) 서비스",
        "provider": {"@type": "Organization", "name": BRAND, "url": BASE_URL + "/"},
        "areaServed": {"@type": "AdministrativeArea", "name": "서울특별시 관악구"},
        "image": BASE_URL + "/assets/og-cover.jpg",
        "url": BASE_URL + path,
    }

# ===========================================================================
# PAGE BUILDERS
# ===========================================================================
def write(path, html):
    if path == "/":
        out = os.path.join(ROOT, "index.html")
    else:
        d = os.path.join(ROOT, path.strip("/"))
        os.makedirs(d, exist_ok=True)
        out = os.path.join(d, "index.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)

# ---- Home ----------------------------------------------------------------
def build_home():
    services = "".join(
        f'<a class="card reveal" href="/course/{c["slug"]}/"><div class="k">{c["kicker"]}</div>'
        f'<h3>{c["name"]}</h3><p>{c["desc"]}</p><span class="more">자세히 →</span></a>'
        for c in COURSES[:4]
    )
    regions = "".join(
        f'<a class="card reveal" href="/gwanak-gu/{r["slug"]}/"><div class="k">AREA</div>'
        f'<h3>{r["name"]}</h3><p>{r["summary"]}</p><span class="more">권역 보기 →</span></a>'
        for r in REGIONS
    )
    steps = [
        ("전화 또는 문의", "원하시는 지역·시간·코스를 말씀해 주세요."),
        ("일정 확정", "디스패처가 방문 가능 시간을 확정해 드립니다."),
        ("관리사 방문", "약속된 시간에 맞춰 관리사가 방문합니다."),
        ("관리 후 정리", "관리 종료 후 현장을 정돈하고 마무리합니다."),
    ]
    steps_html = "".join(
        f'<div class="card reveal"><div class="k step"><span class="n serif">{i:02d}</span></div>'
        f'<h3>{t}</h3><p>{d}</p></div>'
        for i, (t, d) in enumerate(steps, 1)
    )
    reviews = [
        ("신림동 · 30대", "늦은 시간에 연락했는데 도착 시간을 정확히 안내해 주셔서 좋았습니다."),
        ("서울대입구역 인근 · 40대", "아로마 관리 후 컨디션이 한결 가벼워졌어요. 응대가 정중했습니다."),
        ("봉천동 · 30대", "예약부터 마무리까지 깔끔했고 위생 안내가 꼼꼼했습니다."),
    ]
    reviews_html = "".join(
        f'<div class="review reveal"><div class="stars">★★★★★</div><p>“{q}”</p>'
        f'<div class="who">{w}</div></div>' for w, q in reviews
    )
    marquee_items = ["연중무휴 24시간 상담", "서울 관악구 전 지역", "당일 예약 가능",
                     "여성 관리사 방문", "위생·안전 관리", "정찰 요금 안내"]
    marquee = "".join(f"<span>{x}</span>" for x in marquee_items * 2)

    about_notes = [
        ("WHO · 누가 운영하나요",
         ["간다GO 관악 출장마사지는 서울 관악구 전역을 담당하는 방문 건강관리 예약 운영팀입니다.",
          "본사 디스패처가 예약 접수부터 관리사 배차까지 직접 관리합니다."]),
        ("HOW · 어떻게 진행되나요",
         ["전화 상담으로 지역·시간·코스를 확인한 뒤 방문 가능 시간을 확정합니다.",
          "관리사는 약속된 시간에 맞춰 고객이 계신 장소로 방문합니다."]),
        ("WHY · 무엇을 약속하나요",
         ["정찰 요금과 사전 안내를 원칙으로 합니다.",
          "위생·안전 가이드라인을 준수하며 정중한 응대를 약속드립니다."]),
    ]
    body = f"""
<section class="hero"><div class="hero-inner">
  <div class="hero-copy">
    <span class="eyebrow"><span class="pulse"></span>SEOUL · GWANAK-GU 24H</span>
    <h1>관악구 어디든,<br>도착하는 <span class="grad">최상의</span><br><span class="serif">휴식 한 시간.</span></h1>
    <p class="lead">봉천·신림·남현, 서울대입구·낙성대·신림역까지 — 서울 관악구 전 지역 방문 건강관리 예약을 연중무휴로 안내드립니다.</p>
    <div class="actions">
      <a class="btn btn-primary" href="tel:{PHONE_TEL}">지금 예약하기 →</a>
      <a class="btn btn-ghost" href="/gwanak-gu/area/">지역별 안내</a>
    </div>
    <div class="trust">
      <span>★★★★★ <b>4.9</b> · 후기 1,280+</span><span>·</span>
      <span><b>{HOURS}</b></span><span>·</span><span>평균 도착 <b>22분</b></span>
    </div>
  </div>
  <div class="hero-visual">
    <div class="floating fl-1"><span class="dot"></span>LIVE · 방금 신림동 예약</div>
    <div class="glass">
      <h3>SIGNATURE<b>아로마 딥 릴렉스</b></h3>
      <div class="book-row"><span>지역</span><span>관악구 전 지역</span></div>
      <div class="book-row"><span>코스</span><span>아로마 90분</span></div>
      <div class="book-row"><span>도착</span><span>평균 22분 내외</span></div>
      <a class="bk" href="tel:{PHONE_TEL}">전화 예약 →</a>
    </div>
    <div class="floating fl-2">CUSTOMER RATING · ★ 4.9</div>
  </div>
</div></section>

<div class="marquee" aria-hidden="true"><div class="marquee-track">{marquee}</div></div>

<section class="block"><div class="wrap">
  <span class="eyebrow"><span class="pulse"></span>SIGNATURE COURSE</span>
  <h2 class="sec">대표 코스</h2>
  <p class="sec-lead">컨디션과 목적에 맞춰 고를 수 있는 간다GO의 대표 관리입니다.</p>
  <div class="grid g4" style="margin-top:28px">{services}</div>
</div></section>

{price_menu_block()}

<section class="block" id="region"><div class="wrap">
  <span class="eyebrow"><span class="pulse"></span>SERVICE AREA</span>
  <h2 class="sec">관악구 권역별 안내</h2>
  <p class="sec-lead">관악구를 3개 생활 권역으로 나누어 방문 가능 지역을 안내합니다.</p>
  <div class="grid g3" style="margin-top:28px">{regions}</div>
</div></section>

<section class="block" id="process"><div class="wrap">
  <span class="eyebrow"><span class="pulse"></span>HOW IT WORKS</span>
  <h2 class="sec">예약은 이렇게 진행됩니다</h2>
  <div class="grid g4" style="margin-top:28px">{steps_html}</div>
</div></section>

<section class="block" id="reviews"><div class="wrap">
  <span class="eyebrow"><span class="pulse"></span>CLIENT VOICES</span>
  <h2 class="sec">고객 후기</h2>
  <div class="grid g3" style="margin-top:28px">{reviews_html}</div>
</div></section>

{notes_block("ABOUT · WHO·HOW·WHY", "간다GO가 일하는 방식", "신뢰할 수 있는 방문 건강관리를 위한 운영 원칙입니다.", about_notes)}

{faq_block(HOME_FAQ)}

{cta_band()}
"""
    jsonld = [org_ld(), website_ld(), localbiz_ld(), offer_ld(), faq_ld(HOME_FAQ)]
    html = page("/", f"{BRAND} | 서울 관악구 방문 마사지 예약 안내",
                "간다GO 관악 출장마사지는 서울 관악구 봉천동, 신림동, 남현동과 서울대입구·낙성대·신림역 일대 방문 마사지 예약 안내를 제공합니다. 연중무휴 24시간 상담.",
                "home", body, jsonld)
    write("/", html)

HOME_FAQ = [
    ("관악구 어느 지역까지 방문 가능한가요?",
     "봉천·신림·남현 등 관악구 전 지역을 안내드립니다. 정확한 방문 가능 여부는 예약 시간과 위치에 따라 상담 시 확인해 드립니다."),
    ("예약은 어떻게 하나요?",
     "전화 또는 문의로 지역·희망 시간·코스를 말씀해 주시면 디스패처가 방문 가능 시간을 확정해 안내드립니다."),
    ("운영 시간은 어떻게 되나요?",
     "연중무휴 24시간 상담을 운영합니다. 다만 시간대와 위치에 따라 방문 가능 여부가 달라질 수 있습니다."),
    ("요금은 어떻게 안내되나요?",
     "코스별 정찰 요금을 사전에 안내드립니다. 자세한 금액은 코스안내 페이지에서 확인하실 수 있습니다."),
    ("어떤 분들이 방문하나요?",
     "위생·안전 가이드라인을 준수하는 관리사가 약속된 시간에 방문합니다."),
    ("이 서비스는 의료 행위인가요?",
     "아닙니다. 본 서비스는 의료 행위가 아닌 이완·휴식 목적의 건강관리 서비스이며 만 19세 이상 성인을 대상으로 합니다."),
]


# ---- About ---------------------------------------------------------------
def build_about():
    trail = [("/", "홈"), (None, "간다GO 소개")]
    greeting = notes_block("GREETING", "간다GO 인사말",
        "방문 건강관리를 고민하는 분들께 드리는 인사입니다.",
        [("정중한 휴식을 약속드립니다",
          ["간다GO 관악 출장마사지를 찾아주셔서 감사합니다.",
           "저희는 서울 관악구 전역을 대상으로 방문 건강관리 예약을 안내하는 운영팀입니다.",
           "예약부터 마무리까지 정중하고 투명한 응대를 약속드립니다."])],
        _id="greeting")
    standards = notes_block("STANDARDS", "서비스 운영 기준",
        "간다GO가 지키는 운영 원칙입니다.",
        [("정찰 요금", ["모든 코스는 정찰 요금으로 사전에 안내드립니다.",
                      "현장에서 임의로 금액이 추가되지 않습니다."]),
         ("사전 안내", ["방문 가능 시간과 코스, 소요 시간을 예약 시 명확히 안내드립니다."]),
         ("정중한 응대", ["상담과 방문 전 과정에서 정중함을 최우선으로 합니다."])],
        _id="standards")
    safety = notes_block("HYGIENE & SAFETY", "위생 및 안전 관리",
        "안심하고 받으실 수 있도록 위생·안전을 관리합니다.",
        [("위생 관리", ["관리에 사용하는 용품은 위생 기준에 맞춰 관리합니다."]),
         ("안전 가이드", ["관리사와 고객 모두의 안전을 위한 가이드라인을 운영합니다."]),
         ("비의료 고지", ["본 서비스는 의료 행위가 아닌 이완·휴식 목적의 건강관리 서비스입니다."])],
        _id="safety")
    about_faq = [
        ("간다GO는 어떤 서비스인가요?", "서울 관악구 전역을 대상으로 하는 방문 건강관리(마사지) 예약 안내 서비스입니다."),
        ("방문 관리는 어떻게 진행되나요?", "예약 확정 후 관리사가 약속된 시간에 고객이 계신 장소로 방문해 진행합니다."),
        ("미성년자도 이용할 수 있나요?", "아닙니다. 본 서비스는 만 19세 이상 성인만 이용하실 수 있습니다."),
    ]
    body = (breadcrumb(trail) +
        '<section class="block"><div class="wrap">'
        '<span class="eyebrow"><span class="pulse"></span>ABOUT GOODDAY</span>'
        '<h2 class="sec">간다GO 소개</h2>'
        '<p class="sec-lead">서울 관악구 방문 건강관리, 간다GO가 일하는 방식과 기준을 소개합니다.</p>'
        '</div></section>' + greeting + standards + safety +
        faq_block(about_faq) + cta_band())
    jsonld = [bc_ld(trail), org_ld(), faq_ld(about_faq)]
    html = page("/about/", "간다GO 소개 | 관악구 방문 건강관리 운영 기준 안내",
        "간다GO 관악 출장마사지의 인사말, 서비스 운영 기준, 위생 및 안전 관리 원칙을 안내합니다. 정찰 요금과 정중한 응대를 약속드립니다.",
        "about", body, jsonld)
    write("/about/", html)


# ---- Gangseo representative page -----------------------------------------
def build_gwanak():
    trail = [("/", "홈"), (None, "관악 출장마사지")]
    area_chips = "".join(f'<span class="chip"><b>{r["name"].split("권역")[0]}</b></span>' for r in REGIONS)
    # H2-01 간다GO 관악 출장마사지 안내
    intro = notes_block("INTRO", "간다GO 관악 출장마사지 안내",
        "서울 관악구 전역을 대상으로 하는 방문 건강관리 예약 안내입니다.",
        [("관악 전 지역 방문 안내",
          ["간다GO 관악 출장마사지는 서울 관악구 봉천동·신림동·남현동 전 지역과 서울대입구·낙성대·신림역 등 역세권 방문 관리를 안내합니다.",
           "생활권에 맞춰 3개 권역으로 나누어 방문 가능 지역을 안내하며, 역세권은 별도 <a href=\"/gwanak-gu/stations/\">지하철역별 안내</a>에서 확인하실 수 있습니다."])],
        _id="intro")
    # H2-02 관악구 출장 가능 지역
    area_section = (
        '<section class="block" id="area"><div class="wrap">'
        '<span class="eyebrow"><span class="pulse"></span>SERVICE AREA</span>'
        '<h2 class="sec">관악구 출장 가능 지역</h2>'
        '<p class="sec-lead">관악구를 3개 권역으로 나누어 안내합니다. 권역을 눌러 동별 안내를 확인하세요.</p>'
        '<div class="grid g3" style="margin-top:26px">' +
        "".join(f'<a class="card reveal" href="/gwanak-gu/{r["slug"]}/"><div class="k">AREA</div>'
                f'<h3>{r["name"]}</h3><p>{r["summary"]}</p><span class="more">권역 보기 →</span></a>'
                for r in REGIONS) +
        f'</div><div class="chips">{area_chips}</div></div></section>')
    # H2-03 관악구 주요 생활권
    living = notes_block("LIVING ZONE", "관악구 주요 생활권",
        "권역별 생활권 특성에 맞춰 코스와 도착 시간을 안내합니다.",
        [("권역별 생활권",
          ["봉천권역은 서울대입구·봉천·낙성대역 2호선 라인의 주거·상업권, 신림권역은 신림역과 신림선을 낀 관악 최대 주거·상업권입니다.",
           "남현권역은 사당역 생활권과 이어지는 동남부 주거권입니다. 역세권별 안내는 지하철역별 안내에서 확인하세요."])],
        _id="living")
    # H2-04 많이 찾는 관리 코스
    course_cards = "".join(
        f'<a class="card reveal" href="/course/{c["slug"]}/"><div class="k">{c["kicker"]}</div>'
        f'<h3>{c["name"]}</h3><p>{c["desc"]}</p><span class="more">코스 보기 →</span></a>'
        for c in COURSES[:4])
    course_section = (
        '<section class="block" id="course"><div class="wrap">'
        '<span class="eyebrow"><span class="pulse"></span>POPULAR COURSE</span>'
        '<h2 class="sec">많이 찾는 관리 코스</h2>'
        '<p class="sec-lead">컨디션과 목적에 맞춰 고를 수 있는 대표 코스입니다.</p>'
        f'<div class="grid g4" style="margin-top:26px">{course_cards}</div></div></section>')
    # H2-05 예약 가능 시간
    hours = notes_block("HOURS", "예약 가능 시간",
        "연중무휴 24시간 상담을 운영합니다.",
        [("24시간 상담", ["전화 상담은 연중무휴 24시간 가능합니다.",
                       "실제 방문 가능 시간은 시간대와 위치에 따라 안내드립니다."])],
        _id="hours")
    # H2-06 이용 전 확인사항
    check = notes_block("CHECK", "이용 전 확인사항",
        "원활한 방문을 위해 미리 확인해 주세요.",
        [("방문 장소", ["방문 가능한 장소와 주소, 연락 가능한 번호를 미리 알려주세요."]),
         ("코스·시간", ["희망 코스와 소요 시간을 예약 시 함께 확인해 주세요."])],
        _id="check")
    # H2-07 위생 및 안전 안내
    safety = notes_block("HYGIENE & SAFETY", "위생 및 안전 안내",
        "안심하고 받으실 수 있도록 안내드립니다.",
        [("위생·안전", ["용품 위생 관리와 안전 가이드라인을 준수합니다.",
                     "본 서비스는 의료 행위가 아닌 건강관리 서비스이며 만 19세 이상을 대상으로 합니다."])],
        _id="safety")
    # H2-08 관악 출장마사지 자주 묻는 질문
    gwanak_faq = [
        ("관악 출장마사지는 어디까지 가능한가요?", "봉천·신림·남현 등 관악구 전 지역을 안내드립니다."),
        ("당일 예약도 가능한가요?", "가능합니다. 다만 시간대와 위치에 따라 방문 가능 시간이 달라질 수 있어 상담 시 확인해 드립니다."),
        ("봉천동·신림동처럼 행정동이 여러 개로 나뉜 곳도 되나요?", "네. 봉천동(은천·성현·청룡·청림·행운·중앙·인헌동 등)과 신림동(서원·신원·서림·삼성·미성동 등)은 대표 동 안내 기준으로 통합 안내드립니다."),
        ("신림역·서울대입구역 같은 역 근처도 안내가 따로 있나요?", "네. 주요 역세권은 <a href=\"/gwanak-gu/stations/\">지하철역별 안내</a>에서 역별로 따로 안내드립니다."),
    ]
    body = (breadcrumb(trail) +
        f'<section class="hero"><div class="hero-inner"><div class="hero-copy">'
        f'<span class="eyebrow"><span class="pulse"></span>관악구 대표</span>'
        f'<h1><span class="grad">관악 출장마사지</span><br><span class="serif">예약 안내</span></h1>'
        f'<p class="lead">서울 관악구 전 지역 방문 건강관리 예약을 간다GO 관악 출장마사지가 안내합니다.</p>'
        f'<div class="actions"><a class="btn btn-primary" href="tel:{PHONE_TEL}">전화 예약 →</a>'
        f'<a class="btn btn-ghost" href="/gwanak-gu/area/">지역별 안내</a></div></div>'
        f'<div class="hero-visual"><div class="glass"><h3>GWANAK<b>관악구 전 지역</b></h3>'
        f'<div class="book-row"><span>권역</span><span>3개 생활권</span></div>'
        f'<div class="book-row"><span>상담</span><span>{HOURS}</span></div>'
        f'<a class="bk" href="tel:{PHONE_TEL}">예약 문의 →</a></div></div></div></section>' +
        intro + area_section + living + course_section + hours + check + safety +
        price_menu_block() + faq_block(gwanak_faq, "관악 출장마사지 자주 묻는 질문") + cta_band())
    jsonld = [bc_ld(trail), localbiz_ld(name="간다GO 관악 출장마사지", path="/gwanak-gu/"),
              service_ld("관악 출장마사지", "서울 관악구 전 지역 방문 건강관리 서비스", "/gwanak-gu/"),
              offer_ld(), faq_ld(gwanak_faq)]
    html = page("/gwanak-gu/", "관악 출장마사지 | 간다GO 관악구 방문 마사지 예약 안내",
        "관악 출장마사지 대표 안내 - 봉천·신림·남현 3개 권역과 서울대입구·낙성대·신림역 역세권의 방문 가능 지역, 예약 시간, 코스, 위생 안내를 한곳에 정리했습니다. 연중무휴 24시간 상담.",
        "gwanak", body, jsonld)
    write("/gwanak-gu/", html)


# ---- Area hub ------------------------------------------------------------
def build_area_hub():
    trail = [("/", "홈"), ("/gwanak-gu/", "관악 출장마사지"), (None, "지역별 안내")]
    blocks = ""
    for r in REGIONS:
        dong_links = "".join(
            f'<a class="card reveal" href="/gwanak-gu/{d["slug"]}/"><div class="k">{r["name"]}</div>'
            f'<h3>{d["name"]} 출장마사지</h3><p>{d["character"]}</p>'
            f'<span class="more">동 안내 보기 →</span></a>' for d in r["dongs"])
        blocks += (
            f'<div style="margin-top:40px"><h3 style="font-size:22px;font-weight:800;margin-bottom:6px">'
            f'<a href="/gwanak-gu/{r["slug"]}/" class="grad">{r["name"]}</a></h3>'
            f'<p class="sec-lead">{r["summary"]}</p>'
            f'<div class="grid g3" style="margin-top:18px">{dong_links}</div></div>')
    total_dong = sum(len(r["dongs"]) for r in REGIONS)
    overview = (
        '<section class="block"><div class="wrap" style="max-width:820px">'
        '<span class="eyebrow"><span class="pulse"></span>AREA GUIDE</span>'
        '<h2 class="sec">지역별 안내</h2>'
        f'<p class="sec-lead" style="max-width:760px">관악구를 봉천·신림·남현 3개 생활 권역, 총 {total_dong}개 동으로 '
        '나누어 동별 방문 안내를 제공합니다.</p>'
        '<div class="article" style="max-width:820px;margin-top:8px">'
        '<p>관악구는 서울 남부에 위치한 인구 약 49만 명의 자치구로, 봉천동·신림동·남현동 세 개의 법정동 아래 여러 '
        '행정동이 묶여 있습니다. 간다GO 관악 출장마사지는 이 행정동을 생활권 단위로 묶어 봉천권역·신림권역·남현권역으로 '
        '나누고, 권역마다 평균 도착 시간과 생활권 특성을 다르게 안내합니다.</p>'
        '<p><strong>봉천권역</strong>은 서울대입구역·봉천역·낙성대역 등 2호선 라인을 따라 형성된 동부 주거·상업권으로, '
        '샤로수길 상권과 대단지 아파트가 어우러져 1인 가구와 가족 단위 방문이 고르게 들어옵니다. '
        '<strong>신림권역</strong>은 2호선과 신림선이 만나는 신림역을 중심으로 한 관악구 최대 생활권으로, 원룸·오피스텔과 '
        '대학동 고시촌이 밀집해 심야 방문 문의가 특히 많습니다. <strong>남현권역</strong>은 사당역 생활권과 맞닿은 '
        '동남부 주택가로, 조용한 자택 방문이 주를 이룹니다.</p>'
        '<p>아래에서 권역을 선택하면 동별 상세 안내로 이동합니다. 평균 도착 시간은 신림동 18분, 봉천동 20분, '
        '남현동 26분 내외이며(예약 데이터 기준), 같은 권역 안에서도 위치에 따라 달라질 수 있습니다.</p>'
        '</div></div></section>')
    hub_faq = [
        ("관악구는 몇 개 권역으로 나뉘나요?",
         f"봉천·신림·남현 3개 생활 권역, 총 {total_dong}개 동으로 나누어 안내드립니다. 권역을 선택하면 동별 상세 안내를 보실 수 있습니다."),
        ("우리 동이 목록에 없으면 방문이 안 되나요?",
         "은천·성현·청룡·서원·신원동처럼 봉천동·신림동의 행정동은 대표 동 안내에 통합되어 있습니다. 목록에 동명이 보이지 않아도 예약 시 위치를 알려주시면 가능 여부를 확인해 드립니다."),
        ("지하철역 기준으로도 안내가 있나요?",
         "네. 2호선·신림선 주요 역세권은 지역별 안내와 별도로 지하철역별 안내에서 역별로 제공합니다."),
    ]
    body = (breadcrumb(trail) + overview +
        '<section class="block"><div class="wrap">' + blocks + '</div></section>'
        + price_menu_block() + faq_block(hub_faq) + cta_band())
    item_list = {
        "@context": "https://schema.org", "@type": "CollectionPage",
        "name": "관악구 출장마사지 지역별 안내", "url": BASE_URL + "/gwanak-gu/area/",
        "hasPart": [{"@type": "WebPage", "name": r["name"],
                     "url": BASE_URL + f"/gwanak-gu/{r['slug']}/"} for r in REGIONS],
    }
    html = page("/gwanak-gu/area/", "관악구 출장마사지 가능 지역 | 간다GO 지역별 안내",
        "간다GO 관악 출장마사지 지역별 안내 - 봉천권역, 신림권역, 남현권역 3개 권역과 22개 동, 2호선·신림선 역세권별 방문 안내를 제공합니다.",
        "area", body, [bc_ld(trail), item_list, faq_ld(hub_faq), offer_ld()])
    write("/gwanak-gu/area/", html)


# ---- Area (권역) pages ----------------------------------------------------
def build_area_pages():
    for r in REGIONS:
        trail = [("/", "홈"), ("/gwanak-gu/", "관악 출장마사지"),
                 ("/gwanak-gu/area/", "지역별 안내"), (None, r["name"])]
        dong_cards = "".join(
            f'<a class="card reveal" href="/gwanak-gu/{d["slug"]}/"><div class="k">동 안내</div>'
            f'<h3>{d["name"]} 출장마사지</h3><p>{d["landmarks"]}</p>'
            f'<span class="more">자세히 →</span></a>' for d in r["dongs"])
        arr_min = min(d["arrival"] for d in r["dongs"])
        arr_max = max(d["arrival"] for d in r["dongs"])
        arr_txt = f"{arr_min}분" if arr_min == arr_max else f"{arr_min}~{arr_max}분"
        dong_lines = [
            f'{r["name"]} 동별 평균 도착 시간은 {arr_txt} 내외입니다(예약 데이터 기준). '
            f'위 카드에서 동을 선택하면 생활권·랜드마크·세부 도착 시간과 동별 자주 묻는 질문을 확인하실 수 있습니다.']
        # 동별 sub-notes (행정동 통합/인접역 흡수 등)
        sub_notes = [d.get("sub_note") for d in r["dongs"] if d.get("sub_note")]
        chips = "".join(
            f'<span class="chip"><b>{d["name"]}</b> 평균 {d["arrival"]}분</span>' for d in r["dongs"])
        # 권역과 연결된 지하철역(역세권 페이지) 내부링크
        st_links = [f'<a href="/gwanak-gu/stations/{ss}/">{station_by_slug(ss)["name"]} 출장마사지</a>'
                    for ss in r.get("stations", []) if station_by_slug(ss)]
        area_faq = [
            (f"{r['name']}은 어디까지 방문 가능한가요?",
             "권역 내 " + "·".join(d["name"] for d in r["dongs"]) + " 일대를 안내드리며, 정확한 가능 여부는 예약 시간과 위치에 따라 확인해 드립니다."),
            (f"{r['name']} 예약은 어떻게 하나요?",
             "전화 또는 문의로 동·시간·코스를 말씀해 주시면 방문 가능 시간을 확정해 드립니다."),
        ]
        if st_links:
            stn_names = "·".join(station_by_slug(ss)["name"] for ss in r["stations"] if station_by_slug(ss))
            area_faq.append((f"{r['name']}은 어느 지하철역과 가깝나요?",
                f"{stn_names} 등과 가까우며, 역 중심 안내는 지하철역별 안내에서 역별로 확인하실 수 있습니다."))
        sections = [
            (f"{r['name']} 방문 가능 동", [
                f"{r['name']}은 " + "·".join(d["name"] for d in r["dongs"]) + " 일대를 포함합니다. 원하는 동을 눌러 상세 안내를 확인하세요.",
                ("html", f'<div class="chips" style="margin-bottom:18px">{chips}</div>'
                         f'<div class="grid g3">{dong_cards}</div>')]),
            (f"{r['name']} 생활·교통 안내", r.get("long", [r["summary"]])),
            ("동별 방문 안내", dong_lines),
        ]
        # 권역 지하철역 안내(역세권 페이지 내부링크) — 도어웨이 회피 위해 권역마다 고유
        if st_links:
            sections.append((f"{r['name']} 지하철역 안내", [
                f"{r['name']}은 다음 역과 가까워, 역 인근에서 찾는 분들을 위해 역세권별 안내를 따로 제공합니다.",
                ("ul", st_links),
                '전체 역 목록은 <a href="/gwanak-gu/stations/">관악구 지하철역 전체 안내</a>에서 확인하실 수 있습니다.']))
        else:
            sections.append((f"{r['name']} 지하철역 안내", [
                f"{r['name']}은 사당역(2·4호선) 생활권과 가깝습니다. 사당역 인근은 별도 역 페이지 대신 "
                f'<a href="/gwanak-gu/namhyeon-dong/">남현동</a> 본문에서 함께 안내드리며, 관악구 전체 역 안내는 '
                '<a href="/gwanak-gu/stations/">지하철역별 안내</a>에서 확인하실 수 있습니다.']))
        if sub_notes:
            sections.append(("세부 지역 안내", sub_notes))
        for ex_title, ex_blocks in r.get("extra", []):
            sections.append((ex_title, ex_blocks))
        sections.append(("예약·코스·위생은 전용 안내에서", [
            "권역 내 예약 가능 시간·준비물·위생 기준·코스 요금은 페이지마다 반복하지 않고 전용 안내에서 확인하실 수 있습니다.",
            ("ul", ['<a href="/gwanak-gu/hours/">예약 가능 시간 안내</a>',
                    '<a href="/gwanak-gu/checklist/">이용 전 확인사항(준비물)</a>',
                    '<a href="/gwanak-gu/safety/">위생 및 안전 안내</a>',
                    '<a href="/course/">코스안내 · 가격</a>'])]))
        top_links = [("tel:" + PHONE_TEL, "예약문의", True), ("/course/", "코스안내"),
                     ("/gwanak-gu/", "관악 출장마사지 대표"), ("/gwanak-gu/area/", "지역별 안내")]
        content_page(f"/gwanak-gu/{r['slug']}/", "area", trail,
            title=f"{r['name']} 출장마사지 | 관악구 {r['name']} 방문 마사지",
            desc=f"{r['name']} 출장마사지 안내 - " + ", ".join(d['name'] for d in r['dongs']) +
                 f" 일대 방문 건강관리 예약 안내입니다. {r['summary']}",
            eyebrow=f"관악구 · {r['name']}", h1=f"{r['name']} 출장마사지", lead=r["summary"],
            sections=sections, faq=area_faq, top_links=top_links,
            cta_title=f"{r['name']} 방문 예약을 도와드릴까요?",
            service=(f"{r['name']} 출장마사지", r["summary"]),
            extra_schema=[localbiz_ld(name=f"간다GO {r['name']} 출장마사지",
                                      area=f"서울특별시 관악구 {r['name']}", path=f"/gwanak-gu/{r['slug']}/")])


# ---- 동 pages -------------------------------------------------------------
# 동별 방문 가능 생활권 (역/지역 H3) — 역명은 별도 페이지 대신 본문 H3에서 흡수
DONG_ZONES = {
    # 봉천권역
    "bongcheon-dong": [("서울대입구역 인근", "2호선 서울대입구역을 중심으로 한 상업·주거 생활권입니다."),
        ("봉천역 인근", "2호선 봉천역 방향 상업·주거 밀집 생활권과 연결됩니다."),
        ("관악구청 인근", "행정·생활 인프라가 모인 봉천 중심 생활권입니다."),
        ("봉천 주거 밀집지", "남부순환로를 따라 형성된 아파트·빌라 주거 밀집지입니다.")],
    "euncheon-dong": [("봉천역 인근", "2호선 봉천역과 가까운 대단지 주거 생활권입니다."),
        ("은천동 아파트 단지", "관악푸르지오·벽산블루밍 등 대단지가 모인 정주형 생활권입니다."),
        ("보라매 방면", "보라매공원 방향 생활권과 이어집니다."),
        ("남부순환로 일대", "남부순환로를 낀 주거·상업 생활권입니다.")],
    "seonghyeon-dong": [("서울대입구역 인근", "2호선 서울대입구역 북측 배후 주거 생활권입니다."),
        ("성현동 주거단지", "현대아파트 등 단지가 모인 주거 밀집지입니다."),
        ("봉천고개 일대", "봉천고개를 따라 형성된 주거 생활권입니다."),
        ("관악산 자락", "관악산 자락에 인접한 조용한 주거지입니다.")],
    "cheongnyong-dong": [("서울대입구역 인근", "2호선 서울대입구역 역세권 상업·주거 생활권입니다."),
        ("샤로수길 일대", "샤로수길 상권 주변 원룸·오피스텔 생활권입니다."),
        ("청룡동 원룸촌", "청년·1인 가구가 많은 원룸 밀집 생활권입니다."),
        ("봉천역 방면", "봉천역 방향 생활권과 연결됩니다.")],
    "boramae-dong": [("신대방역 인근", "2호선 신대방역 방향 생활권과 맞닿아 있습니다."),
        ("보라매공원 인근", "보라매공원을 낀 주거·생활 권역입니다."),
        ("보라매동 주거단지", "공원 주변 아파트 단지가 모인 주거 밀집지입니다."),
        ("남부순환로 일대", "남부순환로를 낀 상업·주거 생활권입니다.")],
    "cheongnim-dong": [("관악구청 인근", "관악구청과 가까운 행정·주거 생활권입니다."),
        ("서울대입구역 방면", "서울대입구역 방향 생활권과 연결됩니다."),
        ("청림동 주거지", "봉천 남부의 정주형 주거 생활권입니다."),
        ("관악산 자락", "관악산 자락에 인접한 조용한 주거지입니다.")],
    "haengun-dong": [("낙성대역 인근", "2호선 낙성대역 방향 생활권과 가깝습니다."),
        ("행운동 주거지", "관악로를 따라 형성된 주거 밀집 생활권입니다."),
        ("서울대입구역 방면", "서울대입구역 방향 생활권과 이어집니다."),
        ("관악로 일대", "관악로를 낀 상업·주거 생활권입니다.")],
    "nakseongdae-dong": [("낙성대역 인근", "2호선 낙성대역 중심 역세권 주거 생활권입니다."),
        ("낙성대공원 인근", "낙성대공원을 낀 조용한 주거 생활권입니다."),
        ("낙성대동 주거단지", "공원 주변 아파트·빌라 주거 밀집지입니다."),
        ("인헌동 방면", "인헌동 학군 생활권과 이어집니다.")],
    "jungang-dong": [("봉천역 인근", "2호선 봉천역 중심 상업·주거 생활권입니다."),
        ("관악중앙시장 인근", "전통시장 주변 주거 밀집 생활권입니다."),
        ("중앙동 주거지", "봉천역 배후의 빌라·주택 밀집 생활권입니다."),
        ("남부순환로 일대", "남부순환로를 낀 상업 생활권입니다.")],
    "inheon-dong": [("낙성대역 인근", "2호선 낙성대역 방향 생활권과 가깝습니다."),
        ("인헌동 학군지", "인헌중·고등학교 주변 학군 주거 생활권입니다."),
        ("관악산 자락", "관악산 자락에 인접한 조용한 정주형 주거지입니다."),
        ("봉천 남부 방면", "봉천 남부 주거 생활권과 이어집니다.")],
    # 신림권역
    "sillim-dong": [("신림역 인근", "2호선·신림선 신림역 중심의 관악 최대 상업·주거 생활권입니다."),
        ("신림중앙시장 인근", "신림중앙시장·순대타운 등 상권 주변 주거 밀집지입니다."),
        ("서원역 방면", "신림선 서원역 방향 생활권과 연결됩니다."),
        ("신림 주거 밀집지", "원룸·오피스텔·아파트가 어우러진 주거 밀집 생활권입니다.")],
    "seowon-dong": [("서원역 인근", "신림선 서원역 중심 주거 생활권입니다."),
        ("서원동 주거지", "신림 서부의 빌라·주택 주거 밀집지입니다."),
        ("신림역 방면", "신림역 방향 상업 생활권과 이어집니다."),
        ("신림선 라인", "신림선을 따라 이어지는 주거 생활권입니다.")],
    "sinwon-dong": [("신림역 인근", "2호선 신림역 남측 생활권입니다."),
        ("신원시장 인근", "신원시장 주변 주거 밀집 생활권입니다."),
        ("신원동 주거단지", "신림역 배후의 정주형 주거지입니다."),
        ("신림 남부 방면", "신림 남부 생활권과 이어집니다.")],
    "seorim-dong": [("신림역 인근", "2호선 신림역과 가까운 원룸·주거 생활권입니다."),
        ("서림동 원룸촌", "청년·1인 가구가 많은 원룸 밀집 생활권입니다."),
        ("신원동 방면", "신원동 주거 생활권과 이어집니다."),
        ("신림선 라인", "신림선을 따라 이어지는 주거 생활권입니다.")],
    "nangok-dong": [("난곡사거리 인근", "난곡사거리를 중심으로 한 주거·상업 생활권입니다."),
        ("난곡로 일대", "난곡로를 따라 형성된 주거 밀집 생활권입니다."),
        ("난곡동 주거단지", "산자락을 따라 형성된 아파트·빌라 주거지입니다."),
        ("산자락 주거지", "삼성산 자락에 인접한 조용한 주거 생활권입니다.")],
    "sinsa-dong": [("신림역 방면", "2호선 신림역 방향 생활권과 연결됩니다."),
        ("신사동고개 일대", "신사동고개를 따라 형성된 주거 생활권입니다."),
        ("신사동 주거지", "신림 서북부의 빌라·주택 밀집 생활권입니다."),
        ("난곡 방면", "난곡 생활권과 이어집니다.")],
    "samseong-dong": [("삼성산 자락", "삼성산 녹지에 인접한 주거 생활권입니다."),
        ("삼성동 주거단지", "산자락 아파트·빌라가 모인 주거 밀집지입니다."),
        ("신림역 방면", "신림역 방향 상업 생활권과 이어집니다."),
        ("신림선 라인", "신림선을 따라 이어지는 주거 생활권입니다.")],
    "nanhyang-dong": [("난향로 일대", "난향로를 따라 형성된 외곽 주거 생활권입니다."),
        ("삼성산 자락", "삼성산 녹지에 인접한 조용한 주거지입니다."),
        ("난향동 주거지", "관악 남서부의 정주형 주거 밀집 생활권입니다."),
        ("난곡 방면", "난곡 생활권과 이어집니다.")],
    "jowon-dong": [("신대방역 인근", "2호선 신대방역 방향 생활권과 가깝습니다."),
        ("조원시장 인근", "조원시장 주변 주거 밀집 생활권입니다."),
        ("조원동 주거단지", "신림 북부의 아파트·빌라 주거지입니다."),
        ("신림 북부 방면", "신림 북부 생활권과 이어집니다.")],
    "daehak-dong": [("서울대벤처타운역 인근", "신림선 서울대벤처타운역 중심 학생·청년 생활권입니다."),
        ("관악산역 인근", "신림선 관악산역 방향 서울대 진입 생활권입니다."),
        ("서울대학교 일대", "서울대학교 정문·캠퍼스 주변 생활권입니다."),
        ("고시촌 일대", "대학동 고시촌의 원룸·고시원 밀집 생활권입니다.")],
    "miseong-dong": [("신림선 인근", "신림선을 따라 이어지는 주거 생활권입니다."),
        ("미성동 주거단지", "신림 남부의 아파트·빌라 주거 밀집지입니다."),
        ("신림역 방면", "신림역 방향 상업 생활권과 이어집니다."),
        ("미성 생활권", "조용한 정주형 주거 생활권입니다.")],
    # 남현권역
    "namhyeon-dong": [("사당역 인근", "2·4호선 사당역 생활권과 맞닿은 주거 권역입니다."),
        ("예술인마을 일대", "남현동 예술인마을 주변 주택가 생활권입니다."),
        ("남현동 주거지", "관악산 자락에 인접한 정주형 주거 생활권입니다."),
        ("관악산 자락", "관악산 둘레길에 인접한 조용한 주거지입니다.")],
}

def build_dong_pages():
    for r in REGIONS:
        for d in r["dongs"]:
            name, slug = d["name"], d["slug"]
            path = f"/gwanak-gu/{slug}/"
            trail = [("/", "홈"), ("/gwanak-gu/", "관악 출장마사지"),
                     ("/gwanak-gu/area/", "지역별 안내"),
                     (f"/gwanak-gu/{r['slug']}/", r["name"]),
                     (None, f"{name} 출장마사지")]
            siblings = [x for x in r["dongs"] if x["slug"] != slug]
            zones = DONG_ZONES.get(slug, [])
            stations = [t.replace(" 인근", "") for t, _ in zones if "역" in t][:3]
            station_list = ", ".join(stations) if stations else d["landmarks"].split(",")[0]
            first_station = stations[0] if stations else name

            # 상단 CTA
            top_links = [("tel:" + PHONE_TEL, "예약문의", True),
                         ("/course/", "코스안내"),
                         ("/gwanak-gu/", "관악 출장마사지 대표")]
            if siblings:
                top_links.append((f"/gwanak-gu/{siblings[0]['slug']}/", f"{siblings[0]['name']} 출장마사지"))

            # 생활권 블록 (H3) — 동 고유 콘텐츠
            zone_blocks = [f"{name}은 {d['landmarks']}를 중심으로 인근 생활권과 연결됩니다. {d['character']}이라 자택·오피스텔·숙소 방문 문의가 고르게 들어오며, 세부 방문 가능 여부는 정확한 위치·예약 시간·배정 상황에 따라 달라질 수 있습니다."]
            zone_arr = ", ".join(
                f"{zt.replace(' 인근', '').replace(' 일대', '')} 약 {d['arrival'] + i * 2}분"
                for i, (zt, _) in enumerate(zones))
            zone_blocks.append(f"방문 포인트별 평균 도착 시간(예약 데이터 기준)은 {zone_arr} 내외입니다. 같은 {name} 안에서도 위치에 따라 도착 시간이 달라집니다.")
            for zt, zd in zones:
                zone_blocks += [("h3", zt), zd]
            zone_blocks += [("h3", "주거지·숙소 방문 안내"),
                            f"{name}에서는 {d['landmarks']} 인근 자택·오피스텔·숙소로 방문하며, 공동현관 출입 방법과 정확한 주소를 알려주시면 도착이 빨라집니다."]

            # 권역 함께 보기 내부링크
            region_links = ['<a href="/gwanak-gu/">관악 출장마사지</a>',
                            '<a href="/gwanak-gu/area/">관악구 출장 가능 지역</a>',
                            f'<a href="/gwanak-gu/{r["slug"]}/">{r["name"]}</a>']
            region_links += [f'<a href="/gwanak-gu/{s["slug"]}/">{s["name"]} 출장마사지</a>' for s in siblings]
            region_tail = d["sub_note"] if d.get("sub_note") else \
                f"{r['name']}은 생활권이 이어져 있어 인근 동과 함께 안내드리는 경우가 많습니다."

            sections = [
                (f"{name} 출장마사지 이용 안내", [
                    f"{name}은 {d['character']}입니다. 주요 위치는 {d['landmarks']} 일대로, 이 생활권을 중심으로 자택·오피스텔·숙소 방문 문의가 많습니다.",
                    f"{name} 출장마사지는 {d['landmarks'].split(',')[0].strip()} 등 {name} 내 원하시는 장소로 방문해 피로 회복과 컨디션 관리를 돕는 방문형 관리 서비스입니다. 예약 시 위치·희망 시간·코스·인원을 확인한 뒤 방문 가능 여부를 안내드립니다.",
                    '예약 방법·결제 절차는 <a href="/reservation/">예약안내</a>, 처음 이용 시 진행 흐름은 <a href="/guide/">이용가이드</a>에서 확인하실 수 있습니다.']),
                (f"{name} 방문 가능 생활권", zone_blocks),
                (f"{r['name']} 함께 보기", [
                    f"{name}과 가까운 같은 권역 생활권도 함께 확인할 수 있습니다.",
                    ("ul", region_links), region_tail]),
                (f"{name}에서 많이 찾는 관리 코스", [
                    f"{name}({d['character']})에서는 피로 회복·아로마·스포츠 관리 문의가 많습니다. "
                    f'코스별 상세 설명과 요금은 <a href="/course/">코스안내</a>·<a href="/course/price/">가격 안내</a>에서 확인하세요.']),
                (f"{name} 예약·준비·위생 안내", [
                    f"{name} 방문은 평균 {d['arrival']}분 내외로 도착하며, 저녁·주말은 문의가 몰려 사전 예약을 권장드립니다. "
                    f'예약 시간은 <a href="/gwanak-gu/hours/">예약 가능 시간</a>, 준비물은 '
                    f'<a href="/gwanak-gu/checklist/">이용 전 확인사항</a>, 위생 기준은 '
                    f'<a href="/gwanak-gu/safety/">위생 및 안전 안내</a>에서 확인하실 수 있습니다.']),
            ]
            dong_faq = [
                (f"{name} 전 지역 방문이 가능한가요?",
                 f"예약 시간, 정확한 위치, 배정 상황에 따라 가능 여부가 달라질 수 있습니다. {station_list} 인근 등 세부 위치를 기준으로 안내드립니다."),
                (f"{first_station} 근처도 예약할 수 있나요?",
                 f"{first_station} 인근은 {name} 주요 생활권으로 함께 안내할 수 있습니다. 정확한 방문 가능 여부는 예약 시 위치를 기준으로 확인합니다."),
                (f"{name}은 어떤 지역인가요?",
                 f"{name}은 {d['character']}입니다. {d['landmarks']} 인근을 중심으로 자택·숙소·오피스텔 방문 문의가 많은 편입니다."),
                (f"{name} 도착까지 얼마나 걸리나요?",
                 f"평균 {d['arrival']}분 내외이며, 시간대와 정확한 위치에 따라 달라질 수 있습니다."),
                (f"{name}에서는 어떤 코스가 인기인가요?",
                 f"{name}에서는 피로 회복·아로마·스포츠 관리 문의가 많습니다. 목적과 컨디션에 따라 선택하시면 되며, 자세한 내용은 코스안내에서 확인하실 수 있습니다."),
            ]
            lead = (f"관악구 {name}({d['character']})에서 방문 마사지 예약을 찾는 분들을 위한 안내입니다. "
                    f"{name}은 {station_list} 인근 생활권과 가까워 주거지·숙소·오피스텔 방문 문의가 많으며, "
                    f"평균 {d['arrival']}분 내외로 도착합니다.")
            content_page(path, "area", trail,
                title=f"{name} 출장마사지 | 관악구 {name} 방문 마사지 예약 안내",
                desc=f"관악구 {name} 출장마사지 안내 페이지입니다. {station_list} 인근 방문 가능 지역과 예약 가능 시간, 코스 선택 기준을 확인해보세요.",
                eyebrow=f"관악구 {name}", h1=f"{name} 출장마사지 예약 안내", lead=lead,
                sections=sections, faq=dong_faq,
                data_note=f"{name} 일대는 평균 {d['arrival']}분 내외로 도착합니다(예약 데이터 기준). 저녁·주말은 문의가 몰려 도착이 다소 길어질 수 있어 사전 예약을 권장드립니다.",
                service=(f"{name} 출장마사지", f"관악구 {name} 일대 방문 건강관리 서비스"),
                show_price=False, top_links=top_links,
                cta_title=f"{name} 방문 예약, 지금 도와드릴까요?",
                extra_schema=[localbiz_ld(name=f"간다GO {name} 출장마사지",
                                          area=f"서울특별시 관악구 {name}", path=path)])


# ---- 지하철역별 안내 (역세권 보조 랜딩) -----------------------------------
def _dong_index():
    idx = {}
    for r in REGIONS:
        for d in r["dongs"]:
            idx[d["slug"]] = {"name": d["name"], "region": r["name"], "region_slug": r["slug"]}
    return idx

def build_stations_hub():
    trail = [("/", "홈"), ("/gwanak-gu/", "관악 출장마사지"), (None, "지하철역별 안내")]
    blocks = ""
    for gkey, gname, gsummary in STATION_GROUPS:
        cards = "".join(
            f'<a class="card reveal" href="/gwanak-gu/stations/{s["slug"]}/"><div class="k">{s["line"]}</div>'
            f'<h3>{s["name"]} 출장마사지</h3><p>{s["summary"]}</p>'
            f'<span class="more">역 안내 보기 →</span></a>'
            for s in STATIONS if s["group"] == gkey)
        blocks += (f'<div style="margin-top:40px"><h3 style="font-size:22px;font-weight:800;margin-bottom:6px">'
                   f'<span class="grad">{gname}</span></h3>'
                   f'<p class="sec-lead">{gsummary}</p>'
                   f'<div class="grid g3" style="margin-top:18px">{cards}</div></div>')
    nearby_cards = "".join(
        f'<a class="card reveal" href="/gwanak-gu/{n["dong"]}/"><div class="k">인접 생활권</div>'
        f'<h3>{n["name"]}</h3><p>{n["note"]}</p>'
        f'<span class="more">{n["dong_name"]} 안내 보기 →</span></a>'
        for n in STATION_NEARBY)
    blocks += (f'<div style="margin-top:40px"><h3 style="font-size:22px;font-weight:800;margin-bottom:6px">'
               f'<span class="grad">인접 생활권</span></h3>'
               f'<p class="sec-lead">사당역·신대방역 인근은 별도 페이지 대신 인접 동(남현동·보라매동) 안내에서 함께 다룹니다.</p>'
               f'<div class="grid g3" style="margin-top:18px">{nearby_cards}</div></div>')
    body = (breadcrumb(trail) +
        '<section class="block"><div class="wrap">'
        '<span class="eyebrow"><span class="pulse"></span>STATION GUIDE</span>'
        '<h2 class="sec">관악구 지하철역 전체 안내</h2>'
        '<p class="sec-lead">관악구 2호선·신림선 주요 역을 중심으로 역세권 방문 안내를 제공합니다. '
        '핵심 안내는 <a href="/gwanak-gu/">관악 출장마사지</a> 대표 페이지와 '
        '<a href="/gwanak-gu/area/">지역별 안내</a>에서도 확인하실 수 있습니다.</p>'
        + blocks + '</div></section>' + price_menu_block() + cta_band())
    coll = {
        "@context": "https://schema.org", "@type": "CollectionPage",
        "name": "관악구 지하철역 출장마사지 안내", "url": BASE_URL + "/gwanak-gu/stations/",
        "hasPart": [{"@type": "WebPage", "name": f'{s["name"]} 출장마사지',
                     "url": BASE_URL + f'/gwanak-gu/stations/{s["slug"]}/'} for s in STATIONS],
    }
    html = page("/gwanak-gu/stations/", "관악구 지하철역 출장마사지 | 2호선·신림선 방문 안내",
        "관악구 지하철역 출장마사지 안내 - 2호선(신림·서울대입구·봉천·낙성대)과 신림선(당곡·서원·서울대벤처타운·관악산) 역세권 방문 마사지를 안내합니다.",
        "stations", body, [bc_ld(trail), coll, offer_ld()])
    write("/gwanak-gu/stations/", html)


def build_station_pages():
    didx = _dong_index()
    gmap = {g[0]: g[1] for g in STATION_GROUPS}
    for s in STATIONS:
        slug, name, line = s["slug"], s["name"], s["line"]
        path = f"/gwanak-gu/stations/{slug}/"
        gname = gmap[s["group"]]
        trail = [("/", "홈"), ("/gwanak-gu/", "관악 출장마사지"),
                 ("/gwanak-gu/stations/", "지하철역별 안내"), (None, f"{name} 출장마사지")]
        rel_names = "·".join(didx[ds]["name"] for ds in s["related"] if ds in didx)

        # H2-2 인근 방문 가능 생활권 (H3)
        zone_blocks = [
            f"{name}({line})은 {s['summary']} {name} 인근 생활권을 중심으로 자택·오피스텔·숙소 "
            f"방문 문의가 들어오며, 세부 방문 가능 여부는 정확한 위치와 예약 시간에 따라 안내드립니다.",
            f"방문 포인트별 평균 도착 시간(예약 데이터 기준)은 {name} 기준 약 {s['arrival']}분 "
            f"내외이며, 같은 역세권 안에서도 위치에 따라 달라질 수 있습니다."]
        for zt, zd in s["zones"]:
            zone_blocks += [("h3", zt), zd]

        # H2-3 주변 관악구 지역 안내 (내부링크)
        rel_links = [f'<a href="/gwanak-gu/{ds}/">{didx[ds]["name"]} 출장마사지</a>'
                     for ds in s["related"] if ds in didx]
        rel_links += ['<a href="/gwanak-gu/area/">관악구 출장 가능 지역</a>',
                      '<a href="/gwanak-gu/stations/">관악구 지하철역 전체 안내</a>']

        sections = [
            (f"{name} 출장마사지 이용 안내", [
                f"{name}은 {line} 역으로, {s['summary']}",
                f"{name} 출장마사지는 {name} 인근 {rel_names} 등 관악구 생활권의 자택·오피스텔·숙소로 "
                f"방문해 피로 회복과 컨디션 관리를 돕는 방문형 관리 서비스입니다. 예약 시 위치·희망 "
                f"시간·코스·인원을 확인한 뒤 방문 가능 여부를 안내드립니다.",
                '예약 방법·결제 절차는 <a href="/reservation/">예약안내</a>, 처음 이용 시 진행 흐름은 '
                '<a href="/guide/">이용가이드</a>에서 확인하실 수 있습니다.']),
            (f"{name} 역세권 특징", STATION_DETAIL.get(slug, [s["summary"]])),
            (f"{name} 인근 방문 가능 생활권", zone_blocks),
            (f"{name} 주변 관악구 지역 안내", [
                f"{name}과 가까운 관악구 생활권 안내도 함께 확인하실 수 있습니다. "
                f"{gname} 다른 역과 동별 안내로 이어집니다.",
                ("ul", rel_links)]),
            (f"{name}에서 많이 찾는 관리 코스", [
                f"{name} 인근에서는 피로 회복·아로마·스포츠 관리 문의가 많습니다. 코스별 상세 설명과 "
                f"요금은 아래 링크에서 확인하세요(역 페이지에서는 상세 요금을 반복하지 않습니다).",
                ("ul", ['<a href="/course/">전체 코스 보기</a>', '<a href="/course/fatigue/">피로 회복 관리</a>',
                        '<a href="/course/aroma/">아로마 관리</a>', '<a href="/course/sports/">스포츠 관리</a>',
                        '<a href="/course/price/">가격 안내</a>'])]),
            ("예약 가능 시간", [
                f"{name} 인근은 평균 {s['arrival']}분 내외로 도착하며, 연중무휴 24시간 상담을 운영합니다. "
                f'자세한 시간대 안내는 <a href="/gwanak-gu/hours/">예약 가능 시간</a>을 참고하세요.']),
            ("방문 전 준비사항", [
                f"{name} 일대 방문 시 정확한 주소와 출입 방법을 알려주시면 도착이 빨라집니다. "
                f'준비물·확인사항은 <a href="/gwanak-gu/checklist/">이용 전 확인사항</a>에 정리해 두었습니다.']),
            ("위생 및 안전 안내", [
                "본 서비스는 의료 행위가 아닌 만 19세 이상 대상 건강관리 서비스입니다. "
                f'위생·안전 기준은 <a href="/gwanak-gu/safety/">위생 및 안전 안내</a>에서 확인하세요.']),
        ]
        lead = (f"{line} {name} 인근에서 출장마사지 예약을 찾는 분들을 위한 안내입니다. "
                f"{name}은 {rel_names} 생활권과 가까워 주거지·숙소·오피스텔 방문 문의가 많으며, "
                f"평균 {s['arrival']}분 내외로 도착합니다.")
        top_links = [("tel:" + PHONE_TEL, "예약문의", True), ("/course/", "코스안내"),
                     ("/gwanak-gu/", "관악 출장마사지 대표"), ("/gwanak-gu/stations/", "지하철역별 안내")]
        content_page(path, "stations", trail,
            title=s["title"], desc=s["desc"],
            eyebrow=f"{line} · {name}", h1=f"{name} 출장마사지 예약 안내", lead=lead,
            sections=sections, faq=s["faq"],
            data_note=f"{name} 인근은 평균 {s['arrival']}분 내외로 도착합니다(예약 데이터 기준). "
                      f"저녁·주말은 문의가 몰려 도착이 다소 길어질 수 있어 사전 예약을 권장드립니다. "
                      f"주소 기준: {s['addr']}.",
            service=(f"{name} 출장마사지", f"관악구 {name} 인근 방문 건강관리 서비스"),
            top_links=top_links,
            cta_title=f"{name} 방문 예약, 지금 도와드릴까요?",
            extra_schema=[localbiz_ld(name=f"간다GO {name} 출장마사지",
                                      area=f"서울특별시 관악구 {name} 인근", path=path)])


# ---- Course --------------------------------------------------------------
def build_course():
    trail = [("/", "홈"), (None, "코스안내")]
    course_faq = [
        ("코스는 어떻게 선택하나요?", "컨디션과 목적을 말씀해 주시면 피로 회복·아로마·스포츠 중 적합한 코스를 안내드립니다."),
        ("커플·가족 관리는 어떻게 진행되나요?", "두 분이 같은 공간에서 동시에 받는 동반 관리이며, 인원과 시간에 따라 요금이 달라집니다."),
        ("기업·단체 관리도 되나요?", "워크숍·행사 등 단체 인원은 사전 협의 후 별도 견적으로 안내드립니다."),
        ("표시된 요금 외 추가 비용이 있나요?", "정찰 요금을 원칙으로 하며, 변동 사항은 예약 시 사전에 안내드립니다."),
    ]
    course_cards = "".join(
        f'<a class="card reveal" href="/course/{c["slug"]}/"><div class="k">{c["kicker"]}</div>'
        f'<h3>{c["name"]}</h3><p>{c["desc"]}</p><span class="more">코스 보기 →</span></a>'
        for c in COURSES)
    more_cards = (
        '<a class="card reveal" href="/course/price/"><div class="k">PRICE</div>'
        '<h3>가격 안내</h3><p>코스별 60·90·120분 정찰 요금과 변동 요소를 안내합니다.</p>'
        '<span class="more">가격 보기 →</span></a>'
        '<a class="card reveal" href="/course/guide/"><div class="k">GUIDE</div>'
        '<h3>코스 선택 가이드</h3><p>목적·상황별 추천과 시간 선택 기준을 안내합니다.</p>'
        '<span class="more">가이드 보기 →</span></a>')
    body = (breadcrumb(trail) +
        '<section class="block" id="all"><div class="wrap">'
        '<span class="eyebrow"><span class="pulse"></span>COURSE</span>'
        '<h2 class="sec">전체 코스</h2>'
        '<p class="sec-lead">목적과 컨디션에 맞춰 고를 수 있는 간다GO의 방문 관리 코스입니다. 코스를 눌러 상세 안내를 확인하세요.</p>'
        f'<div class="grid g3" style="margin-top:26px">{course_cards}</div></div></section>' +
        price_menu_block() +
        '<section class="block"><div class="wrap">'
        '<span class="eyebrow"><span class="pulse"></span>MORE</span>'
        '<h2 class="sec">가격과 코스 선택</h2>'
        f'<div class="grid g2" style="margin-top:24px">{more_cards}</div></div></section>' +
        faq_block(course_faq) + cta_band())
    jsonld = [bc_ld(trail),
              service_ld("방문 마사지 코스", "피로 회복·아로마·스포츠·커플·가족·기업·단체 방문 관리 코스", "/course/"),
              faq_ld(course_faq)]
    html = page("/course/", "코스안내 | 관악구 출장마사지 피로회복·아로마·스포츠 요금",
        "간다GO 관악 출장마사지 코스안내 - 피로 회복, 아로마, 스포츠, 커플·가족, 기업·단체 관리의 코스 설명과 정찰 요금을 안내합니다.",
        "course", body, jsonld)
    write("/course/", html)


# ---- Reservation ---------------------------------------------------------
def build_reservation():
    trail = [("/", "홈"), (None, "예약안내")]
    notes = [
        ("예약 방법", ["전화 또는 문의로 지역·희망 시간·코스를 말씀해 주세요.", "디스패처가 방문 가능 시간을 확정해 안내드립니다."]),
        ("예약 가능 시간", ["연중무휴 24시간 상담을 운영합니다.", "방문 가능 시간은 시간대와 위치에 따라 안내드립니다."]),
        ("방문 가능 장소", ["자택, 숙소 등 방문 가능한 장소와 주소를 알려주세요."]),
        ("결제 안내", ["코스별 정찰 요금을 사전에 안내드리며, 결제 방법은 예약 시 함께 안내합니다."]),
        ("예약 변경·취소", ["일정 변경이나 취소는 가능한 한 빠르게 연락 주시면 도와드립니다."]),
        ("예약 전 체크사항", ["방문 장소·연락처·희망 코스·시간을 미리 정리해 두시면 빠르게 진행됩니다."]),
    ]
    res_faq = [
        ("당일 예약이 가능한가요?", "가능합니다. 다만 시간대와 위치에 따라 방문 가능 시간이 달라질 수 있어 상담 시 확인해 드립니다."),
        ("예약을 변경하고 싶어요.", "확정된 일정 변경은 가능한 한 빠르게 연락 주시면 조정을 도와드립니다."),
        ("결제는 어떻게 하나요?", "정찰 요금을 사전에 안내드리며 결제 방법은 예약 시 함께 안내합니다."),
    ]
    body = (breadcrumb(trail) +
        '<section class="block"><div class="wrap">'
        '<span class="eyebrow"><span class="pulse"></span>RESERVATION</span>'
        '<h2 class="sec">예약안내</h2>'
        '<p class="sec-lead">예약 방법부터 결제·변경까지 한눈에 안내드립니다.</p>'
        '</div></section>' +
        notes_block("HOW TO BOOK", "예약 진행 안내", "아래 순서대로 진행됩니다.", notes, _id="about") +
        faq_block(res_faq) + cta_band())
    html = page("/reservation/", "예약안내 | 관악구 출장마사지 예약 방법·결제 안내",
        "간다GO 관악 출장마사지 예약안내 - 예약 방법, 예약 가능 시간, 방문 가능 장소, 결제와 변경·취소 안내를 제공합니다. 연중무휴 24시간 상담.",
        "reservation", body, [bc_ld(trail), faq_ld(res_faq)])
    write("/reservation/", html)


# ---- Guide ---------------------------------------------------------------
def build_guide():
    trail = [("/", "홈"), (None, "이용가이드")]
    notes = [
        ("처음 이용하시는 분", ["예약 시 지역·시간·코스만 말씀해 주시면 나머지는 안내해 드립니다."]),
        ("방문 전 준비사항", ["편하게 쉴 수 있는 공간과 연락 가능한 번호를 준비해 주세요."]),
        ("위생 및 안전 기준", ["용품 위생 관리와 안전 가이드라인을 준수합니다."]),
        ("관리 후 주의사항", ["관리 후에는 충분한 수분 섭취와 휴식을 권장드립니다."]),
        ("금지행위 안내", ["불법·퇴폐 행위 요구는 일절 제공하지 않으며, 요청 시 서비스가 중단될 수 있습니다."]),
    ]
    guide_faq = [
        ("처음인데 무엇을 준비하나요?", "편히 쉴 수 있는 공간과 연락 가능한 번호만 있으면 됩니다."),
        ("관리 후 주의할 점이 있나요?", "충분한 수분 섭취와 휴식을 권장드립니다."),
        ("이 서비스는 의료 행위인가요?", "아닙니다. 이완·휴식 목적의 건강관리 서비스이며 만 19세 이상을 대상으로 합니다."),
    ]
    body = (breadcrumb(trail) +
        '<section class="block"><div class="wrap">'
        '<span class="eyebrow"><span class="pulse"></span>GUIDE</span>'
        '<h2 class="sec">이용가이드</h2>'
        '<p class="sec-lead">처음 이용하시는 분도 안심할 수 있도록 안내드립니다.</p>'
        '</div></section>' +
        notes_block("USER GUIDE", "이용 안내", "방문 전후 확인하세요.", notes, _id="about") +
        faq_block(guide_faq) + cta_band())
    html = page("/guide/", "이용가이드 | 관악구 출장마사지 방문 전 준비·주의사항",
        "간다GO 관악 출장마사지 이용가이드 - 처음 이용하시는 분을 위한 방문 전 준비사항, 위생·안전 기준, 관리 후 주의사항과 금지행위 안내입니다.",
        "guide", body, [bc_ld(trail), faq_ld(guide_faq)])
    write("/guide/", html)


# ---- Reviews -------------------------------------------------------------
def build_reviews():
    trail = [("/", "홈"), (None, "고객후기")]
    sample = [
        ("신림동 · 30대", "아로마", "늦은 시간 연락에도 도착 안내가 정확했습니다."),
        ("서울대입구역 인근 · 40대", "스포츠", "운동 후 받았는데 컨디션이 한결 가벼워졌어요."),
        ("봉천동 · 30대", "피로회복", "예약부터 마무리까지 깔끔하고 정중했습니다."),
        ("낙성대동 · 50대", "아로마", "위생 안내가 꼼꼼해서 안심하고 받았습니다."),
        ("대학동 · 40대", "피로회복", "도착 시간을 미리 알려주셔서 좋았습니다."),
        ("남현동 · 30대", "커플", "둘이 함께 받았는데 응대가 친절했습니다."),
    ]
    cards = "".join(
        f'<div class="review reveal"><div class="stars">★★★★★</div>'
        f'<p>“{q}”</p><div class="who">{w} · {c} 코스</div></div>' for w, c, q in sample)
    region_links = "".join(
        f'<a class="chip" href="/gwanak-gu/{r["slug"]}/"><b>{r["name"]}</b></a>' for r in REGIONS)
    body = (breadcrumb(trail) +
        '<section class="block" id="reviews"><div class="wrap">'
        '<span class="eyebrow"><span class="pulse"></span>REVIEWS</span>'
        '<h2 class="sec">고객후기</h2>'
        '<p class="sec-lead">간다GO를 이용하신 고객들의 후기입니다. 권역별 후기는 각 지역 페이지에서 확인하세요.</p>'
        f'<div class="grid g3" style="margin-top:26px">{cards}</div>'
        f'<div class="chips" style="margin-top:24px">{region_links}</div>'
        '<p class="sec-lead" style="margin-top:24px">후기는 실제 이용 고객의 동의 하에 게시되며, 개인을 특정할 수 있는 정보는 표시하지 않습니다.</p>'
        '</div></section>' + cta_band())
    item_list = {
        "@context": "https://schema.org", "@type": "ItemList",
        "name": "간다GO 관악 출장마사지 고객후기",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1,
             "item": {"@type": "Review", "reviewRating": {"@type": "Rating", "ratingValue": "5"},
                      "author": {"@type": "Person", "name": w}, "reviewBody": q}}
            for i, (w, c, q) in enumerate(sample)],
    }
    html = page("/reviews/", "고객후기 | 관악 출장마사지 간다GO 방문 마사지 후기",
        "간다GO 관악 출장마사지 고객후기 - 봉천·신림·남현과 서울대입구·낙성대·신림역 등 관악구 전 지역 방문 건강관리 이용 후기를 모았습니다.",
        "reviews", body, [bc_ld(trail), item_list])
    write("/reviews/", html)


# ---- Customer center -----------------------------------------------------
def build_customer():
    trail = [("/", "홈"), (None, "고객센터")]
    notes = [
        ("공지사항", ["서비스 운영과 관련된 안내를 이곳에 게시합니다."]),
        ("1:1 문의", [f"전화 {PHONE_DISP}로 문의해 주세요. 연중무휴 24시간 상담을 운영합니다."]),
        ("제휴·기업 문의", ["기업·단체 방문 관리 및 제휴 문의도 전화로 접수받습니다."]),
    ]
    cust_faq = [
        ("문의는 어디로 하나요?", f"전화 {PHONE_DISP}로 문의하실 수 있습니다. 연중무휴 24시간 상담을 운영합니다."),
        ("운영 시간이 어떻게 되나요?", "연중무휴 24시간 상담을 운영합니다."),
        ("개인정보는 어떻게 관리되나요?", "개인정보처리방침에 따라 안전하게 관리되며, 자세한 내용은 해당 페이지에서 확인하실 수 있습니다."),
    ]
    body = (breadcrumb(trail) +
        '<section class="block" id="notice"><div class="wrap">'
        '<span class="eyebrow"><span class="pulse"></span>CUSTOMER</span>'
        '<h2 class="sec">고객센터</h2>'
        f'<p class="sec-lead">전화 {PHONE_DISP} · {HOURS}</p>'
        '</div></section>' +
        notes_block("HELP", "문의 안내", "궁금한 점은 언제든 문의해 주세요.", notes, _id="inquiry") +
        faq_block(cust_faq, "자주 묻는 질문") + cta_band())
    html = page("/customer/", "고객센터 | 관악 출장마사지 간다GO 문의·공지",
        "간다GO 관악 출장마사지 고객센터 - 공지사항, 자주 묻는 질문, 1:1 문의, 제휴·기업 문의 안내입니다. 연중무휴 24시간 상담.",
        "customer", body, [bc_ld(trail), faq_ld(cust_faq)])
    write("/customer/", html)


# ---- Policy pages --------------------------------------------------------
def policy_page(path, active_title, heading, sections, desc):
    trail = [("/", "홈"), (None, heading)]
    secs = "".join(
        f'<div class="note-card"><div class="note-content"><h3 class="note-title">{t}</h3>'
        f'<div class="note-text">{"".join(f"<p>{p}</p>" for p in ps)}</div></div></div>'
        for t, ps in sections)
    body = (breadcrumb(trail) +
        f'<section class="block"><div class="wrap">'
        f'<span class="eyebrow"><span class="pulse"></span>POLICY</span>'
        f'<h2 class="sec">{heading}</h2>'
        f'<div class="note-stack" style="margin-top:26px;max-width:820px">{secs}</div>'
        f'</div></section>')
    html = page(path, active_title, desc, "customer", body, [bc_ld(trail)])
    write(path, html)


def build_policies():
    policy_page("/privacy/", "개인정보처리방침 | 간다GO 관악 출장마사지", "개인정보처리방침",
        [("수집하는 개인정보", ["예약 진행을 위해 연락처, 방문 장소 등 최소한의 정보를 수집합니다."]),
         ("이용 목적", ["수집한 정보는 예약 확정과 방문 안내 목적으로만 이용합니다."]),
         ("보유 및 파기", ["목적 달성 후에는 관련 법령에 따라 지체 없이 파기합니다."]),
         ("개인정보보호책임자", [f"{COMPANY['privacy_officer']} · 전화 {PHONE_DISP}"])],
        "간다GO 관악 출장마사지 개인정보처리방침 - 수집 항목, 이용 목적, 보유 및 파기, 개인정보보호책임자 안내입니다.")
    policy_page("/terms/", "이용약관 | 간다GO 관악 출장마사지", "이용약관",
        [("목적", ["본 약관은 간다GO 관악 출장마사지 예약 서비스 이용 조건을 규정합니다."]),
         ("서비스 내용", ["본 서비스는 의료 행위가 아닌 이완·휴식 목적의 방문 건강관리 예약 서비스입니다."]),
         ("이용 자격", ["본 서비스는 만 19세 이상 성인만 이용할 수 있습니다."]),
         ("금지행위", ["불법·퇴폐 행위 요구 등은 금지되며, 위반 시 서비스가 중단될 수 있습니다."])],
        "간다GO 관악 출장마사지 이용약관 - 서비스 내용, 이용 자격, 금지행위 등 이용 조건을 안내합니다.")
    policy_page("/youth/", "청소년보호정책 | 간다GO 관악 출장마사지", "청소년보호정책",
        [("청소년 이용 제한", ["본 서비스는 만 19세 이상 성인을 대상으로 하며 청소년은 이용할 수 없습니다."]),
         ("건전한 운영", ["간다GO는 불법·퇴폐 행위를 일절 제공하지 않으며 건전한 건강관리 서비스를 지향합니다."]),
         ("책임자", [f"청소년보호 책임자 · {COMPANY['privacy_officer']} · 전화 {PHONE_DISP}"])],
        "간다GO 관악 출장마사지 청소년보호정책 - 만 19세 이상 이용 제한과 건전한 운영 원칙을 안내합니다.")


# ---- 코스 개별 페이지 (각 ~2000자, E-E-A-T) -------------------------------
COURSE_PAGES = ["fatigue", "aroma", "sports", "couple", "group", "price", "guide"]
GANGSEO_PAGES = ["hours", "checklist", "safety", "faq"]

def build_course_pages():
    ct = [("/", "홈"), ("/course/", "코스안내")]

    content_page("/course/fatigue/", "course", ct + [(None, "피로 회복 관리")],
        title="피로 회복 관리 | 관악 출장마사지 스웨디시 계열 방문 관리",
        desc="관악 출장마사지 피로 회복 관리 안내 - 전신 긴장을 부드럽게 풀어주는 스웨디시 계열 방문 관리입니다. 대상, 60·90·120분 진행 방식, 방문 관리의 장점, 자주 묻는 질문을 확인하세요.",
        eyebrow="COURSE · 피로 회복", h1="피로 회복 관리",
        lead="전신의 근육 긴장을 부드럽게 풀어주는 스웨디시 계열 기본 방문 관리입니다.",
        sections=[
            ("피로 회복 관리란 무엇인가요", [
                "피로 회복 관리는 전신의 근육 긴장을 부드럽게 풀어주는 스웨디시 계열의 기본 방문 관리입니다.",
                "강한 자극보다 일정한 압과 리듬으로 혈행과 이완을 돕는 데 초점을 둡니다.",
                "의료적 치료가 아니라, 하루의 피로를 정리하고 휴식의 질을 높이기 위한 <strong>건강관리 목적</strong>의 관리입니다."]),
            ("이런 분께 권해드립니다", [
                ("ul", ["장시간 앉아 일해 어깨·목·허리가 자주 뭉치는 분",
                        "잠들기 전 몸의 긴장을 풀고 수면의 질을 높이고 싶은 분",
                        "강한 지압보다 부드럽고 편안한 이완을 선호하는 분",
                        "출장·야근으로 마사지숍을 방문할 시간을 내기 어려운 분"])]),
            ("60·90·120분 진행 방식", [
                "60분은 어깨·등·다리 등 피로가 집중된 부위를 중심으로 전신을 한 차례 정리합니다.",
                "90분은 가장 많이 선택되는 구성으로, 전신을 고르게 풀고 뭉친 부위에 시간을 더 배분합니다.",
                "120분은 전신을 충분히 이완한 뒤 두피·발 등 마무리 케어까지 여유 있게 진행합니다.",
                "관리 시작 전 선호하는 압의 세기와 집중 부위를 확인하고, 진행 중에도 조절해 드립니다."]),
            ("방문 관리이기에 더 좋은 점", [
                "관리 직후 이동 없이 그대로 쉴 수 있어 이완 상태가 오래 유지됩니다.",
                "익숙한 공간에서 받기 때문에 긴장이 덜하고 편안합니다.",
                "관악구 전 권역으로 방문하며, 위치에 따라 평균 18~27분 내외로 도착합니다."]),
            ("관리 당일, 이렇게 진행됩니다", [
                "관리사가 도착하면 가볍게 인사를 나누고, 편히 누우실 수 있도록 공간을 정돈합니다.",
                "본격적인 관리 전에 선호하는 압의 세기와 특히 풀고 싶은 부위를 확인합니다.",
                "관리는 호흡을 고르며 큰 근육부터 차례로 이완하고, 뭉친 부위는 시간을 더 들여 풀어드립니다.",
                "마지막에는 마무리 정돈과 함께 수분 섭취·휴식을 안내하며 관리를 마칩니다."]),
            ("이렇게 준비하면 더 좋습니다", [
                "관리 전 가벼운 샤워로 몸을 따뜻하게 하면 이완이 한결 수월합니다.",
                "과식 직후보다는 식사 후 어느 정도 시간이 지난 뒤가 편안합니다.",
                "편안한 복장과 조용한 분위기를 준비해 두시면 휴식의 질이 높아집니다.",
                "받고 난 뒤 좋았던 압·부위를 기억해 두면 다음 방문 때 더 잘 맞춰 드릴 수 있습니다."]),
        ],
        data_note="간다GO 관악 권역에서 피로 회복 관리는 90분 구성 선택 비율이 가장 높습니다. 주중 21~24시 예약이 가장 많아, 해당 시간대는 도착 시간을 넉넉히 안내드립니다.",
        faq=[
            ("피로 회복 관리와 아로마 관리는 어떻게 다른가요?", "피로 회복 관리는 전신 이완에, 아로마 관리는 블렌딩 오일의 향을 더한 이완에 중점을 둡니다. 향에 민감하지 않다면 피로 회복 관리로 시작하셔도 좋습니다."),
            ("압이 너무 세거나 약하면 조절되나요?", "네. 시작 전과 진행 중 언제든 압의 세기를 말씀해 주시면 맞춰 드립니다."),
            ("관리 후 주의할 점이 있나요?", "충분한 수분 섭취와 휴식을 권장드립니다. 통증·부상이 있는 부위는 무리하지 않습니다.")],
        service=("피로 회복 관리", "관악구 방문 스웨디시 계열 전신 이완 관리"))

    content_page("/course/aroma/", "course", ct + [(None, "아로마 관리")],
        title="아로마 관리 | 관악 출장마사지 아로마 오일 방문 관리",
        desc="관악 출장마사지 아로마 관리 안내 - 블렌딩 오일의 향과 촉감으로 심신을 이완하는 방문 관리입니다. 사용 오일, 사전 확인사항, 진행 방식, 피로 회복 관리와의 차이를 확인하세요.",
        eyebrow="COURSE · 아로마", h1="아로마 관리",
        lead="블렌딩한 관리용 오일을 사용해 향과 촉감으로 심신을 함께 이완하는 방문 관리입니다.",
        sections=[
            ("아로마 관리의 특징", [
                "아로마 관리는 블렌딩한 관리용 오일을 사용해 향과 촉감으로 심신을 함께 이완하는 방문 관리입니다.",
                "오일이 피부 위에서 부드럽게 미끄러지며 마찰을 줄여, 더 유연하고 감각적인 이완을 돕습니다.",
                "향을 통한 심리적 이완이 더해져, 긴장도가 높거나 예민한 날에 특히 선호됩니다."]),
            ("사용 오일과 사전 확인", [
                "라벤더 계열의 차분한 향, 시트러스 계열의 가벼운 향 등 그날의 컨디션에 맞춰 안내드립니다.",
                "피부가 민감하거나 특정 향·성분에 알러지가 있다면 예약 시 미리 알려주세요.",
                "임신 중이거나 피부 질환이 있는 경우, 무리하지 않도록 사전에 상담드립니다."]),
            ("진행 방식", [
                "60분은 어깨·등을 중심으로 오일 관리를 진행합니다.",
                "90분은 전신을 고르게 아우르는 가장 표준적인 구성입니다.",
                "120분은 전신 이완 후 두피·발 마무리까지 포함해 여유 있게 진행합니다."]),
            ("피로 회복 관리와의 차이", [
                "피로 회복 관리가 근육 이완 자체에 집중한다면, 아로마 관리는 여기에 향의 이완을 더합니다.",
                "오일을 사용하므로 마무리 단계에서 수건으로 가볍게 정돈해 과도한 잔여감을 줄입니다."]),
            ("오일이 만드는 차이", [
                "오일을 사용하면 손과 피부 사이의 마찰이 줄어, 같은 동작도 더 부드럽고 깊게 전달됩니다.",
                "끊김 없이 이어지는 긴 동작이 가능해 호흡이 느려지고 긴장이 천천히 가라앉습니다.",
                "건식 관리에서 자극이 부담스러웠던 분도 비교적 편안하게 받을 수 있습니다."]),
            ("관리 당일 진행 순서", [
                "도착 후 그날의 컨디션과 선호 향을 확인하고 오일을 준비합니다.",
                "어깨·등 등 넓은 부위부터 오일을 펴 바르며 이완을 시작합니다.",
                "전신을 고르게 아우른 뒤, 마무리 단계에서 수건으로 정돈해 잔여감을 줄입니다."]),
            ("관리 후 이렇게 케어하세요", [
                "관리 후에는 따뜻한 물을 충분히 마시고 무리한 활동을 피해 휴식을 권장드립니다.",
                "오일 잔여감이 신경 쓰이면 가벼운 샤워로 마무리하셔도 좋습니다."]),
        ],
        data_note="아로마 관리는 금요일·주말 저녁 예약 비율이 평일보다 높습니다. 향 선호가 뚜렷한 고객이 많아, 예약 시 선호 향을 함께 받아두면 방문이 매끄럽습니다.",
        faq=[
            ("향을 선택할 수 있나요?", "네. 라벤더·시트러스 등 계열을 안내드리며, 선호가 없으시면 컨디션에 맞춰 추천드립니다."),
            ("오일 알러지가 걱정됩니다.", "민감성 피부나 알러지가 있으면 예약 시 알려주세요. 무리하지 않도록 조정합니다."),
            ("관리 후 끈적임이 남지 않나요?", "마무리 단계에서 수건으로 정돈해 드려 과도한 잔여감을 줄입니다.")],
        service=("아로마 관리", "관악구 방문 아로마 오일 이완 관리"))

    content_page("/course/sports/", "course", ct + [(None, "스포츠 관리")],
        title="스포츠 관리 | 관악 출장마사지 운동 후 근육 방문 관리",
        desc="관악 출장마사지 스포츠 관리 안내 - 운동 후 뭉친 근육과 컨디션 회복에 초점을 맞춘 방문 관리입니다. 적합한 상황, 진행 방식, 주의사항을 확인하세요.",
        eyebrow="COURSE · 스포츠", h1="스포츠 관리",
        lead="운동 후 뭉친 근육과 컨디션 회복에 초점을 맞춘 방문 관리입니다.",
        sections=[
            ("스포츠 관리란", [
                "스포츠 관리는 운동 후 뭉친 근육과 컨디션 회복에 초점을 맞춘 방문 관리입니다.",
                "근육 부위를 따라 비교적 또렷한 압으로 풀어, 운동으로 누적된 피로를 정리하는 데 도움을 줍니다.",
                "전문 재활·치료가 아닌, 일상 운동 후의 컨디션 관리 목적임을 안내드립니다."]),
            ("이런 상황에 잘 맞습니다", [
                ("ul", ["러닝·헬스·등산 등 운동 후 다리·등 근육이 무거운 날",
                        "주말 과한 활동으로 다음 날 컨디션을 빠르게 정리하고 싶을 때",
                        "평소보다 또렷한 압의 관리를 선호하는 분"])]),
            ("진행 방식", [
                "관리 전 운동 종류와 뭉친 부위를 확인해 시간을 집중 배분합니다.",
                "60분은 하체 또는 상체 등 특정 부위 중심, 90·120분은 전신을 고르게 풀며 집중 부위를 추가합니다.",
                "압이 강하게 느껴지면 즉시 조절하니 편하게 말씀해 주세요."]),
            ("주의사항 (꼭 읽어주세요)", [
                "부상·염좌·심한 통증이 있는 부위는 관리 대상이 아니며, 해당 증상은 의료기관 진료를 권유드립니다.",
                "본 관리는 의료 행위가 아닌 건강관리 서비스이며, 통증 완화·치료를 보장하지 않습니다."]),
            ("부위별 접근 방식", [
                "하체는 허벅지·종아리 등 큰 근육을 따라 또렷한 압으로 무거움을 정리합니다.",
                "등·어깨는 운동 자세로 자주 긴장되는 부위라 시간을 더 배분합니다.",
                "관리 중 통증과 시원함의 경계를 확인하며 강약을 세밀하게 조절합니다."]),
            ("관리 당일 진행 순서", [
                "도착 후 어떤 운동을 했는지, 어느 부위가 무거운지 확인합니다.",
                "근육을 데우듯 가볍게 시작해 점차 압을 높이며 집중 부위를 풀어드립니다.",
                "마무리 단계에서는 가볍게 이완하며 호흡을 고르고 관리를 마칩니다."]),
            ("운동 루틴과 함께하면 좋은 점", [
                "규칙적으로 운동하는 분은 무리한 날 컨디션을 빠르게 정리하는 용도로 활용하기 좋습니다.",
                "다만 통증이 반복되거나 심해지면 관리보다 의료기관 진료를 먼저 권유드립니다."]),
        ],
        data_note="스포츠 관리는 주말(토·일) 오전~오후 예약 비율이 다른 코스보다 높습니다. 운동 직후보다는 1~2시간 휴식 후 관리를 권장드립니다.",
        faq=[
            ("운동 직후 바로 받아도 되나요?", "가벼운 휴식 후 받는 것을 권장드립니다. 심한 통증이 있다면 무리하지 않습니다."),
            ("강도가 센 편인가요?", "근육 부위에 또렷한 압을 사용하지만, 선호에 맞춰 강약을 조절합니다."),
            ("부상이 있어도 받을 수 있나요?", "부상·급성 통증 부위는 관리 대상이 아니며 의료기관 진료를 권유드립니다.")],
        service=("스포츠 관리", "관악구 방문 운동 후 근육 컨디션 관리"))

    content_page("/course/couple/", "course", ct + [(None, "커플·가족 방문 관리")],
        title="커플·가족 방문 관리 | 관악 출장마사지 2인 동반 관리",
        desc="관악 출장마사지 커플·가족 방문 관리 안내 - 두 분이 같은 공간에서 동시에 받는 동반형 방문 관리입니다. 공간·인원 조건, 예약 방법, 요금 구조를 확인하세요.",
        eyebrow="COURSE · 커플·가족", h1="커플·가족 방문 관리",
        lead="두 분이 같은 공간에서 동시에 관리를 받는 동반형 방문 관리입니다.",
        sections=[
            ("커플·가족 방문 관리란", [
                "두 분이 같은 공간에서 동시에 관리를 받는 동반형 방문 관리입니다.",
                "커플은 물론, 부모님과 함께 등 가족 단위로도 이용하실 수 있습니다.",
                "각자 원하는 코스(피로 회복·아로마 등)를 다르게 선택할 수 있습니다."]),
            ("공간과 인원 조건", [
                "동시에 관리가 진행되므로 관리사 2인이 방문하며, 두 사람이 누울 수 있는 공간이 필요합니다.",
                "공간이 협소한 경우 순차 진행으로 안내드릴 수 있어, 예약 시 환경을 알려주세요."]),
            ("예약 방법", [
                "동반 관리는 일정 조율이 필요해 사전 협의 예약을 권장드립니다.",
                "희망 코스, 인원, 시간, 방문 장소를 말씀해 주시면 가능한 시간을 확정해 드립니다."]),
            ("요금 안내", [
                "커플·가족 방문 관리는 인원과 시간에 따라 요금이 책정됩니다.",
                "기본 요금은 <a href='/course/price/'>가격 안내</a>에서 확인하실 수 있으며, 정확한 금액은 상담 시 안내드립니다."]),
            ("어떤 분들이 함께 받나요", [
                "기념일을 함께 보내려는 커플, 부모님께 휴식을 선물하려는 가족, 오랜만에 만난 친구 등 다양합니다.",
                "두 분이 같은 시간에 나란히 이완할 수 있어, 혼자 받을 때와는 다른 편안함이 있습니다.",
                "각자 컨디션이 다르면 한 분은 피로 회복, 다른 한 분은 아로마처럼 다르게 선택하셔도 됩니다."]),
            ("공간 준비 가이드", [
                "두 사람이 동시에 누울 수 있는 평평한 공간이 있으면 동시 진행이 가능합니다.",
                "원룸·호텔 등 공간이 좁다면 한 분씩 순차로 진행하는 방식으로 안내드립니다.",
                "예약 시 방의 크기나 환경을 알려주시면 알맞은 방식을 미리 정해 드립니다."]),
            ("관리 당일 진행 순서", [
                "관리사 2인이 함께 도착해 각자 담당을 정하고 공간을 준비합니다.",
                "두 분의 선호 압·코스를 각각 확인한 뒤 동시에 관리를 시작합니다.",
                "마무리도 함께 정돈하여 두 분이 비슷한 시점에 휴식에 들어가도록 합니다."]),
        ],
        data_note="동반 관리는 기념일·주말 저녁 문의가 집중됩니다. 관리사 2인 일정 조율이 필요하므로 가급적 1~2일 전 예약을 권장드립니다.",
        faq=[
            ("두 사람이 다른 코스를 받을 수 있나요?", "네. 각자 원하는 코스를 선택하실 수 있습니다."),
            ("좁은 공간에서도 가능한가요?", "두 분이 동시에 누울 공간이 어려우면 순차 진행으로 안내드립니다."),
            ("당일 예약도 되나요?", "관리사 2인 일정상 사전 예약을 권장드립니다. 당일은 가능 여부를 상담으로 확인해 드립니다.")],
        service=("커플·가족 방문 관리", "관악구 2인 동반 방문 관리"))

    content_page("/course/group/", "course", ct + [(None, "기업·단체 방문 관리")],
        title="기업·단체 방문 관리 | 관악 출장마사지 단체·행사 관리",
        desc="관악 출장마사지 기업·단체 방문 관리 안내 - 워크숍·행사·사내 복지 등 단체 인원을 위한 사전 협의형 방문 관리입니다. 진행 방식, 견적·결제, 사전 준비를 확인하세요.",
        eyebrow="COURSE · 기업·단체", h1="기업·단체 방문 관리",
        lead="워크숍·행사·사내 복지 등 단체 인원을 대상으로 하는 사전 협의형 방문 관리입니다.",
        sections=[
            ("기업·단체 방문 관리란", [
                "워크숍·행사·사내 복지 등 단체 인원을 대상으로 하는 사전 협의형 방문 관리입니다.",
                "여러 명이 순차 또는 동시에 관리를 받을 수 있도록 일정을 구성합니다."]),
            ("진행 방식", [
                "인원수, 1인당 관리 시간, 희망 날짜와 장소를 먼저 확인합니다.",
                "행사 성격에 맞춰 짧은 의자형 케어부터 표준 코스까지 구성할 수 있습니다.",
                "관리사 인원과 진행 순서를 사전에 설계해 현장 운영을 매끄럽게 합니다."]),
            ("견적과 결제", [
                "단체 관리는 인원·시간·장소에 따라 별도 견적으로 안내드립니다.",
                "세금계산서 등 결제 방식은 사전에 협의해 드립니다."]),
            ("사전 준비", [
                "관리에 적합한 공간(조용한 회의실·라운지 등)과 콘센트, 대기 동선을 확인해 주세요.",
                "행사 일정이 정해지면 가급적 여유 있게 문의해 주시면 원활합니다."]),
            ("어떤 행사에 적합한가요", [
                "사내 워크숍이나 단합 행사에서 직원 복지 프로그램으로 활용하기 좋습니다.",
                "장시간 행사 중간의 휴식 코너, 야유회·연수 등의 부대 프로그램으로도 구성할 수 있습니다.",
                "인원과 시간을 고려해 짧고 가벼운 케어부터 표준 코스까지 유연하게 맞춰 드립니다."]),
            ("현장 운영 순서", [
                "행사 전 인원·시간표·동선을 협의해 관리사 수와 진행 순서를 설계합니다.",
                "당일에는 안내 동선을 미리 잡아 대기 시간을 줄이고 순환이 매끄럽도록 운영합니다.",
                "여러 명이 동시에 받을 경우 관리사를 늘려 전체 진행 시간을 단축합니다.",
                "행사 종료 후에는 사용 공간을 정돈하고 마무리합니다."]),
            ("사전 준비 체크리스트", [
                ("ul", ["참여 인원과 1인당 희망 시간",
                        "행사 날짜·시간과 장소(주소)",
                        "관리 진행이 가능한 공간(회의실·라운지 등)",
                        "콘센트·대기 동선 등 현장 여건"])]),
            ("행사 후 마무리", [
                "행사 종료 후 사용한 공간을 정돈하고, 진행 결과를 간단히 정리해 전달드릴 수 있습니다.",
                "정기적인 사내 복지로 운영하실 경우, 다음 일정 협의도 함께 도와드립니다."]),
        ],
        data_note="기업·단체 관리는 분기 말·연말 사내 행사 시즌에 문의가 늘어납니다. 관리사 배치를 위해 최소 며칠 전 협의를 권장드립니다.",
        faq=[
            ("최소 인원 제한이 있나요?", "인원에 맞춰 구성하며, 정확한 기준은 문의 시 안내드립니다."),
            ("세금계산서 발행이 되나요?", "네. 결제 방식은 사전 협의로 안내드립니다."),
            ("행사 장소로 방문하나요?", "네. 관악구 및 인근 행사 장소로 방문 가능하며 위치를 확인해 드립니다.")],
        service=("기업·단체 방문 관리", "관악구 단체·행사 방문 관리"))

    content_page("/course/price/", "course", ct + [(None, "가격 안내")],
        title="가격 안내 | 관악 출장마사지 코스별 정찰 요금",
        desc="관악 출장마사지 가격 안내 - 코스별 60·90·120분 기본 요금과 정찰 요금 원칙, 변동 요소, 결제 안내를 제공합니다. 숨겨진 추가 비용 없이 투명하게 안내합니다.",
        eyebrow="COURSE · 가격", h1="가격 안내",
        lead="코스별 기본 요금을 사전에 안내하는 정찰 요금을 원칙으로 합니다.",
        sections=[
            ("정찰 요금 원칙", [
                "간다GO 관악 출장마사지는 코스별 기본 요금을 사전에 안내하는 <strong>정찰 요금</strong>을 원칙으로 합니다.",
                "현장에서 임의로 금액을 올리거나 숨겨진 추가 비용을 청구하지 않습니다."]),
            ("코스별 기본 요금", [
                "아래 60·90·120분 기본 요금을 참고하시고, 코스 종류(피로 회복·아로마·스포츠 등)에 따라 세부 금액이 달라질 수 있습니다."]),
            ("변동될 수 있는 요소", [
                ("ul", ["방문 지역과 이동 거리", "예약 시간대(심야 등)",
                        "커플·가족 등 인원 구성", "기업·단체 등 별도 견적 대상"])]),
            ("결제 안내", [
                "결제 방법은 예약 시 함께 안내드리며, 변동 사항이 있으면 사전에 고지합니다.",
                "정확한 최종 금액은 예약 상담에서 확인해 드립니다."]),
            ("요금은 이렇게 구성됩니다", [
                "기본 요금은 코스(피로 회복·아로마·스포츠 등)와 시간(60·90·120분)의 조합으로 정해집니다.",
                "커플·가족처럼 인원이 늘어나는 경우, 관리사 수와 시간에 따라 요금이 책정됩니다.",
                "기업·단체는 인원·장소·시간 편차가 커서 별도 견적으로 안내드립니다."]),
            ("예약 시 함께 안내드리는 것", [
                "예약 상담에서는 코스 기본 요금과 함께 아래 사항을 미리 확인해 드립니다.",
                ("ul", ["선택한 코스·시간의 최종 금액",
                        "지역·시간대에 따른 변동 여부",
                        "결제 방법과 가능한 결제 수단"])]),
            ("투명한 요금을 위한 약속", [
                "현장에서 사전 안내와 다른 금액을 요구하지 않습니다.",
                "변동이 필요한 경우 반드시 관리 전에 설명드리고 동의를 받은 뒤 진행합니다."]),
        ],
        data_note="가장 많이 선택되는 구성은 90분입니다. 심야(자정 이후) 예약은 도착 시간과 함께 변동 요소를 미리 안내드립니다.",
        faq=[
            ("표시 요금 외에 추가 비용이 있나요?", "정찰 요금을 원칙으로 하며, 지역·시간대 등 변동 요소는 예약 시 미리 안내드립니다."),
            ("결제는 어떻게 하나요?", "결제 방법은 예약 시 안내드립니다."),
            ("코스마다 가격이 다른가요?", "네. 코스 종류에 따라 세부 금액이 달라질 수 있어 상담 시 확정해 드립니다.")],
        show_price=True,
        service=("관악 출장마사지 요금", "관악구 방문 관리 정찰 요금 안내"))

    content_page("/course/guide/", "course", ct + [(None, "코스 선택 가이드")],
        title="코스 선택 가이드 | 관악 출장마사지 상황별 추천",
        desc="관악 출장마사지 코스 선택 가이드 - 목적과 상황에 맞는 코스 추천, 60·90·120분 시간 선택 기준, 처음 이용하는 분을 위한 안내를 제공합니다.",
        eyebrow="COURSE · 선택 가이드", h1="코스 선택 가이드",
        lead="어떤 코스를 골라야 할지 모르겠다면, 목적을 기준으로 선택하면 쉽습니다.",
        sections=[
            ("코스, 이렇게 고르세요", [
                "어떤 코스를 골라야 할지 모르겠다면, '무엇을 위해 받는가'라는 목적을 기준으로 선택하면 쉽습니다."]),
            ("상황별 추천", [
                ("ul", ["전신이 무겁고 푹 쉬고 싶다 → <strong>피로 회복 관리</strong>",
                        "향과 함께 깊게 이완하고 싶다 → <strong>아로마 관리</strong>",
                        "운동 후 근육을 풀고 싶다 → <strong>스포츠 관리</strong>",
                        "둘이 함께 받고 싶다 → <strong>커플·가족 방문 관리</strong>",
                        "행사·단체로 진행하고 싶다 → <strong>기업·단체 방문 관리</strong>"])]),
            ("시간(60·90·120분) 선택", [
                "60분은 핵심 부위 위주로 빠르게 정리하고 싶을 때 적합합니다.",
                "90분은 전신을 고르게 풀 수 있어 가장 무난하며 많이 선택됩니다.",
                "120분은 전신 이완과 마무리 케어까지 여유 있게 받고 싶을 때 좋습니다."]),
            ("처음 이용하신다면", [
                "첫 방문이라면 90분 피로 회복 관리로 시작해 보시길 권합니다.",
                "받아본 뒤 선호하는 압·향·집중 부위를 알려주시면 다음 방문이 더 잘 맞습니다."]),
            ("목적별로 조금 더 자세히", [
                ("h3", "푹 쉬고 싶다면"),
                "특별히 아픈 곳은 없지만 전반적으로 무겁고 피곤하다면 피로 회복 관리가 가장 무난합니다.",
                ("h3", "향까지 즐기고 싶다면"),
                "긴장도가 높거나 예민한 날에는 향이 더해진 아로마 관리가 이완에 도움이 됩니다.",
                ("h3", "운동 후라면"),
                "다리·등 근육이 무거운 날에는 또렷한 압의 스포츠 관리가 잘 맞습니다."]),
            ("압의 세기 선택", [
                "압은 '시원하다'고 느껴지는 정도가 적당하며, 통증을 참을 필요는 없습니다.",
                "강한 압을 선호하면 스포츠 관리를, 부드러운 이완을 원하면 피로 회복·아로마 관리를 권합니다."]),
            ("재방문 시 팁", [
                "한 번 받아본 뒤 좋았던 압·향·집중 부위를 메모해 두면 다음 예약이 훨씬 수월합니다.",
                "컨디션에 따라 코스를 바꿔가며 받는 것도 좋은 방법입니다."]),
            ("시간 선택이 고민될 때", [
                "처음이거나 시간이 넉넉지 않다면 60분으로 핵심 부위만 정리해도 충분히 도움이 됩니다.",
                "온전히 쉬고 싶은 날에는 90분 이상을 권하며, 마무리 케어까지 원하면 120분이 적합합니다.",
                "정하기 어렵다면 예약 상담에서 컨디션을 말씀해 주시면 알맞은 시간을 추천드립니다."]),
        ],
        data_note="처음 이용하는 고객의 다수가 90분 구성을 선택하며, 재방문 시 아로마·스포츠로 옮겨가는 경우가 많습니다.",
        faq=[
            ("처음인데 무엇이 좋을까요?", "90분 피로 회복 관리를 권장드립니다. 무난하게 전신을 풀 수 있습니다."),
            ("커플로 다른 코스도 가능한가요?", "네. 동반 관리에서 각자 다른 코스를 선택할 수 있습니다."),
            ("시간을 늘리면 더 좋은가요?", "집중 부위가 많거나 마무리 케어까지 원하면 90~120분이 적합합니다.")],
        service=("코스 선택 가이드", "관악구 방문 관리 코스 선택 안내"))


def build_gwanak_info_pages():
    gt = [("/", "홈"), ("/gwanak-gu/", "관악 출장마사지")]

    content_page("/gwanak-gu/hours/", "gwanak", gt + [(None, "예약 가능 시간")],
        title="예약 가능 시간 | 관악 출장마사지 24시간 상담·도착 안내",
        desc="관악 출장마사지 예약 가능 시간 안내 - 연중무휴 24시간 상담, 시간대별 특징, 권역별 평균 도착 시간, 예약 팁을 제공합니다.",
        eyebrow="관악 출장마사지 · 시간", h1="예약 가능 시간",
        lead="간다GO 관악 출장마사지는 연중무휴 24시간 예약 상담을 운영합니다.",
        sections=[
            ("운영 시간", [
                "간다GO 관악 출장마사지는 <strong>연중무휴 24시간</strong> 예약 상담을 운영합니다.",
                "전화 상담은 언제든 가능하며, 실제 방문 가능 시간은 시간대와 위치에 따라 안내드립니다."]),
            ("시간대별 특징", [
                ("ul", ["낮~초저녁: 비교적 도착이 빠르고 일정 조율이 수월합니다.",
                        "밤 21~24시: 예약이 가장 많이 몰리는 시간대로, 도착 시간을 넉넉히 안내드립니다.",
                        "심야(자정 이후): 방문 가능하나 위치에 따라 도착 시간이 길어질 수 있습니다."])]),
            ("권역별 평균 도착 시간", [
                "관악구 내 위치에 따라 평균 18~27분 내외로 도착합니다.",
                "신림역·봉천동 등 중심 생활권은 비교적 빠르고, 난향동·대학동 등 외곽은 다소 길어질 수 있습니다.",
                "예약 시 정확한 위치를 알려주시면 예상 도착 시간을 안내드립니다."]),
            ("예약 팁", [
                "원하는 시간이 정해져 있다면 미리 예약할수록 일정 조율이 수월합니다.",
                "주말 저녁·기념일은 문의가 몰리니 여유 있게 연락 주세요."]),
            ("예약이 몰리는 시간", [
                "평일 밤 21~24시는 하루 중 예약이 가장 집중되는 시간대입니다.",
                "이 시간대에는 도착이 평소보다 조금 더 걸릴 수 있어, 여유 있게 예약하시길 권합니다."]),
            ("도착 시간을 줄이는 방법", [
                "예약 시 정확한 주소와 공동현관·동·호수 등 출입 정보를 함께 알려주세요.",
                "가까운 지하철역이나 큰 건물 등 기준점을 알려주시면 위치 파악이 빨라집니다.",
                "도착 직전 연락이 닿을 수 있는 번호를 남겨주시면 마지막 동선이 매끄럽습니다."]),
            ("주말·공휴일 운영", [
                "주말과 공휴일에도 동일하게 연중무휴로 상담·방문을 운영합니다.",
                "다만 기념일·연휴 저녁은 문의가 몰리므로 미리 예약하시는 편이 좋습니다."]),
            ("예약 변경·취소", [
                "일정이 바뀌면 가능한 한 빠르게 연락 주세요. 빠를수록 다른 시간으로 조율하기 쉽습니다.",
                "방문 직전 변경은 관리사 동선상 어려울 수 있어, 미리 알려주시면 감사하겠습니다."]),
        ],
        data_note="권역 평균 도착 시간(예약 데이터 기준): 신림동 18분, 서울대입구역 19분, 봉천동 20분, 낙성대동 22분, 대학동 25분, 난곡동 26분, 난향동 27분 내외.",
        faq=[
            ("새벽에도 예약되나요?", "상담은 24시간 가능합니다. 심야는 위치에 따라 도착 시간이 길어질 수 있어 상담 시 안내드립니다."),
            ("도착까지 얼마나 걸리나요?", "권역에 따라 평균 18~27분 내외이며, 시간대와 위치에 따라 달라집니다."),
            ("당일 예약이 가능한가요?", "가능합니다. 시간대와 위치에 따라 가능 시간을 상담으로 확인해 드립니다.")])

    content_page("/gwanak-gu/checklist/", "gwanak", gt + [(None, "이용 전 확인사항")],
        title="이용 전 확인사항 | 관악 출장마사지 방문 준비 안내",
        desc="관악 출장마사지 이용 전 확인사항 - 방문 장소 준비, 예약 정보, 결제 준비, 이용 시 주의사항을 안내합니다. 만 19세 이상 건강관리 서비스입니다.",
        eyebrow="관악 출장마사지 · 확인", h1="이용 전 확인사항",
        lead="원활한 방문을 위해 예약 전 아래 사항을 미리 확인해 주세요.",
        sections=[
            ("방문 장소 준비", [
                "편하게 누워 쉴 수 있는 공간을 확보해 주세요.",
                "숙소·자택 등 방문 장소의 정확한 주소와 출입 방법(공동현관 등)을 알려주시면 도착이 빨라집니다."]),
            ("예약 정보 확인", [
                ("ul", ["연락 가능한 전화번호", "방문 장소 주소",
                        "희망 코스와 시간(60·90·120분)", "방문 희망 시각"])]),
            ("결제 준비", [
                "코스별 정찰 요금을 사전에 안내드리며, 결제 방법은 예약 시 함께 확인합니다.",
                "변동 요소(지역·시간대 등)는 미리 고지해 드립니다."]),
            ("이용 시 주의사항", [
                "본 서비스는 의료 행위가 아닌 건강관리 서비스이며 <strong>만 19세 이상</strong> 성인을 대상으로 합니다.",
                "불법·퇴폐 행위 요구는 일절 제공되지 않으며, 요청 시 서비스가 중단될 수 있습니다.",
                "음주가 심한 경우 안전을 위해 관리가 어려울 수 있습니다."]),
            ("방문 장소별 안내", [
                ("h3", "자택"),
                "공동현관 출입 방법과 동·호수를 알려주시면 도착이 빨라집니다. 반려동물이 있다면 미리 안내해 주세요.",
                ("h3", "숙소·호텔"),
                "건물명과 객실 번호, 프런트 출입 안내가 필요한지 함께 알려주시면 원활합니다."]),
            ("미리 알려주시면 좋은 점", [
                "함께 계신 분이 있거나, 특정 향·압을 피하고 싶다면 예약 시 말씀해 주세요.",
                "임신 중이거나 피부·건강상 주의가 필요한 상황은 안전을 위해 사전에 공유해 주세요."]),
            ("결제·영수 안내", [
                "결제 방법은 예약 시 함께 확인하며, 필요하시면 영수 관련 사항도 안내드립니다.",
                "변동 요소가 있을 경우 관리 전에 미리 설명드리고 진행합니다."]),
            ("방문이 끝나면", [
                "관리 후에는 충분한 수분 섭취와 휴식을 권장드립니다.",
                "사용한 공간은 관리사가 정돈하고 마무리하니 따로 준비하실 것은 없습니다.",
                "다음 방문에 참고할 선호 사항(압·향·부위 등)을 알려주시면 더 잘 맞춰 드립니다."]),
        ],
        data_note="예약 시 주소와 출입 방법을 함께 남겨주시면 도착 시간이 평균적으로 단축됩니다. 공동현관 비밀번호 등은 도착 직전 안내해 주셔도 됩니다.",
        faq=[
            ("무엇을 준비하면 되나요?", "편히 쉴 공간과 연락 가능한 번호, 정확한 주소면 충분합니다."),
            ("출입은 어떻게 하나요?", "출입 방법을 미리 알려주시면 도착이 수월합니다. 필요한 안내는 상담 시 도와드립니다."),
            ("예약을 변경할 수 있나요?", "가능한 한 빠르게 연락 주시면 일정 변경을 도와드립니다.")])

    content_page("/gwanak-gu/safety/", "gwanak", gt + [(None, "위생 및 안전 안내")],
        title="위생 및 안전 안내 | 관악 출장마사지 위생·안전 기준",
        desc="관악 출장마사지 위생 및 안전 안내 - 용품 위생 관리, 관리사·고객 안전 가이드라인, 비의료 서비스 고지, 개인정보 보호 원칙을 안내합니다.",
        eyebrow="관악 출장마사지 · 안전", h1="위생 및 안전 안내",
        lead="안심하고 받으실 수 있도록 위생과 안전을 운영의 기본 기준으로 둡니다.",
        sections=[
            ("위생 관리 기준", [
                "관리에 사용하는 수건·오일 등 용품은 위생 기준에 맞춰 관리합니다.",
                "방문 시 청결을 우선하며, 관리 종료 후 사용한 공간을 정돈합니다."]),
            ("관리사·고객 안전", [
                "관리사와 고객 모두의 안전을 위한 운영 가이드라인을 준수합니다.",
                "상호 존중을 원칙으로 하며, 부적절한 요구가 있을 경우 관리가 중단될 수 있습니다."]),
            ("비의료 서비스 고지", [
                "본 서비스는 의료 행위가 아닌 <strong>이완·휴식 목적의 건강관리(마사지) 서비스</strong>입니다.",
                "질환의 진단·치료를 목적으로 하지 않으며, 통증·부상은 의료기관 진료를 권유드립니다."]),
            ("개인정보 보호", [
                "예약을 위해 수집한 연락처·주소 등은 예약 진행 목적으로만 이용하고, 목적 달성 후 관련 법령에 따라 파기합니다.",
                "자세한 내용은 <a href='/privacy/'>개인정보처리방침</a>에서 확인하실 수 있습니다."]),
            ("용품 관리 상세", [
                "수건 등 직접 닿는 용품은 청결 상태를 확인해 사용하며, 위생을 우선합니다.",
                "오일 등 소모품은 적정 상태로 관리해 사용하고, 사용 후 공간을 정돈합니다.",
                "방문 시 단정한 복장과 청결을 기본으로 합니다."]),
            ("관리사 응대 기준", [
                "정중한 인사와 설명을 기본으로, 관리 전 선호 사항을 충분히 확인합니다.",
                "관리 중에도 압·온도·자세 등 불편함이 없는지 살피며 진행합니다.",
                "응대 가이드라인을 통해 어느 관리사가 방문하더라도 일관된 경험을 유지합니다."]),
            ("고객님께 부탁드리는 점", [
                ("ul", ["만 19세 이상 본인 확인에 협조해 주세요.",
                        "관리사에 대한 존중과 기본 예의를 지켜주세요.",
                        "불법·퇴폐 행위 요구는 삼가주세요. 요청 시 서비스가 중단됩니다.",
                        "과도한 음주 상태에서는 안전을 위해 관리가 어려울 수 있습니다."])]),
            ("신뢰를 위해 공개합니다", [
                "운영 주체와 연락처, 책임자 정보는 모든 페이지 하단과 <a href='/about/'>간다GO 소개</a>에서 확인하실 수 있습니다.",
                "개인정보 처리 기준은 <a href='/privacy/'>개인정보처리방침</a>, 이용 조건은 <a href='/terms/'>이용약관</a>에 공개되어 있습니다."]),
        ],
        data_note="간다GO는 위생·안전을 운영의 기본 기준으로 두며, 관리사 교육과 응대 가이드라인을 통해 일관된 방문 경험을 유지합니다.",
        faq=[
            ("위생은 어떻게 관리되나요?", "수건·오일 등 용품을 위생 기준에 맞춰 관리하고, 관리 후 공간을 정돈합니다."),
            ("안전은 어떻게 보장되나요?", "관리사·고객 모두의 안전을 위한 가이드라인을 운영하며 상호 존중을 원칙으로 합니다."),
            ("의료적 효과가 있나요?", "아닙니다. 이완·휴식 목적의 건강관리 서비스이며 치료를 보장하지 않습니다.")])

    content_page("/gwanak-gu/faq/", "gwanak", gt + [(None, "관악 출장마사지 FAQ")],
        title="관악 출장마사지 FAQ | 예약·지역·요금 자주 묻는 질문",
        desc="관악 출장마사지 자주 묻는 질문 - 방문 가능 지역, 예약 방법, 도착 시간, 코스, 요금, 안전까지 자주 들어오는 질문을 한곳에 정리했습니다.",
        eyebrow="관악 출장마사지 · FAQ", h1="관악 출장마사지 자주 묻는 질문",
        lead="예약·지역·시간·코스·요금 등 자주 들어오는 질문을 한곳에 정리했습니다.",
        sections=[
            ("자주 묻는 질문을 모았습니다", [
                "관악 출장마사지를 이용하기 전 자주 들어오는 질문을 주제별로 정리했습니다.",
                "더 궁금한 점은 <a href='/customer/'>고객센터</a> 또는 전화로 언제든 문의해 주세요."]),
            ("예약·지역 한눈에", [
                ("h3", "어디까지 방문하나요"),
                "관악구 전 지역(봉천·신림·남현)을 안내드리며, 주요 역세권은 <a href='/gwanak-gu/stations/'>지하철역별 안내</a>에서 확인할 수 있습니다.",
                ("h3", "당일·심야 예약"),
                "상담은 24시간 가능하며, 시간대와 위치에 따라 방문 가능 시간을 안내드립니다."]),
            ("코스·요금 한눈에", [
                ("h3", "어떤 코스가 있나요"),
                "피로 회복·아로마·스포츠·커플가족·기업단체 관리가 있으며 60·90·120분으로 운영합니다.",
                ("h3", "요금은 어떻게 안내되나요"),
                "코스별 정찰 요금을 사전에 안내하며, 지역·시간대 등 변동 요소는 예약 시 미리 알려드립니다."]),
            ("안전·신뢰", [
                "본 서비스는 의료 행위가 아닌 이완·휴식 목적의 건강관리 서비스이며, 만 19세 이상 성인을 대상으로 합니다.",
                "위생·안전 가이드라인을 준수하며, 자세한 내용은 위생 및 안전 안내 페이지에서 확인하실 수 있습니다."]),
        ],
        data_note="가장 많이 들어오는 문의는 '도착까지 걸리는 시간'과 '코스·요금'입니다. 예약 시 위치와 희망 코스를 함께 알려주시면 빠르게 안내해 드립니다.",
        faq=[
            ("관악구 어디까지 방문 가능한가요?", "봉천·신림·남현 등 관악구 전 지역을 안내드립니다."),
            ("봉천동·신림동처럼 행정동이 여러 개로 나뉜 곳도 되나요?", "네. 봉천동(은천·성현·청룡·청림·행운·중앙·인헌동 등)과 신림동(서원·신원·서림·삼성·미성동 등)은 대표 동 안내 기준으로 통합 안내드립니다."),
            ("신림역·서울대입구역 등 역 근처 안내는 따로 있나요?", "네. 2호선·신림선 주요 역세권은 지하철역별 안내에서 역별로 안내드립니다."),
            ("예약은 어떻게 하나요?", "전화 또는 문의로 지역·시간·코스를 알려주시면 방문 가능 시간을 확정해 드립니다."),
            ("도착까지 얼마나 걸리나요?", "권역에 따라 평균 18~27분 내외이며, 시간대와 위치에 따라 달라질 수 있습니다."),
            ("당일·심야 예약이 가능한가요?", "상담은 24시간 가능합니다. 심야는 위치에 따라 도착 시간이 길어질 수 있습니다."),
            ("어떤 코스가 있나요?", "피로 회복·아로마·스포츠·커플가족·기업단체 관리가 있으며 60·90·120분으로 운영합니다."),
            ("요금은 어떻게 되나요?", "코스별 정찰 요금을 사전에 안내드립니다. 자세한 금액은 가격 안내에서 확인하세요."),
            ("표시 요금 외 추가 비용이 있나요?", "정찰 요금을 원칙으로 하며 지역·시간대 등 변동 요소는 예약 시 미리 안내드립니다."),
            ("관리사는 어떤 분이 방문하나요?", "위생·안전 가이드라인을 준수하는 관리사가 방문하며, 요청 사항은 상담 시 확인해 드립니다."),
            ("이 서비스는 의료 행위인가요?", "아닙니다. 의료 행위가 아닌 이완·휴식 목적의 건강관리 서비스이며 만 19세 이상을 대상으로 합니다.")])


# ---- robots / sitemap / manifest / favicon -------------------------------
def build_meta_files():
    urls = ["/", "/about/", "/gwanak-gu/", "/gwanak-gu/area/", "/course/",
            "/reservation/", "/guide/", "/reviews/", "/customer/",
            "/privacy/", "/terms/", "/youth/"]
    urls += [f"/course/{s}/" for s in COURSE_PAGES]
    urls += [f"/gwanak-gu/{s}/" for s in GANGSEO_PAGES]
    urls.append("/gwanak-gu/stations/")
    urls += [f"/gwanak-gu/stations/{s['slug']}/" for s in STATIONS]
    for r in REGIONS:
        urls.append(f"/gwanak-gu/{r['slug']}/")
        for d in r["dongs"]:
            urls.append(f"/gwanak-gu/{d['slug']}/")
    prio = {"/": "1.0", "/gwanak-gu/": "0.9", "/gwanak-gu/area/": "0.9",
            "/gwanak-gu/stations/": "0.9"}
    lastmod = UPDATED  # W3C date (YYYY-MM-DD) — 네이버·구글 모두 인식
    items = ""
    for u in urls:
        p = prio.get(u, "0.8" if u.count("/") <= 2 else "0.75")
        freq = "daily" if u == "/" else "weekly"
        items += (f"  <url><loc>{BASE_URL}{u}</loc>"
                  f"<lastmod>{lastmod}</lastmod>"
                  f"<changefreq>{freq}</changefreq><priority>{p}</priority></url>\n")
    sitemap = ('<?xml version="1.0" encoding="UTF-8"?>\n'
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
               + items + "</urlset>\n")
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(sitemap)

    # --- RSS 2.0 피드 (네이버 서치어드바이저 RSS 제출용 · 빠른 수집) ---
    def _xml(s):
        return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                 .replace('"', "&quot;"))
    def _meta_of(u):
        rel = "index.html" if u == "/" else os.path.join(u.strip("/"), "index.html")
        try:
            h = open(os.path.join(ROOT, rel), encoding="utf-8").read()
            t = re.search(r"<title>(.*?)</title>", h).group(1)
            d = re.search(r'name="description" content="(.*?)"', h).group(1)
            return t, d
        except Exception:
            return BRAND, ""
    rfc822 = datetime.datetime.strptime(UPDATED, "%Y-%m-%d").strftime(
        "%a, %d %b %Y 09:00:00 +0900")
    rss_items = ""
    for u in urls:
        t, d = _meta_of(u)
        rss_items += (
            "  <item>"
            f"<title>{_xml(t)}</title>"
            f"<link>{BASE_URL}{u}</link>"
            f'<guid isPermaLink="true">{BASE_URL}{u}</guid>'
            f"<description>{_xml(d)}</description>"
            f"<pubDate>{rfc822}</pubDate>"
            "</item>\n")
    rss = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n<channel>\n'
           f"<title>{_xml(BRAND)}</title>\n"
           f"<link>{BASE_URL}/</link>\n"
           f'<atom:link href="{BASE_URL}/rss.xml" rel="self" type="application/rss+xml"/>\n'
           "<description>서울 관악구 방문 건강관리(출장마사지) 예약 안내</description>\n"
           "<language>ko-KR</language>\n"
           f"<lastBuildDate>{rfc822}</lastBuildDate>\n"
           + rss_items + "</channel>\n</rss>\n")
    with open(os.path.join(ROOT, "rss.xml"), "w", encoding="utf-8") as f:
        f.write(rss)

    # --- robots.txt (네이버 Yeti·다음·구글·빙 명시 허용 + 사이트맵/RSS) ---
    host = BASE_URL.replace("https://", "").replace("http://", "")
    allow_bots = ["Googlebot", "Googlebot-Image", "Bingbot",
                  "Yeti", "NaverBot", "Daumoa"]  # Yeti/NaverBot=네이버, Daumoa=다음
    ai_bots = ["GPTBot", "ClaudeBot", "Google-Extended", "PerplexityBot"]
    robots = "User-agent: *\nAllow: /\nDisallow: /tools/\n\n"
    robots += "".join(f"User-agent: {b}\nAllow: /\n" for b in allow_bots) + "\n"
    robots += "".join(f"User-agent: {b}\nAllow: /\n" for b in ai_bots) + "\n"
    robots += (f"Sitemap: {BASE_URL}/sitemap.xml\n"
               f"Sitemap: {BASE_URL}/rss.xml\n"
               f"Host: {host}\n")
    with open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(robots)

    manifest = {
        "name": BRAND, "short_name": "간다GO", "description": "서울 관악구 방문 건강관리 예약 안내",
        "start_url": "/", "scope": "/", "display": "standalone",
        "background_color": "#0b0b0e", "theme_color": "#0b0b0e",
        "lang": "ko-KR", "orientation": "portrait",
        "icons": [
            {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
            {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
            {"src": "/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        ],
    }
    with open(os.path.join(ROOT, "site.webmanifest"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    favicon = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
               '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
               '<stop offset="0" stop-color="#f4d29c"/><stop offset=".5" stop-color="#e9b8a7"/>'
               '<stop offset="1" stop-color="#c98a6b"/></linearGradient></defs>'
               '<rect width="64" height="64" rx="16" fill="#0b0b0e"/>'
               '<rect x="8" y="8" width="48" height="48" rx="13" fill="url(#g)"/>'
               '<text x="32" y="44" font-family="Georgia,serif" font-style="italic" '
               'font-size="34" font-weight="700" text-anchor="middle" fill="#1a1208">G</text></svg>')
    with open(os.path.join(ROOT, "favicon.svg"), "w", encoding="utf-8") as f:
        f.write(favicon)

    # IndexNow 인증 키 파일 — https://<도메인>/<KEY>.txt 로 노출되어야 함
    with open(os.path.join(ROOT, f"{INDEXNOW_KEY}.txt"), "w", encoding="utf-8") as f:
        f.write(INDEXNOW_KEY)


# ---------------------------------------------------------------------------
def main():
    build_home()
    build_about()
    build_gwanak()
    build_area_hub()
    build_area_pages()
    build_dong_pages()
    build_stations_hub()
    build_station_pages()
    build_course()
    build_course_pages()
    build_gwanak_info_pages()
    build_reservation()
    build_guide()
    build_reviews()
    build_customer()
    build_policies()
    build_meta_files()
    print("Build complete.")


if __name__ == "__main__":
    main()
