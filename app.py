from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import urllib.request
import urllib.parse
import ssl
import random

app = Flask(__name__)


@app.route("/", methods=["GET"])
def home():
    return "Server is running."


# 1. 랜덤 숫자 테스트
@app.route("/text", methods=["GET", "POST"])
def text_skill():
    response = {
        "version": "2.0",
        "template": {
            "outputs": [{
                "simpleText": {
                    "text": str(random.randint(1, 10))
                }
            }]
        }
    }
    return jsonify(response)


# 2. 이미지 테스트
@app.route("/image", methods=["GET", "POST"])
def image_skill():
    response = {
        "version": "2.0",
        "template": {
            "outputs": [{
                "simpleImage": {
                    "imageUrl": "https://t1.daumcdn.net/friends/prod/category/M001_friends_ryan2.jpg",
                    "altText": "hello I'm Ryan"
                }
            }]
        }
    }
    return jsonify(response)


# 3. 사용자가 보낸 발화를 그대로 돌려주기
@app.route("/echo", methods=["POST"])
def echo_skill():
    data = request.get_json(silent=True) or {}
    user_input = data.get("userRequest", {}).get("utterance", "입력값이 없습니다.")

    response = {
        "version": "2.0",
        "template": {
            "outputs": [{
                "simpleText": {
                    "text": user_input
                }
            }]
        }
    }
    return jsonify(response)


# 4. 발화 내용을 네이버 뉴스에서 검색해서 제목 크롤링

@app.route("/naver-news", methods=["POST"])
def naver_news_skill():
    data = request.get_json(silent=True) or {}
    # 발화 추출
    user_input = data.get("userRequest", {}).get("utterance", "").strip()
    
    # "AI" 등의 짧은 단어에서 공백 제거
    search_query = user_input.replace(" ", "")

    if not search_query:
        return jsonify({"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "검색어를 입력해주세요."}}]}})

    url = "https://search.naver.com/search.naver"
    
    # 중요: 브라우저인 척 하기 위해 헤더 보강
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://www.naver.com"
    }
    
    params = {
        "where": "news",
        "query": search_query,
        "sm": "tab_pge",
        "sort": "0" # 관련도순
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=5)
        # 만약 네이버에서 차단했다면 status_code가 200이 아님
        if response.status_code != 200:
            return jsonify({"version": "2.0", "template": {"outputs": [{"simpleText": {"text": f"네이버 접속 실패 (코드: {response.status_code})"}}]}})

        soup = BeautifulSoup(response.text, "html.parser")
        
        # 최신 네이버 뉴스 제목 클래스는 .news_tit 입니다.
        # 만약 이게 안 잡히면 .news_area 내의 a태그를 시도합니다.
        items = soup.select(".news_tit")

        titles = []
        for item in items[:5]:
            title_text = item.get_text(strip=True)
            titles.append(title_text)

        if titles:
            result_text = f"'{search_query}' 뉴스 검색 결과입니다.\n\n"
            result_text += "\n".join([f"{i+1}. {t}" for i, t in enumerate(titles)])
        else:
            # 검색 결과가 없는 게 아니라 '제목' 요소를 못 찾은 경우일 수 있음
            result_text = f"검색 결과 요소를 찾을 수 없습니다. (입력값: {search_query})"

    except Exception as e:
        result_text = f"서버 오류 발생: {str(e)}"

    return jsonify({
        "version": "2.0",
        "template": {
            "outputs": [{"simpleText": {"text": result_text[:1000]}}]
        }
    })


# 5. 울산 날씨 크롤링
@app.route("/ulsan-weather", methods=["GET", "POST"])
def ulsan_weather_skill():
    try:
        context = ssl._create_unverified_context()
        url = "https://search.naver.com/search.naver?query=%EC%9A%B8%EC%82%B0%20%EB%82%A0%EC%94%A8"

        webpage = urllib.request.urlopen(url, context=context)
        soup = BeautifulSoup(webpage, "html.parser")

        temps = soup.find("div", class_="temperature_text")
        summary = soup.find("p", class_="summary")

        if temps and summary:
            result_text = "울산 " + temps.get_text(strip=True) + " " + summary.get_text(strip=True)
        else:
            result_text = "날씨 정보를 가져오지 못했습니다."

    except Exception as e:
        result_text = f"날씨 조회 중 오류가 발생했습니다: {str(e)}"

    response = {
        "version": "2.0",
        "template": {
            "outputs": [{
                "simpleText": {
                    "text": result_text[:1000]
                }
            }]
        }
    }
    return jsonify(response)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

