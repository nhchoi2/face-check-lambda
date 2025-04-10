import json
import boto3

def lambda_handler(event, context):
    rekognition = boto3.client('rekognition')

    # 예시: S3 버킷 + 이미지 파일 이름 하드코딩 (테스트용)
    bucket = "your-bucket-name"
    image_key = "test.jpg"  # 버킷에 미리 올려둔 이미지

    try:
        response = rekognition.detect_faces(
            Image={
                'S3Object': {
                    'Bucket': 'nhchoi-posting',
                    'Name': '증명사진.png'
                }
            },
            Attributes=['ALL']
        )
        return {
            'statusCode': 200,
            'body': json.dumps(response['FaceDetails'])
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(str(e))
        }
