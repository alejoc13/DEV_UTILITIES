import requests
from typing import Tuple, List
import json



class Smartsheet:
    def __init__(self, token: str):
        """
        Constructor de la Clase
        Args:
            :param  token is the token to connect to smartsheet
        """
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

    def get_sheet(self, sheet_id: int) -> Tuple[List[dict], List[dict]]:
        """
        Obtain a sheet on Smartsheet using requests library
        Args:
            :param sheet_id Is smartsheet id to obtain
        Return:
            :return data is the data for any row in the sheet
            :columns:info is all information about existing columns on sheet
        """
        url = f"https://api.smartsheet.com/2.0/sheets/{sheet_id}"
        response = requests.get(url=url, headers=self.headers)
        if response.status_code != 200:
            print(response.text)
            return [], []
        response = response.json()
        data = response['rows']
        columns_info = response['columns']
        print("sheet obtained")
        return data, columns_info

    def getReports(self, reportID: int) -> Tuple[List[dict], List[dict]]:
        """
        Obtain a Smartsheer report with pagination
        Args:
            :param reportID is the reprot ID on smartsheet
        Returns:
            :return data is the data for any row in the report
            :columns:info is all information about existing columns on report
        """
        numPage = 1
        PAGE_SIZE = 2500
        url = f"https://api.smartsheet.com/2.0/reports/{reportID}?pageSize={PAGE_SIZE}&page={numPage}"
        response = requests.get(url=url, headers=self.headers)
        if response.status_code != 200:
            print(response.text)
            return [], []
        response = response.json()
        data = response['rows']
        totalRows = response['totalRowCount']
        columns_info = response['columns']
        numPage += 1
        while len(data) < totalRows:
            url = f"https://api.smartsheet.com/2.0/reports/{reportID}?pageSize={PAGE_SIZE}&page={numPage}"
            response = requests.get(url=url, headers=self.headers)
            response = response.json()
            partData = response['rows']
            data.extend(partData)
            numPage += 1
        return data, columns_info

    def createNewRow(self, sheet_id: int, payload: dict) -> None:
        """
        Create new rows in a sheet
        Args:
            :param sheet_id is the sheet ID on smartsheet
            :param payload contains a dictionary with all the information for new rows
        """
        url = f"https://api.smartsheet.com/2.0/sheets/{sheet_id}/rows"
        json_payload = json.dumps(payload)
        response = requests.post(
            url=url, headers=self.headers, data=json_payload)
        print(response.status_code)
        if response.status_code != 200:
            print(response.text)
        return

    def updateRows(self, sheet_id: int, payload: dict) -> None:
        """
        Update rows in a sheet
        Args:
            :param shee_id is the sheet ID on smartsheet
            :param payload contains a dictionary with all the information for update rows
        """
        url = f"https://api.smartsheet.com/2.0/sheets/{sheet_id}/rows"
        json_payload = json.dumps(payload)
        response = requests.put(
            url=url, headers=self.headers, data=json_payload)
        print(response.status_code)
        if response.status_code != 200:
            print(response.text)

    def deleteRows(self, sheet_id: int, delete_ids: list) -> None:
        """
        Delete rows in a sheet
        Args:
            :param sheet_id is the sheet ID on smartsheet
            :param delete_ids is the list of IDs to delete
        """
        for row_id in delete_ids:
            delete_url = f"https://api.smartsheet.com/2.0/sheets/{sheet_id}/rows/{row_id}"
            response = requests.delete(url=delete_url, headers=self.headers)
        return
