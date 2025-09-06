# PDF Chat with Gemini AI

PDF 문서를 업로드하고 Gemini AI와 대화할 수 있는 웹 애플리케이션입니다.

## 🚀 주요 기능

- **PDF 업로드**: 드래그 앤 드롭 또는 클릭으로 PDF 파일 업로드
- **AI 채팅**: 업로드된 PDF 내용에 대해 Gemini AI와 실시간 대화
- **반응형 디자인**: 모바일과 데스크톱에서 모두 사용 가능
- **세션 관리**: 업로드된 PDF 정보를 세션에 저장하여 지속적인 대화 가능

## 📋 요구사항

- Python 3.7 이상
- Google Gemini API 키

## 🛠️ 설치 및 설정

### 1. 저장소 클론
```bash
git clone <repository-url>
cd pdf-chat-app
```

### 2. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. Gemini API 키 설정

1. [Google AI Studio](https://makersuite.google.com/app/apikey)에서 API 키를 발급받으세요.
2. `pdf_chat_app.py` 파일에서 다음 줄을 수정하세요:
```python
GOOGLE_API_KEY = 'your-gemini-api-key-here'  # 실제 API 키로 변경
```

### 5. 애플리케이션 실행
```bash
python pdf_chat_app.py
```

브라우저에서 `http://localhost:5000`으로 접속하세요.

## 📖 사용법

### 1. PDF 업로드
- 왼쪽 패널의 업로드 영역을 클릭하거나 PDF 파일을 드래그하여 업로드
- 지원 형식: PDF 파일만

### 2. AI와 대화
- PDF 업로드 후 오른쪽 채팅 패널에서 질문 입력
- Enter 키 또는 전송 버튼으로 질문 전송
- AI가 PDF 내용을 바탕으로 답변 제공

### 3. 세션 관리
- "세션 초기화" 버튼으로 현재 PDF 정보 삭제
- 새로운 PDF 업로드 가능

## 🏗️ 프로젝트 구조

```
pdf-chat-app/
├── pdf_chat_app.py      # Flask 애플리케이션 메인 파일
├── templates/
│   └── index.html       # 웹 인터페이스 템플릿
├── requirements.txt     # Python 의존성 목록
└── README.md           # 프로젝트 문서
```

## 🔧 주요 기술 스택

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **PDF 처리**: PyPDF2
- **AI**: Google Gemini API
- **UI/UX**: 반응형 디자인, 드래그 앤 드롭

## 🔒 보안 고려사항

- 실제 배포 시 `app.secret_key`를 안전한 값으로 변경하세요
- API 키는 환경 변수로 관리하는 것을 권장합니다
- 파일 업로드 크기 제한을 설정하는 것을 권장합니다

## 🚀 배포

### 로컬 개발 서버
```bash
python pdf_chat_app.py
```

### 프로덕션 배포
```bash
# Gunicorn 사용 예시
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 pdf_chat_app:app
```

## 🐛 문제 해결

### 일반적인 문제들

1. **API 키 오류**
   - Gemini API 키가 올바르게 설정되었는지 확인
   - API 키의 권한과 할당량 확인

2. **PDF 읽기 오류**
   - PDF 파일이 손상되지 않았는지 확인
   - 텍스트가 포함된 PDF인지 확인 (이미지만 있는 PDF는 처리 불가)

3. **업로드 실패**
   - 파일 크기가 너무 큰지 확인
   - PDF 파일 형식인지 확인

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 지원

문제가 발생하거나 질문이 있으시면 이슈를 생성해주세요.

using bithumb API.

run listasset.py
