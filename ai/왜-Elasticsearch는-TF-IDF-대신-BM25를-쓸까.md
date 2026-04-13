# 왜 Elasticsearch는 TF-IDF 대신 BM25를 쓸까?

"elephant"가 200번 등장한 문서는 100번 등장한 문서보다 정말 2배 더 관련 있을까? Elasticsearch의 `_score` 뒤에 숨은 공식을 뜯어본다.

## 결론부터 말하면

**Elasticsearch의 `_score`는 BM25 공식으로 계산된다.** Lucene 6(2016)부터 기본 랭킹 함수가 TF-IDF에서 BM25로 바뀌었고, Elasticsearch 5.0(2016)도 이를 따라 전환했다. 핵심 차이는 두 가지다. TF-IDF가 가진 **"Term Frequency가 무한히 선형 증가"** 문제를 포화 곡선으로 누르고, **"긴 문서가 부당하게 유리한"** 문제를 문서 길이 정규화로 보정했다.

```mermaid
flowchart LR
    Q["Query<br>'elephant'"] --> T[Tokenize]
    T --> PERTERM["Per-term<br>Score"]
    PERTERM --> BM25["BM25 Formula<br>k1=1.2, b=0.75"]
    BM25 --> SUM["Sum across<br>query terms"]
    SUM --> SCORE["_score"]

    style BM25 fill:#1565C0,color:#fff
    style SCORE fill:#2E7D32,color:#fff
```

| 항목 | TF-IDF | BM25 |
|---|---|---|
| Term Frequency | 선형 증가 (무제한) | 포화 곡선 ($k_1$로 조절) |
| 문서 길이 | 미반영 | 평균 대비 정규화 ($b$로 조절) |
| 기본 파라미터 | — | $k_1 = 1.2$, $b = 0.75$ |
| Elasticsearch 채택 | 4.x까지 | 5.0부터 기본값 |

Java 개발자라면 이미 매일 ES의 `_score`를 보고 있을 것이다. 그 숫자가 실제로 어떻게 나오는지 지금부터 뜯어보자.

## 1. 왜 TF-IDF로는 부족했는가?

### 1.1 TF-IDF의 직관

먼저 TF-IDF를 한 줄로 복습하자. "문서에 검색어가 많이 나올수록(TF) 관련 있고, 그 검색어가 다른 문서에는 드물수록(IDF) 변별력이 있다"는 아이디어다. 두 값을 곱해서 점수를 낸다.

$$
\text{TF-IDF}(t, D) = \text{TF}(t, D) \times \log\frac{N}{\text{DF}(t)}
$$

단순하고 직관적이다. Lucene도 오랫동안 이 방식을 썼다. 하지만 실제 검색엔진에서 굴려보면 두 가지 치명적인 문제가 드러난다.

### 1.2 문제 1: "코끼리가 200번"

첫 번째 문제는 **Term Frequency가 무한히 선형으로 증가**한다는 것이다. 만약 한 문서에 "elephant"가 200번 등장하고 다른 문서에 100번 등장한다면, TF-IDF는 앞 문서의 점수를 정확히 2배로 매긴다.

하지만 상식적으로 이게 맞을까? 한 문서 안에 검색어가 10번쯤 나왔다면 이미 "아, 이 문서는 코끼리에 관한 문서구나"가 확실해진다. 거기서 100번, 200번으로 늘어난다고 관련성이 극적으로 올라가지는 않는다. **정보의 한계효용이 체감** 한다는 뜻이다.

Java 개발자라면 `HashMap`의 `loadFactor`를 떠올려보면 감이 올 것이다. 초기에는 버킷 하나당 엔트리가 추가될 때마다 성능에 유의미한 영향을 준다. 하지만 일정 수준이 넘으면 추가 엔트리 한 개의 영향력은 급격히 떨어진다. TF에도 같은 사고가 필요한데, TF-IDF에는 그런 장치가 없다.

### 1.3 문제 2: 긴 문서가 유리해지는 편향

두 번째 문제는 **문서 길이 편향** 이다. 단순히 문서가 길다는 이유만으로 검색어가 더 많이 등장할 확률이 올라간다. 한 문단짜리 블로그 글이 10만 자 학술 논문을 이길 수 없게 되는 것이다. 정말로 더 관련 있어서가 아니라, **그냥 길어서** 말이다.

