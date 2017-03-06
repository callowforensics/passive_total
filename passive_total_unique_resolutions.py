#!/usr/bin/env python3
import requests
import csv
import os
import sys

__author__ = "Andrew Callow"
__copyright__ = "Copyright (C) 2016, HPE ESS"
__title__ = "passive_total_unique_resolutions.py"
__license__ = "Proprietary"
__version__ = "1.0"
__email__ = "andrew.callow@hpe.com"
__status__ = "Prototype"

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Incorrect number of arguments entered!")
        print("Usage: passive_total_api_key passive_total_user_name queries output_directory")
        print(r"Example abcdefghijklmnopqrstuvwxyz123456 johndoe@nowhere.com c:\queries.txt c:\results")
        sys.exit()

    api_key = sys.argv[1]  # Set the api key
    user_name = sys.argv[2]   # Set the user name
    query_file = sys.argv[3]  # Set the base output path
    output_dir = sys.argv[4]  # Set the user name
    api_url = "https://api.passivetotal.org/v2/dns/passive/unique/"  # api url

    # Get the query_urls
    with open(query_file, "r") as f:
        queries = [line.strip() for line in f if line != "\n"]

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for query in queries:
        # Set the completion flag
        completed = False
        # This will change later in code if there is more than 1 page of results to be returned.
        page = None
        # Empty list to store all results for the query.
        all_results = []
        # Loop that runs until all pages have been collected.
        while True:
            # Set the query string.
            payload = {"query": query,
                       "page": page}
            # Set the authentication.
            authentication = (user_name, api_key)
            # Make the request.
            print("Querying resolutions for: {}\n".format(query.replace(".", "(.)")))
            dns_query = requests.get(api_url, auth=authentication, params=payload)
            # Check if we have a 200 response.
            if dns_query.status_code == 200:
                dns_query = dns_query.json()
                completed = True
            else:
                print("Error in getting data for the domain: {}".format(query.replace(".", "(.)")))
                break

            # Only print summary information if the page variable is set to None.
            if not page:
                # Print a summary of the initial results
                header = "Unique resolutions for: {}\n".format(query.replace(".", "(.)"))
                print(header, end="")
                print("-" * len(header))
                print("Unique Resolutions: {}".format(dns_query["total"]))

            # Check if there are any additional pages to get.
            if dns_query["pager"]:
                page = dns_query["pager"]["next"]

            # parse the data.
            for result in dns_query["frequency"]:
                # Create empty dictionary to store data.
                facets = {"domain": query, "ip": result[0], "frequency": result[1]}
                # store all of the results
                all_results.append([facets["domain"], facets["ip"], facets["frequency"]])

            # Quit loop if there are no more pages to get.
            if not page:
                break

        if completed:
            # Write the CSV file.
            with open(os.path.join(output_dir, "{}_unique.csv".format(query)), "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                header = ["Domain", "IP", "Frequency"]
                writer.writerow(header)
                for result in all_results:
                    writer.writerow(result)
            print("CSV file for {} created in {}\n".format(query.replace(".", "(.)"), output_dir))

