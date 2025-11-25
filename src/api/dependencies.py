"""API 공통 의존성 모듈

향후 인증, 로깅, 레이트 리밋 등의 공통 기능을 여기에 추가합니다.
"""

from src.systems.build_graph import build_graph

# 그래프 캐시 (싱글톤 패턴)
_graph_cache = None


async def get_graph():
    """Multi-Agent 그래프 인스턴스를 반환합니다.

    그래프는 한 번만 생성되고 캐시됩니다.
    """
    global _graph_cache
    if _graph_cache is None:
        _graph_cache = await build_graph()
    return _graph_cache


def reset_graph_cache():
    """그래프 캐시를 초기화합니다. (테스트용)"""
    global _graph_cache
    _graph_cache = None
