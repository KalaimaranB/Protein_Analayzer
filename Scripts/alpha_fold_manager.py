import time, multiprocessing, os
import dash_bio as dashbio
from dash import Dash, html, Input, Output, callback
from dash_bio.utils import PdbParser, create_mol3d_style
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from manager import Manager


class Alpha_fold_manager(Manager):
    """
    A manager class to handle tasks related to AlphaFold protein structure predictions.

    Methods
    -------
    create_instance(unprotID):
        Initializes the instance with the appropriate AlphaFold API URL using the provided UniProt ID.

    execute():
        Executes the process of retrieving the protein structure data, starting the Dash app, capturing a screenshot, and then terminating the Dash app.

    create_mol3d_style(atoms, visualization_type='cartoon', color_element='residue'):
        Generates styles for the Molecule3dViewer visualization based on atom and residue data.

    run_dash_app():
        Runs the Dash application to visualize the protein structure using Molecule3dViewer.

    capture_screenshot(dash_url):
        Captures a screenshot of the Dash application using Selenium and saves it to a file.
    """

    def create_instance(self, unprotID):
        """
        Initializes the instance with the appropriate AlphaFold API URL using the provided UniProt ID.

        Parameters
        ----------
        unprotID : str
            The UniProt ID for the protein of interest.
        """
        self.url = f"https://alphafold.ebi.ac.uk/api/prediction/{unprotID}?key=AIzaSyCeurAJz7ZGjPQUtEaerUkBZ3TaBkXrY94"

    def execute(self):
        """
        Executes the process of retrieving the protein structure data, starting the Dash app,
        capturing a screenshot, and then terminating the Dash app.
        """
        data = self.get_api_data(self.url, "JSON data for image retrieved", JSON=True)
        self.file_link = data[0]["pdbUrl"]

        # Start the Dash app in a separate process
        dash_process = multiprocessing.Process(target=self.run_dash_app)
        dash_process.start()

        # Allow some time for the Dash app to start
        time.sleep(5)

        # Capture the screenshot
        self.capture_screenshot("http://127.0.0.1:8050")

        # Terminate the Dash app process
        dash_process.terminate()

    def create_mol3d_style(
        self, atoms, visualization_type="cartoon", color_element="residue"
    ):
        """
        Generates styles for the Molecule3dViewer visualization based on atom and residue data.

        Parameters
        ----------
        atoms : list
            List of atom dictionaries containing atom data.
        visualization_type : str, optional
            Type of visualization for the Molecule3dViewer (default is 'cartoon').
        color_element : str, optional
            Element to color the atoms by (default is 'residue').

        Returns
        -------
        list
            A list of styles for each atom.
        """
        styles = []
        residue_colors = {
            "ALA": "#9ed696",  # Alanine
            "ARG": "#25b783",  # Arginine
            "ASN": "#d5e879",  # Asparagine
            "ASP": "#7ccca9",  # Aspartic Acid
            "CYS": "#9ed696",  # Cysteine (same as Alanine)
            "GLN": "#25b783",  # Glutamine (same as Arginine)
            "GLU": "#d5e879",  # Glutamic Acid (same as Asparagine)
            "GLY": "#7ccca9",  # Glycine (same as Aspartic Acid)
            "HIS": "#c4b8a6",  # Histidine (similar to #9ed696)
            "ILE": "#f1e3a7",  # Isoleucine (similar to #d5e879)
            "LEU": "#bad4cc",  # Leucine (similar to #7ccca9)
            "LYS": "#b5e2e6",  # Lysine (similar to #25b783)
            "MET": "#f2c2a7",  # Methionine (similar to #9ed696)
            "PHE": "#b9a48d",  # Phenylalanine (similar to #7ccca9)
            "PRO": "#f7d08a",  # Proline (similar to #d5e879)
            "SER": "#c2b9d6",  # Serine (similar to #9ed696)
            "THR": "#a5b8d3",  # Threonine (similar to #25b783)
            "TRP": "#f0e6c8",  # Tryptophan (similar to #d5e879)
            "TYR": "#f0c7ab",  # Tyrosine (similar to #7ccca9)
            "VAL": "#f2d2e4",  # Valine (similar to #25b783)
        }

        for atom in atoms:
            if color_element == "residue":
                residue_name = atom["residue_name"]
                color = residue_colors.get(residue_name, "white")
            else:
                color = "white"

            styles.append({"color": color, "visualization_type": visualization_type})

        return styles

    def run_dash_app(self):
        """
        Runs the Dash application to visualize the protein structure using Molecule3dViewer.
        """
        app = Dash(__name__)

        parser = PdbParser(self.file_link)
        data = parser.mol3d_data()
        styles = self.create_mol3d_style(
            data["atoms"], visualization_type="cartoon", color_element="residue"
        )

        app.layout = html.Div(
            [
                dashbio.Molecule3dViewer(
                    id="dashbio-default-molecule3d",
                    modelData=data,
                    zoom={
                        "factor": 1.1,
                        "animationDuration": 0,
                        "fixedPath": False,
                    },
                    styles=styles,
                ),
                "Selection data",
                html.Hr(),
                html.Div(id="default-molecule3d-output"),
            ]
        )

        @callback(
            Output("default-molecule3d-output", "children"),
            Input("dashbio-default-molecule3d", "selectedAtomIds"),
        )
        def show_selected_atoms(atom_ids):
            """
            Display information about the selected atoms in the Molecule3dViewer.

            Parameters
            ----------
            atom_ids : list
                List of IDs of the selected atoms in the Molecule3dViewer.

            Returns
            -------
            list or str
                A list of Div elements with information about the selected atoms, or a message indicating no atoms are selected.
            """
            if atom_ids is None or len(atom_ids) == 0:
                return "No atom has been selected. Click somewhere on the molecular structure to select an atom."
            return [
                html.Div(
                    [
                        html.Div("Element: {}".format(data["atoms"][atm]["elem"])),
                        html.Div("Chain: {}".format(data["atoms"][atm]["chain"])),
                        html.Div(
                            "Residue name: {}".format(
                                data["atoms"][atm]["residue_name"]
                            )
                        ),
                        html.Br(),
                    ]
                )
                for atm in atom_ids
            ]

        app.run(debug=False, use_reloader=False)  # Turn off reloader if inside Jupyter

    def capture_screenshot(self, dash_url):
        """
        Captures a screenshot of the Dash application using Selenium and saves it to a file.

        Parameters
        ----------
        dash_url : str
            The URL of the Dash application to capture.
        """
        # Setup Selenium with headless Chrome
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1920x1080")

        driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()), options=options
        )

        try:
            # Open the Dash app in the browser
            driver.get(dash_url)

            # Allow some time for the Molecule3dViewer to render
            time.sleep(6)

            # Take a screenshot of the 3D viewer element
            screenshot = driver.find_element(
                By.ID, "dashbio-default-molecule3d"
            ).screenshot_as_png

            # Get the directory of the current script
            current_dir = os.path.dirname(os.path.abspath(__file__))

            # Define the path to the Graphics folder relative to the current script directory
            graphics_folder_path = os.path.join(current_dir, "..", "Graphics")

            # Ensure the Graphics folder exists
            if not os.path.exists(graphics_folder_path):
                os.makedirs(graphics_folder_path)

            # Define the full path for the screenshot file
            screenshot_path = os.path.join(graphics_folder_path, "Protein_image.png")

            # Save the screenshot to a file
            with open(screenshot_path, "wb") as f:
                f.write(screenshot)

            print("Protein image saved to Protein_image.png")

        finally:
            driver.quit()