이 두 문제를 어떻게 풀까? 여기서 BM25가 등장한다.

## 2. BM25의 핵심 아이디어

### 2.1 Saturation: $k_1$이라는 조절 손잡이

BM25는 TF를 그대로 쓰지 않고, **포화 함수** (saturation function)로 감싼다. 공식의 TF 부분만 뽑아보면:

$$
\text{TF}_{\text{BM25}} = \frac{f \cdot (k_1 + 1)}{f + k_1}
$$

여기서 $f$는 문서 내 검색어 등장 횟수, $k_1$은 포화 곡선의 기울기를 조절하는 파라미터다. 이 식이 왜 "포화"인지는 값을 직접 대입해보면 바로 보인다. $k_1 = 1.2$일 때 TF별 기여도는 이렇게 변한다.

| $f$ (TF) | TF-IDF의 TF | BM25의 TF항 |
|---|---|---|
| 1 | 1.00 | 1.00 |
| 2 | 2.00 | 1.38 |
| 5 | 5.00 | 1.77 |
| 10 | 10.00 | 1.96 |
| 100 | 100.00 | 2.17 |
| $\infty$ | $\infty$ | **2.20** |

TF-IDF는 무한히 치솟는다. BM25는 $k_1 + 1 = 2.2$라는 상한선에 점점 가까워질 뿐이다. 결과적으로 **"코끼리가 10번 등장한 문서와 100번 등장한 문서의 점수 차이는 무시할 만큼 작다"** 가 된다. 이게 바로 우리가 원하던 동작이다.

그럼 $k_1$은 정확히 무슨 의미인가? 공식적으로는 **"평균 길이 문서에서 TF가 얼마일 때 최대 점수의 절반이 되는가"** 를 결정하는 값이다. $k_1 = 1.2$는 TF가 1~2 정도일 때부터 이미 기여도가 완만해지기 시작한다는 뜻이다. Elasticsearch는 이 값을 기본으로 준다.

### 2.2 문서 길이 정규화: $b$

두 번째 문제(긴 문서 편향)는 **분모에 문서 길이 항을 넣어서** 해결한다. 전체 BM25 공식은 이렇게 생겼다.

$$
\text{BM25}(D, Q) = \sum_{t \in Q} \text{IDF}(t) \cdot \frac{f(t, D) \cdot (k_1 + 1)}{f(t, D) + k_1 \cdot \left(1 - b + b \cdot \dfrac{|D|}{\text{avgdl}}\right)}
$$

복잡해 보이지만 핵심은 분모의 $\left(1 - b + b \cdot \dfrac{|D|}{\text{avgdl}}\right)$ 부분뿐이다. $|D|$는 이 문서의 길이, $\text{avgdl}$은 전체 코퍼스의 평균 문서 길이다.

- 문서가 **평균보다 길면** 분모가 커져서 점수가 **작아진다**
- 문서가 **평균보다 짧으면** 분모가 작아져서 점수가 **커진다**

즉 "긴 문서라는 이유만으로 받는 보너스"를 상쇄한다. $b$는 이 정규화를 얼마나 강하게 적용할지 조절하는 손잡이다. $b = 0$이면 길이 정규화가 완전히 꺼지고, $b = 1$이면 완전 정규화가 된다. Elasticsearch 기본값은 $b = 0.75$로, **"적당히 정규화하되 과하지는 않게"** 라는 타협점이다.

### 2.3 두 손잡이를 언제 어떻게 돌리는가

$k_1$과 $b$는 BM25의 두 조절 손잡이다. Java 비유를 이어가자면, JVM의 GC 파라미터와 비슷하다. 기본값이 대부분의 경우에 잘 동작하지만, 워크로드 특성에 따라 튜닝할 여지가 있다.

| 파라미터 | 의미 | 올리면 (→ 2.0, 1.0) | 내리면 (→ 0.5, 0.25) |
|---|---|---|---|
| $k_1$ | TF 포화 속도 | TF가 많을수록 점수 가중 (반복이 의미 있을 때) | 한 번만 등장해도 점수 거의 만점 |
| $b$ | 길이 정규화 강도 | 짧은 문서 우대 강화 | 길이 영향 감소 |

