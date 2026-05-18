from pathlib import Path
import re


RAW_DIR = Path("./raw")


PATTERN = re.compile(
    r"^_(\d+)_([a-z0-9_]+)-(\d+)\.txt$"
)


def main() -> None:
    files = sorted(RAW_DIR.glob("*.txt"))

    renamed = 0

    for file_path in files:
        match = PATTERN.match(file_path.name)

        if not match:
            print(f"Skipping: {file_path.name}")
            continue

        book_number = int(match.group(1))
        slug = match.group(2)
        chapter = match.group(3)

        new_name = (
            f"_{book_number:02d}_"
            f"{slug}-"
            f"{chapter}.txt"
        )

        if new_name == file_path.name:
            continue

        new_path = file_path.with_name(new_name)

        print(
            f"{file_path.name} -> {new_name}"
        )

        file_path.rename(new_path)

        renamed += 1

    print()
    print(f"Renamed files: {renamed}")


if __name__ == "__main__":
    main()

# eladfinish@Elads-MacBook-Pro Bible-RAG % python3 rename_books.py
# _1_bereshit-01.txt -> _01_bereshit-01.txt
# _1_bereshit-02.txt -> _01_bereshit-02.txt
# _1_bereshit-03.txt -> _01_bereshit-03.txt
# _1_bereshit-04.txt -> _01_bereshit-04.txt
# _1_bereshit-05.txt -> _01_bereshit-05.txt
# _1_bereshit-06.txt -> _01_bereshit-06.txt
# _1_bereshit-07.txt -> _01_bereshit-07.txt
# _1_bereshit-08.txt -> _01_bereshit-08.txt
# _1_bereshit-09.txt -> _01_bereshit-09.txt
# _1_bereshit-10.txt -> _01_bereshit-10.txt
# _1_bereshit-11.txt -> _01_bereshit-11.txt
# _1_bereshit-12.txt -> _01_bereshit-12.txt
# _1_bereshit-13.txt -> _01_bereshit-13.txt
# _1_bereshit-14.txt -> _01_bereshit-14.txt
# _1_bereshit-15.txt -> _01_bereshit-15.txt
# _1_bereshit-16.txt -> _01_bereshit-16.txt
# _1_bereshit-17.txt -> _01_bereshit-17.txt
# _1_bereshit-18.txt -> _01_bereshit-18.txt
# _1_bereshit-19.txt -> _01_bereshit-19.txt
# _1_bereshit-20.txt -> _01_bereshit-20.txt
# _1_bereshit-21.txt -> _01_bereshit-21.txt
# _1_bereshit-22.txt -> _01_bereshit-22.txt
# _1_bereshit-23.txt -> _01_bereshit-23.txt
# _1_bereshit-24.txt -> _01_bereshit-24.txt
# _1_bereshit-25.txt -> _01_bereshit-25.txt
# _1_bereshit-26.txt -> _01_bereshit-26.txt
# _1_bereshit-27.txt -> _01_bereshit-27.txt
# _1_bereshit-28.txt -> _01_bereshit-28.txt
# _1_bereshit-29.txt -> _01_bereshit-29.txt
# _1_bereshit-30.txt -> _01_bereshit-30.txt
# _1_bereshit-31.txt -> _01_bereshit-31.txt
# _1_bereshit-32.txt -> _01_bereshit-32.txt
# _1_bereshit-33.txt -> _01_bereshit-33.txt
# _1_bereshit-34.txt -> _01_bereshit-34.txt
# _1_bereshit-35.txt -> _01_bereshit-35.txt
# _1_bereshit-36.txt -> _01_bereshit-36.txt
# _1_bereshit-37.txt -> _01_bereshit-37.txt
# _1_bereshit-38.txt -> _01_bereshit-38.txt
# _1_bereshit-39.txt -> _01_bereshit-39.txt
# _1_bereshit-40.txt -> _01_bereshit-40.txt
# _1_bereshit-41.txt -> _01_bereshit-41.txt
# _1_bereshit-42.txt -> _01_bereshit-42.txt
# _1_bereshit-43.txt -> _01_bereshit-43.txt
# _1_bereshit-44.txt -> _01_bereshit-44.txt
# _1_bereshit-45.txt -> _01_bereshit-45.txt
# _1_bereshit-46.txt -> _01_bereshit-46.txt
# _1_bereshit-47.txt -> _01_bereshit-47.txt
# _1_bereshit-48.txt -> _01_bereshit-48.txt
# _1_bereshit-49.txt -> _01_bereshit-49.txt
# _1_bereshit-50.txt -> _01_bereshit-50.txt
# _2_shemot-01.txt -> _02_shemot-01.txt
# _2_shemot-02.txt -> _02_shemot-02.txt
# _2_shemot-03.txt -> _02_shemot-03.txt
# _2_shemot-04.txt -> _02_shemot-04.txt
# _2_shemot-05.txt -> _02_shemot-05.txt
# _2_shemot-06.txt -> _02_shemot-06.txt
# _2_shemot-07.txt -> _02_shemot-07.txt
# _2_shemot-08.txt -> _02_shemot-08.txt
# _2_shemot-09.txt -> _02_shemot-09.txt
# _2_shemot-10.txt -> _02_shemot-10.txt
# _2_shemot-11.txt -> _02_shemot-11.txt
# _2_shemot-12.txt -> _02_shemot-12.txt
# _2_shemot-13.txt -> _02_shemot-13.txt
# _2_shemot-14.txt -> _02_shemot-14.txt
# _2_shemot-15.txt -> _02_shemot-15.txt
# _2_shemot-16.txt -> _02_shemot-16.txt
# _2_shemot-17.txt -> _02_shemot-17.txt
# _2_shemot-18.txt -> _02_shemot-18.txt
# _2_shemot-19.txt -> _02_shemot-19.txt
# _2_shemot-20.txt -> _02_shemot-20.txt
# _2_shemot-21.txt -> _02_shemot-21.txt
# _2_shemot-22.txt -> _02_shemot-22.txt
# _2_shemot-23.txt -> _02_shemot-23.txt
# _2_shemot-24.txt -> _02_shemot-24.txt
# _2_shemot-25.txt -> _02_shemot-25.txt
# _2_shemot-26.txt -> _02_shemot-26.txt
# _2_shemot-27.txt -> _02_shemot-27.txt
# _2_shemot-28.txt -> _02_shemot-28.txt
# _2_shemot-29.txt -> _02_shemot-29.txt
# _2_shemot-30.txt -> _02_shemot-30.txt
# _2_shemot-31.txt -> _02_shemot-31.txt
# _2_shemot-32.txt -> _02_shemot-32.txt
# _2_shemot-33.txt -> _02_shemot-33.txt
# _2_shemot-34.txt -> _02_shemot-34.txt
# _2_shemot-35.txt -> _02_shemot-35.txt
# _2_shemot-36.txt -> _02_shemot-36.txt
# _2_shemot-37.txt -> _02_shemot-37.txt
# _2_shemot-38.txt -> _02_shemot-38.txt
# _2_shemot-39.txt -> _02_shemot-39.txt
# _2_shemot-40.txt -> _02_shemot-40.txt
# _3_vayikra-01.txt -> _03_vayikra-01.txt
# _3_vayikra-02.txt -> _03_vayikra-02.txt
# _3_vayikra-03.txt -> _03_vayikra-03.txt
# _3_vayikra-04.txt -> _03_vayikra-04.txt
# _3_vayikra-05.txt -> _03_vayikra-05.txt
# _3_vayikra-06.txt -> _03_vayikra-06.txt
# _3_vayikra-07.txt -> _03_vayikra-07.txt
# _3_vayikra-08.txt -> _03_vayikra-08.txt
# _3_vayikra-09.txt -> _03_vayikra-09.txt
# _3_vayikra-10.txt -> _03_vayikra-10.txt
# _3_vayikra-11.txt -> _03_vayikra-11.txt
# _3_vayikra-12.txt -> _03_vayikra-12.txt
# _3_vayikra-13.txt -> _03_vayikra-13.txt
# _3_vayikra-14.txt -> _03_vayikra-14.txt
# _3_vayikra-15.txt -> _03_vayikra-15.txt
# _3_vayikra-16.txt -> _03_vayikra-16.txt
# _3_vayikra-17.txt -> _03_vayikra-17.txt
# _3_vayikra-18.txt -> _03_vayikra-18.txt
# _3_vayikra-19.txt -> _03_vayikra-19.txt
# _3_vayikra-20.txt -> _03_vayikra-20.txt
# _3_vayikra-21.txt -> _03_vayikra-21.txt
# _3_vayikra-22.txt -> _03_vayikra-22.txt
# _3_vayikra-23.txt -> _03_vayikra-23.txt
# _3_vayikra-24.txt -> _03_vayikra-24.txt
# _3_vayikra-25.txt -> _03_vayikra-25.txt
# _3_vayikra-26.txt -> _03_vayikra-26.txt
# _3_vayikra-27.txt -> _03_vayikra-27.txt
# _4_bamidbar-01.txt -> _04_bamidbar-01.txt
# _4_bamidbar-02.txt -> _04_bamidbar-02.txt
# _4_bamidbar-03.txt -> _04_bamidbar-03.txt
# _4_bamidbar-04.txt -> _04_bamidbar-04.txt
# _4_bamidbar-05.txt -> _04_bamidbar-05.txt
# _4_bamidbar-06.txt -> _04_bamidbar-06.txt
# _4_bamidbar-07.txt -> _04_bamidbar-07.txt
# _4_bamidbar-08.txt -> _04_bamidbar-08.txt
# _4_bamidbar-09.txt -> _04_bamidbar-09.txt
# _4_bamidbar-10.txt -> _04_bamidbar-10.txt
# _4_bamidbar-11.txt -> _04_bamidbar-11.txt
# _4_bamidbar-12.txt -> _04_bamidbar-12.txt
# _4_bamidbar-13.txt -> _04_bamidbar-13.txt
# _4_bamidbar-14.txt -> _04_bamidbar-14.txt
# _4_bamidbar-15.txt -> _04_bamidbar-15.txt
# _4_bamidbar-16.txt -> _04_bamidbar-16.txt
# _4_bamidbar-17.txt -> _04_bamidbar-17.txt
# _4_bamidbar-18.txt -> _04_bamidbar-18.txt
# _4_bamidbar-19.txt -> _04_bamidbar-19.txt
# _4_bamidbar-20.txt -> _04_bamidbar-20.txt
# _4_bamidbar-21.txt -> _04_bamidbar-21.txt
# _4_bamidbar-22.txt -> _04_bamidbar-22.txt
# _4_bamidbar-23.txt -> _04_bamidbar-23.txt
# _4_bamidbar-24.txt -> _04_bamidbar-24.txt
# _4_bamidbar-25.txt -> _04_bamidbar-25.txt
# _4_bamidbar-26.txt -> _04_bamidbar-26.txt
# _4_bamidbar-27.txt -> _04_bamidbar-27.txt
# _4_bamidbar-28.txt -> _04_bamidbar-28.txt
# _4_bamidbar-29.txt -> _04_bamidbar-29.txt
# _4_bamidbar-30.txt -> _04_bamidbar-30.txt
# _4_bamidbar-31.txt -> _04_bamidbar-31.txt
# _4_bamidbar-32.txt -> _04_bamidbar-32.txt
# _4_bamidbar-33.txt -> _04_bamidbar-33.txt
# _4_bamidbar-34.txt -> _04_bamidbar-34.txt
# _4_bamidbar-35.txt -> _04_bamidbar-35.txt
# _4_bamidbar-36.txt -> _04_bamidbar-36.txt
# _5_devarim-01.txt -> _05_devarim-01.txt
# _5_devarim-02.txt -> _05_devarim-02.txt
# _5_devarim-03.txt -> _05_devarim-03.txt
# _5_devarim-04.txt -> _05_devarim-04.txt
# _5_devarim-05.txt -> _05_devarim-05.txt
# _5_devarim-06.txt -> _05_devarim-06.txt
# _5_devarim-07.txt -> _05_devarim-07.txt
# _5_devarim-08.txt -> _05_devarim-08.txt
# _5_devarim-09.txt -> _05_devarim-09.txt
# _5_devarim-10.txt -> _05_devarim-10.txt
# _5_devarim-11.txt -> _05_devarim-11.txt
# _5_devarim-12.txt -> _05_devarim-12.txt
# _5_devarim-13.txt -> _05_devarim-13.txt
# _5_devarim-14.txt -> _05_devarim-14.txt
# _5_devarim-15.txt -> _05_devarim-15.txt
# _5_devarim-16.txt -> _05_devarim-16.txt
# _5_devarim-17.txt -> _05_devarim-17.txt
# _5_devarim-18.txt -> _05_devarim-18.txt
# _5_devarim-19.txt -> _05_devarim-19.txt
# _5_devarim-20.txt -> _05_devarim-20.txt
# _5_devarim-21.txt -> _05_devarim-21.txt
# _5_devarim-22.txt -> _05_devarim-22.txt
# _5_devarim-23.txt -> _05_devarim-23.txt
# _5_devarim-24.txt -> _05_devarim-24.txt
# _5_devarim-25.txt -> _05_devarim-25.txt
# _5_devarim-26.txt -> _05_devarim-26.txt
# _5_devarim-27.txt -> _05_devarim-27.txt
# _5_devarim-28.txt -> _05_devarim-28.txt
# _5_devarim-29.txt -> _05_devarim-29.txt
# _5_devarim-30.txt -> _05_devarim-30.txt
# _5_devarim-31.txt -> _05_devarim-31.txt
# _5_devarim-32.txt -> _05_devarim-32.txt
# _5_devarim-33.txt -> _05_devarim-33.txt
# _5_devarim-34.txt -> _05_devarim-34.txt
# _6_yehoshua-01.txt -> _06_yehoshua-01.txt
# _6_yehoshua-02.txt -> _06_yehoshua-02.txt
# _6_yehoshua-03.txt -> _06_yehoshua-03.txt
# _6_yehoshua-04.txt -> _06_yehoshua-04.txt
# _6_yehoshua-05.txt -> _06_yehoshua-05.txt
# _6_yehoshua-06.txt -> _06_yehoshua-06.txt
# _6_yehoshua-07.txt -> _06_yehoshua-07.txt
# _6_yehoshua-08.txt -> _06_yehoshua-08.txt
# _6_yehoshua-09.txt -> _06_yehoshua-09.txt
# _6_yehoshua-10.txt -> _06_yehoshua-10.txt
# _6_yehoshua-11.txt -> _06_yehoshua-11.txt
# _6_yehoshua-12.txt -> _06_yehoshua-12.txt
# _6_yehoshua-13.txt -> _06_yehoshua-13.txt
# _6_yehoshua-14.txt -> _06_yehoshua-14.txt
# _6_yehoshua-15.txt -> _06_yehoshua-15.txt
# _6_yehoshua-16.txt -> _06_yehoshua-16.txt
# _6_yehoshua-17.txt -> _06_yehoshua-17.txt
# _6_yehoshua-18.txt -> _06_yehoshua-18.txt
# _6_yehoshua-19.txt -> _06_yehoshua-19.txt
# _6_yehoshua-20.txt -> _06_yehoshua-20.txt
# _6_yehoshua-21.txt -> _06_yehoshua-21.txt
# _6_yehoshua-22.txt -> _06_yehoshua-22.txt
# _6_yehoshua-23.txt -> _06_yehoshua-23.txt
# _6_yehoshua-24.txt -> _06_yehoshua-24.txt
# _7_shoftim-01.txt -> _07_shoftim-01.txt
# _7_shoftim-02.txt -> _07_shoftim-02.txt
# _7_shoftim-03.txt -> _07_shoftim-03.txt
# _7_shoftim-04.txt -> _07_shoftim-04.txt
# _7_shoftim-05.txt -> _07_shoftim-05.txt
# _7_shoftim-06.txt -> _07_shoftim-06.txt
# _7_shoftim-07.txt -> _07_shoftim-07.txt
# _7_shoftim-08.txt -> _07_shoftim-08.txt
# _7_shoftim-09.txt -> _07_shoftim-09.txt
# _7_shoftim-10.txt -> _07_shoftim-10.txt
# _7_shoftim-11.txt -> _07_shoftim-11.txt
# _7_shoftim-12.txt -> _07_shoftim-12.txt
# _7_shoftim-13.txt -> _07_shoftim-13.txt
# _7_shoftim-14.txt -> _07_shoftim-14.txt
# _7_shoftim-15.txt -> _07_shoftim-15.txt
# _7_shoftim-16.txt -> _07_shoftim-16.txt
# _7_shoftim-17.txt -> _07_shoftim-17.txt
# _7_shoftim-18.txt -> _07_shoftim-18.txt
# _7_shoftim-19.txt -> _07_shoftim-19.txt
# _7_shoftim-20.txt -> _07_shoftim-20.txt
# _7_shoftim-21.txt -> _07_shoftim-21.txt
# _8_shemuel_a-01.txt -> _08_shemuel_a-01.txt
# _8_shemuel_a-02.txt -> _08_shemuel_a-02.txt
# _8_shemuel_a-03.txt -> _08_shemuel_a-03.txt
# _8_shemuel_a-04.txt -> _08_shemuel_a-04.txt
# _8_shemuel_a-05.txt -> _08_shemuel_a-05.txt
# _8_shemuel_a-06.txt -> _08_shemuel_a-06.txt
# _8_shemuel_a-07.txt -> _08_shemuel_a-07.txt
# _8_shemuel_a-08.txt -> _08_shemuel_a-08.txt
# _8_shemuel_a-09.txt -> _08_shemuel_a-09.txt
# _8_shemuel_a-10.txt -> _08_shemuel_a-10.txt
# _8_shemuel_a-11.txt -> _08_shemuel_a-11.txt
# _8_shemuel_a-12.txt -> _08_shemuel_a-12.txt
# _8_shemuel_a-13.txt -> _08_shemuel_a-13.txt
# _8_shemuel_a-14.txt -> _08_shemuel_a-14.txt
# _8_shemuel_a-15.txt -> _08_shemuel_a-15.txt
# _8_shemuel_a-16.txt -> _08_shemuel_a-16.txt
# _8_shemuel_a-17.txt -> _08_shemuel_a-17.txt
# _8_shemuel_a-18.txt -> _08_shemuel_a-18.txt
# _8_shemuel_a-19.txt -> _08_shemuel_a-19.txt
# _8_shemuel_a-20.txt -> _08_shemuel_a-20.txt
# _8_shemuel_a-21.txt -> _08_shemuel_a-21.txt
# _8_shemuel_a-22.txt -> _08_shemuel_a-22.txt
# _8_shemuel_a-23.txt -> _08_shemuel_a-23.txt
# _8_shemuel_a-24.txt -> _08_shemuel_a-24.txt
# _8_shemuel_a-25.txt -> _08_shemuel_a-25.txt
# _8_shemuel_a-26.txt -> _08_shemuel_a-26.txt
# _8_shemuel_a-27.txt -> _08_shemuel_a-27.txt
# _8_shemuel_a-28.txt -> _08_shemuel_a-28.txt
# _8_shemuel_a-29.txt -> _08_shemuel_a-29.txt
# _8_shemuel_a-30.txt -> _08_shemuel_a-30.txt
# _8_shemuel_a-31.txt -> _08_shemuel_a-31.txt
# _9_shemuel_b-01.txt -> _09_shemuel_b-01.txt
# _9_shemuel_b-02.txt -> _09_shemuel_b-02.txt
# _9_shemuel_b-03.txt -> _09_shemuel_b-03.txt
# _9_shemuel_b-04.txt -> _09_shemuel_b-04.txt
# _9_shemuel_b-05.txt -> _09_shemuel_b-05.txt
# _9_shemuel_b-06.txt -> _09_shemuel_b-06.txt
# _9_shemuel_b-07.txt -> _09_shemuel_b-07.txt
# _9_shemuel_b-08.txt -> _09_shemuel_b-08.txt
# _9_shemuel_b-09.txt -> _09_shemuel_b-09.txt
# _9_shemuel_b-10.txt -> _09_shemuel_b-10.txt
# _9_shemuel_b-11.txt -> _09_shemuel_b-11.txt
# _9_shemuel_b-12.txt -> _09_shemuel_b-12.txt
# _9_shemuel_b-13.txt -> _09_shemuel_b-13.txt
# _9_shemuel_b-14.txt -> _09_shemuel_b-14.txt
# _9_shemuel_b-15.txt -> _09_shemuel_b-15.txt
# _9_shemuel_b-16.txt -> _09_shemuel_b-16.txt
# _9_shemuel_b-17.txt -> _09_shemuel_b-17.txt
# _9_shemuel_b-18.txt -> _09_shemuel_b-18.txt
# _9_shemuel_b-19.txt -> _09_shemuel_b-19.txt
# _9_shemuel_b-20.txt -> _09_shemuel_b-20.txt
# _9_shemuel_b-21.txt -> _09_shemuel_b-21.txt
# _9_shemuel_b-22.txt -> _09_shemuel_b-22.txt
# _9_shemuel_b-23.txt -> _09_shemuel_b-23.txt
# _9_shemuel_b-24.txt -> _09_shemuel_b-24.txt
#
# Renamed files: 287
