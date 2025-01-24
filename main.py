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


class StatementParser:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.is_section_has_substrings = False
        self.current_section_transactions: List[Transaction] = []
        self.section_started = False

        self.account_number = None
        self.combibed_statement = False

    def extract_with_pdf_plumber(self) -> Statement:
        sections: List[Section] = []

        current_section_name: str | None = None
        filename = os.path.basename(self.pdf_path)
        date_match_filename = re.search(r"eStmt_(\d{4}-\d{2}-\d{2})", filename)
        if date_match_filename:
            statement_date = date_match_filename.group(1)
        else:
            statement_date = "Unknown Date"
        with pdfplumber.open(self.pdf_path) as pdf:
            previous_line: str | None = None
            for page in pdf.pages:
                text = page.extract_text()
                for line in text.splitlines():
                    self.set_account_number(line)
                    if self.section_started:
                        if line.startswith("Total"):
                            self.section_started = False
                            if current_section_name:
                                sections.append(
                                    Section(
                                        current_section_name,
                                        self.current_section_transactions,
                                        self.account_number
                                    )
                                )
                                self.current_section_transactions = []
                                current_section_name = None
                            continue
                        sublines = self.find_possible_substrings(line)
                        # handle case when two check tables posted horizontally
                        # next to each other
                        for subline in sublines:
                            self.parse_single_transaction(subline)
                        continue
                    else:
                        new_section_started = line.startswith(
                            "Date") and line.endswith("Amount")
                        if new_section_started:
                            # handle case when table continues on another page
                            if previous_line and \
                                    previous_line.endswith(" - continued"):
                                previous_line = previous_line.replace(
                                    " - continued", "")
                            current_section_name = previous_line
                            self.section_started = True
                            self.is_section_has_substrings = \
                                self.check_section_has_substrings(line)
                    date_match = date_pattern.search(line)
                    if date_match:
                        previous_line = line
                    elif self.section_started:
                        # Keep the previous_line as is if in date range
                        # but no date_match
                        pass
                    else:
                        # Update previous_line normally when not in date range
                        previous_line = line
        return Statement(statement_date, sections)

    def set_account_number(self, line: str):
        if not self.combibed_statement:
            # global account number is single per statement and
            # always must exist
            global_account_number = parse_single_global_account_number(
                line)
            if global_account_number:
                self.account_number = global_account_number
        # In case of combibed statement override global account
        # number with number from combined statement
        if line.startswith("Account number:"):
            parsed_account_number = parse_combibed_account_number(
                line)
            if parsed_account_number:
                self.account_number = parsed_account_number
                self.combibed_statement = True

    def parse_single_transaction(self, line: str):
        date_match = date_pattern.search(line)
        if date_match:
            parts = line.split()
            date = parts[0]
            amount = parts[-1]
            description_parts = parts[1:-1]
            description = " ".join(description_parts)
            transaction = Transaction(
                date, description, amount)
            self.current_section_transactions.append(transaction)
        elif (
                self.section_started
                and not date_match):
            # line is continuation of the prev date line
            # 07/24/19 compant payroll $100
            # CO ID:CXXXXXXXXX WEB
            # Concatenate such lines
            if len(self.current_section_transactions) == 0:
                print(
                    "Can not create multiline transaction for "
                    "empty transaction list")
                sys.exit(1)
            last_transaction = self.current_section_transactions[-1]
            last_transaction.description += " " + line

    def find_possible_substrings(self, line: str) -> List[str]:
        date_matches = list(date_pattern.finditer(line))
        if len(date_matches) <= 1:
            return [line]
        if len(date_matches) > 2:
            print(
                "Line has more than 2 duplicates."
                f"It's not supported yet {line}")
            sys.exit(1)
            # print(f"Date: {match.group(0)}, Index: {match.start()}")
        second_date_index = date_matches[1].start()
        line1 = line[:second_date_index].strip()
        line2 = line[second_date_index:].strip()
        return [line1, line2]

    def check_section_has_substrings(self, line: str) -> bool:
        amount_indices = [i for i in range(
            len(line)) if line.startswith('Amount', i)]
        date_indices = [i for i in range(
            len(line)) if line.startswith('Date', i)]

        if len(date_indices) < 2:
            return False

        if len(amount_indices) > 2 and len(date_indices) > 2:
            print(
                "Line has more than 2 duplicates."
                f"It's not supported yet {line}")
            sys.exit(1)

        second_date_index = date_indices[1]

        part1 = line[:second_date_index].strip()
        part2 = line[second_date_index:].strip()
        return part1 == part2


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
                fieldnames = ['date', 'description', 'amount', 'statement']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                if not file_exists:
                    writer.writeheader()
                for transaction in section.transactions:
                    writer.writerow({
                        'date': transaction.date,
                        'description': transaction.description,
                        'amount': transaction.amount,
                        'statement': statement.date
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
    parser.add_argument(
        "--out_dir", help="Output dir to save generated cvs files",
        required=True
    )

    args = parser.parse_args()

    file_writer = FileWriterClass(args.out_dir)
    if args.statement:
        statement = StatementParser(args.statement).extract_with_pdf_plumber()
        file_writer.append_statement(statement)
    elif args.dir:
        for filename in os.listdir(args.dir):
            if filename.endswith(".pdf"):
                pdf_path = os.path.join(args.dir, filename)
                statement = StatementParser(
                    pdf_path).extract_with_pdf_plumber()
                file_writer.append_statement(statement)
