import requests
import json
from typing import Tuple, List, Optional
import time




def createColumnDict(columns_info: List[dict], columns_names: Optional[set] = None) -> dict:
    """
    Create a dictionary  to manipulate information, retruns a dictionari where keys are columns names
    and as valuas ar another dictionary with the following structure: 
    {column_name:{id: columns_id, index: column_index}}

    :param columns_info are the list of columns obtained from smartsheet
    :param columns_names are the columns you want to use specificly,but is None by default   to use all columns
    :return info_columns return a dictionary with column index and id, necesries to manipulate info and write on sheets 
    """
    if columns_names:
        info_columns = {}
        for col in columns_info:
            if col["title"] in columns_names:
                info_columns[col["title"]] = {
                    "index": col["index"], "id": col["id"]}
            if len(info_columns) == len(columns_names):
                break
    else:
        info_columns = {col["title"]: {"index": col["index"], "id": col["id"]}
                        for col in columns_info}

    return info_columns


class Smartsheet:

    def __init__(self, TOKEN: str):
        """
        Constructor de la Clase
        Args:
            :param  token is the token to connect to smartsheet
        """
        self.token = TOKEN
        self.header = {
            'Authorization': f'Bearer {TOKEN}',
            'Content-Type': 'application/json'
        }
        self.queryNotFound = "ignoreRowsNotFound=true"
        self.len_movement = 800
        self.allow_movement = False

    def getSheet(self, sheetId: int,return_name:bool = False) -> Tuple[List[dict], List[dict]]:
        """Function to obtain sheet data and columns info from smartsheet 

        Args:
            sheetId (int): Sheet ID on smartsheet

        Returns:
            data, columns: data from cells, columns info
        """
        url = f"https://api.smartsheet.com/2.0/sheets/{sheetId}?columnType=true"
        response = requests.get(url=url, headers=self.header)
        if response.status_code != 200:
            print("no conected")
            return None, None
        response = response.json()
        print(f"conected to {response['name']}")
        if return_name == True:
            return response["rows"], response["columns"], response["name"]
        else:
            return response["rows"], response["columns"]

    def createNewRow(self, sheetId: int, payload: dict) -> None:
        """
        Create new rows in a sheet
        Args:
            :param sheetId is the sheet ID on smartsheet
            :param payload contains a dictionary with all the information for new rows
        """
        url = f"https://api.smartsheet.com/2.0/sheets/{sheetId}/rows"
        json_payload = json.dumps(payload)
        response = requests.post(
            url=url, headers=self.header, data=json_payload)
        print(response.status_code)
        if response.status_code != 200:
            response = response.json()
            print(response)
        return

    def updateRows(self, sheetId: int, payload: dict) -> None:
        """
        Update rows in a sheet
        Args:
            :param sheetId is the sheet ID on smartsheet
            :param payload contains a dictionary with all the information for update rows
        """
        url = f"https://api.smartsheet.com/2.0/sheets/{sheetId}/rows"
        json_payload = json.dumps(payload)
        response = requests.put(
            url=url, headers=self.header, data=json_payload)
        print(response.status_code)
        if response.status_code != 200:
            print(response.text)

    def deleteRows(self, sheetId: int, deleteIds: list) -> None:
        """
        Delete rows in a sheet
        Args:
            :param sheetId is the sheet ID on smartsheet
            :param deleteIds is the list of IDs to delete
        """
        for rowId in deleteIds:
            delete_url = f"https://api.smartsheet.com/2.0/sheets/{sheetId}/rows?ids={rowId}"
            response = requests.delete(url=delete_url, headers=self.header)
            if response.status_code != 200:
                print(response.text)
        return

    def moveFullRows(self, originId: int, targetId: int) -> None:
        """Move full sheet to another aoivind to move the firs row alwais

        Args:
            originId (int): sheet origin of the data id
            targetId (int): target sheet for the data id
        """
        data, _ = self.getSheet(sheetId=originId)
        data = list(filter(lambda row: row["rowNumber"] != 1, data))
        ids_to_move = [row["id"] for row in data]
        url = f"https://api.smartsheet.com/2.0/sheets/{originId}/rows/move?{self.queryNotFound}"
        len_movement = self.len_movement
        control = self.allow_movement
        for i in range(0, len(ids_to_move), len_movement):
            while control == False:
                print("test of amount of rows amount is in progress")
                ids_lot = ids_to_move[i:i+len_movement]
                print(f"try to move {len(ids_lot)} rows")
                payload = {
                    "rowIds": ids_lot,
                    "to": {
                        "sheetId": targetId
                    }
                }
                response = requests.post(
                    url=url, headers=self.header, data=json.dumps(payload))
                if response.status_code != 200:
                    len_movement -= 50
                    print(f"new lot of rows is seted in {len_movement}")
                else: 
                    print(f"row will be moved in lots of {len_movement}")
                    control = True
            ids_lot = ids_to_move[i:i+len_movement]
            print(f"moving {len(ids_lot)} rows")
            payload = {
                "rowIds": ids_lot,
                "to": {
                    "sheetId": targetId
                }
            }
            response = requests.post(
                url=url, headers=self.header, data=json.dumps(payload))
            if response.status_code != 200:
                print(response.text)
            else:
                print("Success!")

    def moveRowsByCriteria(self, originId: int, targetId: int, criteria: dict) -> None:
        """Function to move lines from a sheet to other. it works with exact search and it is not avaliable for
        multipcik columns. Code is avaliable to do not sent XXX lines that are the lines where formulas are storage

        Args:
            originId (int): Id of origin sheet of data
            targetId (int): ID of sheet where info will go
            criteria (dict): {column: name of the column, values:listo of values to move lines to another sheet}
        """
        AVOID_LINES = ["xxx", "XXX"]
        data, columns = self.getSheet(sheetId=originId)
        column_name = criteria["column"]
        column_name_set = set([column_name])
        use_to_filter = createColumnDict(
            columns_info=columns, columns_names=column_name_set)
        data = list(filter(lambda row: (row["cells"][use_to_filter[column_name]["index"]].get("value") in criteria["values"])
                           and (row["cells"][use_to_filter[column_name]["index"]].get("value") in criteria["values"] not in AVOID_LINES), data))
        ids_to_move = [row["id"] for row in data]
        print(f"is necessary to move {len(ids_to_move)} rows")
        if len(ids_to_move) == 0:
            print("nothing to move")
            return 
        url = f"https://api.smartsheet.com/2.0/sheets/{originId}/rows/move?{self.queryNotFound}"
        len_movement = self.len_movement
        control = self.allow_movement
        for i in range(0, len(ids_to_move), len_movement):
            while control == False:
                print("test of amount of rows amount is in progress")
                ids_lot = ids_to_move[i:i+len_movement]
                print(f"try to move {len(ids_lot)} rows")
                payload = {
                    "rowIds": ids_lot,
                    "to": {
                        "sheetId": targetId
                    }
                }
                response = requests.post(
                    url=url, headers=self.header, data=json.dumps(payload))
                if response.status_code != 200:
                    len_movement -= 50
                    print(f"new lot of rows is seted in {len_movement}")
                else: 
                    print(f"row will be moved in lots of {len_movement}")
                    control = True
            ids_lot = ids_to_move[i:i+len_movement]
            payload = {
                "rowIds": ids_lot,
                "to": {
                    "sheetId": targetId
                }
            }
            response = requests.post(
                url=url, headers=self.header, data=json.dumps(payload))
            if response.status_code != 200:
                print(response.text)
            else:
                print("Success!")

    def createSheetCopy(self, sheetId: int, destinationId: int, destinationType: str, sheet_name: str, include:list = None) -> Optional[int]:
        url = f"https://api.smartsheet.com/2.0/sheets/{sheetId}/copy"
        if include:
            url += f"?include={','.join(include)}" 
        payload = {
            "destinationType": destinationType,
            "destinationId": destinationId,
            "newName": sheet_name
        }
        response = requests.post(
            url=url, headers=self.header, data=json.dumps(payload))
        if response.status_code != 200:
            print(response.text)
            return None
        print("Success creating copy")
        response = response.json()
        print(response)
        return response["result"]["id"]

    def createteHistoryCopy(self, sheetId: int, destinationId: int, destinationType: str, sheet_name: str) -> None:
        new_sheet_id = self.createSheetCopy(
            sheetId=sheetId, destinationId=destinationId, destinationType=destinationType, sheet_name=sheet_name)
        print("waiting for sheet data consolidations")
        try:
            print("start data moving")
            self.moveFullRows(originId=sheetId, targetId=new_sheet_id)
        except Exception as e:
            print("failed historic copy")
            print(e)

    def create_columns(self, sheetIds: list, payload: list, reference_column: Optional[str] = None) -> None:
        """Update groups of sheets with new columns, it allow to create columns on groups of sheets or
        an unique sheet, always use a list to add the sheets.

        Args:
            sheetIds (list): List of sheets to be affected -> [1234,4324323,34535443],[1234]
            payload (list): list of columns to be created
            reference_column (Optional[str], optional): This value is optional and refers the column where the columns will be added on the rigth
        """
        for id in sheetIds:
            url = f"https://api.smartsheet.com/2.0/sheets/{id}/columns"
            _, columns = self.getSheet(sheetId=id)
            count = 1
            if reference_column:
                temporal = set([reference_column])
                columns = createColumnDict(
                    columns_info=columns, columns_names=temporal)
                base_index = columns[reference_column]["index"]
            else:
                base_index = columns[-1]["index"]

            for data_col in payload:
                new_index = base_index+count
                temporal_dict = {"index": new_index}
                new_col = {**data_col, **temporal_dict}
                count += 1
                response = requests.post(
                    url=url, headers=self.header, data=json.dumps([new_col]))
                if response.status_code != 200:
                    print(f"fialied to create columns {response.text}")
                else:
                    print(f"success creating {new_col['title']}")

    def update_columns(self, sheetIds: list, row_data: dict) -> None:
        """provide a solution to modify on programatic way columns in a sheet or in a group of sheets

        Args:
            sheetIds (list): list of sheet ids that will be affected [1234,543453423,1234324312] or [1234] if it is an unique sheet
            row_data (dict): data necesary to modify the columns e.g

            row_data = {
                "current_column_name_1": {
                    "title": new_title,
                    "hiden": False,
                    "index": 34

                },
                "current_column_name_2": {
                    "hidden": True,
                    "description": new description for the column 
                }
            }
        """
        for sheetId in sheetIds:
            _, columns = self.getSheet(sheetId=sheetId)
            columns = createColumnDict(
                columns_info=columns, columns_names=set(row_data.keys()))
            for current_name, partial_payload in row_data.items():
                try:
                    columnId = columns[current_name]["id"]
                    url = f"https://api.smartsheet.com/2.0/sheets/{sheetId}/columns/{columnId}"
                    response = requests.put(
                        url=url, headers=self.header, data=json.dumps(partial_payload))
                    if response.status_code != 200:
                        print(response.text)
                    else:
                        print("success")
                except ValueError as e:
                    print(f"fail with {current_name}")
                    print(e)

    def delete_columns(self, sheetIds: list, list_columns: set) -> None:
        for sheetId in sheetIds:
            _, columns = self.getSheet(sheetId=sheetId)
            columns = createColumnDict(
                columns_info=columns, columns_names=list_columns)
            for col_name, data in columns.items():
                print(col_name)
                columnId = data["id"]
                url = f"https://api.smartsheet.com/2.0/sheets/{sheetId}/columns/{columnId}"
                print(f" deleting {col_name}")
                response = requests.delete(url=url, headers=self.header)
                if response.status_code != 200:
                    print("failed")
                    print(response.text)
                else:
                    print("success")

    def changeSheetPlace(self, sheetIds: list, destinationId: int, destinationType: str = "folder") -> None:
        for sheetId in sheetIds:
            url = f"https://api.smartsheet.com/2.0/sheets/{sheetId}/move"
            payload = {
                "destinationType": destinationType,
                "destinationId": destinationId
            }
            response = requests.post(
                url=url, headers=self.header, data=json.dumps(payload))
            if response.status_code != 200:
                print(response.text())
            else:
                print("success")

    def getAttachmentsList(self, sheetId: int, rowId: int) -> Optional[list]:
        print("obtaining Attachments list")
        url = f"https://api.smartsheet.com/2.0/sheets/{sheetId}/rows/{rowId}/attachments?includeAll=true"
        response = requests.get(url=url, headers=self.header)
        if response.status_code == 200:
            response = response.json()
            print(response["data"])
            return response["data"]
        else:
            print("failed to obtain attacments")
            return None

    def getAttachmentUrl(self, sheetId: int, attachmentId: int) -> Optional[dict]:
        print("Obtaining url to download document")
        url = f"https://api.smartsheet.com/2.0/sheets/{sheetId}/attachments/{attachmentId}"
        response = requests.get(url=url, headers=self.header)
        if response.status_code != 200:
            print("failed to obtain document url")
            return None
        response = response.json()
        return response

    def webhookCreation(self, payload: dict) -> Optional[dict]:
        url = "https://api.smartsheet.com/2.0/webhooks"
        response = requests.post(
            url=url, headers=self.header, data=json.dumps(payload))
        if response.status_code != 200:
            print("failed webhook creation")
            print(response.text)
            return None
        return response.json()

    def enableWebHook(self, webhookId: int, update_payload: dict = {"enabled": True}) -> None:
        url = f"https://api.smartsheet.com/2.0/webhooks/{webhookId}"
        response = requests.put(
            url=url, headers=self.header, data=json.dumps(update_payload))
        response = response.json()
        if response["result"]["enabled"] != True:
            print("webhook not enabled")
            return
        print("webhook enabled")
        return

    def copyRowsByCriteria(self, originId: int, targetId: int, criteria: dict) -> None:
        """Function to copy lines from a sheet to other. it works with exact search and it is not avaliable for
        multipcik columns. Code is avaliable to do not sent XXX lines that are the lines where formulas are storage

        Args:
            originId (int): Id of origin sheet of data
            targetId (int): ID of sheet where info will go
            criteria (dict): {column: name of the column, values:listo of values to copy lines to another sheet}
        """
        AVOID_LINES = ["xxx", "XXX"]
        data, columns = self.getSheet(sheetId=originId)
        column_name = criteria["column"]
        column_name_set = set([column_name])
        use_to_filter = createColumnDict(
            columns_info=columns, columns_names=column_name_set)
        data = list(filter(lambda row: (row["cells"][use_to_filter[column_name]["index"]].get("value") in criteria["values"])
                           and (row["cells"][use_to_filter[column_name]["index"]].get("value") in criteria["values"] not in AVOID_LINES), data))
        ids_to_move = [row["id"] for row in data]
        url = f"https://api.smartsheet.com/2.0/sheets/{originId}/rows/copy?{self.queryNotFound}&include=all"
        len_movement = self.len_movement
        for i in range(0, len(ids_to_move), len_movement):
            while control == False:
                print("test of amount of rows amount is in progress")
                ids_lot = ids_to_move[i:i+len_movement]
                print(f"try to move {len(ids_lot)} rows")
                payload = {
                    "rowIds": ids_lot,
                    "to": {
                        "sheetId": targetId
                    }
                }
                response = requests.post(
                    url=url, headers=self.header, data=json.dumps(payload))
                if response.status_code != 200:
                    len_movement -= 50
                    print(f"new lot of rows is seted in {len_movement}")
                else: 
                    print(f"row will be moved in lots of {len_movement}")
                    control = True
            ids_lot = ids_to_move[i:i+len_movement]
            payload = {
                "rowIds": ids_lot,
                "to": {
                    "sheetId": targetId
                }
            }
            response = requests.post(
                url=url, headers=self.header, data=json.dumps(payload))
            if response.status_code != 200:
                print(response.text)
            else:
                print("Success!")
            time.sleep(5)

    def attachFile(self, body: bytes, mime_type: str, rowId: int, sheetId: int, name_file: str) -> None:
        headers = {
            'Authorization': f'Bearer {self.token}',
            "Content-Type": mime_type,
            'Content-Disposition': f'attachment; filename="{name_file}"'
        }
        url = f"https://api.smartsheet.com/2.0/sheets/{sheetId}/rows/{rowId}/attachments"
        response = requests.post(url=url, headers=headers, data=body)
        print(response)

    def deleteRowsByCriteria(self, sheetId: int, criteria: Optional[dict] = None) -> None:
        """Function to delete lines from a sheet. it works with exact search and it is not avaliable for
        multipcik columns. Code is avaliable to do not delete XXX and the first lines that are the lines where formulas are storaged

        Args:
            sheetId (int): Id of origin sheet of data
            targetId (int): ID of sheet where info will go
            Optional criteria (dict): {column: name of the column, values:listo of values to move lines to another sheet} if not criteria all sheet will be deleted
        """
        url = f"https://api.smartsheet.com/2.0/sheets/{sheetId}/rows?ids="
        deleteSteps = self.len_movement
        data, columns = self.getSheet(sheetId=sheetId)
        AVOID_LINES = ["xxx", "XXX"]
        control = self.allow_movement
        if not criteria:
            print("deleting full sheet")
            data, _ = self.getSheet(sheetId=sheetId)
            idsLot = [str(row["id"]) for row in data if row["rowNumber"] != 1]
        else:
            print("preparing lines to be deleted")
            column_name = criteria["column"]
            column_name_set = set([column_name])
            use_to_filter = createColumnDict(
                columns_info=columns, columns_names=column_name_set)
            data = list(filter(lambda row: (row["cells"][use_to_filter[column_name]["index"]].get("value") in criteria["values"])
                               and (row["cells"][use_to_filter[column_name]["index"]].get("value") in criteria["values"] not in AVOID_LINES), data))
            idsLot = [str(row["id"]) for row in data if row["rowNumber"] != 1]

        for index in range(0, len(idsLot), deleteSteps):
            lotToDelete = idsLot[index:index+deleteSteps]
            if len(lotToDelete) > 0:
                text_format = ",".join(lotToDelete)
            else:
                print("no ids to delete")
                continue
            temp_url = url + text_format
            temp_url += f"&{self.queryNotFound}"
            response = requests.delete(url=temp_url, headers=self.header)
            if response.status_code == 200:
                print("success deleting rows")
            else:
                print(response.text)

    def createUsersGroup(self, name: str, emails: list, description: str = None) -> None:
        """Use it to create groups in smartsheet to share workspaces, sheets and others

        Args:
            name (str): expected name group
            emails (list): list of emails to use on the groups creation
            description (str, optional): Provide a description of the groups if you want to have it. Defaults to None.
        """
        payload = {
            "name": name,
            "members": [{"email": email} for email in emails]
        }
        if description:
            payload["description"] = description
        url = f"https://api.smartsheet.com/2.0/groups"
        response = requests.post(
            url=url, headers=self.header, data=json.dumps(payload))
        if response.status_code != 200:
            print(response.text)
        else:
            print("success")

    def obtainGroupId(self, name: str) -> Optional[int]:
        """Obtain Group ID based on Groups names
        Args:
            name (str): Group to search Id
        Returns:
            Optional[int]: If Group exist you will receive the Id of the group 
        """
        url = f"https://api.smartsheet.com/2.0/groups?includeAll=true"
        response = requests.get(url=url, headers=self.header)
        if response.status_code != 200:
            print("not conected to groups")
            print(response.text)
            return
        response = response.json()
        groupsInfo = response["data"]
        for group in groupsInfo:
            if group["name"] == name:
                return group["id"]
        else:
            print(f"group {name} not found")
            return None

    def UpdateGroupMembersByName(self, groupName: str, emails: list, action: str = "add") -> None:
        """Add or delete members from a group based on email

        Args:
            groupName (str): Provide the name of the group to be modified
            emails (list): list of emails to add or delete
            action (str, optional): Define the action to do, only avalible add and remove. Defaults to "add".

        Returns:
            _type_: _description_
        """
        groupId = self.obtainGroupId(name=groupName)
        if not groupId:
            print("not possible to continue")
            return
        url = f"https://api.smartsheet.com/2.0/groups/{groupId}/members"
        if action == "add":
            new_emails = [{"email": email} for email in emails if "@" in email]
            response = requests.post(
                url=url, headers=self.header, data=json.dumps(new_emails))
            if response.status_code != 200:
                print(response.status_code)
            else:
                print("success")
                return
        elif action == "remove":
            url = f"https://api.smartsheet.com/2.0/groups/{groupId}"
            response = requests.get(url=url, headers=self.header)
            response = response.json()
            members = response["members"]
            for member_info in members:
                if member_info["email"] in emails:
                    userId = member_info["id"]
                    url = f"https://api.smartsheet.com/2.0/groups/{groupId}/members/{userId}"
                    response = requests.delete(url=url, headers=self.header)
                    if response.status_code != 200:
                        print(f"fail deleting {member_info['email']}")
                    else:
                        print("success")
                else:
                    continue
        else:
            print("not valid action")
            return None
