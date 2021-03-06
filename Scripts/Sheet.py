import gspread
import pandas
from oauth2client.service_account import ServiceAccountCredentials
from gspread_dataframe import set_with_dataframe
from gspread_formatting import *
import logging
import json


class CellColor:
    """ contains cell colors """
    def __init__(self):
        self.RED = Color(0.96, 0.73, 0.48)
        self.ORANGE = Color(0.9, 0.96, 0.48)
        self.GREEN = Color(0.56, 0.95, 0.48)


class Sheet:
    """
    Class to handle all google sheet operations
    """
    def __init__(self, name, members):
        """

        :param name: name of current sheet
        :param members: current members
        """
        self.name = name
        self.players = members
        self.scope = ["https://spreadsheets.google.com/feeds",
                      "https://www.googleapis.com/auth/spreadsheets",
                      "https://www.googleapis.com/auth/drive.file",
                      "https://www.googleapis.com/auth/drive"]
        self.creds = ServiceAccountCredentials.from_json_keyfile_name("cloud-auth.json", self.scope)
        self.client = gspread.authorize(self.creds)
        self.CellColor = CellColor()
        self.Logging = logging.Logger(name="Sheet-Logger", level=logging.DEBUG)

    def create_tracker_sheet(self, data_frame: pandas.DataFrame):
        """
        Creates the initial sheet
        :param data_frame: data frame containing initial information
        :return: None
        """

        # Checks if sheet already exists
        try:
            ss = self.client.open(self.name)
        # If not, create the sheet
        except gspread.exceptions.SpreadsheetNotFound:
            print(f"new spreadsheet: {self.name}")
            ss = self.client.create(self.name)

        # Tries to invite emails from config.json to google sheet
        try:
            with open("./Information/config.json", "r") as file:
                config = json.load(file)
                for user in config["users_email"]:
                    print(f'Shared with: {user}')
                    ss.share(user, perm_type='user',
                             role='writer', notify=False)
        # Request can be exceeded
        except gspread.exceptions.APIError as e:
            print("Share Requests Exceeded")

        # Populate First Tab
        self.add_formatting(ss.sheet1)
        set_with_dataframe(ss.sheet1, data_frame)

    def add_worksheet(self, name, progress_list: pandas.DataFrame, index: int):
        """
        Creates additional sheets
        :param name: name of worksheet
        :param progress_list: dataframe to be added
        :param index: worksheet index
        :return: None
        """

        # Open the google sheet
        ss = self.client.open(self.name)

        # Tries to create the sheet if one does not exist with the same name
        try:
            worksheet = ss.add_worksheet(title=name, rows="50", cols="20")
        except Exception as e:
            worksheet = ss.get_worksheet(index)

        # Populates the sheet
        self.add_formatting(worksheet)
        set_with_dataframe(worksheet, progress_list)

    def update_worksheet(self, name: str, data: pandas.DataFrame):
        """
        Updates certain worksheets
        :param name: worksheet name
        :param data: dataframe to fill the sheet
        :return: None
        """
        worksheet = self.client.open(self.name).worksheet(name)
        set_with_dataframe(worksheet, data)

    def add_formatting(self, worksheet):
        """
        Adds conditional formatting to a worksheet
        :param worksheet: worksheet for the rules to be added to
        :return: None
        """
        rule1 = ConditionalFormatRule(
            ranges=[GridRange.from_a1_range('A:E81', worksheet)],
            booleanRule=BooleanRule(
                condition=BooleanCondition('NUMBER_EQ', ['0']),
                format=CellFormat(backgroundColor=self.CellColor.RED)
            )
        )
        rule2 = ConditionalFormatRule(
            ranges=[GridRange.from_a1_range('A:E81', worksheet)],
            booleanRule=BooleanRule(
                condition=BooleanCondition('NUMBER_EQ', ['1']),
                format=CellFormat(backgroundColor=self.CellColor.ORANGE)
            )
        )
        rule3 = ConditionalFormatRule(
            ranges=[GridRange.from_a1_range('A:E81', worksheet)],
            booleanRule=BooleanRule(
                condition=BooleanCondition('NUMBER_EQ', ['2']),
                format=CellFormat(backgroundColor=self.CellColor.GREEN)
            )
        )

        rules = get_conditional_format_rules(worksheet)

        # Clear old rules
        rules.clear()

        # Add rules
        rules.append(rule1)
        rules.append(rule2)
        rules.append(rule3)

        # Save rules
        rules.save()
