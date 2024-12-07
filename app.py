from flask import Flask, request, jsonify
import googlemaps
import os

app = Flask(__name__)

# Google Maps API 키 설정 (환경 변수에서 가져오기)
API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
gmaps = googlemaps.Client(key=API_KEY)

def search_restaurants(location, keyword, radius=1000, max_results=5):
    try:
        # Google Places API를 사용해 장소 검색
        places_result = gmaps.places(query=keyword, location=location, radius=radius)

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

            # 리뷰 추출 (장점과 단점)
            reviews = details['result'].get('reviews', [])
            pros, cons = extract_pros_cons(reviews)

            restaurant = {
                '가게 이름': name,
                '주소': address,
                '평점': f"{rating} ({reviews_total} 리뷰)",
                '영업 상태': business_status,  # 영업 상태 추가
                '장점': pros[:2],  # 최대 2개의 장점
                '단점': cons[:2]   # 최대 2개의 단점
            }
            restaurants.append(restaurant)

        return restaurants

    except Exception as e:
        return {"error": str(e)}

def extract_pros_cons(reviews):
    """리뷰에서 장점과 단점을 추출하는 함수"""
    pros = []
    cons = []

    for review in reviews:
        text = review.get('text', '')
        if 'good' in text.lower() or 'great' in text.lower() or 'excellent' in text.lower() or 'nice' in text.lower():
            pros.append(text)
        if 'bad' in text.lower() or 'poor' in text.lower() or 'disappointing' in text.lower() or 'terrible' in text.lower():
            cons.append(text)

    return pros, cons

@app.route('/recommend', methods=['GET'])
def recommend():
    location = request.args.get('location')
    keyword = request.args.get('keyword')

    if not location or not keyword:
        return jsonify({"error": "location and keyword parameters are required"}), 400

    results = search_restaurants(location, keyword)
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)


