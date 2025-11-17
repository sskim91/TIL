# LLM 데이터 전처리의 중요성

LLM에게 데이터를 제공할 때 전처리가 왜 필요하고, 어떻게 해야 하는지 알아봅니다.

## 결론부터 말하면

**데이터 전처리는 LLM의 성능을 좌우하는 가장 중요한 요소입니다.**

전처리 없이 데이터를 제공하면:
- ❌ 토큰 낭비 (비용 증가)
- ❌ 응답 품질 저하
- ❌ 잘못된 컨텍스트 학습
- ❌ 느린 응답 속도

```python
# ❌ 전처리 없음 - 불필요한 정보가 가득
raw_data = """
<html><head><title>Product</title></head>
<body>
    <div class="header">...</div>
    <div class="content">
        Product Name: iPhone 15
        Price: $999
    </div>
    <div class="footer">...</div>
</body>
</html>
"""

# ✅ 전처리 완료 - 핵심 정보만 추출
processed_data = """
Product: iPhone 15
Price: $999
"""
```

**결과**: 토큰 사용량 90% 감소, 응답 정확도 향상

## 1. 데이터 전처리가 중요한 이유

### 1.1 토큰 제한과 비용

LLM은 처리할 수 있는 토큰 수가 제한되어 있습니다:

```python
# GPT-4의 경우
MAX_TOKENS = 128_000  # 입력 + 출력 합계

# 비용 예시 (GPT-4 Turbo 기준)
INPUT_COST_PER_1K = 0.01  # $0.01 per 1K tokens
OUTPUT_COST_PER_1K = 0.03  # $0.03 per 1K tokens

# 전처리 없이 100,000 토큰 사용
cost_without_preprocessing = (100_000 / 1_000) * INPUT_COST_PER_1K
# = $1.00 per request

# 전처리 후 10,000 토큰 사용
cost_with_preprocessing = (10_000 / 1_000) * INPUT_COST_PER_1K
# = $0.10 per request

# 90% 비용 절감!
```

### 1.2 응답 품질 (Signal-to-Noise Ratio)

불필요한 정보는 "노이즈"가 되어 LLM의 주의를 분산시킵니다:

```python
# ❌ 노이즈가 많은 입력
noisy_input = """
==========================================
LOG FILE - DO NOT DELETE
==========================================
[2024-01-01 00:00:01] INFO: Server started
[2024-01-01 00:00:02] DEBUG: Connection pool initialized
[2024-01-01 00:00:03] DEBUG: Cache warming up
... (10,000 lines of logs)
[2024-01-01 12:34:56] ERROR: Database connection failed
[2024-01-01 12:34:57] INFO: Retrying...
==========================================
"""

# ✅ 핵심 정보만 추출
clean_input = """
Error Summary:
- Time: 2024-01-01 12:34:56
- Type: Database connection failed
- Action: Retrying
"""
```

### 1.3 컨텍스트 윈도우 활용

제한된 컨텍스트 윈도우를 효율적으로 사용해야 합니다:

```python
# LLM의 컨텍스트 윈도우
context_window = 128_000  # tokens

# 전처리 없이 데이터 제공
raw_docs = load_all_documents()  # 500,000 tokens
# 결과: 대부분의 문서를 버려야 함

# 전처리 후 데이터 제공
processed_docs = summarize_and_extract_key_points(raw_docs)  # 50,000 tokens
# 결과: 모든 핵심 정보를 포함할 수 있음
```

## 2. 필요한 전처리 작업

### 2.1 텍스트 정제 (Text Cleaning)

```python
import re
from typing import str

def clean_text(text: str) -> str:
    """
    텍스트에서 불필요한 요소 제거
    """
    # HTML 태그 제거
    text = re.sub(r'<[^>]+>', '', text)

    # 여러 공백을 하나로
    text = re.sub(r'\s+', ' ', text)

    # 특수 문자 제거 (선택적)
    text = re.sub(r'[^\w\s가-힣.,!?-]', '', text)

    # 앞뒤 공백 제거
    text = text.strip()

    return text

# 사용 예시
raw_html = """
<div class="content">
    <h1>제목입니다</h1>
    <p>이것은    여러   공백이   있는    텍스트입니다.</p>
    <script>alert('XSS')</script>
</div>
"""

cleaned = clean_text(raw_html)
# 결과: "제목입니다 이것은 여러 공백이 있는 텍스트입니다."
```

