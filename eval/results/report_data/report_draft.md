# Bible-RAG: Custom RAG Pipeline over the Hebrew Tanakh

## 1. Corpus

The corpus used in this project is the full Hebrew Tanakh (Bible), consisting of 929 chapters.
The data is structured hierarchically by book, chapter, and verse.
Tanakh is highly suitable for RAG due to its fact-dense nature (genealogy, history, geography) and the critical importance of exact citations in biblical scholarship.

Key Statistics:
- 929 Chapters
- 23,202 Verses
- Over 30,000 Chunks

## 2. System Architecture

The system follows a modular RAG architecture:
1. **Ingestion**: Processes raw UTF-16 text files into structured JSON.
2. **Preprocessing**: Normalizes Hebrew text, removing cantillation (teamim) for better embedding quality while preserving original text for display.
3. **Indexing**: Uses `intfloat/multilingual-e5-base` embeddings stored in a FAISS vector index (IndexFlatIP for cosine similarity).
4. **Retrieval**: Supports hybrid search combining semantic (Dense) and keyword-based (BM25) retrieval.
5. **Generation**: Uses OpenAI's GPT-4o model with a strict system prompt to ensure grounding and accurate citations.
6. **Interface**: A FastAPI backend serves a React-based web demo with interactive strategy comparison.

## 3. Preprocessing and Chunking

We implement several preprocessing steps:
- `text_plain`: Hebrew text without niqqud or teamim (used for embeddings).
- `display_text`: Original text with niqqud preserved.
- Structural marker extraction (e.g., {פ}, {ס}).

Chunking Strategies:
- **Single Verse**: Each verse is a standalone chunk.
- **Sliding Window**: Overlapping windows of 5 verses to provide broader narrative context.

## 4. Embedding and Indexing

We chose `intfloat/multilingual-e5-base` as the embedding model due to its strong performance in multilingual retrieval tasks. Embeddings are L2-normalized and indexed using **FAISS IndexFlatIP**, enabling efficient and accurate semantic similarity searches.

## 5. Retrieval

The system supports multiple retrieval modes:
- **Dense Only**: Pure vector search.
- **Lexical Only**: BM25 keyword matching (vital for names and specific terms).
- **Hybrid**: A weighted combination of both, optimized for biblical Hebrew.
- **Query Routing**: Detects query types (e.g., genealogy vs. enumeration) to adjust retrieval weights dynamically.

## 6. Answer Generation

The generation engine receives the retrieved chunks and is instructed to:
1. Answer ONLY based on the provided context.
2. Provide exact Book:Chapter:Verse citations.
3. State clearly if the information is missing from the context.

## 7. Evaluation Results

The following table summarizes the retrieval performance of the baseline strategies:

| Strategy | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| hybrid | 0.100 | 0.120 | 0.140 | 0.112 |
| dense_only | 0.060 | 0.080 | 0.080 | 0.067 |
| lexical_only | 0.080 | 0.100 | 0.140 | 0.095 |


## 8. Ablation Study

We conducted ablation experiments to measure the impact of different retrieval and indexing choices.

### Retrieval Strategy Ablation

| Variant | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| hybrid | 0.100 | 0.120 | 0.140 | 0.112 |
| dense_only | 0.060 | 0.080 | 0.080 | 0.067 |
| lexical_only | 0.080 | 0.100 | 0.140 | 0.095 |

### Top-K Ablation (Strategy: Hybrid)

| Top-K | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| 3 | 0.100 | 0.120 | 0.140 | 0.112 |
| 5 | 0.100 | 0.120 | 0.140 | 0.112 |
| 10 | 0.100 | 0.120 | 0.140 | 0.116 |


## 9. Failure Analysis

Common failure modes identified during evaluation:

Total Failures Analyzed: 43

| Category | Count |
|---|---:|
| retrieval_miss | 42 |
| generation_error | 1 |


### Representative Failure Examples:

| Question | Category | Reason | Suggested Fix |
|---|---|---|---|
| באיזה מקום נאמר: "וַיָּבֹא הָעָם ... וַיֵּשְׁבוּ שָׁם עַד הָעֶרֶב לִפְנֵי הָאֱלֹהִים וַיִּשְׂאוּ קוֹלָם וַיִּבְכּוּ בְּכִי גָדוֹל"? | retrieval_miss | No relevant chunks were found in the top retrieved results. | Improve embedding model or add lexical/keyword boost. |
| אַשְׁרֵי אֲנָשֶׁיךָ אַשְׁרֵי עֲבָדֶיךָ אֵלֶּה הָעֹמְדִים לְפָנֶיךָ תָּמִיד הַשֹּׁמְעִים אֶת־חָכְמָתֶךָ מי אמר למי את הדברים? | retrieval_miss | No relevant chunks were found in the top retrieved results. | Improve embedding model or add lexical/keyword boost. |
| כמה זמן היה ארון ה' בשדה פלישתים? | generation_error | Correct context was retrieved, but the LLM failed to extract the correct answer. | Refine the generation prompt or use a more capable LLM. |
| וְאִם־יֶשׁ־בִּי עָון וֶהֱמִתָנִי נאמר ל: | retrieval_miss | No relevant chunks were found in the top retrieved results. | Improve embedding model or add lexical/keyword boost. |
| וּבְנֵי־יִשְׂרָאֵל עָשׂוּ כַּאֲשֶׁר צִוָּה ה' אֶת־מֹשֶׁה. מהו הציווי אותו עשו בני ישראל? | retrieval_miss | No relevant chunks were found in the top retrieved results. | Improve embedding model or add lexical/keyword boost. |


## 10. Future Improvements

1. **Enhanced Metadata Retrieval**: Implementing specialized handlers for structural questions (e.g., book counts).
2. **Reranking Layer**: Adding a second-stage cross-encoder to improve precision.
3. **Better Hebrew Normalization**: Advanced lemmatization to handle complex biblical morphology.
4. **Gold Set Refinement**: Expanding the evaluation set with more granular 'must-cite' identifiers.

