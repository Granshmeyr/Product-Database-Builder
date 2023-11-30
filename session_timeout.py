import requests
import gspread
from typing import List
from datetime import datetime, timedelta
from dateutil.parser import parse


def main():
    gclient = gspread.service_account()

    food_depot_logins_document = gclient.open_by_key("KEY_HERE")
    session_token_sheet = food_depot_logins_document.worksheet("Session Tokens")

    try:
        token_rows = session_token_sheet.get_all_records(numericise_ignore=["all"])
    except:
        raise Exception("No rows in Session Tokens.")

    invalid_token_indices = []
    for i, _dict in enumerate(token_rows):
        if _dict.get("timestamp", "") == "":
            continue

        timestamp = datetime.strptime(_dict["timestamp"], "%m/%d/%Y %H:%M:%S")
        time_difference = datetime.now() - timestamp

        if time_difference.total_seconds() >= 8 * 3600:
            invalid_token_indices.append(i + 1)

    if not invalid_token_indices:
        raise Exception(f"No invalid timestamps in {token_rows}.")

    invalid_index_lists = group_consecutive_in_list(invalid_token_indices)
    invalid_ranges = []

    for i in invalid_index_lists:
        invalid_ranges.append(row_index_list_to_range(i, "A", "D"))

    session_token_sheet.batch_clear(invalid_ranges)


def group_consecutive_in_list(input_list: List[int]) -> List[List[int]]:
    result = []
    current_sublist = []

    for number in input_list:
        if not current_sublist or number == current_sublist[-1] + 1:
            current_sublist.append(number)
        else:
            result.append(current_sublist.copy())
            current_sublist = [number]

    if current_sublist:
        result.append(current_sublist)

    return result


def row_index_list_to_range(
    index_list: List[int], start_column: str, end_column: str
) -> str:
    def capitalize(letter):
        if letter.isupper():
            return letter

        return letter.upper()

    return f"{capitalize(start_column)}{index_list[0] + 1}:{capitalize(end_column)}{index_list[-1] + 1}"


if __name__ == "__main__":
    main()