### 2.2 청킹 (Chunking)

긴 문서를 의미있는 단위로 분할:

```python
from typing import List

def chunk_text(
    text: str,
    chunk_size: int = 1000,  # tokens
    overlap: int = 200       # overlap between chunks
) -> List[str]:
    """
    텍스트를 청크로 분할 (with overlap for context)
    """
    words = text.split()
    chunks = []

    # 간단한 단어 기반 청킹 (실제로는 토큰 기반 사용)
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = ' '.join(words[start:end])
        chunks.append(chunk)
        start = end - overlap  # overlap 적용

    return chunks

# 사용 예시
long_document = "..." # 10,000 words
chunks = chunk_text(long_document, chunk_size=500, overlap=50)

# 각 청크를 독립적으로 처리하거나
# 벡터 DB에 저장하여 검색에 활용
```

**왜 Overlap이 필요한가?**

```python
# ❌ Overlap 없음
chunk1 = "...and the main character decided to"
chunk2 = "leave the city and never return..."
# 문맥이 끊김!

# ✅ Overlap 있음
chunk1 = "...and the main character decided to leave the city..."
chunk2 = "...decided to leave the city and never return..."
# 문맥이 유지됨!
```

### 2.3 정규화 (Normalization)

일관된 형식으로 데이터 변환:

```python
from datetime import datetime
import re

def normalize_data(text: str) -> str:
    """
    데이터를 일관된 형식으로 정규화
    """
    # 날짜 형식 통일
    # "2024/01/01", "2024.01.01", "01-01-2024" -> "2024-01-01"
    date_patterns = [
        (r'(\d{4})[/.](\d{2})[/.](\d{2})', r'\1-\2-\3'),
        (r'(\d{2})-(\d{2})-(\d{4})', r'\3-\1-\2'),
    ]

    for pattern, replacement in date_patterns:
        text = re.sub(pattern, replacement, text)

    # 화폐 형식 통일
    # "$1,000", "1000 USD", "₩1,000" -> "1000 USD"
    text = re.sub(r'\$(\d{1,3}(?:,\d{3})*)', r'\1 USD', text)
    text = re.sub(r'₩(\d{1,3}(?:,\d{3})*)', r'\1 KRW', text)

    # 대소문자 통일 (선택적)
    # text = text.lower()

    return text

# 사용 예시
messy_data = """
Meeting: 2024/01/15
Budget: $50,000
Deadline: 15-03-2024
Cost: ₩1,000,000
"""

normalized = normalize_data(messy_data)
# 결과:
# Meeting: 2024-01-15
# Budget: 50000 USD
# Deadline: 2024-03-15
# Cost: 1000000 KRW
```

### 2.4 중복 제거 (Deduplication)

```python
from typing import List, Set

def remove_duplicates(texts: List[str], similarity_threshold: float = 0.9) -> List[str]:
    """
    유사하거나 중복된 텍스트 제거
    """
    unique_texts = []
    seen_hashes: Set[str] = set()

    for text in texts:
        # 간단한 해시 기반 중복 제거
        text_hash = hash(text.strip().lower())

        if text_hash not in seen_hashes:
            unique_texts.append(text)
            seen_hashes.add(text_hash)

    return unique_texts

# 고급: Semantic Similarity 기반 중복 제거
from sentence_transformers import SentenceTransformer
import numpy as np

def remove_semantic_duplicates(
    texts: List[str],
    threshold: float = 0.9
) -> List[str]:
    """
    의미적으로 유사한 텍스트 제거
    """
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = model.encode(texts)

    unique_indices = []
    for i, emb1 in enumerate(embeddings):
        is_duplicate = False
        for j in unique_indices:
            # Cosine similarity
            similarity = np.dot(emb1, embeddings[j]) / (
                np.linalg.norm(emb1) * np.linalg.norm(embeddings[j])
            )
            if similarity > threshold:
                is_duplicate = True
                break

        if not is_duplicate:
            unique_indices.append(i)

    return [texts[i] for i in unique_indices]
```