$k_1$을 2.0 쪽으로 올리는 건 언제 좋을까? 법률 판례처럼 **긴 문서 안에서 용어가 반복될수록 실제로 관련성이 높은** 코퍼스에서 그렇다. 반대로 $k_1$을 0.5로 내리는 건 트윗처럼 **짧고 키워드 스터핑이 의심되는** 코퍼스에서 유용하다.

## 3. Elasticsearch에서 직접 확인하기

이론은 이쯤 하고, 실제로 ES가 어떻게 BM25를 쓰는지 보자. 가장 쉬운 방법은 쿼리에 `"explain": true`를 붙이는 것이다.

```json
GET /articles/_search
{
  "explain": true,
  "query": {
    "match": { "content": "elephant" }
  }
}
```

응답의 `_explanation` 필드에 BM25 계산 과정이 그대로 찍힌다. 다음은 실제 출력을 간소화한 예시다.

```
weight(content:elephant in 42) [PerFieldSimilarity], result of:
  score(freq=5.0), computed as boost * idf * tf from:
    idf, computed as log(1 + (N - n + 0.5) / (n + 0.5)) from:
      N=1000, n=12
    tf, computed as freq / (freq + k1 * (1 - b + b * dl / avgdl)) from:
      freq=5.0, k1=1.2, b=0.75, dl=320, avgdl=280
```

**이 출력 하나가 2장 전체의 내용을 요약한다.** IDF 계산에 쓰이는 N(전체 문서 수)과 n(검색어를 포함한 문서 수), TF 계산에 쓰이는 `k1`, `b`, 그리고 `dl`(현재 문서 길이)과 `avgdl`(평균 문서 길이)까지 전부 보인다. "내 검색 결과가 왜 이 순서로 나왔는지"를 추적하고 싶을 때 가장 먼저 켜야 할 기능이다.

$k_1$이나 $b$를 바꾸고 싶다면 인덱스 매핑에서 `similarity`를 커스터마이징하면 된다.

```json
PUT /articles
{
  "settings": {
    "index": {
      "similarity": {
        "custom_bm25": {
          "type": "BM25",
          "k1": 1.5,
          "b": 0.5
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "content": {
        "type": "text",
        "similarity": "custom_bm25"
      }
    }
  }
}
```

다만 기본값이 잘 동작한다면 굳이 건드리지 말 것을 권한다. 튜닝은 검색 품질을 **측정** 할 수 있을 때만 의미가 있다. NDCG나 MRR 같은 랭킹 평가 지표로 Before/After를 비교할 수 없다면, 손잡이를 돌려봐야 "느낌상 좋아진 것 같은" 착각만 남는다.

## 4. 정리

### 핵심 포인트

1. **`_score`는 BM25 공식의 결과물이다**
   - Elasticsearch 5.0 / Lucene 6부터 기본 랭킹 함수가 TF-IDF에서 BM25로 바뀌었다. 매일 보던 숫자의 정체가 드러났다.

2. **BM25 = TF-IDF + 포화 + 길이 정규화**
   - TF가 무한히 늘어나지 않도록 $k_1$으로 상한을 걸고, 긴 문서가 불공정한 이득을 얻지 않도록 $b$로 정규화한다. "정보의 한계효용 체감"을 공식에 녹여낸 결과물이다.

3. **기본값 $k_1 = 1.2$, $b = 0.75$는 대부분 충분하다**
   - 튜닝은 NDCG, MRR 같은 지표로 품질을 측정할 수 있을 때만 시도하라. `"explain": true`로 실제 계산 과정을 언제든 확인할 수 있다는 점이 BM25의 또 다른 강점이다.

---

## 출처

- [Practical BM25 - Part 2: The BM25 Algorithm and its Variables](https://www.elastic.co/blog/practical-bm25-part-2-the-bm25-algorithm-and-its-variables) - Elastic 공식 블로그
- [BM25: Complete Guide to the Search Algorithm Behind Elasticsearch](https://mbrenndoerfer.com/writing/bm25-search-algorithm-elasticsearch-implementation)
- [Understanding the BM25 full text search algorithm - Evan Schwartz](https://emschwartz.me/understanding-the-bm25-full-text-search-algorithm/)
- [BM25: The Next Generation of Lucene Relevance - OpenSource Connections](https://opensourceconnections.com/blog/2015/10/16/bm25-the-next-generation-of-lucene-relevation/)
