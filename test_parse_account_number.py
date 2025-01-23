from main import parse_combibed_account_number
from main import parse_single_global_account_number


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


if __name__ == "__main__":
    test_parse_account_number()
    test_parse_single_global_account_number()