### 2.5 구조화 (Structuring)

비구조화된 데이터를 구조화:

```python
from typing import Dict, Any
import json

def structure_log_data(log_text: str) -> Dict[str, Any]:
    """
    로그 텍스트를 구조화된 JSON으로 변환
    """
    # 예: 서버 로그 파싱
    log_pattern = r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] (\w+): (.+)'

    import re
    matches = re.findall(log_pattern, log_text)

    structured_logs = []
    for timestamp, level, message in matches:
        structured_logs.append({
            'timestamp': timestamp,
            'level': level,
            'message': message
        })

    return {
        'total_logs': len(structured_logs),
        'logs': structured_logs,
        'errors': [log for log in structured_logs if log['level'] == 'ERROR']
    }

# 사용 예시
raw_logs = """
[2024-01-01 10:00:00] INFO: Server started
[2024-01-01 10:00:05] ERROR: Connection failed
[2024-01-01 10:00:10] INFO: Retrying...
"""

structured = structure_log_data(raw_logs)
print(json.dumps(structured, indent=2, ensure_ascii=False))
# {
#   "total_logs": 3,
#   "logs": [...],
#   "errors": [{"timestamp": "2024-01-01 10:00:05", ...}]
# }
```

## 3. 전처리 전략 by Use Case

### 3.1 RAG (Retrieval-Augmented Generation)

```python
from typing import List, Dict
from sentence_transformers import SentenceTransformer
import chromadb

class RAGPreprocessor:
    """
    RAG를 위한 문서 전처리 파이프라인
    """
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.client = chromadb.Client()
        self.collection = self.client.create_collection("documents")

    def preprocess_for_rag(self, documents: List[str]) -> List[Dict[str, Any]]:
        """
        RAG용 문서 전처리
        1. Clean
        2. Chunk
        3. Embed
        4. Store in Vector DB
        """
        processed_docs = []

        for doc_id, doc in enumerate(documents):
            # 1. Clean
            cleaned = clean_text(doc)

            # 2. Chunk with metadata
            chunks = chunk_text(cleaned, chunk_size=500, overlap=50)

            for chunk_id, chunk in enumerate(chunks):
                # 3. Embed
                embedding = self.model.encode(chunk)

                # 4. Store with metadata
                metadata = {
                    'doc_id': doc_id,
                    'chunk_id': chunk_id,
                    'length': len(chunk)
                }

                self.collection.add(
                    embeddings=[embedding.tolist()],
                    documents=[chunk],
                    metadatas=[metadata],
                    ids=[f"doc{doc_id}_chunk{chunk_id}"]
                )

                processed_docs.append({
                    'text': chunk,
                    'metadata': metadata
                })

        return processed_docs

    def retrieve(self, query: str, top_k: int = 3) -> List[str]:
        """
        쿼리와 관련된 문서 검색
        """
        query_embedding = self.model.encode(query)

        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k
        )

        return results['documents'][0]

# 사용 예시
preprocessor = RAGPreprocessor()

documents = [
    "Python은 동적 타입 언어입니다...",
    "Java는 정적 타입 언어입니다...",
    # ... more documents
]

# 전처리 및 저장
processed = preprocessor.preprocess_for_rag(documents)

# 검색 및 생성
query = "Python의 타입 시스템은?"
relevant_docs = preprocessor.retrieve(query, top_k=3)

# LLM에 전달
context = "\n\n".join(relevant_docs)
prompt = f"""
Context:
{context}

Question: {query}

Answer:
"""
```

### 3.2 Fine-tuning 데이터 준비

