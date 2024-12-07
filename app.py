from flask import Flask, request, jsonify, render_template
import googlemaps
import os

app = Flask(__name__)

# Google Maps API 키 설정 (환경 변수에서 가져오기)
API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
gmaps = googlemaps.Client(key=API_KEY)

def get_reviews(place_id):
    """Google Places API에서 리뷰를 가져와 장점과 단점을 추출하는 함수"""
    details = gmaps.place(place_id=place_id, fields=['reviews'])
    reviews = details['result'].get('reviews', [])
    
    pros, cons = [], []
    for review in reviews[:5]:
        text = review.get('text', '')
        if 'good' in text.lower() or 'great' in text.lower():
            pros.append(text)
        if 'bad' in text.lower() or 'slow' in text.lower():
            cons.append(text)
    
    return pros[:2], cons[:2]

@app.route('/')
def home():
    """홈 페이지 렌더링"""
    return render_template('index.html')

@app.route('/recommend', methods=['GET'])
def recommend():
    """맛집 추천 API 엔드포인트"""
    location = request.args.get('location')
    keyword = request.args.get('keyword')
    
    if not location or not keyword:
        return jsonify({"error": "location and keyword parameters are required"}), 400
    
    try:
        places_result = gmaps.places(query=keyword, location=location, radius=1000)
        
        restaurants = []
        for place in places_result.get('results', [])[:5]:
            place_id = place['place_id']
            details = gmaps.place(place_id=place_id, fields=['name', 'formatted_address', 'rating', 'user_ratings_total'])
            
            pros, cons = get_reviews(place_id)
            name = details['result'].get('name', '정보 없음')
            address = details['result'].get('formatted_address', '정보 없음')
            rating = details['result'].get('rating', 'N/A')
            reviews_total = details['result'].get('user_ratings_total', 0)

            restaurant = {
                '가게 이름': name,
                '주소': address,
                '평점': f"{rating} ({reviews_total} 리뷰)",
                '장점': pros,
                '단점': cons
            }
            restaurants.append(restaurant)
        
        return jsonify(restaurants)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
