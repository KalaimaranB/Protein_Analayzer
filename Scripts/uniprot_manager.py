import time
import requests
import logging
import json
import os
from Bio import SeqIO, Entrez
from io import StringIO
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import matplotlib.pyplot as plt
from collections import Counter
from matplotlib import font_manager
from io import StringIO
import utilities
from manager import Manager

Entrez.email = "kalaimaranb25@gmail.com"


# Class to store all functionality related to UniProt
class UniProt(Manager):
    """
    Class encapsulating functionality related to UniProt data retrieval and analysis.

    Inherits from Manager class and extends its functionality to manage UniProt data operations,
    including fetching protein records from Entrez, querying UniProt IDs, retrieving protein
    information, and generating graphical representations of natural variants and mutagenesis.

    Attributes:
        ACCESSION (str): Accession number of the protein record.
        specie_name (str): Name of the species associated with the protein.
        all_good (bool): Flag indicating overall success of operations.
        taxon_ID (str): Taxonomic identifier associated with the species.

    Methods:
        create_instance(ACCESSION, specie_name):
            Initializes instance attributes including ACCESSION, specie_name, and taxon_ID.
            Configures font settings for matplotlib plots.

        execute():
            Executes the UniProt data retrieval and analysis workflow.
            Attempts to fetch protein records, retrieve UniProt IDs, fetch protein information,
            and generate a natural variants plot.
            Returns a dictionary containing processed protein information.

        find_entrez_protein_record():
            Finds and fetches the protein record from Entrez based on the provided ACCESSION.
            Returns the fetched protein record in GenBank format.

        get_uniprot_id(record):
            Attempts to retrieve a UniProt ID for a given protein record.
            Uses multiple methods including peptide search, UniParc search, and UniProtKB search.
            Returns the identified UniProt ID or an empty string if not found.

        find_protein_info(primaryAccession):
            Fetches detailed protein information from UniProt based on the provided UniProt primary accession.
            Returns the retrieved protein information in JSON format.

        build_data_dict(data):
            Constructs a structured dictionary containing essential protein information from the retrieved data.
            Returns the constructed data dictionary.

        create_natural_variants_graph(data):
            Generates a plot visualizing natural variants and mutagenesis events in the protein sequence.
            Saves the plot as a PNG file named 'variations_plot.png' in the 'Graphics' folder.
    """

    def create_instance(self, ACCESSION, specie_name, font_path, graphics_folder_path):
        """
        Initialize instance attributes and configure font settings for matplotlib plots.

        Args:
            ACCESSION (str): Accession number of the protein record.
            specie_name (str): Name of the species associated with the protein.
            font_path (str): The path to the font file.
            graphics_folder_path (str): The path to the folder for saving graphics.

        Returns:
            None
        """
        self.ACCESSION = ACCESSION
        self.specie_name = specie_name
        self.all_good = True
        self.taxon_ID = self.get_taxon_id(specie_name)
        self.font_path = os.path.join(font_path, "Lexend-Light.ttf")
        self.graphics_path = graphics_folder_path
        # Add the font to the font manager
        font_manager.fontManager.addfont(self.font_path)

        # Set the font properties
        plt.rcParams["font.family"] = "Lexend"
        plt.rcParams["font.sans-serif"] = "Lexend"

    def execute(self):
        """
        Execute the UniProt data retrieval and analysis workflow.

        Attempts to fetch protein records from Entrez, retrieve UniProt IDs,
        fetch detailed protein information, and generate a natural variants plot.
        Logs errors if any step fails and returns processed protein information.

        Returns:
            dict: Processed protein information in a structured dictionary format.
        """
        uniprot_id = ""

        record = self.find_entrez_protein_record()
        maxTries = 3
        i = 0
        while i < maxTries:
            uniprot_id = self.get_uniprot_id(record)
            if uniprot_id == "":
                i += 1
            else:
                break

        protein_data = self.find_protein_info(uniprot_id)
        protein_info = self.build_data_dict(protein_data)

        original_logging_level = logging.getLogger().level
        try:
            self.create_natural_variants_graph(protein_info)
        except Exception as e:
            logging.info(f"Variant graph could not be produced: {e}")
        finally:
            logging.getLogger().setLevel(original_logging_level)
        return protein_info

    def find_entrez_protein_record(self):
        """
        Fetches and parses the protein record from Entrez database.

        This method uses the Entrez module to fetch a protein record based on
        the provided ACCESSION ID. It reads the record in GenBank format,
        extracts the NIH ID, and logs success or failure accordingly.

        Returns:
            SeqRecord or None: A SeqRecord object containing the protein record
            if successful, None if an error occurs.
        """
        logging.info("Finding protein record")
        try:
            Entrez.email = "kalaimaranb25@gmail.com"
            handle = Entrez.efetch(
                db="protein", id=self.ACCESSION, rettype="gb", retmode="text"
            )
            record = handle.read()
            handle.close()
            # Parse the GenBank record
            record = SeqIO.read(StringIO(record), "genbank")
            self.NIH_ID = record.name
            logging.info("Protein record found")
            return record
        except Exception as er:
            logging.debug(f"Protein record could not be located due to {er}")
            return None

    def get_taxon_id(self, species_name):
        """
        Retrieves the taxonomic ID (taxon ID) for a given species name from NCBI Taxonomy.

        This method uses the Entrez module to search the NCBI Taxonomy database
        for the taxonomic ID associated with the provided species_name.

        Args:
            species_name (str): The scientific name of the species.

        Returns:
            str or None: The taxonomic ID (taxon ID) of the species if found,
            None if the species name cannot be found in the database.
        """
        try:
            handle = Entrez.esearch(db="taxonomy", term=species_name, retmode="xml")
            record = Entrez.read(handle)
            handle.close()
        except Exception as e:
            logging.warning(f"Error querying NCBI Taxonomy: {e}")
            return None

        if record["IdList"]:
            taxon_id = record["IdList"][0]
            return taxon_id
        else:
            logging.error("Taxon ID not found")
            return None

    # Mehtods to get the Uniprot ID
    def peptide_search_for_uniprot_id(self, peptide_sequence):
        """
        Perform a peptide sequence search using UniProt Peptide Search API.

        This method divides the peptide sequence into chunks of 70 characters,
        sends a POST request to UniProt Peptide Search API, handles retries,
        and retrieves the protein IDs associated with the matched peptides.

        Args:
            peptide_sequence (str): The peptide sequence to search.

        Returns:
            str: The protein IDs retrieved from the UniProt search.
                Returns an empty string ("") if an error occurs during the process.
        """
        # Separate the entire sequence into parts of length 70 to be sent for UniProt Peptide Query
        chunks = []
        for i in range(0, len(peptide_sequence), 70):
            chunks.append(str(peptide_sequence[i : i + 70]))
        sequence_string = ",".join(chunks)

        # Generate URL & search
        url = "https://peptidesearch.uniprot.org/asyncrest"
        data = {"peps": sequence_string, "lEQi": "off", "spOnly": "off"}

        # Create a session to handle retries
        session = requests.Session()
        retry_strategy = Retry(
            total=3,  # Total number of retries
            backoff_factor=1,  # Time to wait between retries (exponential backoff)
            status_forcelist=[429, 500, 502, 503, 504],  # Retry on these status codes
            method_whitelist=[
                "HEAD",
                "GET",
                "OPTIONS",
                "POST",
            ],  # Retry for these HTTP methods
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)

        # Initial POST request with retry mechanism
        try:
            response = session.post(url, data=data, timeout=30)
        except requests.exceptions.RequestException as e:
            logging.error(f"Initial request failed: {e}")
            return ""

        # Check if the request is accepted and wait for processing
        if response.status_code == 202:
            logging.info("Request for protein ID list accepted. Waiting.")
            link = response.headers.get("Location")
            retries = 3  # Number of retries
            while retries > 0:
                try:
                    if link:
                        result_response = session.get(
                            link, timeout=30
                        )  # Set timeout for the GET request
                        if result_response.status_code == 200:
                            logging.info(
                                "Results for protein id retrieved successfully"
                            )
                            return self.search_and_filter_protein_id_list(
                                result_response.text
                            )
                        elif result_response.status_code == 202:
                            logging.info("Still processing, waiting for 5 seconds...")
                            time.sleep(5)
                        else:
                            logging.error(
                                f"Failed to retrieve the result. Status code: {result_response.status_code}"
                            )
                            return ""
                    else:
                        logging.error("Empty link received from server.")
                        return ""
                except requests.Timeout:
                    logging.info(
                        "GET request timed out, retrying in 5 seconds... Target link was: "
                        + link
                    )
                    retries -= 1
                    time.sleep(5)
            logging.error("Maximum retries exceeded.")
            return ""
        else:
            logging.error(
                f"Initial request failed. Status code: {response.status_code}"
            )
            return ""

    def uniparc_search(self, record):
        """
        Search for UniParc data related to a given record.

        This method queries the UniParc API for sequence features related to
        the provided record. It identifies the sequence feature with the highest
        match length, extracts the corresponding sequence, and performs further
        operations related to UniProtKB and taxonomy search.

        Args:
            record (SeqRecord): The sequence record to query UniParc.

        Returns:
            str: The peptide sequence retrieved from UniParc.
                Returns an empty string ("") if an error occurs during the process.
        """
        try:
            record_name = record.name
            data = self.get_api_data(
                f"https://rest.uniprot.org/uniparc/stream?format=json&query=%28{record_name}%29",
                "Got UniParc query results",
                JSON=True,
            )
            data = data["results"][0]
            resultList = data["sequenceFeatures"]

            # Figure out which has the highest match
            match_lengths = []
            for entry in resultList:
                sum = 0
                for spot in entry["locations"]:
                    sum += spot["end"] - spot["start"]
                match_lengths.append(sum)
            max_value = max(match_lengths)
            max_index = match_lengths.index(max_value)

            # Construct a list of characters
            target_locations = resultList[max_index]["locations"]
            full_sequence = data["sequence"]["value"]
            return_sequence = ""
            for pos in target_locations:
                start = pos["start"] - 1  # Convert to 0-based index
                end = pos["end"]  # No need to subtract 1 since slicing is end-exclusive
                return_sequence += full_sequence[start:end]

            logging.info("Peptide sequence found successfully")

            self.uniprotKB_search(
                resultList[max_index]["interproGroup"]["id"],
                self.get_taxon_id(self.specie_name),
            )

            return self.peptide_search_for_uniprot_id(return_sequence)
        except Exception as e:
            logging.error(f"Error in uniparc_search: {e}")
            return ""

    def uniprotKB_search(self, query, tax_id, ref_seq=""):
        """
        Perform a search in UniProtKB database for a specific query and taxonomy ID.

        This method queries the UniProtKB API to retrieve entries based on the provided
        query and taxonomy ID. It filters the entries by review status and annotation score,
        returning the UniProt entry ID of the highest scoring reviewed entry found.

        Args:
            query (str): The query string to search in UniProtKB.
            tax_id (str): The taxonomy ID to filter the search results.

        Returns:
            str: The UniProt entry ID of the highest scoring reviewed entry.
                Returns an empty string ("") if an error occurs during the process.
        """
        tsv_result = utilities.fetch_tsv_from_api(
            f"https://rest.uniprot.org/uniprotkb/stream?fields=accession%2Creviewed%2Cid%2Cprotein_name%2Cgene_names%2Cannotation_score%2Csequence&format=tsv&query=%28{query}+AND+%28taxonomy_id%3A{tax_id}%29%29"
        )
        raw_data = utilities.tsv_string_to_json(tsv_result)

        if isinstance(raw_data, str):
            try:
                raw_data = json.loads(raw_data)
            except json.JSONDecodeError:
                raise ValueError("raw_data is not a valid JSON string")

        try:
            # Step 1: Filter based on review status
            reviewed_entries = [
                entry for entry in raw_data if entry["Reviewed"] == "reviewed"
            ]

            # Step 2: Loop through annotation scores from 5 down to 1
            for score in range(5, 0, -1):
                score_str = str(
                    float(score)
                )  # Convert to string to match the data format
                filtered_entries = [
                    entry
                    for entry in reviewed_entries
                    if entry["Annotation"] == score_str
                ]
                if filtered_entries:
                    break  # Exit the loop once we find entries with the current score

            # Step 3: Search the remaining results for the one with the highest sequence match
            sorted_protein_entries = self.sort_protein_entries_by_sequence_match(
                filtered_entries, ref_seq
            )

            print(sorted_protein_entries[0])

            # CRITICAL: ADD STEP TO FILTER BASED ON SEQUENCE MATCH QUALITY
            return filtered_entries[0]["Entry"]
        except Exception as er:
            logging.warning(f"Error occurred during UniProt search using Name: {er}")

    def longest_common_substring_length(self, s1, s2):
        """Helper function to find the length of the longest common substring"""
        m, n = len(s1), len(s2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        longest = 0
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if s1[i - 1] == s2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                    longest = max(longest, dp[i][j])
                else:
                    dp[i][j] = 0
        return longest

    def sort_protein_entries_by_sequence_match(
        self, protein_entries, reference_sequence
    ):
        """
        Sorts a list of protein entries based on the longest character-by-character match with a reference sequence.

        Args:
            protein_entries (list): List of protein entries, each entry is a dictionary containing at least 'Entry' and 'Sequence'.
            reference_sequence (str): The reference sequence to compare against.

        Returns:
            list: Sorted list of protein entries.
        """
        protein_entries.sort(
            key=lambda entry: self.longest_common_substring_length(
                reference_sequence, entry["Sequence"]
            ),
            reverse=True,
        )
        return protein_entries

    def get_uniprot_id(self, record):
        """
        Retrieve a UniProt ID for a given sequence record.

        This method attempts to retrieve a UniProt ID using multiple methods:
        1. Peptide sequence search using `peptide_search_for_uniprot_id`.
        2. UniParc search using `uniparc_search`.
        3. UniProtKB search using the sequence record name and description.

        Args:
            record (SeqRecord): The sequence record for which to retrieve the UniProt ID.

        Returns:
            str: The retrieved UniProt ID.
                Returns an empty string ("") if no valid UniProt ID is found.
        """

        # Helper function to log results
        def log_and_return(message, level, result):
            getattr(logging, level)(message)
            return result

        logging.info("Searching for potential UniProt ID")

        # First try to get using peptide sequence
        tries = 0
        maxTries = 2
        while True:
            if tries < maxTries:
                try:
                    result = self.peptide_search_for_uniprot_id(record.seq)
                    break
                except requests.TooManyRedirects:
                    logging.debug("Too many redirects!")
                    pass
            else:
                break
        if result:
            return log_and_return(
                "SUCCESS: Initial peptide search succeeded", "info", result
            )

        logging.debug("WARNING: Initial peptide search failed")

        # If the result is empty, try a UniParc search
        result = self.uniparc_search(record)
        if result:
            return log_and_return("SUCCESS: UniParc search succeeded", "info", result)

        logging.debug("WARNING: UniParc search failed")

        # If the result is empty, try a UniProtKB search with record name
        result = self.uniprotKB_search(record.name, self.taxon_ID, record.seq)
        if result:
            return log_and_return(
                "SUCCESS: UniProtKB search with record name succeeded", "info", result
            )

        logging.debug("WARNING: UniProtKB search with record name failed")

        # If the result is empty, try a UniProtKB search with record description
        result = self.uniprotKB_search(record.description, self.taxon_ID, record.seq)
        if result:
            return log_and_return(
                "SUCCESS: UniProtKB search with record description succeeded",
                "info",
                result,
            )

        logging.debug("WARNING: UniProtKB search with record description failed")

        # If still empty, try searching using Accession number
        result = self.uniprotKB_search(
            self.ACCESSION, self.get_taxon_id(self.specie_name), record.seq
        )
        if result:
            return log_and_return(
                "SUCCESS: UniProtKB search with accession succeeded", "info", result
            )

        logging.critical("Failed to find an appropriate UniProt ID")
        self.all_good = False
        return ""

    # Once the Uniprot ID is collected, process using these methods
    def search_and_filter_protein_id_list(self, accessions_text):
        """
        Search and filter a list of protein IDs retrieved from UniProt.

        This method takes a comma-separated string of protein accessions, queries
        the UniProt API to fetch detailed information for each accession, and filters
        the results based on species name, review status, and annotation score.

        Args:
            accessions_text (str): Comma-separated string of protein accessions.

        Returns:
            str or dict: If successful, returns the primary accession of the highest
                        scoring reviewed entry found. Returns an error message string
                        if filtering based on species name, review status, or annotation
                        score leads to zero results.
        """
        logging.info("Searching protein id list for best match")

        # Split the accessions by comma
        accessions = accessions_text.split(",")

        # Create the base URL
        base_url = "https://rest.uniprot.org/uniprotkb/accessions"

        # Join accessions with '%2C' (comma URL encoded)
        accessions_param = "%2C".join(accessions)

        # Construct the full API URL
        api_url = f"{base_url}?accessions={accessions_param}&format=json"

        rdata = self.get_api_data(
            api_url, "Data collected, starting to filter", JSON=True
        )
        data = rdata["results"]

        # First filter based on specie_name
        processed_data1 = [
            entry
            for entry in data
            if entry["organism"]["scientificName"] == self.specie_name
        ]
        if len(processed_data1) == 0:
            logging.error("Filtering based on species name led to 0 results")
            return ""

        # Then filter on reviewed status
        processed_data2 = [
            entry
            for entry in processed_data1
            if "unreviewed" not in entry.get("entryType", [])
        ]
        if len(processed_data2) == 0:
            logging.error("Filtering based on review status led to 0 results")
            return ""

        # Then filter on annotation score
        final_results = []
        annotation_score = 5

        # Loop until final_results is not empty or annotation_score is less than 1
        while not final_results and annotation_score > 0:
            final_results = [
                entry
                for entry in processed_data2
                if int(entry["annotationScore"]) == annotation_score
            ]
            annotation_score -= 1

        if len(final_results) == 0:
            return "ERROR - Filtering based on annotation score led to 0 results"

        return final_results[0]["primaryAccession"]

    def find_protein_info(self, primaryAccession):
        """
        Retrieve detailed protein information from UniProt for a given primary accession.

        This method constructs a URL using the provided primary accession, queries the
        UniProt API, and retrieves the protein information in JSON format.

        Args:
            primaryAccession (str): The primary accession of the protein to retrieve info.

        Returns:
            dict: JSON data containing detailed information about the protein.
                Returns an empty dictionary if an error occurs during retrieval.
        """
        logging.info(f"Grabbing protein info from UniProt for {primaryAccession}")
        target_url = f"https://rest.uniprot.org/uniprotkb/{primaryAccession}.json"
        return self.get_api_data(target_url, "Protein ID results found", JSON=True)

    def build_data_dict(self, data):
        """
        Build a structured data dictionary from UniProt protein information.

        This method takes JSON data retrieved from UniProt and extracts relevant
        information to build a structured dictionary containing details such as
        accession, UniProt link, annotation score, organism info, gene name,
        sequence, cofactors, natural variants, and mutagenesis.

        Args:
            data (dict): JSON data retrieved from UniProt containing protein information.

        Returns:
            dict: A structured dictionary with extracted protein information.
        """
        # First update the core information
        data_dict = {
            "primaryAccession": data["primaryAccession"],
            "uniprotLink": f"https://www.uniprot.org/uniprotkb/{data['primaryAccession']}/entry",
            "filterLevel": "reviewed&annotationScore=5",
            "entryAudit": data["entryAudit"],
            "annotationScore": data["annotationScore"],
            "organismInfo": data["organism"],
            "fullName": data["proteinDescription"]["recommendedName"]["fullName"][
                "value"
            ],
            "geneName": data["genes"][0]["geneName"]["value"],
            "sequence": data["sequence"],
            "cofactors": "",
            "tissue_specific_expression": "",
            "inductive_expression": "",
            "naturalVariants": [],
            "mutagenesis": [],
        }

        # Search comment type data for information
        for comment in data["comments"]:
            if comment["commentType"] == "TISSUE SPECIFICITY":
                data_dict.update(
                    {"tissue_specific_expression": comment["texts"][0]["value"]}
                )
            elif comment["commentType"] == "INDUCTION":
                data_dict.update({"inductive_expression": comment["texts"][0]["value"]})
            elif comment["commentType"] == "COFACTOR":
                for cofactor in comment["cofactors"]:
                    data_dict["cofactors"] += f"{cofactor['name']} "

                data_dict["cofactors"] += "- "
                for note in comment["note"]["texts"]:
                    data_dict["cofactors"] += f"{note['value']} "

        # Add info about natural variants & mutagenesis
        for feature in data["features"]:
            if feature["type"] == "Natural variant":
                entrydict = {
                    "startPos": feature["location"]["start"]["value"],
                    "endPos": feature["location"]["end"]["value"],
                }
                data_dict["naturalVariants"].append(entrydict)

            elif feature["type"] == "Mutagenesis":
                entrydict = {
                    "startPos": feature["location"]["start"]["value"],
                    "endPos": feature["location"]["end"]["value"],
                }
                data_dict["mutagenesis"].append(entrydict)

        return data_dict

    def create_natural_variants_graph(self, data):
        """
        Create a plot visualizing natural variants and mutagenesis in a protein sequence.

        This method generates a graphical representation (plot) that illustrates the positions
        and frequencies of natural variants and mutagenesis events within a protein sequence.

        Args:
            data (dict): Dictionary containing protein data including natural variants and mutagenesis.
                        Should have keys 'naturalVariants', 'mutagenesis', and 'sequence'.

        Returns:
            None

        Generates:
            A PNG image file named 'variations_plot.png' saved in the 'Graphics' folder relative to
            the script's directory. The plot displays rectangles representing natural variants and
            mutagenesis events, with colors indicating different types, and includes labels and a legend.

        Notes:
            - The plot is saved at 300 DPI resolution.
            - Adjusts the logging level temporarily to suppress non-error log messages during plot creation.
        """
        logging.info("Starting to produce variations plot")

        # Extract data
        natural_variants = data["naturalVariants"]
        mutagenesis = data["mutagenesis"]
        total_length = data["sequence"]["length"]

        # Verify that total_length is correctly extracted
        if not isinstance(total_length, int) or total_length <= 0:
            logging.error("Invalid sequence length")
            return

        # Count occurrences of each (startPos, endPos) pair for both datasets
        natural_counter = Counter(
            (variant["startPos"], variant["endPos"]) for variant in natural_variants
        )
        mutagenesis_counter = Counter(
            (variant["startPos"], variant["endPos"]) for variant in mutagenesis
        )

        # Combine counters for overlapping regions and separate tracking for coloring
        combined_counter = Counter()
        for key in set(natural_counter.keys()).union(set(mutagenesis_counter.keys())):
            combined_counter[key] = natural_counter[key] + mutagenesis_counter[key]

        logging.info("Information for variations plot has been processed.")

        # Create a plot with specified figure size (8 inches wide by 4 inches tall)
        fig, ax = plt.subplots(figsize=(8, 4))

        # Plot each natural variant as a rectangle with a very thin border
        for (start, end), count in natural_counter.items():
            ax.add_patch(
                plt.Rectangle(
                    (start, 1),
                    end - start + 1,
                    count,
                    facecolor="#16abe5",
                    edgecolor="black",
                    linewidth=0.1,
                )
            )

        # Plot each mutagenesis variant as a rectangle with a very thin border
        for (start, end), count in mutagenesis_counter.items():
            # Adjust the base height to start after natural variants
            base_height = natural_counter[(start, end)] + 1
            ax.add_patch(
                plt.Rectangle(
                    (start, base_height),
                    end - start + 1,
                    count,
                    facecolor="#30b683",
                    edgecolor="black",
                    linewidth=0.1,
                )
            )

        # Set limits and labels
        ax.set_xlim(0, total_length)  # Explicitly set x-axis limit to total_length
        ax.set_ylim(0, max(combined_counter.values()) + 2)
        plt.title("Figure 2: Mutagenesis and Natural Variations")
        plt.xlabel("Location")
        plt.ylabel("Frequency")

        # Add legend
        ax.legend(
            handles=[
                plt.Rectangle(
                    (0, 0),
                    1,
                    1,
                    facecolor="#16abe5",
                    edgecolor="black",
                    linewidth=0.5,
                    label="Natural",
                ),
                plt.Rectangle(
                    (0, 0),
                    1,
                    1,
                    facecolor="#30b683",
                    edgecolor="black",
                    linewidth=0.5,
                    label="Mutagenesis",
                ),
            ],
            loc="lower center",
            ncol=2,
            bbox_to_anchor=(0.5, -0.4),
        )

        plt.tight_layout()

        # Save the plot as a PNG image
        plot_path = os.path.join(self.graphics_path, "variations_plot.png")
        try:
            plt.savefig(plot_path, dpi=300)
        except Exception as e:
            logging.error(f"Failed to save graph: {e}")
            self.all_good = False

        logging.info("Variations plot produced")