```python
from typing import List, Dict, Tuple
import json

class FineTuningPreprocessor:
    """
    Fine-tuning을 위한 데이터 전처리
    """
    @staticmethod
    def prepare_instruction_dataset(
        examples: List[Tuple[str, str, str]]
    ) -> List[Dict[str, str]]:
        """
        Instruction-following 형식으로 변환

        Args:
            examples: List of (instruction, input, output) tuples
        """
        dataset = []

        for instruction, user_input, expected_output in examples:
            # OpenAI fine-tuning format
            formatted = {
                "messages": [
                    {
                        "role": "system",
                        "content": instruction
                    },
                    {
                        "role": "user",
                        "content": user_input
                    },
                    {
                        "role": "assistant",
                        "content": expected_output
                    }
                ]
            }
            dataset.append(formatted)

        return dataset

    @staticmethod
    def validate_dataset(dataset: List[Dict]) -> Tuple[bool, List[str]]:
        """
        데이터셋 유효성 검사
        """
        errors = []

        for i, example in enumerate(dataset):
            # 필수 필드 확인
            if 'messages' not in example:
                errors.append(f"Example {i}: Missing 'messages' field")
                continue

            messages = example['messages']

            # 메시지 개수 확인
            if len(messages) < 2:
                errors.append(f"Example {i}: Need at least 2 messages")

            # Role 확인
            roles = [msg['role'] for msg in messages]
            if roles[-1] != 'assistant':
                errors.append(f"Example {i}: Last message must be 'assistant'")

            # 토큰 길이 확인 (대략적)
            total_tokens = sum(len(msg['content'].split()) for msg in messages)
            if total_tokens > 4000:  # 예시 제한
                errors.append(f"Example {i}: Too long ({total_tokens} tokens)")

        return len(errors) == 0, errors

# 사용 예시
examples = [
    (
        "You are a Python expert. Explain concepts clearly.",
        "What is self in Python?",
        "self는 인스턴스 자기 자신을 가리키는 참조입니다. Java의 this와 동일합니다."
    ),
    # ... more examples
]

preprocessor = FineTuningPreprocessor()
dataset = preprocessor.prepare_instruction_dataset(examples)

# 유효성 검사
is_valid, errors = preprocessor.validate_dataset(dataset)
if not is_valid:
    print("Errors found:")
    for error in errors:
        print(f"  - {error}")
else:
    # JSONL 형식으로 저장
    with open('training_data.jsonl', 'w', encoding='utf-8') as f:
        for example in dataset:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')
```

### 3.3 프롬프트 최적화

```python
from typing import Dict, Any

class PromptPreprocessor:
    """
    프롬프트를 위한 데이터 전처리
    """
    @staticmethod
    def format_for_prompt(data: Dict[str, Any]) -> str:
        """
        구조화된 데이터를 프롬프트 친화적 형식으로 변환
        """
        # JSON을 읽기 쉬운 텍스트로 변환
        formatted_lines = []

        for key, value in data.items():
            # 키 이름을 자연어로 변환
            readable_key = key.replace('_', ' ').title()

            if isinstance(value, list):
                formatted_lines.append(f"{readable_key}:")
                for item in value:
                    formatted_lines.append(f"  - {item}")
            elif isinstance(value, dict):
                formatted_lines.append(f"{readable_key}:")
                for sub_key, sub_value in value.items():
                    formatted_lines.append(f"  {sub_key}: {sub_value}")
            else:
                formatted_lines.append(f"{readable_key}: {value}")

        return "\n".join(formatted_lines)

    @staticmethod
    def compress_for_token_limit(text: str, max_tokens: int = 1000) -> str:
        """
        토큰 제한에 맞게 텍스트 압축
        """
        # 간단한 단어 기반 추정 (실제로는 tiktoken 사용)
        words = text.split()
        estimated_tokens = len(words) * 1.3  # 대략적 추정

        if estimated_tokens <= max_tokens:
            return text

        # 중요도 기반 요약 (실제로는 더 정교한 방법 사용)
        # 여기서는 앞부분 + 뒷부분 유지
        target_words = int(max_tokens / 1.3)
        half = target_words // 2

        compressed = (
            ' '.join(words[:half]) +
            "\n\n[... content truncated ...]\n\n" +
            ' '.join(words[-half:])
        )

        return compressed

# 사용 예시
data = {
    'user_name': 'John Doe',
    'order_items': ['iPhone 15', 'AirPods', 'MagSafe Charger'],
    'shipping_address': {
        'street': '123 Main St',
        'city': 'Seoul',
        'country': 'Korea'
    },
    'total_amount': 1500000
}

preprocessor = PromptPreprocessor()
formatted = preprocessor.format_for_prompt(data)

print(formatted)
# User Name: John Doe
# Order Items:
#   - iPhone 15
#   - AirPods
#   - MagSafe Charger
# Shipping Address:
#   street: 123 Main St
#   city: Seoul
#   country: Korea
# Total Amount: 1500000

# LLM에 전달하기 좋은 형식!
```

