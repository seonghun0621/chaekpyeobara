# -*- coding: utf-8 -*-
"""Untitled3.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1uhzqdVLIgx-RNuF9vtIOqQr0crUY1g7W
"""

import streamlit as st
import requests
import re
import json
import openai
from datetime import datetime
import random
    
# 알라딘 API 인증키
TTB_KEY = "ttbtmdwn021442001"

#도서관 정보나루 API 인증키
LIB_KEY = "661a88b506497d2578c01548eb504b824b8fe475c0d9a08379b712caf9577067"


# 책 검색 함수
def search_book(book_title):
    search_url = "http://www.aladin.co.kr/ttb/api/ItemSearch.aspx"
    params = {
        "ttbkey": TTB_KEY,
        "Query": book_title,
        "QueryType": "Title",
        "MaxResults": 1,
        "SearchTarget": "Book",
        "output": "js",
        "Version": "20131101"
    }
    response = requests.get(search_url, params=params)
    data = response.json()

    if "item" in data and len(data["item"]) > 0:
        book = data["item"][0]
        book_info = {
            "title": book.get("title", "제목 정보 없음"),
            "author": book.get("author", "저자 정보 없음"),
            "publisher": book.get("publisher", "출판사 정보 없음"),
            "price": book.get("priceStandard", "가격 정보 없음"),
            "isbn": book.get("isbn13", None)
        }

        if book_info["isbn"]:
            lookup_url = "http://www.aladin.co.kr/ttb/api/ItemLookUp.aspx"
            lookup_params = {
                "ttbkey": TTB_KEY,
                "itemIdType": "ISBN",
                "ItemId": book_info["isbn"],
                "output": "js",
                "Version": "20131101"
            }
            lookup_response = requests.get(lookup_url, params=lookup_params)
            lookup_data = lookup_response.json()

            if "item" in lookup_data and len(lookup_data["item"]) > 0:
                details = lookup_data["item"][0]
                book_info["page_count"] = details.get("subInfo", {}).get("itemPage", "쪽수 정보 없음")
            else:
                book_info["page_count"] = "쪽수 정보 없음"
        else:
            book_info["page_count"] = "쪽수 정보 없음"

        return book_info
    else:
        return {"error": "책 정보를 찾을 수 없습니다. 다시 시도해주세요."}

# 목표 읽기 계획 생성 함수
def calculate_daily_pages(total_pages, target_days):
    try:
        daily_pages = total_pages // target_days
        remaining_pages = total_pages % target_days
        return daily_pages, remaining_pages
    except ZeroDivisionError:
        return 0, 0

# 목표를 재조정하는 함수
def recalculate_goal_dynamic(remaining_pages, pages_read_today, remaining_days):
    remaining_pages -= pages_read_today
    if remaining_pages <= 0:
        return remaining_pages, 0, 0, "책을 다 읽었어요!"
    
    new_daily_goal = remaining_pages // remaining_days
    remaining_days -= 1
    
    return remaining_pages, new_daily_goal, remaining_days, f"남은 목표 일수는 {remaining_days}일이에요."
    
