import requests
from bs4 import BeautifulSoup
import urllib.parse
import time

def search_titles(region: str, keywords: list) -> dict:
    """
    네이버 검색을 통해 특정 지역과 키워드에 맞는 최신 게시글 제목을 스크래핑합니다.

    Args:
        region (str): 검색할 지역 (예: "서울")
        keywords (list): 검색할 키워드 목록 (예: ["축제", "사고"])

    Returns:
        dict: 키워드를 key로, 제목 리스트를 value로 갖는 딕셔너리
    """
    # 일부 웹사이트는 자동화된 요청을 차단하므로, 실제 브라우저처럼 보이게 헤더를 설정합니다.
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    result = {}

    for keyword in keywords:
        # 한글 검색어가 URL에 포함될 수 있도록 인코딩합니다.
        query = urllib.parse.quote_plus(f"{region} {keyword}")
        # 'view' 탭을 사용하여 블로그, 카페 등 최신 정보를 우선 검색합니다.
        url = f"https://search.naver.com/search.naver?where=view&query={query}"
        
        try:
            # 웹페이지에 GET 요청을 보냅니다.
            res = requests.get(url, headers=headers, timeout=10)
            res.raise_for_status()  # 요청이 실패하면 예외를 발생시킵니다.
            
            # BeautifulSoup을 사용하여 HTML을 파싱합니다.
            soup = BeautifulSoup(res.text, "html.parser")

            titles = []
            # view 탭의 제목은 'title_link' 클래스를 가진 a 태그에 주로 포함됩니다.
            for a_tag in soup.select("a.title_link"):
                title = a_tag.get_text()
                if title:
                    titles.append(title.strip())
            
            # 중복을 제거하고 최대 5개의 결과만 저장합니다.
            result[keyword] = list(set(titles))[:5]
            
            # 네이버의 과도한 요청 차단을 피하기 위해 각 키워드 검색 사이에 약간의 지연을 줍니다.
            time.sleep(0.5)

        except requests.exceptions.RequestException as e:
            # 네트워크 오류 발생 시 해당 키워드는 빈 결과로 처리합니다.
            print(f"Error fetching data for {keyword}: {e}")
            result[keyword] = ["오류: 관련 소식을 불러오는 데 실패했습니다."]
            
    return result