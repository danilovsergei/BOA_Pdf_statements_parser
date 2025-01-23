import csv
import re
import pdfplumber
from typing import List
import os
import sys
import argparse

date_pattern = re.compile(r"\d{2}/\d{2}/\d{2}")


class Transaction:
    def __init__(self, date, description, amount):
        self.date = date
        self.description = description
        self.amount = amount

    def __str__(self):
        return self.date + ", " + self.description + "," + self.amount


class Section:
    def __init__(self, name: str, transactions: List[Transaction],
                 account=None):
        self.name: str = name
        self.transactions: List[Transaction] = transactions
        self.account = account

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


def parse_combibed_account_number(line: str) -> str | None:
    """
    Parses the account number from a line of text.

    This account number exists only in combined statements with
    several account numbers

    Args:
        line: The line of text to parse.

    Returns:
        The extracted account number, or None if not found.
    """
    account_match = re.search(
        r"Account number:\s*([\d\s]+)", line)
    if account_match:
        return account_match.group(1).strip()
    return None


def parse_single_global_account_number(line: str) -> str | None:
    """
    Parses the single global account number from a line of text.

    This account number exists in every statement and one per statement
    Example line:
    ! JOHN DOW ! Account # 1234 1234 1234 ! September 21, 2018

    Args:
        line: The line of text to parse.

    Returns:
        The extracted account number, or None if not found.
    """
    account_match = re.search(r"! Account #\s*([\d\s]+)\s*!", line)
    if account_match:
        return account_match.group(1).strip()
    return None


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

    account_number = None  # Initialize account_number

    with pdfplumber.open(pdf_path) as pdf:
        is_in_date_range = False
        previous_line: str | None = None
        for page in pdf.pages:
            text = page.extract_text()
            for line in text.splitlines():
                # global account number is single per statement and
                # always must exist
                global_account_number = parse_single_global_account_number(
                    line)
                if global_account_number:
                    account_number = global_account_number
                # In case of combibed statement override global account number
                # with number from combined statement
                if line.startswith("Account number:"):
                    parsed_account_number = parse_combibed_account_number(line)
                    if parsed_account_number:
                        account_number = parsed_account_number
                if is_in_date_range:
                    if line.startswith("Total"):
                        is_in_date_range = False
                        if current_section_name:
                            sections.append(
                                Section(
                                    current_section_name,
                                    current_section_transactions,
                                    account_number
                                )
                            )
                            current_section_transactions = []
                            current_section_name = None
                        continue
                    date_match = date_pattern.search(line)  # Moved line
                    if date_match:
                        parts = line.split()
                        date = parts[0]
                        amount = parts[-1]
                        description_parts = parts[1:-1]
                        description = " ".join(description_parts)
                        transaction = Transaction(date, description, amount)
                        current_section_transactions.append(transaction)
                    elif (
                            is_in_date_range
                            and not date_match):
                        # line is continuation of the prev date line
                        # 07/24/19 compant payroll $100
                        # CO ID:CXXXXXXXXX WEB
                        # Concatenate such lines
                        if len(current_section_transactions) == 0:
                            print(
                                "Can not create multiline transaction for "
                                "empty transaction list")
                            sys.exit(1)
                        last_transaction = current_section_transactions[-1]
                        last_transaction.description += " " + line
                        continue
                else:
                    new_section_started = line.startswith(
                        "Date") and line.endswith("Amount")
                    if new_section_started:
                        if previous_line and \
                                previous_line.endswith(" - continued"):
                            previous_line = previous_line.replace(
                                " - continued", "")
                        current_section_name = previous_line
                        is_in_date_range = True
                date_match = date_pattern.search(line)
                if date_match:
                    previous_line = line
                elif is_in_date_range:
                    # Keep the previous_line as is if in date range
                    # but no date_match
                    pass
                else:
                    # Update previous_line normally when not in date range
                    previous_line = line
    return Statement(statement_date, sections)


class FileWriterClass:
    def __init__(self, directory):
        self.directory = directory

    def append_statement(self, statement: Statement):
        for section in statement.sections:
            account_number_prefix = ""
            if not section.account:
                print(
                    "Parse error: Failed to get account number for "
                    f"statement {statement.date}")
                sys.exit(1)
            account_number_prefix = f"{section.account[-4:]}_"
            file_path = os.path.join(
                self.directory, f"{account_number_prefix}{section.name}.csv")
            file_exists = os.path.exists(file_path)
            with open(file_path, 'a') as csvfile:
                fieldnames = ['date', 'description', 'amount', 'account']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                if not file_exists:
                    writer.writeheader()
                for transaction in section.transactions:
                    writer.writerow({
                        'date': transaction.date,
                        'description': transaction.description,
                        'amount': transaction.amount
                    })


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Process Bank of America statements."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--dir", help="Directory containing statement PDFs to process"
    )
    group.add_argument(
        "--statement", help="Path to a single statement PDF to process"
    )
    args = parser.parse_args()

    file_writer = FileWriterClass(
        "/home/sdanilov/Build/PDF-Scraper-for-Bank-of-America-Statements/"
        "data/out"
    )

    if args.statement:
        statement = extract_with_pdf_plumber(args.statement)
        file_writer.append_statement(statement)
    elif args.dir:
        for filename in os.listdir(args.dir):
            if filename.endswith(".pdf"):
                pdf_path = os.path.join(args.dir, filename)
                statement = extract_with_pdf_plumber(pdf_path)
                file_writer.append_statement(statement)
