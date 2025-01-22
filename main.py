import re
import pdfplumber

path = (
    "/home/sdanilov/Build/PDF-Scraper-for-Bank-of-America-Statements/"
    "data/checking-3675/eStmt_2019-08-22.pdf"
)
date_pattern = re.compile(r"\d{2}/\d{2}/\d{2}")


def extract_with_pdf_plumber(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        is_in_date_range = False
        previous_line = None
        for page in pdf.pages:
            text = page.extract_text()
            for line in text.splitlines():
                if is_in_date_range:
                    if line.startswith("Total"):
                        is_in_date_range = False
                        continue
                    if date_pattern.search(line):
                        print(line)
                else:
                    if line.startswith("Date") and line.endswith("Amount"):
                        if previous_line and previous_line.endswith(
                            " - continued"
                        ):
                            previous_line = previous_line.replace(
                                " - continued", ""
                            )
                            print(previous_line)
                        is_in_date_range = True
                previous_line = line


if __name__ == "__main__":
    extract_with_pdf_plumber(path)
