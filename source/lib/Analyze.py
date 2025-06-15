import pandas as pd
import numpy as np
import os
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

# --- 1. 설정 및 데이터 생성 ---

# 모델 및 컬럼 정보 저장 경로 (분류/회귀 모델 분리)
CLASSIFIER_PATH = "demand_classifier.joblib"
REGRESSOR_PATH = "demand_regressor.joblib"
COLUMNS_PATH = "model_columns.joblib"
CATEGORIES = ["문구", "생활용품", "전자기기", "음료", "식품", "기타"]

def generate_synthetic_data(num_samples=2500):
    """
    수요 예측 모델 훈련을 위한 가상 데이터를 생성합니다.
    수요 수준(증가, 보통, 감소)과 함께 예상 변동 수량을 포함합니다.
    """
    data = []
    for _ in range(num_samples):
        temp = np.random.randint(0, 35)
        is_raining = np.random.choice([1, 0])
        is_hot_wave = 1 if temp >= 30 else 0
        has_festival = np.random.choice([1, 0])
        has_concert = np.random.choice([1, 0])
        category = np.random.choice(CATEGORIES)
        
        # 수요 수준 및 변동 수량 결정 로직 (감소 시나리오 강화)
        demand = "수요 보통"
        quantity_change = np.random.randint(-2, 3) # -2 ~ +2

        # 카테고리별 수요 변화 로직
        if category == "음료":
            if is_hot_wave:
                demand = "수요 증가"
                quantity_change = np.random.randint(15, 30)
            elif has_festival or has_concert:
                demand = "수요 증가"
                quantity_change = np.random.randint(10, 25)
        elif category == "식품":
            if has_festival or has_concert:
                demand = "수요 증가"
                quantity_change = np.random.randint(8, 20)
        elif category == "생활용품":
            if is_raining:
                demand = "수요 증가" # 우산 등
                quantity_change = np.random.randint(5, 15)
            # 폭염 시 야외 활동 감소로 일부 생활용품 수요 감소
            elif is_hot_wave and np.random.rand() > 0.6:
                demand = "수요 감소"
                quantity_change = np.random.randint(-10, -3)
        elif category == "문구":
            # 비가 오면 문구류 수요 감소
            if is_raining:
                demand = "수요 감소"
                quantity_change = np.random.randint(-8, -1)

        data.append([temp, is_raining, is_hot_wave, has_festival, has_concert, category, demand, quantity_change])

    columns = ["temperature", "is_raining", "is_hot_wave", "has_festival", "has_concert", "category", "demand", "quantity_change"]
    return pd.DataFrame(data, columns=columns)

# --- 2. 모델 훈련 및 관리 ---

def train_model():
    """
    분류(Classifier)와 회귀(Regressor) 모델을 각각 훈련하고 파일로 저장합니다.
    """
    print("수요 예측 모델 훈련을 시작합니다 (분류/회귀)...")
    
    df = generate_synthetic_data()
    df_encoded = pd.get_dummies(df, columns=['category'], drop_first=True)
    
    X = df_encoded.drop(['demand', 'quantity_change'], axis=1)
    y_class = df_encoded['demand']
    y_quant = df_encoded['quantity_change']
    
    X_train, X_test, y_class_train, y_class_test, y_quant_train, y_quant_test = train_test_split(
        X, y_class, y_quant, test_size=0.2, random_state=42, stratify=y_class
    )
    
    # 1. 분류 모델 훈련 ('수요 감소'에 가중치 부여)
    class_weights = {'수요 감소': 3, '수요 보통': 1, '수요 증가': 1.2}
    classifier = RandomForestClassifier(n_estimators=100, random_state=42, class_weight=class_weights)
    classifier.fit(X_train, y_class_train)
    print(f"분류 모델 정확도: {classifier.score(X_test, y_class_test):.2f}")
    
    # 2. 회귀 모델 훈련
    regressor = RandomForestRegressor(n_estimators=100, random_state=42)
    regressor.fit(X_train, y_quant_train)
    print(f"회귀 모델 R^2 점수: {regressor.score(X_test, y_quant_test):.2f}")

    # 모델 및 컬럼 저장
    joblib.dump(classifier, CLASSIFIER_PATH)
    joblib.dump(regressor, REGRESSOR_PATH)
    joblib.dump(X.columns.tolist(), COLUMNS_PATH)
    
    print(f"모델이 '{CLASSIFIER_PATH}'와 '{REGRESSOR_PATH}'에 저장되었습니다.")
    return classifier, regressor, X.columns.tolist()

def load_model_and_columns():
    """
    저장된 분류기와 회귀 모델을 불러옵니다. 파일이 없으면 새로 훈련합니다.
    """
    if not all(os.path.exists(p) for p in [CLASSIFIER_PATH, REGRESSOR_PATH, COLUMNS_PATH]):
        print("저장된 모델을 찾을 수 없습니다.")
        return train_model()
    else:
        print(f"저장된 모델들을 불러옵니다.")
        classifier = joblib.load(CLASSIFIER_PATH)
        regressor = joblib.load(REGRESSOR_PATH)
        columns = joblib.load(COLUMNS_PATH)
        return classifier, regressor, columns

# --- 3. 수요 예측 ---

def predict_demand(category, weather_data, event_data, classifier, regressor, model_columns):
    """
    현재 정보를 기반으로 수요 변화 확률과 예상 변동 수량을 예측합니다.
    """
    # 1. 입력 데이터로부터 특성(Feature) 추출
    temp = float(weather_data.get('온도', 0))
    is_raining = 1 if weather_data.get('is_raining', False) else 0
    is_hot_wave = 1 if temp >= 30 else 0
    has_festival = 1 if event_data.get('축제') else 0
    has_concert = 1 if event_data.get('공연') else 0

    # 2. DataFrame 생성 및 인코딩
    input_df = pd.DataFrame([[temp, is_raining, is_hot_wave, has_festival, has_concert, category]],
                              columns=["temperature", "is_raining", "is_hot_wave", "has_festival", "has_concert", "category"])
    input_encoded = pd.get_dummies(input_df)
    final_df = input_encoded.reindex(columns=model_columns, fill_value=0)
    
    # 3. 예측 수행
    # 3.1. 확률 예측
    probabilities = classifier.predict_proba(final_df)[0]
    class_order = classifier.classes_
    
    # 3.2. 수량 예측
    quantity_prediction = regressor.predict(final_df)[0]
    
    # 4. 결과 포맷팅
    highest_prob_index = np.argmax(probabilities)
    predicted_class = class_order[highest_prob_index]
    predicted_prob = probabilities[highest_prob_index]
    
    # 확률을 10% 단위로 반올림
    prob_percent = round(predicted_prob * 10) * 10
    
    # 수량 포맷팅
    quantity_str = f"{round(quantity_prediction):+d}개" # + 또는 - 부호 포함
    
    return f"{prob_percent}% 확률로 {predicted_class} ({quantity_str} 예상)"

