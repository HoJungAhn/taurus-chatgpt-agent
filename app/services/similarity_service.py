"""
TF-IDF + Cosine Similarity 기반 유사도 저장/검색 서비스 모듈.

SQLite에 error_stack과 ChatGPT 결과를 저장하고, 새 요청이 들어올 때
동일 interface_id 범위 내에서 유사도를 계산하여 캐시 히트 여부를 판단한다.

알고리즘 선택 이유:
- TF-IDF (Term Frequency-Inverse Document Frequency): Java 클래스명/메서드명 같은
  도메인 특화 토큰에 높은 가중치를 부여하여 stacktrace 비교에 적합
- Cosine Similarity: 텍스트 길이에 무관하게 방향(의미)의 유사도를 측정
- 벡터를 DB에 저장하지 않고 조회 시 즉석 계산: 직렬화 복잡성 제거, 소규모 데이터에 충분
"""

import logging
import sqlite3
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


class BaseSimilarityService(ABC):
    """
    유사도 서비스 추상 인터페이스.

    TFIDFSimilarityService가 기본 구현체이며, 향후 BM25나 sentence-transformers 등
    다른 알고리즘으로 교체 시 이 인터페이스만 유지하면 라우트 코드 변경이 불필요하다.
    """

    @abstractmethod
    def save(self, interface_id: str, error_stack: str, chatgpt_result: str) -> None:
        """ChatGPT 성공 응답을 DB에 저장한다. timeout/오류 시에는 호출하지 않는다."""
        ...

    @abstractmethod
    def find_similar(self, interface_id: str, error_stack: str) -> Tuple[Optional[str], Optional[float]]:
        """
        동일 interface_id 범위 내에서 유사한 error_stack을 검색한다.

        Returns:
            (chatgpt_result, max_sim): HIT 시 결과 문자열과 유사도
            (None, max_sim): MISS 시 None과 유사도
            (None, None): stored=0 (데이터 없음) 시
        """
        ...

    @abstractmethod
    def get_summary(self) -> Dict:
        """전체 저장 건수와 고유 interface_id 수를 반환한다 (dashboard용)."""
        ...

    @abstractmethod
    def get_all_interfaces(self) -> List[Dict]:
        """interface_id별 저장 현황과 레코드 목록을 반환한다 (dashboard용)."""
        ...


