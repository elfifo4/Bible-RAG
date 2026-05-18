from src.rag_system import BibleRAG
import sys

def main():
    print("--- Bible-RAG System ---")

    # Initialize the RAG system
    try:
        rag = BibleRAG()
    except Exception as e:
        print(f"Error initializing RAG system: {e}")
        print("Tip: Make sure you have run 'python -m src.build_index' first.")
        sys.exit(1)

    # Example question
    question = "How was the world created?"
    print(f"\nQuestion: {question}")
    print("Thinking...")

    # Get answer
    result = rag.answer(question)

    # Print results
    print(f"\nAnswer:\n{result['answer']}")

    print("\nSources Cited:")
    for src in result['context']:
        print(f"- {src['ref_en']} ({src['ref']})")
        # To show the actual text retrieved:
        # print(f"  Text: {src['text'][:100]}...")

if __name__ == "__main__":
    main()