## 4. 실무에서의 전처리 파이프라인

### 4.1 전체 파이프라인 예시

```python
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

@dataclass
class PreprocessingConfig:
    """전처리 설정"""
    max_length: int = 1000
    chunk_size: int = 500
    chunk_overlap: int = 50
    remove_html: bool = True
    remove_special_chars: bool = True
    normalize_whitespace: bool = True
    deduplicate: bool = True

class DataPreprocessingPipeline:
    """
    실무용 데이터 전처리 파이프라인
    """
    def __init__(self, config: Optional[PreprocessingConfig] = None):
        self.config = config or PreprocessingConfig()
        self.logger = logging.getLogger(__name__)

    def process(self, raw_data: List[str]) -> List[Dict[str, Any]]:
        """
        전체 전처리 파이프라인 실행
        """
        self.logger.info(f"Starting preprocessing for {len(raw_data)} documents")

        # Step 1: Clean
        cleaned = [self._clean(doc) for doc in raw_data]
        self.logger.info(f"Cleaning complete: {len(cleaned)} documents")

        # Step 2: Deduplicate
        if self.config.deduplicate:
            cleaned = remove_duplicates(cleaned)
            self.logger.info(f"After deduplication: {len(cleaned)} documents")

        # Step 3: Chunk
        chunked = []
        for doc in cleaned:
            chunks = chunk_text(
                doc,
                chunk_size=self.config.chunk_size,
                overlap=self.config.chunk_overlap
            )
            chunked.extend(chunks)
        self.logger.info(f"Chunking complete: {len(chunked)} chunks")

        # Step 4: Validate and filter
        valid_chunks = [
            chunk for chunk in chunked
            if self._is_valid_chunk(chunk)
        ]
        self.logger.info(f"After validation: {len(valid_chunks)} chunks")

        # Step 5: Format
        formatted = [
            {
                'text': chunk,
                'metadata': self._extract_metadata(chunk),
                'token_count': self._estimate_tokens(chunk)
            }
            for chunk in valid_chunks
        ]

        self.logger.info("Preprocessing complete")
        return formatted

    def _clean(self, text: str) -> str:
        """텍스트 정제"""
        if self.config.remove_html:
            text = clean_text(text)

        if self.config.normalize_whitespace:
            text = ' '.join(text.split())

        return text

    def _is_valid_chunk(self, chunk: str) -> bool:
        """청크 유효성 검사"""
        # 너무 짧은 청크 제외
        if len(chunk.split()) < 10:
            return False

        # 의미없는 반복 문자 제외
        if len(set(chunk)) < 10:
            return False

        return True

    def _extract_metadata(self, chunk: str) -> Dict[str, Any]:
        """메타데이터 추출"""
        return {
            'length': len(chunk),
            'word_count': len(chunk.split()),
            'has_code': '```' in chunk or 'def ' in chunk or 'class ' in chunk
        }

    def _estimate_tokens(self, text: str) -> int:
        """토큰 수 추정 (간단한 버전)"""
        # 실제로는 tiktoken 사용
        return int(len(text.split()) * 1.3)