class TFIDFSimilarityService(BaseSimilarityService):
    """
    TF-IDF + Cosine Similarity를 사용하는 SQLite 기반 유사도 서비스 구현체.

    DB 연결은 FastAPI lifespan 이벤트(init_db/close_db)로 관리된다.
    check_same_thread=False: FastAPI의 async 환경에서 여러 코루틴이 같은 연결을 공유하기 위해 필요.
    """

    def __init__(self, db_path: str, threshold: float, max_records_per_interface: int = 5):
        """
        Args:
            db_path: SQLite DB 파일 경로 (환경 변수 SIMILARITY_DB_PATH)
            threshold: 캐시 히트 판단 유사도 임계값 (환경 변수 SIMILARITY_THRESHOLD, 기본 0.8)
            max_records_per_interface: interface_id당 최대 저장 건수 (환경 변수 SIMILARITY_MAX_RECORDS, 기본 5)
        """
        self.db_path = db_path
        self.threshold = threshold
        self.max_records_per_interface = max_records_per_interface
        self._conn: Optional[sqlite3.Connection] = None

    def init_db(self) -> None:
        """
        SQLite 연결을 열고 테이블과 인덱스를 생성한다.
        IF NOT EXISTS 구문으로 이미 존재하는 경우 재생성을 방지한다.
        interface_id 인덱스는 동일 interface_id 조회 성능을 위해 생성한다.
        기존 DB에 last_accessed_at 컬럼이 없으면 ALTER TABLE로 추가한다.
        """
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS similarity_store (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                interface_id      TEXT    NOT NULL,
                error_stack       TEXT    NOT NULL,
                chatgpt_result    TEXT    NOT NULL,
                created_at        TEXT    NOT NULL,   -- ISO 8601 UTC 형식
                last_accessed_at  TEXT    NULL        -- LRU 기준: 마지막 cache HIT 시각
            )
        """)
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_interface_id ON similarity_store(interface_id)"
        )
        # 기존 DB 파일에 last_accessed_at 컬럼이 없으면 추가 (마이그레이션)
        existing_columns = [
            row[1]
            for row in self._conn.execute("PRAGMA table_info(similarity_store)").fetchall()
        ]
        if "last_accessed_at" not in existing_columns:
            self._conn.execute(
                "ALTER TABLE similarity_store ADD COLUMN last_accessed_at TEXT NULL"
            )
        self._conn.commit()

    def close_db(self) -> None:
        """DB 연결을 닫는다. 앱 종료 시 lifespan에서 호출된다."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def save(self, interface_id: str, error_stack: str, chatgpt_result: str) -> None:
        """
        ChatGPT 정제 결과를 DB에 저장한다.
        created_at은 UTC 기준 ISO 8601 형식으로 저장한다.
        저장 후 interface_id당 건수가 max_records_per_interface를 초과하면
        last_accessed_at 기준 가장 오래된 row를 삭제한다 (LRU 축출).

        Note: ChatGPT timeout 또는 오류 시에는 이 메서드를 호출하지 않는다.
        """
        created_at = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            "INSERT INTO similarity_store (interface_id, error_stack, chatgpt_result, created_at) VALUES (?, ?, ?, ?)",
            (interface_id, error_stack, chatgpt_result, created_at),
        )
        # INSERT 후 해당 interface_id의 건수 확인
        count = self._conn.execute(
            "SELECT COUNT(*) FROM similarity_store WHERE interface_id = ?",
            (interface_id,),
        ).fetchone()[0]
        # max_records_per_interface 초과 시 last_accessed_at 기준 가장 오래된 row 삭제 (NULL 우선)
        if count > self.max_records_per_interface:
            self._conn.execute(
                """
                DELETE FROM similarity_store
                WHERE id = (
                    SELECT id FROM similarity_store
                    WHERE interface_id = ?
                    ORDER BY last_accessed_at ASC NULLS FIRST
                    LIMIT 1
                )
                """,
                (interface_id,),
            )
        self._conn.commit()

    def find_similar(self, interface_id: str, error_stack: str) -> Tuple[Optional[str], Optional[float]]:
        """
        동일 interface_id의 저장된 error_stack들과 TF-IDF + Cosine Similarity를 계산한다.

        검색 흐름:
        1. 동일 interface_id의 모든 error_stack을 DB에서 조회
        2. 저장된 텍스트들 + 새 error_stack을 합쳐 TF-IDF 벡터로 변환
        3. 새 벡터와 기존 벡터들 간 Cosine Similarity 계산
        4. 최대 유사도가 threshold 이상이면 해당 chatgpt_result 반환
        5. 데이터 없거나 threshold 미만이면 None 반환 → ChatGPT 호출로 진행

        Args:
            interface_id: 검색 범위를 제한하는 인터페이스 식별자
            error_stack: 유사도 비교 대상 신규 error stacktrace

        Returns:
            (chatgpt_result, max_sim): HIT 시 결과 문자열과 유사도
            (None, max_sim): MISS 시 None과 유사도
            (None, None): stored=0 (데이터 없음) 시
        """
        # 동일 interface_id의 기존 데이터 전체 조회 (id 포함: HIT 시 last_accessed_at 갱신용)
        cursor = self._conn.execute(
            "SELECT id, error_stack, chatgpt_result FROM similarity_store WHERE interface_id = ?",
            (interface_id,),
        )
        rows = cursor.fetchall()

        # 저장된 데이터가 없으면 즉시 (None, None) 반환 — similarity 계산 불가
        if not rows:
            logger.info(
                "similarity_search | interface_id=%s stored=0 result=SKIP",
                interface_id,
            )
            return None, None

        stored_ids = [row[0] for row in rows]
        stored_stacks = [row[1] for row in rows]
        stored_results = [row[2] for row in rows]

        # corpus = 기존 텍스트들 + 신규 텍스트 (마지막 원소가 신규)
        # TfidfVectorizer.fit_transform으로 전체 corpus를 한 번에 벡터화
        corpus = stored_stacks + [error_stack]
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(corpus)

        # 신규 벡터(마지막)와 기존 벡터들 간 Cosine Similarity 계산
        new_vec = tfidf_matrix[-1]
        stored_vecs = tfidf_matrix[:-1]
        similarities = cosine_similarity(new_vec, stored_vecs)[0]

        max_idx = similarities.argmax()
        max_sim = float(similarities[max_idx])

        if max_sim >= self.threshold:
            # HIT: last_accessed_at을 현재 UTC 시각으로 갱신 (LRU 기준 유지)
            now = datetime.now(timezone.utc).isoformat()
            self._conn.execute(
                "UPDATE similarity_store SET last_accessed_at = ? WHERE id = ?",
                (now, stored_ids[max_idx]),
            )
            self._conn.commit()
            logger.info(
                "similarity_search | interface_id=%s stored=%d max_sim=%.4f threshold=%.2f result=HIT",
                interface_id, len(rows), max_sim, self.threshold,
            )
            return stored_results[max_idx], max_sim

        logger.info(
            "similarity_search | interface_id=%s stored=%d max_sim=%.4f threshold=%.2f result=MISS",
            interface_id, len(rows), max_sim, self.threshold,
        )
        return None, max_sim

    def get_summary(self) -> Dict:
        """
        전체 저장 현황 요약을 반환한다 (dashboard 상단 통계용).

        Returns:
            {"total": 전체 레코드 수, "unique_interfaces": 고유 interface_id 수}
        """
        cursor = self._conn.execute("SELECT COUNT(*), COUNT(DISTINCT interface_id) FROM similarity_store")
        total, unique_interfaces = cursor.fetchone()
        return {"total": total, "unique_interfaces": unique_interfaces}

    def get_all_interfaces(self) -> List[Dict]:
        """
        interface_id별 저장 현황과 레코드 목록을 반환한다 (dashboard 목록용).
        최근 저장 순으로 정렬되며, 각 interface_id 내 레코드도 최신 순으로 정렬된다.

        Returns:
            [
                {
                    "interface_id": str,
                    "count": int,
                    "latest": str (ISO 8601),
                    "records": [{"error_stack": str, "chatgpt_result": str, "created_at": str}, ...]
                },
                ...
            ]
        """
        # interface_id별 집계: 건수와 최근 저장 시각
        cursor = self._conn.execute(
            "SELECT interface_id, COUNT(*) as count, MAX(created_at) as latest FROM similarity_store GROUP BY interface_id ORDER BY latest DESC"
        )
        interfaces = []
        for interface_id, count, latest in cursor.fetchall():
            # 해당 interface_id의 레코드 전체 조회 (최신 순)
            records_cursor = self._conn.execute(
                "SELECT error_stack, chatgpt_result, created_at FROM similarity_store WHERE interface_id = ? ORDER BY created_at DESC",
                (interface_id,),
            )
            records = [
                {"error_stack": r[0], "chatgpt_result": r[1], "created_at": r[2]}
                for r in records_cursor.fetchall()
            ]
            interfaces.append({
                "interface_id": interface_id,
                "count": count,
                "latest": latest,
                "records": records,
            })
        return interfaces
