from main import parse_combibed_account_number
from main import parse_single_global_account_number
from main import StatementParser


def test_parse_account_number():
    test_line = "Account number: 1234 1234 1234"
    expected_account_number = "1234 1234 1234"
    actual_account_number = parse_combibed_account_number(test_line)
    assert actual_account_number == \
        expected_account_number, "Expected account number:" \
        f"{expected_account_number}, but got: {actual_account_number}"
    print("Unit test for parse_account_number passed!")


def test_parse_single_global_account_number():
    test_line = "JOHN DOW ! Account # 1234 1234 1234 ! September 21, 2018 " \
        "to October 23, 2018"
    expected_account_number = "1234 1234 1234"
    actual_account_number = parse_single_global_account_number(test_line)
    assert actual_account_number == \
        expected_account_number, "Expected account number:" \
        f"<{expected_account_number}>, but got: <{actual_account_number}>"
    print("Unit test for parse_account_number passed!")


def test_check_table_duplicated():
    test_line = "Date Check # Amount Date Check # Amount"
    parser = StatementParser("")

    res = parser.check_section_has_substrings(test_line)
    assert res is True, f"Expected True, but got: {res}"
    print("Unit test for check_table_duplicated passed!")


def test_find_duplicated_strings():
    test_line = "06/11/19 193 -15,750.00 06/11/19 194 -260.00"
    parser = StatementParser("")
    res = parser.find_possible_substrings(test_line)
    expected_res = ['06/11/19 193 -15,750.00', '06/11/19 194 -260.00']
    assert res == expected_res, \
        f"Expected res to be {expected_res}, but got {res}"


if __name__ == "__main__":
    test_parse_account_number()
    test_parse_single_global_account_number()
    test_check_table_duplicated()
    test_find_duplicated_strings()