# 사용 예시
raw_documents = [
    "<html><body>Document 1 content...</body></html>",
    "Document 2 content...",
    # ... more documents
]

config = PreprocessingConfig(
    max_length=2000,
    chunk_size=500,
    deduplicate=True
)

pipeline = DataPreprocessingPipeline(config)
processed = pipeline.process(raw_documents)

print(f"Processed {len(processed)} chunks")
for chunk in processed[:3]:
    print(f"- Tokens: {chunk['token_count']}, Length: {chunk['metadata']['length']}")
```

### 4.2 모니터링 및 품질 관리

```python
from typing import List, Dict
from collections import Counter
import matplotlib.pyplot as plt

class PreprocessingMonitor:
    """
    전처리 품질 모니터링
    """
    @staticmethod
    def analyze_preprocessing_quality(
        original: List[str],
        processed: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        전처리 전후 품질 분석
        """
        # Token distribution
        token_counts = [chunk['token_count'] for chunk in processed]

        # Chunk statistics
        stats = {
            'original_docs': len(original),
            'processed_chunks': len(processed),
            'avg_tokens_per_chunk': sum(token_counts) / len(token_counts),
            'min_tokens': min(token_counts),
            'max_tokens': max(token_counts),
            'total_tokens': sum(token_counts),
            'chunks_with_code': sum(1 for c in processed if c['metadata']['has_code'])
        }

        # Compression ratio
        original_chars = sum(len(doc) for doc in original)
        processed_chars = sum(len(chunk['text']) for chunk in processed)
        stats['compression_ratio'] = processed_chars / original_chars

        return stats

    @staticmethod
    def visualize_token_distribution(processed: List[Dict[str, Any]]):
        """
        토큰 분포 시각화
        """
        token_counts = [chunk['token_count'] for chunk in processed]

        plt.figure(figsize=(10, 6))
        plt.hist(token_counts, bins=50, edgecolor='black')
        plt.xlabel('Token Count')
        plt.ylabel('Frequency')
        plt.title('Token Distribution After Preprocessing')
        plt.axvline(x=sum(token_counts)/len(token_counts),
                    color='r', linestyle='--', label='Mean')
        plt.legend()
        plt.savefig('token_distribution.png')
        plt.close()

# 사용 예시
monitor = PreprocessingMonitor()
stats = monitor.analyze_preprocessing_quality(raw_documents, processed)

print("Preprocessing Quality Report:")
print(f"  Original documents: {stats['original_docs']}")
print(f"  Processed chunks: {stats['processed_chunks']}")
print(f"  Average tokens per chunk: {stats['avg_tokens_per_chunk']:.1f}")
print(f"  Compression ratio: {stats['compression_ratio']:.2%}")
print(f"  Chunks with code: {stats['chunks_with_code']}")
```

## 5. 전처리 Best Practices

### 5.1 ✅ Do's

```python
# ✅ 1. 파이프라인 형태로 구성
def preprocess_pipeline(data):
    data = clean(data)
    data = normalize(data)
    data = chunk(data)
    data = validate(data)
    return data

# ✅ 2. 로깅 추가
import logging
logger = logging.getLogger(__name__)
logger.info(f"Processing {len(data)} documents")

# ✅ 3. 설정 파일 사용
config = {
    'chunk_size': 500,
    'overlap': 50,
    'max_tokens': 4000
}

# ✅ 4. 중간 결과 저장
processed_data.to_parquet('preprocessed_data.parquet')

# ✅ 5. 품질 검증
assert all(len(chunk) > 0 for chunk in chunks)
assert sum(token_counts) < MAX_CONTEXT_LENGTH
```

### 5.2 ❌ Don'ts

```python
# ❌ 1. 전처리 없이 raw 데이터 사용
llm.generate(raw_html_content)  # 비효율적!

# ❌ 2. 하드코딩된 값
chunk_size = 500  # 설정 파일로 관리할 것

# ❌ 3. 에러 핸들링 없음
chunks = [chunk_text(doc) for doc in docs]  # 하나라도 실패하면 전체 실패

# ✅ 올바른 방법
chunks = []
for doc in docs:
    try:
        chunks.extend(chunk_text(doc))
    except Exception as e:
        logger.error(f"Failed to chunk document: {e}")
        continue

# ❌ 4. 토큰 수 무시
prompt = f"Context: {entire_database}\n\nQuestion: {query}"  # 토큰 제한 초과!

# ❌ 5. 중복 데이터 방치
# 같은 내용이 여러 번 포함되면 비용 낭비 + 혼란
```

## 6. 실전 예제: 문서 QA 시스템

### 완전한 전처리 파이프라인

```python
import os
from typing import List, Dict, Any
from dataclasses import dataclass
import chromadb
from sentence_transformers import SentenceTransformer
import openai

@dataclass
class Document:
    """문서 데이터 클래스"""
    content: str
    metadata: Dict[str, Any]

class DocumentQASystem:
    """
    문서 기반 QA 시스템 (전처리 포함)
    """
    def __init__(self, openai_api_key: str):
        self.preprocessor = DataPreprocessingPipeline()
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.chroma_client = chromadb.Client()
        self.collection = self.chroma_client.create_collection("qa_docs")
        openai.api_key = openai_api_key

    def ingest_documents(self, documents: List[Document]):
        """
        문서 수집 및 전처리
        """
        print(f"Ingesting {len(documents)} documents...")

        # 1. 원본 텍스트 추출
        raw_texts = [doc.content for doc in documents]

        # 2. 전처리
        processed = self.preprocessor.process(raw_texts)
        print(f"Preprocessed into {len(processed)} chunks")

        # 3. 임베딩 및 저장
        for i, chunk_data in enumerate(processed):
            embedding = self.embedding_model.encode(chunk_data['text'])

            self.collection.add(
                embeddings=[embedding.tolist()],
                documents=[chunk_data['text']],
                metadatas=[chunk_data['metadata']],
                ids=[f"chunk_{i}"]
            )

        print("Ingestion complete!")

    def answer_question(self, question: str, top_k: int = 3) -> str:
        """
        질문에 답변
        """
        # 1. 질문 임베딩
        question_embedding = self.embedding_model.encode(question)

        # 2. 관련 문서 검색
        results = self.collection.query(
            query_embeddings=[question_embedding.tolist()],
            n_results=top_k
        )

        relevant_docs = results['documents'][0]

        # 3. 컨텍스트 구성
        context = "\n\n---\n\n".join(relevant_docs)

        # 4. LLM에 질문
        prompt = f"""
다음 문서를 참고하여 질문에 답변해주세요.

문서:
{context}

질문: {question}

답변:
"""

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )

        return response.choices[0].message.content

# 사용 예시
qa_system = DocumentQASystem(openai_api_key=os.getenv("OPENAI_API_KEY"))

# 문서 수집
documents = [
    Document(
        content="""
        Python의 self는 인스턴스 자기 자신을 가리키는 참조입니다.
        Java의 this와 동일한 역할을 합니다.
        모든 인스턴스 메서드의 첫 번째 매개변수로 self를 명시해야 합니다.
        """,
        metadata={'source': 'python_guide.md', 'section': 'self'}
    ),
    Document(
        content="""
        Python의 *args는 가변 위치 인자를 튜플로 받습니다.
        **kwargs는 가변 키워드 인자를 딕셔너리로 받습니다.
        함수가 유연하게 인자를 받을 수 있게 해줍니다.
        """,
        metadata={'source': 'python_guide.md', 'section': 'args_kwargs'}
    ),
    # ... more documents
]

# 문서 수집 및 전처리
qa_system.ingest_documents(documents)

# 질문하기
question = "Python의 self는 무엇인가요?"
answer = qa_system.answer_question(question)
print(f"Q: {question}")
print(f"A: {answer}")
```

## 7. 성능 최적화 팁

### 7.1 배치 처리

```python
from typing import List
import asyncio

async def process_batch_async(documents: List[str], batch_size: int = 100):
    """
    비동기 배치 처리로 성능 향상
    """
    results = []

    for i in range(0, len(documents), batch_size):
        batch = documents[i:i+batch_size]

        # 배치 내 문서를 병렬 처리
        tasks = [process_document_async(doc) for doc in batch]
        batch_results = await asyncio.gather(*tasks)

        results.extend(batch_results)

    return results

async def process_document_async(document: str) -> Dict[str, Any]:
    """
    단일 문서 비동기 처리
    """
    # 전처리 작업 (I/O bound)
    cleaned = clean_text(document)
    chunks = chunk_text(cleaned)

    return {
        'original_length': len(document),
        'processed_chunks': len(chunks)
    }

# 사용
documents = [...]  # 10,000 documents
results = asyncio.run(process_batch_async(documents, batch_size=100))
```

### 7.2 캐싱

```python
from functools import lru_cache
import hashlib

class CachedPreprocessor:
    """
    캐싱을 사용한 전처리기
    """
    def __init__(self):
        self.cache = {}

    def process_with_cache(self, text: str) -> str:
        """
        캐시를 사용한 전처리
        """
        # 텍스트 해시 생성
        text_hash = hashlib.md5(text.encode()).hexdigest()

        # 캐시 확인
        if text_hash in self.cache:
            return self.cache[text_hash]

        # 전처리 수행
        processed = self._expensive_preprocessing(text)

        # 캐시 저장
        self.cache[text_hash] = processed

        return processed

    def _expensive_preprocessing(self, text: str) -> str:
        """
        비용이 큰 전처리 작업
        """
        # 정제, 정규화, 청킹 등
        return clean_text(text)

# 또는 함수 레벨 캐싱
@lru_cache(maxsize=1000)
def cached_clean_text(text: str) -> str:
    """
    LRU 캐시를 사용한 텍스트 정제
    """
    return clean_text(text)
```

## 8. 요약

### 전처리가 필요한 이유

| 이유 | 설명 | 영향 |
|-----|------|------|
| **토큰 제한** | LLM은 처리 가능한 토큰 수가 제한됨 | 불필요한 데이터 제거 필수 |
| **비용** | 토큰당 과금 | 전처리로 90% 비용 절감 가능 |
| **응답 품질** | 노이즈가 많으면 주의 분산 | 깨끗한 데이터 = 정확한 답변 |
| **속도** | 입력이 적을수록 빠름 | 전처리로 응답 시간 단축 |

### 핵심 전처리 작업

1. **텍스트 정제** (Text Cleaning)
   - HTML 태그 제거
   - 불필요한 공백 정리
   - 특수 문자 처리

2. **청킹** (Chunking)
   - 긴 문서를 의미있는 단위로 분할
   - Overlap으로 문맥 유지

3. **정규화** (Normalization)
   - 일관된 형식으로 변환
   - 날짜, 화폐, 대소문자 통일

4. **중복 제거** (Deduplication)
   - 동일하거나 유사한 내용 제거
   - 토큰 낭비 방지

5. **구조화** (Structuring)
   - 비구조화된 데이터를 JSON 등으로 변환
   - LLM이 이해하기 쉬운 형태

### 실무 체크리스트

```
✅ 데이터 정제 (Clean)
✅ 토큰 수 체크 (Token Count)
✅ 청크 크기 최적화 (Chunk Size)
✅ 중복 제거 (Deduplicate)
✅ 메타데이터 추가 (Metadata)
✅ 품질 검증 (Validate)
✅ 로깅 및 모니터링 (Monitor)
✅ 캐싱 (Cache)
```

## 관련 문서

- Python의 Type Hints와 데이터 검증
- Python Collection Types 비교
- 실전 Python 비동기 처리 (asyncio)
