## ADDED Requirements

### Requirement: 동일 interface_id 내 유사도 비교
새로운 `error_stack` 수신 시, 동일 `interface_id`에 저장된 텍스트들과 TF-IDF + Cosine Similarity로 비교해야 한다.
타 `interface_id` 데이터는 비교 대상에 포함하지 않아야 한다.

#### Scenario: 유사 결과 존재 시 기존 결과 반환
- **WHEN** 동일 `interface_id` 내에 유사도 threshold 이상의 `error_stack`이 존재할 때
- **THEN** 해당 `chatgpt_result`를 반환해야 한다 (ChatGPT 호출 없음)

#### Scenario: 유사 결과 없을 때 None 반환
- **WHEN** 동일 `interface_id` 내 모든 유사도가 threshold 미만일 때
- **THEN** `None`을 반환하여 ChatGPT 호출로 진행해야 한다

#### Scenario: 저장 데이터 없을 때 None 반환
- **WHEN** 해당 `interface_id`에 저장된 데이터가 없을 때
- **THEN** `None`을 반환해야 한다

#### Scenario: 타 interface_id 데이터 미참조
- **WHEN** 다른 `interface_id`에 동일한 `error_stack`이 저장되어 있을 때
- **THEN** 해당 데이터는 유사도 비교 대상에 포함되지 않아야 한다

---

### Requirement: 유사도 threshold 환경 변수 설정
유사도 임계값(threshold)은 `SIMILARITY_THRESHOLD` 환경 변수로 설정 가능해야 한다.

#### Scenario: 기본 threshold 적용
- **WHEN** `SIMILARITY_THRESHOLD` 환경 변수가 설정되지 않았을 때
- **THEN** 기본값 `0.8`이 threshold로 사용되어야 한다

#### Scenario: 사용자 정의 threshold 적용
- **WHEN** `SIMILARITY_THRESHOLD=0.9`로 설정했을 때
- **THEN** 유사도 0.9 이상인 경우에만 기존 결과를 반환해야 한다
