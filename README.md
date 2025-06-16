# 인벤토리 관리 시스템 (Inventory Management System)
Tkinter를 기반으로 한 GUI 인벤토리 관리 프로그램입니다. 사용자 계정 관리, 상품 재고 관리 기능을 제공하며, 수요 예측과 같은 AI 기능을 확장할 수 있도록 설계되었습니다.

* * *

## 🌟 주요 기능   
* 계정 관리:   
안전한 비밀번호 암호화(bcrypt)를 통한 사용자 로그인 및 로그아웃   
관리자 계정을 통한 사용자 계정 생성 및 삭제   

* 재고 관리:   
직관적인 GUI를 통한 상품 추가, 수정, 삭제, 조회 (CRUD)
사용자별로 독립된 인벤토리 데이터 관리

* 관리자 기능:   
일반 사용자의 인벤토리를 '읽기 전용'으로 조회 가능   

* 확장성:   
수요 예측 등 AI 기능 추가를 고려한 모듈식 구조   

## 💻 기술 스택 및 요구사항   
### 주요 기술   
언어: Python 3.x   
GUI: Tkinter (파이썬 기본 내장)   
데이터베이스: SQLite 3 (파이썬 기본 내장)   

### 하드웨어적 요구사항   

#### 최소 사양   
> CPU: 1.5 GHz 이상의 듀얼 코어 프로세서   
> RAM: 4 GB   
> 저장 공간: 2 GB 이상의 여유 공간   

#### 권장 사양   
> CPU: 2.0 GHz 이상의 쿼드 코어 프로세서   
> RAM: 8 GB 이상   
> 저장 공간: 5 GB 이상의 여유 공간 (SSD 권장)
   
### 소프트웨어 요구사항   

운영체제 (Operating System)   
> Windows 10 또는 그 이상   
> macOS 10.13 (High Sierra) 또는 그 이상   
> 최신 Linux 배포판 (Ubuntu, Fedora 등)   

Python 버전 (Python Version)   
> Python 3.8 이상을 권장합니다.   
> 파이썬 설치 시 GUI 라이브러리인 Tkinter와 데이터베이스 엔진인 SQLite3가 기본적으로 포함되어 있어야 합니다.

필수 라이브러리 (Required Libraries)   
>프로젝트의 requirements.txt 파일에 명시된 모든 라이브러리.   

## 🚀 설치 및 실행 방법   
1. 프로젝트 복제 (Clone)
   
터미널을 열고 아래 명령어를 입력하여 프로젝트를 복제합니다.
```
  git clone [프로젝트의 Git 저장소 URL]   
  cd [프로젝트 폴더명]   
```
3. 가상 환경 생성 및 활성화

#가상 환경 생성 (최초 1회)   
```
  python -m venv venv
```
#가상 환경 활성화 (실행할 때마다 필요)   
#Windows:
```
  venv\Scripts\activate
``` 
#macOS / Linux:   
```
  source venv/bin/activate
```  
3. 필수 라이브러리 설치   
   
아래 명령어를 사용하여 requirements.txt 파일에 명시된 모든 라이브러리를 한 번에 설치합니다.   
```
  pip install -r requirements.txt
```
4. 필요 api   

공공 데이터 포털의 회원가입 후 로그인하여 "기상청_단기예보 ((구)_동네예보) 조회서비스" 서비스의 api key를 획득해야 합니다.   
얻은 api key를 lib/interface.py에 입력해야 합니다.   
22번째 줄을 보게되면 다음과 같은 부분이 있습니다.   
```
   KMA_API_KEY = "여기에 api key가 필요" 
```
해당 부분에 ' 혹은 "로 감싼 api key를 입력하십시오. 권장되는 api_key는 decoding된 key입니다.

6. 프로그램 실행   

모든 준비가 끝났다면, 아래 명령어로 프로그램을 실행합니다.   
```
   python main.py
```   
## 📂 프로젝트 구조   
Inventory-Management-System/   
├── lib/                      # 핵심 로직 및 UI 정의 패키지   
│   ├── __init__.py           # lib 폴더를 패키지로 인식시킴   
│   ├── interface.py          # GUI 및 애플리케이션 흐름 제어   
│   ├── account_management.py # 계정 관련 데이터베이스 로직   
│   └── inventory.py          # 재고 관련 데이터베이스 로직   
├── venv/                     # 가상 환경 폴더   
├── main.py                   # 프로그램 실행 파일 (Entry Point)   
├── requirements.txt          # 외부 라이브러리 목록   
└── README.md                 # 프로젝트 소개 및 안내 문서   

* * *
🧑‍💻 작성자
taegyu-heo
