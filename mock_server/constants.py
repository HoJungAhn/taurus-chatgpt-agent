"""
mock 서버 고정 응답 텍스트 상수 모듈.

mock 서버는 모든 요청에 동일한 분석 결과를 반환한다.
응답 내용을 변경해야 할 경우 이 파일의 MOCK_ANALYSIS_RESULT 상수만 수정하면 된다.

실제 운영에서는 ChatGPT가 입력된 error_stack에 맞는 동적 응답을 생성하지만,
mock 서버의 목적은 전체 서비스 플로우 검증이므로 고정 응답으로 충분하다.
"""

# mock 서버가 모든 ChatGPT 요청에 대해 반환하는 고정 분석 결과.
# NullPointerException을 예시로 작성되었으며, 실제 입력 내용과 무관하게 항상 이 값을 반환한다.
MOCK_ANALYSIS_RESULT = """오류 분석 결과:

[오류 유형] java.lang.NullPointerException

[오류 원인]
NullPointerException은 null 참조에 대해 메서드를 호출하거나 필드에 접근하려 할 때 발생합니다.
주로 객체 초기화 누락, 메서드 반환값 null 처리 미흡, 또는 컬렉션/배열의 null 요소 접근이 원인입니다.

[해결 방법]
1. 오류 발생 라인에서 사용된 객체가 null인지 확인하세요.
2. null 가능성이 있는 객체에 대해 null 체크를 추가하세요. (if (obj != null) 또는 Optional 활용)
3. 메서드 반환값이 null일 수 있는 경우 반환 전 기본값을 지정하거나 Optional로 감싸세요.
4. 의존성 주입(DI) 프레임워크 사용 시 Bean이 올바르게 주입되었는지 확인하세요."""
