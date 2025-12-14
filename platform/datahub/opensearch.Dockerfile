# 기존 버전과 동일한 태그 사용
FROM opensearchproject/opensearch:2.17.0

# 한국어 형태소 분석기(Nori) 설치
RUN /usr/share/opensearch/bin/opensearch-plugin install analysis-nori