# 목표 저장하기
def save_goal(book_title, target_days, daily_pages, remaining_pages):
    goal_data = {
        "book_title": book_title,
        "target_days": target_days,
        "daily_pages": daily_pages,
        "remaining_pages": remaining_pages,
        "date_completed": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    try:
        with open("reading_goals.json", "a", encoding="utf-8") as file:
            existing_data = load_goals()
            existing_data.append(goal_data)
            with open("reading_goals.json", "w", encoding="utf-8") as write_file:
                json.dump(existing_data, write_file, ensure_ascii=False, indent=4)
            st.write("📂 목표가 성공적으로 저장되었습니다!")
    except Exception as e:
        st.write(f"저장 중 오류 발생: {e}")

def load_goals():
    try:
        with open("reading_goals.json", "r", encoding="utf-8") as file:
            goals = json.load(file)
            if isinstance(goals, list):
                return goals
            else:
                return []
    except Exception as e:
        st.write(f"목표 불러오기 중 오류 발생: {e}")
        return []

def initialize_file():
    try:
        with open("reading_goals.json", "r", encoding="utf-8") as file:
            pass
    except FileNotFoundError:
        with open("reading_goals.json", "w", encoding="utf-8") as file:
            json.dump([], file, ensure_ascii=False, indent=4)

initialize_file()

def give_challenge(book_title):
    st.write(f"🎯 **{book_title}** 책을 다 읽은 것을 축하드려요! 🦦")
    st.write("새로운 도전 과제를 제공합니다!")
    st.write("다음 도전은 무엇인가요? 다시 목표를 설정해볼까요? 🐾")

st.set_page_config(page_title="책펴바라 - 숲속 도서관", layout="wide")
st.title("책펴바라 숲속 도서관에 오신 것을 환영합니다! 🦦📚")

tab1, tab2, tab3, tab4 = st.tabs(["책 검색 및 목표 설정", "독서 감상문 쓰기", "독서 감상 주고받기", "책 추천받기"])

import time

with tab1:
    book_title = st.text_input("검색할 책 제목을 입력하세요:")

    if book_title:
        book_info = search_book(book_title)

        if "error" not in book_info:
            st.write(f"책 이름: **'{book_info['title']}'**")
            st.write(f"지은이: **{book_info['author']}**")
            st.write(f"출판사: **{book_info['publisher']}**")
            st.write(f"가격: **{book_info['price']}원**")
            st.write(f"쪽수: **{book_info['page_count']}쪽**")
        else:
            st.write(book_info["error"])

        target_days_input = st.text_input("\n목표 읽기 기간(일)을 입력해주세요:")
        if target_days_input:
            target_days = int(re.sub(r'\D', '', target_days_input))
            daily_pages, remaining_pages = calculate_daily_pages(int(book_info["page_count"]), target_days)

            st.write(f"하루에 **{daily_pages}쪽**씩 읽으면 됩니다.")
            if remaining_pages > 0:
                st.write(f"마지막 날 추가로 읽어야 할 페이지: **{remaining_pages}쪽**")
            st.write("오늘부터 시작해볼까요?")

            total_pages = int(book_info["page_count"])
            remaining_pages = total_pages
            remaining_days = target_days

            # 반복문으로 책을 다 읽을 때까지 진행
            while remaining_pages > 0:
                # 고유한 key 생성: time 값을 추가하여 고유한 key를 생성
                key = f"pages_read_{remaining_pages}_{remaining_days}_{int(time.time())}"
                pages_read_today = st.number_input(
                    f"오늘 읽은 페이지 수를 입력해주세요 (남은 페이지: {remaining_pages}):", 
                    min_value=0, 
                    max_value=remaining_pages,
                    key=key
                )

                if pages_read_today > 0:
                    remaining_pages, new_daily_goal, remaining_days, status = recalculate_goal_dynamic(remaining_pages, pages_read_today, remaining_days)

                    if remaining_pages == 0:
                        st.write("우와~! 🦦 책을 다 읽었어요! 🎉")
                        save_goal(book_info['title'], target_days, daily_pages, remaining_pages)
                        give_challenge(book_info['title'])
                        break
                    else:
                        st.write(f"남은 페이지: {remaining_pages}쪽")
                        st.write(f"내일부터 하루 목표는 {new_daily_goal}쪽입니다.")
                        st.write(f"남은 목표 일수: {remaining_days}일")
        else:
            st.write("목표 읽기 기간을 입력해 주세요!")

        st.write("📅 지난 목표 확인하기:")
        goals = load_goals()

        if goals:
            for goal in goals:
                st.write(f"📖 책 제목: {goal['book_title']}")
                st.write(f"📅 목표 기간: {goal['target_days']}일")
                st.write(f"📘 하루 목표 페이지: {goal['daily_pages']}페이지")
                st.write(f"📚 남은 페이지: {goal['remaining_pages']}페이지")
                st.write(f"✅ 완료일: {goal['date_completed']}")
                st.write("---")
        else:
            st.write("저장된 목표가 없습니다.")
            
# 목표 불러오기
goals = load_goals()  # 여기에 목표를 불러오는 코드가 필요
with tab2:
    st.subheader("📚 새 도전 과제 & 감상문 기록")
    
    # 감상문 작성 기능
    st.write("읽은 책에 대한 감상문을 작성하고 공유해보세요!")
    selected_goal_title = st.selectbox(
    "감상문을 작성할 책을 선택하세요:", 
    [goal['book_title'] for goal in goals] if goals else []
    )
    review_text = st.text_area("감상문을 여기에 작성하세요:", height=200)
    if st.button("감상문 저장하기"):
        if selected_goal_title and review_text.strip():
            try:
                # 감상문 저장
                reviews_file = "reading_reviews.json"
                try:
                    with open(reviews_file, "r", encoding="utf-8") as file:
                        reviews = json.load(file)
                except (FileNotFoundError, json.JSONDecodeError):
                    reviews = []
                
                reviews.append({
                    "book_title": selected_goal_title,
                    "review": review_text,
                    "date_written": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                with open(reviews_file, "w", encoding="utf-8") as file:
                    json.dump(reviews, file, ensure_ascii=False, indent=4)
                st.success("📖 감상문이 저장되었습니다! 잘했어요! 🦦")
            except Exception as e:
                st.error(f"감상문 저장 중 오류가 발생했습니다: {e}")
        else:
            st.warning("책 제목과 감상문을 입력해 주세요!")

    # 저장된 감상문 불러오기
    st.write("📖 내가 작성한 감상문:")
    try:
        with open("reading_reviews.json", "r", encoding="utf-8") as file:
            reviews = json.load(file)
        if reviews:
            for review in reviews:
                st.write(f"📚 책 제목: {review['book_title']}")
                st.write(f"📝 감상문: {review['review']}")
                st.write(f"📅 작성일: {review['date_written']}")
                st.write("---")
        else:
            st.write("작성된 감상문이 없습니다.")
    except (FileNotFoundError, json.JSONDecodeError):
        st.write("작성된 감상문이 없습니다.")

    # 새로운 도전 과제 제공
    st.write("🎯 새로운 도전 과제")
    st.write("읽은 책을 바탕으로 새로운 목표를 설정해보세요!")
    new_challenge_title = st.text_input("새로운 도전 과제를 입력하세요:")
    challenge_deadline = st.date_input("목표 마감일을 설정하세요:")
    if st.button("도전 과제 저장하기"):
        try:
            # 도전 과제 저장
            challenges_file = "reading_challenges.json"
            try:
                with open(challenges_file, "r", encoding="utf-8") as file:
                    challenges = json.load(file)
            except (FileNotFoundError, json.JSONDecodeError):
                challenges = []
            
            challenges.append({
                "challenge": new_challenge_title,
                "deadline": challenge_deadline.strftime("%Y-%m-%d"),
                "date_created": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            with open(challenges_file, "w", encoding="utf-8") as file:
                json.dump(challenges, file, ensure_ascii=False, indent=4)
            st.success("🎯 도전 과제가 저장되었습니다!")
        except Exception as e:
            st.error(f"도전 과제 저장 중 오류가 발생했습니다: {e}")

    # 저장된 도전 과제 불러오기
    st.write("📌 저장된 도전 과제:")
    try:
        with open("reading_challenges.json", "r", encoding="utf-8") as file:
            challenges = json.load(file)
        if challenges:
            for challenge in challenges:
                st.write(f"🔖 도전 과제: {challenge['challenge']}")
                st.write(f"⏳ 마감일: {challenge['deadline']}")
                st.write(f"📅 생성일: {challenge['date_created']}")
                st.write("---")
        else:
            st.write("저장된 도전 과제가 없습니다.")
    except (FileNotFoundError, json.JSONDecodeError):
        st.write("저장된 도전 과제가 없습니다.")

# 알라딘 API 검색 함수 (예시로 간단히 작성)
def search_book(book_title):
    # 여기에 알라딘 API 호출 코드 추가 (예시로 간단한 응답 반환)
    # 실제 API 호출을 구현하려면 해당 API의 문서를 참고하세요.
    try:
        # 예시: 책 정보를 반환 (API를 통해 실제 책 정보를 받아올 부분)
        book_info = {
            "title": book_title,
            "author": "저자명",
            "publisher": "출판사명",
            "price": 20000,
            "isbn": "978-1234567890",
            "description": "책에 대한 간단한 설명"
        }
        return book_info
    except Exception as e:
        return {"error": f"책 정보를 가져오는 데 실패했습니다: {e}"}

# ChatGPT와 대화하는 함수
def chat_with_gpt(book_title, user_feedback):
    prompt = f"책 제목: {book_title}\n감상문: {user_feedback}\nChatGPT에게 질문: 이 책에 대해 어떻게 생각하나요?"
    
    response = openai.Completion.create(
        model="text-davinci-003",  # 또는 사용하고자 하는 모델
        prompt=prompt,
        max_tokens=100
    )
    
    return response.choices[0].text.strip()

import openai
api_key = st.secrets["general"]["open_api_key"]
openai.api_key = "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"
    
# 탭 3 - 알라딘 API와 ChatGPT 통합
with tab3:
    st.subheader("🤖 책 정보 검색 & ChatGPT와 대화")

    # 사용자 입력
    book_title = st.text_input("📚 책 제목을 입력하세요:")
    user_feedback = st.text_area("✍️ 이 책에 대한 감상을 입력하세요:")

    if st.button("🔍 책 검색 및 대화 시작"):
        if book_title.strip() == "":
            st.warning("책 제목을 입력해주세요!")
        elif user_feedback.strip() == "":
            st.warning("책에 대한 감상을 입력해주세요!")
        else:
            try:
                # 알라딘 API를 통해 책 정보 가져오기
                book_info = search_book(book_title)

                if "error" in book_info:
                    st.error(book_info["error"])
                else:
                    # 책 정보 출력
                    st.write("📖 **책 정보**")
                    st.write(f"- **제목:** {book_info['title']}")
                    st.write(f"- **저자:** {book_info['author']}")
                    st.write(f"- **출판사:** {book_info['publisher']}")
                    st.write(f"- **가격:** {book_info['price']}원")
                    st.write(f"- **ISBN:** {book_info['isbn']}")
                    st.write(f"- **줄거리:** {book_info['description']}")

                    # JSON 파일 저장
                    with open("book_info.json", "w", encoding="utf-8") as file:
                        json.dump(book_info, file, ensure_ascii=False, indent=4)
                    st.success("📂 책 정보를 'book_info.json'에 저장했습니다!")

                    # ChatGPT와 대화 시작
                    gpt_response = chat_with_gpt(book_title, user_feedback)
                    st.write("🤖 **ChatGPT의 대답**")
                    st.write(gpt_response)

            except Exception as e:
                st.error(f"오류 발생: {e}")




# 탭 4 - 책 추천받기
with tab4:
    st.subheader("🦫 책펴바라에게 책 추천받기 📖")

#사용자 입력받기
gender = st.selectbox("성별을 선택하세요", ["남성", "여성", "미상"])
age = st.selectbox("나이를 선택하세요", ["영유아", "유아", "초등", "청소년", "20대", "30대", "40대", "50대", "60세 이상", "미상"])
major_topic = st.selectbox("관심 대주제를 선택하세요", ["총류", "철학", "종교", "사회과학", "자연과학", "기술과학", "예술", "언어", "문학", "역사"])
region = st.selectbox("지역을 선택하세요", ["서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종", "경기", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"])

# 코드 매핑
gender_map = {"남성": 0, "여성": 1, "미상": 2}
age_map = {"영유아": 0, "유아": 6, "초등": 8, "청소년": 14, "20대": 20, "30대": 30, "40대": 40, "50대": 50, "60세 이상": 60, "미상": -1}
major_topic_map = {"총류": 0, "철학": 1, "종교": 2, "사회과학": 3, "자연과학": 4, "기술과학": 5, "예술": 6, "언어": 7, "문학": 8, "역사": 9}
region_map = {"서울": 11, "부산": 21, "대구": 22, "인천": 23, "광주": 24, "대전": 25, "울산": 26, "세종": 29, "경기": 31, "강원": 32, "충북": 33, "충남": 34, "전북": 35, "전남": 36, "경북": 37, "경남": 38, "제주": 39}

# 변환
selected_gender = gender_map[gender]
selected_age = age_map[age]
selected_major_topic = major_topic_map[major_topic]
selected_region = region_map[region]

#API 호출
def fetch_books(api_key, gender, age, region, major_topic):
    url = "http://data4library.kr/api/loanItemSrchByLib"
    params = {
        "authKey": LIB_KEY,
        "gender": gender,
        "age": age,
        "region": region,
        "kdc": major_topic,
        "format": "json",
        "pageSize": 100
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json().get("docs", [])
    else:
        st.error(f"API 호출 실패: {response.status_code}")
        return []

#추천도서 랜덤 3권 선택
def recommend_books(books):
    if len(books) == 0:
        st.warning("조건에 맞는 도서를 찾지 못했습니다.")
        return []

    # 랜덤으로 3권 선택
    return random.sample(books, min(3, len(books)))

def generate_recommendation_reason(selected_books):
    titles = ", ".join([book["bookname"] for book in selected_books])
    prompt = f"""
    사용자가 선택한 조건에 맞는 도서 '{titles}'를 추천합니다.
    각 도서가 왜 추천되었는지 간단히 설명해주세요.
    """
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        max_tokens=300
    )
    return response.choices[0].text.strip()

if st.button("책 추천받기"):
    # API 호출
    books = fetch_books("LIB_KEY", selected_gender, selected_age, selected_region, selected_major_topic)

    # 추천 도서 선택
    selected_books = recommend_books(books)

    # 추천 도서 출력
    if selected_books:
        st.write("추천 도서 목록:")
        for book in selected_books:
            st.write(f"- **{book['bookname']}**")
            st.write(f"  저자: {book['authors']}, 출판사: {book['publisher']}, 출판년도: {book['publication_year']}")
            st.write(f"[상세 페이지]({book['bookDtlUrl']})")
            st.markdown("---")

        # 추천 이유 생성
        reason = generate_recommendation_reason(selected_books)
        st.write("**추천 이유:**")
        st.write(reason)
