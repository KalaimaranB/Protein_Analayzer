import csv, json, requests
from io import StringIO


def tsv_string_to_json(tsv_string):
    # Use StringIO to read the TSV string as if it were a file
    tsv_file = StringIO(tsv_string)
    reader = csv.DictReader(tsv_file, delimiter="\t")

    # Convert the TSV data to a list of dictionaries
    data = [row for row in reader]

    # Convert the list of dictionaries to a JSON string
    json_data = json.dumps(data, indent=4)
    return json_data


def fetch_tsv_from_api(api_url):
    response = requests.get(api_url)
    response.raise_for_status()  # Check that the request was successful
    return response.content.decode("utf-8")
