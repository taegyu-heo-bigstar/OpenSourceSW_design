import threading
import time
import json
import os

CONFIG_FILE = "timer_config.json"

class Timer:
    """
    주기적인 작업을 백그라운드에서 실행하는 타이머 클래스입니다.
    애플리케이션 전체에서 하나의 인스턴스만 유지되도록 설계되었습니다.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Timer, cls).__new__(cls)
        return cls._instance

    def __init__(self, callback=None):
        # __init__은 매번 호출될 수 있으므로, 초기화는 한 번만 수행합니다.
        if not hasattr(self, 'is_initialized'):
            self.callback = callback
            self.interval = self._load_interval()
            self.stop_event = threading.Event()
            self.thread = None
            self.is_initialized = True

    def _load_interval(self):
        """설정 파일에서 인터벌 값을 불러옵니다. 없으면 기본값(3600초)을 반환합니다."""
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                return config.get("interval", 3600)
        return 3600 # 기본값: 1시간

    def _save_interval(self):
        """현재 인터벌 값을 설정 파일에 저장합니다."""
        with open(CONFIG_FILE, 'w') as f:
            json.dump({"interval": self.interval}, f)

    def set_interval(self, seconds):
        """타이머의 간격을 설정하고 파일에 저장합니다."""
        if seconds > 0:
            self.interval = seconds
            self._save_interval()
            print(f"타이머 간격이 {seconds}초로 설정되었습니다.")

    def get_interval(self):
        """현재 설정된 인터벌 값을 반환합니다."""
        return self.interval

    def _run(self):
        """타이머의 메인 루프. 주기적으로 콜백 함수를 실행합니다."""
        while not self.stop_event.is_set():
            # 다음 실행까지 현재 인터벌만큼 대기합니다.
            # wait은 sleep과 달리 중간에 중단(stop)될 수 있어 더 안전합니다.
            self.stop_event.wait(self.interval)
            
            if not self.stop_event.is_set() and self.callback:
                try:
                    self.callback()
                except Exception as e:
                    print(f"타이머 콜백 실행 중 오류 발생: {e}")

    def start(self):
        """백그라운드 스레드에서 타이머를 시작합니다."""
        if self.thread is None or not self.thread.is_alive():
            self.stop_event.clear()
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
            print("자동 알림 타이머가 시작되었습니다.")

    def stop(self):
        """타이머를 안전하게 중지합니다."""
        if self.thread and self.thread.is_alive():
            self.stop_event.set()
            self.thread.join(timeout=2) # 스레드가 종료될 때까지 잠시 대기
            print("자동 알림 타이머가 중지되었습니다.")
