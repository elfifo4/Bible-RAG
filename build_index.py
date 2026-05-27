import os
import sys

# Ensure the project root is in the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.build_index import main

if __name__ == "__main__":
    main()
