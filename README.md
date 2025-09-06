# SojuCoin - Asset Management Dashboard

비트코인 및 암호화폐 자산 관리를 위한 웹 대시보드입니다. Bithumb API를 활용하여 실시간 가격 정보, 주문 관리, 자동 매도 설정 등의 기능을 제공합니다.

## 🚀 주요 기능

### 📊 자산 관리
- **실시간 자산 현황**: 보유 코인 수량, 평균 매수가, 현재가, 수익률 표시
- **자동 새로고침**: 5초마다 자동으로 데이터 업데이트
- **모바일 최적화**: 반응형 디자인으로 모바일에서도 편리한 사용

### 💰 주문 관리
- **실시간 주문 현황**: 미체결 주문 목록 및 상태 확인
- **주문 취소**: 개별 주문 취소 기능
- **주문 내역**: 매수/매도 주문 히스토리

### 📈 차트 분석
- **실시간 차트**: 5분, 15분, 일봉 차트 제공
- **거래량 분석**: 가격 차트와 함께 거래량 표시
- **다양한 코인 지원**: 20여개 주요 암호화폐 지원

### ⚙️ 자동 매도 설정
- **목표가 설정**: 코인별 매도 목표가 설정
- **수익률 관리**: 목표 수익률 기반 자동 매도
- **실시간 모니터링**: 설정된 목표가 달성 시 알림

## 📋 요구사항

- Python 3.7 이상
- Anaconda 환경 (pytorch3d 환경 권장)
- Bithumb API 접근 권한

## 🛠️ 설치 및 설정

### 1. 저장소 클론
```bash
git clone <repository-url>
cd richcoin
```

### 2. Anaconda 환경 활성화
```bash
conda activate pytorch3d
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 백엔드 서버 실행
```bash
cd backend
python listasset.py
```

### 5. 웹 대시보드 접속
브라우저에서 `http://localhost:8003`으로 접속하세요.

## 📖 사용법

### 1. 자산 현황 확인
- 메인 대시보드에서 보유 코인 현황 확인
- 실시간 가격 정보 및 수익률 모니터링

### 2. 주문 관리
- 미체결 주문 목록에서 주문 상태 확인
- 필요시 개별 주문 취소

### 3. 차트 분석
- "Chart" 버튼을 클릭하여 차트 페이지 이동
- 원하는 코인과 시간대(5분/15분/일봉) 선택
- 가격 추이 및 거래량 분석

### 4. 자동 매도 설정
- 코인별 매도 목표가 설정
- 수익률 기반 자동 매도 활성화/비활성화

## 🏗️ 프로젝트 구조

```
richcoin/
├── backend/
│   ├── listasset.py          # FastAPI 백엔드 서버
│   ├── sell_prices.json      # 매도가 설정 데이터
│   └── profit_rates.json     # 수익률 설정 데이터
├── mycoin/                   # Django 프로젝트 (추가 기능)
├── templates/
│   └── index.html           # 메인 대시보드 템플릿
├── chart.html               # 차트 페이지
├── index.html               # 메인 대시보드
├── requirements.txt         # Python 의존성 목록
└── README.md               # 프로젝트 문서
```

## 🔧 주요 기술 스택

### Backend
- **FastAPI**: 고성능 웹 API 프레임워크
- **Bithumb API**: 실시간 암호화폐 데이터
- **JWT**: 사용자 인증 및 세션 관리
- **APScheduler**: 자동 새로고침 스케줄링

### Frontend
- **HTML5/CSS3**: 반응형 웹 디자인
- **JavaScript (Vanilla)**: 동적 UI 및 API 통신
- **Chart.js**: 실시간 차트 렌더링
- **Flexbox**: 모바일 최적화 레이아웃

## 📊 API 엔드포인트

### 자산 관리
- `GET /assets` - 보유 자산 현황
- `GET /orders` - 미체결 주문 목록
- `POST /cancel-order` - 주문 취소

### 차트 데이터
- `GET /chart-data/days/{currency}` - 일봉 데이터
- `GET /chart-data/minutes/{currency}` - 분봉 데이터
- `GET /coinlist` - 지원 코인 목록

### 자동 매도
- `GET /auto-sell` - 자동 매도 상태
- `POST /toggle-auto-sell` - 자동 매도 토글
- `POST /update-sell-price` - 매도가 업데이트

## 🔒 보안 고려사항

- JWT 토큰 기반 인증 시스템
- CORS 설정으로 안전한 API 통신
- 세션 기반 사용자 상태 관리
- API 키 환경 변수 관리 권장

## 🚀 배포

### 로컬 개발
```bash
conda activate pytorch3d
cd backend
python listasset.py
```

### 프로덕션 배포
```bash
# Gunicorn 사용 예시
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8003 listasset:app
```

## 🐛 문제 해결

### 일반적인 문제들

1. **API 연결 오류**
   - Bithumb API 서버 상태 확인
   - 네트워크 연결 상태 확인

2. **차트 로딩 실패**
   - 백엔드 서버 실행 상태 확인
   - 브라우저 콘솔에서 오류 메시지 확인

3. **자동 새로고침 중단**
   - 브라우저 탭이 활성 상태인지 확인
   - 네트워크 연결 상태 확인

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

---

**SojuCoin Dashboard** - 암호화폐 자산 관리의 새로운 경험을 제공합니다.