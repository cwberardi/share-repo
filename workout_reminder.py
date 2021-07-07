import datetime
import os

import pandas as pd
import pygsheets
import telegram

TELEGRAM_API_TOKEN = os.environ["TELEGRAM_API_TOKEN_MARATHON"]
bot = telegram.Bot(token=TELEGRAM_API_TOKEN)
chat_id = -408362490


def authenticate_google_sheets():
    client = pygsheets.authorize(service_account_file="service_account.json")

    sheet = client.open_by_key("1fVzd7BPb9llb3--eSNeA5h5rxSuR-J20l1iOmbqfMFc")
    return sheet


def clean_worksheet():
    sheet = authenticate_google_sheets()
    wk = sheet[0]
    workout_df = wk.get_as_df(has_header=False, index_column=1, end="Q36")
    workout_df = workout_df.drop(index="ACTUAL").drop(
        columns=[1, 2, 3, 4, 5, 6, 7, 8, 9]
    )
    workout_df.rename(
        columns={
            idx: label
            for idx, label in zip(
                workout_df.columns.tolist(), workout_df.iloc[0].values.tolist()
            )
        },
        inplace=True,
    )
    workout_df.drop(workout_df.head(5).index, inplace=True)
    workout_df.index = workout_df.index.astype(str) + " 2021"
    workout_df.index = pd.to_datetime(workout_df.index, format="%d %b %Y")

    series_dict = {}
    for row in workout_df.itertuples():
        series_dict[row.Index] = row.M
        series_dict[row.Index + datetime.timedelta(days=1)] = row.T
        series_dict[row.Index + datetime.timedelta(days=2)] = row.W
        series_dict[row.Index + datetime.timedelta(days=3)] = row.R
        series_dict[row.Index + datetime.timedelta(days=4)] = row.F
        series_dict[row.Index + datetime.timedelta(days=5)] = row.SA
        series_dict[row.Index + datetime.timedelta(days=6)] = row.SU

    workouts = pd.Series(series_dict)
    workouts.index = pd.to_datetime(workouts.index)
    return workouts


def main(event=None, context=None):
    workouts = clean_worksheet()
    date = pd.Timestamp.today()
    try:
        today_workout = workouts[date.strftime("%m/%d/%Y")]
        bot.send_message(
            chat_id=chat_id,
            text=f"Workout for {date.strftime('%d %b')}: <b><i>{today_workout}</i></b>",
            parse_mode="HTML",
        )
    except KeyError:
        bot.send_message(
            chat_id=chat_id,
            text=f"Workout for {date.strftime('%d %b')}: no workout loaded, check spreadsheet",
        )


if __name__ == "__main__":
    main()
