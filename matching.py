import os
import csv
from datetime import datetime

from matcher import Matcher
from student import Student
from past_matches import create_past_matches_mapping 

CURRENT_MONTH_FILE_NAME = "coffee-2020-02.csv"
SIGNUP_DATA_DIR_NAME = "signup_data"
PAST_MATCHES_DIR_NAME = "previous_matches"

NAME_COL = 17
EMAIL_COL = 18
YEAR_COL = 19
GENDER_COL = 20
SAME_GENDER_PREF_COL = 22
INTRO_COL = 23
STAY_ENROLLED_COL = 24

lower_years = []
upper_years = []
lower_year_name_email_map = {}
upper_year_name_email_map = {}

# These are words that will appear in most intros, and should be ignored when calculating
# the similarity score.
# TODO: improve the set of words that we should ignore.
ignored_words = ["I", "I'm", "and", "a", "to"]

def main():
    # Iterate through the files of matching results from previous months to create mapping.
    for filename in os.listdir(PAST_MATCHES_DIR_NAME):
        with open(os.path.join(PAST_MATCHES_DIR_NAME, filename)) as f:
            reader = csv.reader(f)
            create_past_matches_mapping(reader)

    with open(f"{SIGNUP_DATA_DIR_NAME}/{CURRENT_MONTH_FILE_NAME}", "r") as f:
        reader = csv.reader(f)
        # Skip first 3 rows because they're all headers.
        for _ in range(3):
            next(reader)
        for row in reader:
            handle_student_row(row)

    # Iterate through the files of signup data from previous months.
    for filename in os.listdir(SIGNUP_DATA_DIR_NAME):
        if filename == CURRENT_MONTH_FILE_NAME or not filename.endswith(".csv"):
            continue
        with open(os.path.join(SIGNUP_DATA_DIR_NAME, filename)) as f:
            reader = csv.reader(f)
            # Skip first 3 rows because they're all headers.
            for _ in range(3):
                next(reader)
            for row in reader:
                # Add the students who want to stay enrolled in CS Coffee Chat.
                if (row[STAY_ENROLLED_COL].strip() == "Yes" and 
                    row[NAME_COL] not in lower_year_name_email_map and 
                    row[NAME_COL] not in upper_year_name_email_map):
                    print(row[NAME_COL])
                    handle_student_row(row)

    lower_year_rankings = {}
    for lower_year in lower_years:
        current_rankings = {}
        for upper_year in upper_years:
            current_rankings[upper_year] = calculate_points(lower_year, upper_year)
        current_rankings = sorted(current_rankings.items(), key=lambda item: item[1], reverse=True)
        rankings_list = list(map(lambda key_value_pair: key_value_pair[0].name, current_rankings))
        lower_year_rankings[lower_year.name] = rankings_list

    upper_year_rankings = {}
    for upperYear in upper_years:
        current_rankings = {}
        for lower_year in lower_years:
            current_rankings[lower_year] = calculate_points(upperYear, lower_year)
        current_rankings = sorted(current_rankings.items(), key=lambda item: item[1], reverse=True)
        rankings_list = list(map(lambda key_value_pair: key_value_pair[0].name, current_rankings))
        upper_year_rankings[upperYear.name] = rankings_list

    matcher = Matcher(upper_year_rankings, lower_year_rankings)

    # matches is a list of lower year students, ordered based on which upper year student
    # they are matched with.
    matches = matcher.match()

    csv_header_row = ["Emails", "Mentor name", "Mentee 1 name"]
    current_month = datetime.now().strftime("%B")
    current_year = datetime.now().strftime("%Y")
    current_date_title = f"matching_data/{current_month}_{current_year}_matching.csv"
    with open(current_date_title, "w+") as f:
        writer = csv.writer(f)
        writer.writerow(csv_header_row)
        for index, match in enumerate(matches):
            print(f"{upper_years[index].name} with {match}")
            emails = f"{upper_years[index].email}, {lower_year_name_email_map[match]}"
            current_row = [emails, upper_years[index].name, match]
            writer.writerow(current_row)
    f.close()

def calculate_points(ranker, rankee):
    """
    Quantify how much the ranker might prefer to be matched with the rankee based on
    whether or not the ranker has a gender preference, and how similar their intros are.
    """
    points = 0
    ranker_words = ranker.intro.split()
    rankee_words = rankee.intro.split()
    words_in_common = set(ranker_words).intersection(set(rankee_words))
    for word in ignored_words:
        words_in_common.discard(word)
    points += len(words_in_common)
    if ranker.should_match_with_same_gender:
        if ranker.gender == rankee.gender:
            points += 10
    return points

def handle_student_row(row):
    """
    Take in one row from the signup data and create a Student object from it, and
    also add it to the correct dictionaries.
    """
    year = 0
    # TODO: don't automatically put BCS into upper years.
    if row[YEAR_COL] == "5+" or row[YEAR_COL] == "BCS":
        year = 5
    else:
        year = int(row[YEAR_COL])
    should_match_with_same_gender = False
    if row[SAME_GENDER_PREF_COL] == "Yes":
        should_match_with_same_gender = True
    student = Student(name=row[NAME_COL], email=row[EMAIL_COL], year=year, gender=row[GENDER_COL],
                      should_match_with_same_gender=should_match_with_same_gender, intro=row[INTRO_COL])
    if student.year < 3:
        lower_years.append(student)
        lower_year_name_email_map[student.name] = student.email
    else:
        upper_years.append(student)
        upper_year_name_email_map[student.name] = student.email

if __name__ == "__main__":
    main()


