import os
import sys
from src.rag_system import BibleRAG
from src.utils import logger

def main():
    print("\n" + "="*50)
    print("      BIBLE-RAG: Advanced Retrieval System")
    print("="*50)

    # Check for API Key
    if os.getenv("OPENAI_API_KEY") is None:
        print("WARNING: OPENAI_API_KEY environment variable not set.")
        print("Generation will fail unless you've hardcoded the key in config.py.")

    print("\nInitializing System...")
    try:
        rag = BibleRAG()
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        print("\nERROR: Could not initialize RAG system.")
        print("Please ensure you have run 'python3 -m src.build_index' first.")
        sys.exit(1)

    print("\nSystem Ready. Enter your question below.")
    print("Type 'exit' or 'quit' to close.\n")

    while True:
        try:
            question = input("Q: ").strip()
        except EOFError:
            break

        if question.lower() in ['exit', 'quit', 'צא']:
            print("Goodbye!")
            break

        if not question:
            continue

        print("\nThinking...")
        try:
            result = rag.answer(question)

            print("\n" + "-"*30)
            print("ANSWER:")
            print(result['answer'])
            print("-"*30)

            print("\nSOURCES (Top Ranked):")
            for i, src in enumerate(result['context']):
                print(f"{i+1}. [{src['score']:.4f}] {src['ref_en']} ({src['ref']})")
                # Print a bit of the text for verification
                snippet = src['text'][:120].replace('\n', ' ')
                print(f"   Text: {snippet}...")
            print("-" * 50)

        except Exception as e:
            logger.error(f"Error during query execution: {e}")
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
