import re
import pdfplumber

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
            f"{self.date}, "
            f"{self.description}, "
            f"{self.amount}"
        )


class Section:
    def __init__(self, name, transactions):
        self.name = name
        self.transactions = transactions

    def __str__(self):
        return f"{self.name}\n{[str(t) for t in self.transactions]}"


def extract_with_pdf_plumber(pdf_path):
    sections = []
    current_section_transactions = []
    current_section_name = None
    with pdfplumber.open(pdf_path) as pdf:
        is_in_date_range = False
        previous_line = None
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
    return sections


if __name__ == "__main__":
    sections = extract_with_pdf_plumber(path)
    for section in sections:
        print(section.name)
        for transaction in section.transactions:
            print(f"\t{transaction}")
