from typing import Optional,List,Union
import datetime


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


def prepareDate(date: str)-> Union[datetime.datetime,str]:
    if ":" in date:
        date = date[0:10]
        
    try:
        date_array = date.split("-")
        date_value = datetime.datetime(year=int(date_array[0]), month=int(date_array[1]),day=int(date_array[2]))
        return date_value
    except:
        return "no date"