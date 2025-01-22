import re
import pdfplumber
from typing import List
import os


path = (
    "/home/sdanilov/Build/PDF-Scraper-for-Bank-of-America-Statements/"
    "data/checking-3675/eStmt_2019-08-22.pdf"
)
date_pattern = re.compile(r"\d{2}/\d{2}/\d{2}")


class Transaction:
    def __init__(self, date, description, amount):
        self.date = date
        self.description = description
        self.amount = amount

    def __str__(self):
        return (
            self.date
            + ", "
            + self.description
            + ","
            + self.amount
        )


class Section:
    def __init__(self, name: str, transactions: List[Transaction]):
        self.name: str = name
        self.transactions: List[Transaction] = transactions

    def __str__(self):
        transaction_strings = [str(t) for t in self.transactions]
        return f"{self.name}\n" + "\n".join(transaction_strings)


class Statement:
    def __init__(self, date: str, sections: List[Section]):
        self.date: str = date
        self.sections: List[Section] = sections

    def __str__(self):
        sections = [str(t) for t in self.sections]
        return f"{self.date}\n" + "\n".join(sections)


def extract_with_pdf_plumber(pdf_path: str) -> Statement:
    sections: List[Section] = []
    current_section_transactions: List[Transaction] = []
    current_section_name: str | None = None
    filename = os.path.basename(pdf_path)
    date_match_filename = re.search(r"eStmt_(\d{4}-\d{2}-\d{2})", filename)
    if date_match_filename:
        statement_date = date_match_filename.group(1)
    else:
        statement_date = "Unknown Date"

    with pdfplumber.open(pdf_path) as pdf:
        is_in_date_range = False
        previous_line: str | None = None
        for page in pdf.pages:
            text = page.extract_text()
            for line in text.splitlines():
                if is_in_date_range:
                    if line.startswith("Total"):
                        is_in_date_range = False
                        if current_section_name:
                            sections.append(
                                Section(current_section_name,
                                        current_section_transactions)
                            )
                            current_section_transactions = []
                            current_section_name = None
                        continue
                    date_match = date_pattern.search(line)
                    if date_match:
                        parts = line.split()  # Simple split
                        date = parts[0]
                        amount = parts[-1]
                        description_parts = parts[1:-1]
                        description = " ".join(description_parts)
                        transaction = Transaction(date,
                                                  description,
                                                  amount)
                        current_section_transactions.append(transaction)
                else:
                    if line.startswith("Date") and line.endswith("Amount"):
                        if previous_line and previous_line.endswith(
                            " - continued"
                        ):
                            previous_line = previous_line.replace(
                                " - continued", ""
                            )
                        current_section_name = previous_line
                        is_in_date_range = True
                previous_line = line
    return Statement(statement_date, sections)


if __name__ == "__main__":
    statement = extract_with_pdf_plumber(path)
    print(statement)
