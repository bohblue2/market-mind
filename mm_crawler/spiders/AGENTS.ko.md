# SPIDERS 지식 베이스

## 개요
Naver 뉴스/리서치 소스를 위한 Scrapy 스파이더 패키지.

## 구조
```text
spiders/
├── base_domain_spider.py         # 도메인 파이프라인 조합용 베이스 스파이더
├── naver/
│   ├── naver_news_list.py        # 종목(code)별 금융 뉴스 목록 크롤
│   ├── naver_news_content.py     # 기사 본문 수집 및 파싱
│   ├── naver_main_news_list.py   # 메인/전망/분석 섹션 크롤러
│   └── naver_research_list.py    # 시장/기업/산업 리서치 크롤러
├── hankyung/
│   └── hankyung_consensus_list.py
└── commons.py                    # 리포트 URL 파싱 헬퍼
```

## 어디를 보면 되나
| 작업 | 위치 | 비고 |
|------|------|------|
| 금융 뉴스 목록 동작 추가 | `naver/naver_news_list.py` | `NaverArticleItem` 또는 `NaverArticleListFailedItem`을 생성 |
| 기사 본문 파싱 추가 | `naver/naver_news_content.py` | XPath + BeautifulSoup 정리를 사용 |
| 섹션 뉴스 크롤 추가 | `naver/naver_main_news_list.py` | `BaseNaverNewsSpider` / `BaseNaverSectionNewsSpider` 재사용 |
| 리서치 소스 추가 | `naver/naver_research_list.py` | `NaverResearchBase` + `parse_with_common_columns`/`parse_with_extra_columns` 재사용 |
| 한경 컨센서스 동작 추가 | `hankyung/hankyung_consensus_list.py` | `HankyungConsensusItem`을 생성 |
| 리포트 URL 구성 요소 파싱 | `commons.py` | `NaverReportItem`을 반환 |

## 컨벤션
- 스파이더 `name`은 안정적으로 유지; CLI 스케줄링이 의존함.
- 새 단독 크롤 플로우보다 베이스 클래스를 확장하는 방식을 선호.
- 파이프라인이 의존하는 요청 메타 키(`article_id`, `media_id`, `ticker`, `page`)는 일관되게 유지.
- 각 도메인 스파이더에서 `pipeline_domain`을 설정하고, `DomainPipelineSpider`가 설정에서 `ITEM_PIPELINES`를 조합하도록 둠.
- 모든 스크랩 타임스탬프 파싱은 KST 로컬라이즈를 유지.

## DomainPipelineSpider 파이프라인 연결 방식
`DomainPipelineSpider`( `spiders/base_domain_spider.py` )는 Scrapy의 `Spider.update_settings(cls, settings)`를 오버라이드해서 스파이더 초기화 시점에 `ITEM_PIPELINES`를 조합한다.

이게 필요한 이유:
- 스파이더마다 `ITEM_PIPELINES`를 반복 정의하지 않기 위해서. 파이프라인은 도메인 단위로 `scrapy_settings.py`의 `DOMAIN_ITEM_PIPELINES`에 한 번만 등록한다.
- 공통 파이프라인 + 도메인 파이프라인 + 스파이더별 오버라이드를 항상 같은 규칙으로(결정적으로) 합치기 위해서.

조합 규칙:
- 설정에서 `COMMON_ITEM_PIPELINES`와 `DOMAIN_ITEM_PIPELINES`를 읽는다.
- 스파이더 클래스가 `pipeline_domain = "naver"` 같은 값을 정의하면 `DOMAIN_ITEM_PIPELINES[pipeline_domain]`를 선택한다.
- 스파이더의 `custom_settings`에 `ITEM_PIPELINES`가 있으면 마지막에 merge해서 최종 우선순위를 갖게 한다.
- `settings.set("ITEM_PIPELINES", merged, priority="spider")`로 병합된 값을 다시 설정해 스파이더별 파이프라인 구성을 확정한다.

주의사항:
- 프로젝트 레벨의 `ITEM_PIPELINES`는 자동으로 merge되지 않는다. 공통/도메인/스파이더 오버라이드는 각각 `COMMON_ITEM_PIPELINES` / `DOMAIN_ITEM_PIPELINES` / `custom_settings["ITEM_PIPELINES"]`에 넣어야 한다.
- CLI에서 `-s ITEM_PIPELINES=...`를 사용하면(스파이더 설정보다 우선순위가 높아서) 이 구성을 덮어쓸 수 있다.

## 안티 패턴
- `pipelines/naver.py` 또는 `pipelines/canonical.py`의 DB 매핑과 동기화 없이 아이템 필드 이름을 바꾸지 말 것.
- 다운스트림 실패 저장을 검증하지 않고 `naver/naver_news_list.py`의 fatal/non-fatal 에러 enum 동작을 바꾸지 말 것.
- 새 스파이더를 만들 때 `custom_settings`의 미들웨어/파이프라인 선언을 무심코 제거하지 말 것; 스파이더 패밀리별 기본값이 다름.
- content/title 누락 브랜치를 조용히 삼키지 말 것; 기존 TODO는 알려진 갭이며 명시적으로 처리해야 함.
