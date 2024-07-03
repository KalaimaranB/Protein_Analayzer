import logging, time, json, os
import matplotlib.pyplot as plt
from matplotlib import font_manager
from manager import Manager
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import Select


class GenomeAllianceManager(Manager):
    """
    A class to manage genome information retrieval, processing, and visualization
    using the Genome Alliance API and related resources.

    Attributes:
        uniprotID (str): The UniProt ID of the gene.
        taxonID (str): The taxon ID for the gene.
        all_good (bool): A flag to indicate the successful creation of the instance.
        disease_info (list): A list of dictionaries containing disease information.
    """

    DISEASE_INFO = [
        # Infectious disease agent info
        {"DOID": "0050117", "Name": "All disease by infectious agent", "Count": 0},
        {"DOID": "104", "Name": "Bacterial infectious disease", "Count": 0},
        {"DOID": "1564", "Name": "Fungal infectious disease", "Count": 0},
        {"DOID": "1398", "Name": "Parasitic infectious disease", "Count": 0},
        {"DOID": "934", "Name": "Viral infectious disease", "Count": 0},
        # Anatomical Diseases
        {"DOID": "7", "Name": "All disease of anatomical entity", "Count": 0},
        {"DOID": "1287", "Name": "Cardiovascular system disease", "Count": 0},
        {"DOID": "331", "Name": "Central Nervous system disease", "Count": 0},
        {"DOID": "28", "Name": "Endocrine system disease", "Count": 0},
        {"DOID": "77", "Name": "Gastrointestinal system disease", "Count": 0},
        {"DOID": "74", "Name": "Hematopoietic system disease", "Count": 0},
        {"DOID": "2914", "Name": "Immune system disease", "Count": 0},
        {"DOID": "16", "Name": "Integumentary system disease", "Count": 0},
        {"DOID": "17", "Name": "Musculoskeletal system disease", "Count": 0},
        {"DOID": "574", "Name": "Peripheral nervous system disease", "Count": 0},
        {"DOID": "15", "Name": "Reproductive system disease", "Count": 0},
        {"DOID": "1579", "Name": "Respiratory system disease", "Count": 0},
        {"DOID": "0050155", "Name": "Sensory system disease", "Count": 0},
        {"DOID": "0060118", "Name": "Thoracic disease", "Count": 0},
        {"DOID": "18", "Name": "Urinary system disease", "Count": 0},
        # Cellular Proliferation
        {"DOID": "0060072", "Name": "Benign neoplasm", "Count": 0},
        {"DOID": "162", "Name": "Cancer", "Count": 0},
        {"DOID": "0060071", "Name": "Pre-malignant neoplasm", "Count": 0},
        # All genetic disease
        {"DOID": "0080014", "Name": "Chromosomal disease", "Count": 0},
        {"DOID": "0050177", "Name": "Monogenic disease", "Count": 0},
        {"DOID": "0080577", "Name": "Polygenic disease", "Count": 0},
        # All other disease
        {"DOID": "150", "Name": "Disease of mental health", "Count": 0},
        {"DOID": "0014667", "Name": "Disease of metabolism", "Count": 0},
        {"DOID": "0080015", "Name": "Physical disorder", "Count": 0},
        {"DOID": "225", "Name": "Syndrome", "Count": 0},
    ]

    def create_instance(self, uniprotID, taxonID, font_path, graphics_folder_path):
        """
        Initializes the instance with the given UniProt ID and taxon ID, sets up the
        disease information, and configures the font for plotting.

        Args:
            uniprotID (str): The UniProt ID of the gene.
            taxonID (str): The taxon ID for the gene.
            font_path (str): The path to the font file.
            graphics_folder_path (str): The path to the folder for saving graphics.
        """
        self.uniprotID = uniprotID
        self.taxonID = taxonID
        self.graphics_folder_path = graphics_folder_path
        self.all_good = True

        font_path = os.path.join(font_path, "Lexend-Light.ttf")

        try:
            font_manager.fontManager.addfont(font_path)
            plt.rcParams["font.family"] = "Lexend"
            plt.rcParams["font.sans-serif"] = "Lexend"
        except Exception as e:
            logging.error(f"Failed to load font: {e}")
            self.all_good = False

        self.disease_info = self.DISEASE_INFO.copy()

    def execute(self):
        """
        Executes the workflow to retrieve and process genome and disease information,
        and generate a graph of disease annotations.

        Returns:
            dict: A dictionary containing gene information, pathway names, pathway data,
                  and disease results.
        """
        if not self.all_good:
            logging.error("Instance was not properly created, aborting execution.")
            return {}

        GA_id = self.get_GA_id()
        gene_info = self.get_gene_info(GA_id)
        raw_disease_info = self.get_disease_info(GA_id)
        disease_results = self.process_disease_info(raw_disease_info)
        pathwayData = self.get_pathway_data(GA_id)
        self.produce_graph()
        pathwayNames = self.get_pathway_list(pathwayData)

        return {
            "gene_info": gene_info,
            "pathway_names": pathwayNames,
            "pathway_data": pathwayData,
            "disease_results": disease_results,
        }

    def get_GA_id(self):
        """
        Retrieves the Genome Alliance ID for the given UniProt ID.

        Returns:
            str: The Genome Alliance ID.
        """
        try:
            url = f"https://www.alliancegenome.org/api/search?category=gene&debug=false&limit=1&q={self.uniprotID}"
            rawDict = self.get_api_data(
                url, "Genome Alliance Gene ID retrieved", JSON=True
            )
            return rawDict["results"][0]["id"]
        except Exception as e:
            logging.error(f"Failed to retrieve Genome Alliance ID: {e}")
            self.all_good = False
            return None

    def get_gene_info(self, id):
        """
        Retrieves gene information for the given Genome Alliance ID.

        Args:
            id (str): The Genome Alliance ID.

        Returns:
            dict: A dictionary containing gene information.
        """
        try:
            raw_data = self.get_api_data(
                f"https://www.alliancegenome.org/api/gene/{id}",
                "Gene information retrieved",
            )
            json_string = raw_data.decode("utf-8")
            return json.loads(json_string)
        except Exception as e:
            logging.error(f"Failed to retrieve gene information: {e}")
            self.all_good = False
            return {}

    def get_disease_info(self, id):
        """
        Retrieves disease information for the given Genome Alliance ID.

        Args:
            id (str): The Genome Alliance ID.

        Returns:
            list: A list of dictionaries containing disease information.
        """
        results = []
        base_url = "https://www.alliancegenome.org/api/disease"
        params = {
            "asc": "true",
            "debug": "false",
            "focusTaxonId": self.taxonID,
            "geneID": id,
            "includeNegation": "false",
            "limit": 50,
            "page": 1,
        }

        try:
            for page in range(1, 4):
                params["page"] = page
                data = self.get_api_data(
                    base_url,
                    f"Success in retrieving info on page {page}",
                    params=params,
                    JSON=True,
                )
                if data != "ERROR":
                    results.extend(data.get("results", []))
                else:
                    break
        except Exception as er:
            logging.error(f"Failed to retrieve disease information: {er}")
            print(results)
            self.all_good = False

        return results

    def process_disease_info(self, data):
        """
        Processes the raw disease information to categorize and count disease annotations.

        Args:
            data (list): A list of dictionaries containing raw disease information.

        Returns:
            dict: A dictionary containing categorized disease information.
        """
        results = []
        final_result = {"marker in": [], "implicated in": []}

        try:
            for entry in data:
                resultDict = {
                    "diseaseName": entry["object"]["name"],
                    "diseaseID": entry["object"]["curie"],
                    "associationType": entry["relation"]["name"],
                }
                if resultDict["associationType"] == "is_marker_for":
                    final_result["marker in"].append(resultDict)
                else:
                    final_result["implicated in"].append(resultDict)
                results.append(resultDict)
        except Exception as e:
            logging.error(f"Failed to process disease information due to {e}")
            self.all_good = False

        self.update_disease_info_counts(data)
        # self.disease_info = self.update_disease_info(results)
        return final_result

    def update_disease_info_counts(self, entries):
        """
        Updates the disease information counts based on the results.

        Args:
            entries (list): A list of dictionaries containing raw disease information.
        """
        for entry in entries:
            if "parentSlimIDs" in entry:
                for parent_id in entry["parentSlimIDs"]:
                    for disease in self.disease_info:
                        if parent_id.split(":")[1] == disease["DOID"]:
                            disease["Count"] += 1

    def produce_graph(self):
        """
        Produces and saves a graph of disease annotation counts by category.
        """
        if not self.all_good:
            logging.error("Cannot produce graph due to previous errors.")
            return

        data = self.disease_info
        original_logging_level = logging.getLogger().level
        logging.getLogger().setLevel(logging.ERROR)

        filtered_data = [
            item for item in data if "All" not in item["Name"] and item["Count"] > 0
        ]
        sorted_data = sorted(filtered_data, key=lambda x: x["Count"])

        names = [item["Name"] for item in sorted_data]
        counts = [item["Count"] for item in sorted_data]

        plt.figure(figsize=(10, 6))
        plt.barh(names, counts, color="#30b683")
        plt.xlabel("Annotation Count")
        plt.ylabel("Disease Category")
        plt.title(
            "Figure 1: Disease Annotation Level by Category", fontdict={"fontsize": 14}
        )
        plt.tight_layout()

        plot_path = os.path.join(
            self.graphics_folder_path, "disease_annotations_plot.png"
        )

        try:
            plt.savefig(plot_path, dpi=300, bbox_inches="tight")
        except Exception as e:
            logging.error(f"Failed to save graph: {e}")
            self.all_good = False

        logging.getLogger().setLevel(original_logging_level)

    def get_pathway_data(self, GA_ID):
        """
        Retrieves pathway data for the given Genome Alliance ID using Selenium to interact
        with the web page.

        Args:
            GA_ID (str): The Genome Alliance ID.

        Returns:
            list: A list of dictionaries containing pathway information.
        """
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_experimental_option(
            "prefs", {"download.default_directory": os.path.dirname(__file__)}
        )

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=chrome_options
        )
        pathways = []

        try:
            entry_url = f"https://www.alliancegenome.org/gene/{GA_ID}"
            driver.get(entry_url)
            time.sleep(2)

            select_element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "html/body/div[1]/div/div[2]/div/div[2]/div/div[2]/div[7]/div/div[1]/div[3]/div/div/div[1]/select",
                    )
                )
            )
            select = Select(select_element)

            options = select.options

            for option in options:
                path = {
                    "Name": option.text,
                    "Url": f"https://reactome.org/content/detail/{option.get_attribute('value')}",
                }
                pathways.append(path)

        except Exception as e:
            logging.error(f"Failed to retrieve pathway data: {e}")
            self.all_good = False
        finally:
            driver.quit()

        return pathways

    def get_pathway_list(self, pathway):
        """
        Extracts and returns a comma-separated list of pathway names.

        Args:
            pathway (list): A list of dictionaries containing pathway information.

        Returns:
            str: A comma-separated list of pathway names.
        """
        try:
            names = [entry["Name"] for entry in pathway]
            return ", ".join(names)
        except Exception as e:
            logging.error(f"Failed to extract pathway list: {e}")
            self.all_good = False
            return ""
