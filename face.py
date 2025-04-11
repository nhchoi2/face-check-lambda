from flask import Flask, request, jsonify  # Flask 모듈과 요청/응답 도구 임포트
import boto3  # AWS 서비스와 연동하는 boto3 라이브러리
import os
import uuid  # 고유한 파일명을 만들기 위한 유니크 ID 생성용

app = Flask(__name__)  # Flask 애플리케이션 인스턴스 생성

# AWS 클라이언트 설정
# S3와 Rekognition 서비스를 사용할 수 있도록 boto3 클라이언트 생성
s3 = boto3.client('s3')
rekognition = boto3.client('rekognition')

# S3에 업로드할 버킷 이름 (사용자가 생성한 버킷)
BUCKET_NAME = 'nhchoi-posting'

@app.route('/analyze-face', methods=['POST'])  # POST 요청을 처리할 API 엔드포인트 정의
def analyze_face():
    # 요청 내에 'image' 파일이 포함되어 있는지 확인
    if 'image' not in request.files:
        return jsonify({'error': 'No image file uploaded'}), 400

    # 업로드된 이미지 파일 객체 가져오기
    image_file = request.files['image']
    
    # 중복 방지를 위해 고유한 이름 생성 (UUID + 원래 파일명 조합)
    file_name = f"{uuid.uuid4().hex}_{image_file.filename}"
    
    # 이미지 파일을 S3에 업로드
    s3.upload_fileobj(image_file, BUCKET_NAME, file_name)

    # 업로드된 이미지에 대해 Rekognition의 얼굴 감지 기능 호출
    response = rekognition.detect_faces(
        Image={'S3Object': {'Bucket': BUCKET_NAME, 'Name': file_name}},  
        Attributes=['ALL']  # 얼굴의 세부 속성까지 모두 분석 요청
    )
    

    # 분석 결과를 JSON 형식으로 반환
    return jsonify(response)


@app.route('/compare-faces', methods=['POST'])
def compare_faces():
    # 두 개의 이미지를 요청에서 받음
    source_image = request.files.get('source')
    target_image = request.files.get('target')
    
    if not source_image or not target_image:
        return jsonify({'error': 'source와 target 이미지를 모두 업로드해야 합니다.'}), 400

    # 각각 S3에 업로드 (임시 파일명 부여)
    source_key = f"{uuid.uuid4().hex}_{source_image.filename}"
    target_key = f"{uuid.uuid4().hex}_{target_image.filename}"
    s3.upload_fileobj(source_image, BUCKET_NAME, source_key)
    s3.upload_fileobj(target_image, BUCKET_NAME, target_key)

    # Rekognition 비교 수행
    response = rekognition.compare_faces(
        SourceImage={'S3Object': {'Bucket': BUCKET_NAME, 'Name': source_key}},
        TargetImage={'S3Object': {'Bucket': BUCKET_NAME, 'Name': target_key}},
        SimilarityThreshold=0  # 유사도 기준
    )

    results = []
    for face_match in response.get('FaceMatches', []):
        similarity = face_match['Similarity']
        confidence = face_match['Face']['Confidence']
        results.append({
            '유사도(%)': round(similarity, 2),
            '신뢰도(%)': round(confidence, 2)
        })

    if not results:
        return jsonify({'결과': '유사한 얼굴이 감지되지 않았습니다.'})

    return jsonify({'비교결과': results})


if __name__ == '__main__':
    app.run(debug=True)

