#!/usr/bin/env python3
import requests
import csv
import os
import sys
from operator import itemgetter

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
    api_url = "https://api.passivetotal.org/v2/dns/passive/"  # api url

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Get the query_urls
    with open(query_file, "r") as f:
        queries = [line.strip() for line in f if line != "\n"]

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
            print("Querying resolutions for: {}".format(query.replace(".", "(.)")))
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
                header = "\nResults for: {}\n".format(query.replace(".", "(.)"))
                print(header, end="")
                print("-" * len(header))
                print("First Seen: {}".format(dns_query["firstSeen"]))
                print("Last Seen: {}".format(dns_query["lastSeen"]))
                print("Query Type: {}".format(dns_query["queryType"]))
                print("Total Results: {}".format(dns_query["totalRecords"]))

            # Check if there are any additional pages to get.
            if dns_query["pager"]:
                page = dns_query["pager"]["next"]

            # parse the data.
            for result in dns_query["results"]:
                # Create empty dictionary to store data.
                facets = {"value": "",
                          "resolve": "",
                          "firstSeen": "",
                          "lastSeen": "",
                          "collected": "",
                          "source": "",
                          "recordHash": ""}
                # Loop through the facets' keys, if the key exists store the data, else store a "-".
                for key in facets.keys():
                    if key in result:
                        # Handles the multiple source entries.
                        if key == "source":
                            for source_index, source_name in enumerate(result["source"], 1):
                                if source_index != len(result["source"]):
                                    facets["source"] += source_name + "|"
                                else:
                                    facets["source"] += source_name
                        else:
                            facets[key] = result[key]
                    else:
                        if key == "value":
                            facets["value"] = query
                        else:
                            # Store a "-" for non-existing keys.
                            facets[key] = "-"

                # store all of the results
                all_results.append([facets["value"], facets["resolve"], facets["firstSeen"], facets["lastSeen"],
                                    facets["collected"], facets["source"], facets["recordHash"]])

            # Quit loop if there are no more pages to get.
            if not page:
                break

        if completed:
            # Replace the "None" entries.
            for index, item in enumerate(all_results):
                if item == "None":
                    item[index] = "-"

            # Sort the data by using the 2nd index position of each list as the key.
            sorted_results = sorted(all_results, key=itemgetter(2), reverse=True)

            # Write the CSV file.
            with open(os.path.join(output_dir, "{}_all_resolutions.csv".format(query)), "w", encoding="utf-8",
                      newline="")\
                    as f:
                writer = csv.writer(f)
                header = ["Domain", "Resolution", "First Seen", "Last Seen", "Collected", "Source", "Record Hash"]
                writer.writerow(header)
                for result in sorted_results:
                    writer.writerow(result)
            print("CSV file for {} created in {}\n".format(query.replace(".", "(.)"), output_dir))

