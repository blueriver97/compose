<!-- TOC -->

- [확장 프로그램 설치](#확장-프로그램-설치)
- [ES 인덱스 변환 및 검색 개선](#es-인덱스-변환-및-검색-개선)
  - [1. datasetindex_v2 구성 백업](#1-datasetindex_v2-구성-백업)
  - [2. datasetindex_v2_backup 인덱스 생성 및 Document 복사](#2-datasetindex_v2_backup-인덱스-생성-및-document-복사)
  - [3. Ngram 추가 및 Description, FieldDescription 필드 내 Keyword 설정 Ngram으로 수정](#3-ngram-추가-및-description-fielddescription-필드-내-keyword-설정-ngram으로-수정)
  - [4. datasetindex_v2_custom 인덱스 생성 및 Document 복사](#4-datasetindex_v2_custom-인덱스-생성-및-document-복사)
  - [5. datasetindex_v2 인덱스 삭제 및 datasetindex_v2_custom 인덱스에 Alias 등록](#5-datasetindex_v2-인덱스-삭제-및-datasetindex_v2_custom-인덱스에-alias-등록)
- [ES 검색어 분석 테스트](#es-검색어-분석-테스트)
_ [검색어 분석 테스트](#검색어-분석-테스트)
_ [인덱스 설정 조회](#인덱스-설정-조회)
_ [인덱스 생성](#인덱스-생성)
_ [인덱스 삭제](#인덱스-삭제)
<!-- TOC -->

---

# 확장 프로그램 설치

- SwitchOmega 활성화 시 접속 가능
  - https://chromewebstore.google.com/detail/elasticvue/hkedbapjpblbodpgbajblpnlpenaebaa?hl=ko&utm_source=ext_sidebar

# ES 인덱스 변환 및 검색 개선

### 1. datasetindex_v2 구성 백업

- datasetindex_v2_origin.json 생성

### 2. datasetindex_v2_backup 인덱스 생성 및 Document 복사

- PUT /datasetindex_v2_backup

  ```json
  datasetindex_v2_origin.json 내용 참조
  ```

- POST /\_reindex

  ```json
  {
    "source": {
      "index": "datasetindex_v2"
    },
    "dest": {
      "index": "datasetindex_v2_backup"
    }
  }
  ```

### 3. Ngram 추가 및 Description, FieldDescription 필드 내 Keyword 설정 Ngram으로 수정

- datasetindex_v2_custom.json 생성

### 4. datasetindex_v2_custom 인덱스 생성 및 Document 복사

- PUT /datasetindex_v2_custom

  ```json
  datasetindex_v2_custom.json 내용 참조
  ```

- POST /\_reindex

  ```json
  {
    "source": {
      "index": "datasetindex_v2"
    },
    "dest": {
      "index": "datasetindex_v2_custom"
    }
  }
  ```

### 5. datasetindex_v2 인덱스 삭제 및 datasetindex_v2_custom 인덱스에 Alias 등록

# ES 검색어 분석 테스트

### 검색어 분석 테스트

- POST /<index-name>/\_analyze
  ```json
  {
    "analyzer": "custom_delimiter_analyzer",
    "text": "helloworld"
  }
  ```

### 인덱스 설정 조회

- GET /<index-name>/\_settings?pretty

### 인덱스 생성

- PUT /<index-name>
  ```json
  {
    "settings": {
      "analysis": {
        "tokenizer": {
          "standard_tokenizer": {
            "type": "standard"
          }
        },
        "filter": {
          "word_delimiter_filter": {
            "type": "word_delimiter",
            "split_on_case_change": "true",
            "generate_word_parts": "true",
            "generate_number_parts": "true",
            "catenate_words": "true"
          }
        },
        "analyzer": {
          "custom_delimiter_analyzer": {
            "type": "custom",
            "tokenizer": "standard_tokenizer",
            "filter": ["lowercase", "word_delimiter_filter"]
          }
        }
      }
    },
    "mappings": {
      "properties": {
        "name": {
          "type": "text",
          "analyzer": "custom_delimiter_analyzer"
        }
      }
    }
  }
  ```

### 인덱스 삭제

- DELETE /<index-name>
