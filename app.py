from flask import Flask, request, jsonify
from flask_cors import CORS  # CORS 추가
import googlemaps
import os
import html
import logging

app = Flask(__name__)

# CORS 설정: 특정 Origin만 허용 (예: 프론트엔드 도메인)
CORS(app)

# 로깅 설정 (DEBUG 레벨로 설정)
logging.basicConfig(level=logging.DEBUG)

@app.route('/test', methods=['GET'])
def test():
    return jsonify({"message": "CORS is enabled!"})

# Google Maps API 키 설정 (환경 변수에서 가져오기)
API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
if not API_KEY:
    raise ValueError("GOOGLE_MAPS_API_KEY 환경 변수가 설정되지 않았습니다. .env 파일 또는 시스템 환경 변수에서 API 키를 설정해주세요.")

gmaps = googlemaps.Client(key=API_KEY)

def search_restaurants(location, keyword, radius=1000, max_results=5):
    try:
        # 위치 문자열을 좌표로 변환
        geocode_result = gmaps.geocode(location)
        if not geocode_result:
            return {"error": "Invalid location. Please provide a valid location."}
        
        coordinates = geocode_result[0]['geometry']['location']
        lat_lng = (coordinates['lat'], coordinates['lng'])
        
        # radius 값 제한 (최대 5000 미터)
        radius = min(radius, 5000)

        # Google Places API를 사용해 장소 검색
        logging.debug(f"Searching for '{keyword}' near '{location}' with radius {radius} meters")
        places_result = gmaps.places(query=keyword, location=lat_lng, radius=radius)

        restaurants = []
        for place in places_result.get('results', [])[:max_results]:
            place_id = place['place_id']

            # Google Places API로 장소 세부 정보 가져오기
            details = gmaps.place(
                place_id=place_id,
                fields=['name', 'formatted_address', 'rating', 'user_ratings_total', 'business_status', 'reviews']
            )

            # 영업 상태 확인
            business_status = details['result'].get('business_status', 'UNKNOWN')
            if business_status == 'CLOSED_PERMANENTLY':
                continue  # 영구 폐업인 경우 제외

            # 식당 정보 추출
            name = details['result'].get('name', '정보 없음')
            address = details['result'].get('formatted_address', '정보 없음')
            rating = details['result'].get('rating', 'N/A')
            reviews_total = details['result'].get('user_ratings_total', 0)

            # 리뷰 추출 (장점, 단점, 특성)
            reviews = details['result'].get('reviews', [])
            pros, cons = extract_pros_cons(reviews)
            features = extract_features(reviews)

            restaurant = {
                '가게 이름': name,
                '주소': address,
                '평점': f"{rating} ({reviews_total} 리뷰)",
                '영업 상태': business_status,
                '특성': features[:2],
                '장점': pros[:2],
                '단점': cons[:2]
            }
            restaurants.append(restaurant)

        return restaurants

    except googlemaps.exceptions.ApiError as e:
        logging.error(f"Google Maps API error: {e}")
        return {"error": f"Google Maps API error: {e}", "message": "Google Maps API 호출 중 오류가 발생했습니다. API 키를 확인해 주세요."}
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return {"error": str(e), "message": "알 수 없는 오류가 발생했습니다. 다시 시도해 주세요."}

def extract_pros_cons(reviews):
    """리뷰에서 장점과 단점을 추출하는 함수"""
    pros = []
    cons = []

    positive_keywords = ['good', 'great', 'excellent', 'nice', 'amazing', 'delicious', 'friendly']
    negative_keywords = ['bad', 'poor', 'disappointing', 'terrible', 'rude', 'dirty', 'slow']

    for review in reviews:
        text = review.get('text', '')
        clean_text = html.unescape(text)
        
        if any(word in clean_text.lower() for word in positive_keywords):
            pros.append(clean_text)
        if any(word in clean_text.lower() for word in negative_keywords):
            cons.append(clean_text)

    return pros, cons

def extract_features(reviews):
    """리뷰에서 주요 특성을 추출하는 함수"""
    features = []
    feature_keywords = ['noodle', 'soup', 'pancake', 'dumpling', 'broth', 'service', 'taste']

    for review in reviews:
        text = review.get('text', '')
        clean_text = html.unescape(text)
        
        if any(word in clean_text.lower() for word in feature_keywords):
            features.append(clean_text)

    return features

@app.route('/recommend', methods=['GET'])
def recommend():
    location = request.args.get('location')
    keyword = request.args.get('keyword')

    if not location or not keyword:
        return jsonify({"error": "location and keyword parameters are required", "message": "위치와 키워드를 모두 입력해 주세요."}), 400

    results = search_restaurants(location, keyword)
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
