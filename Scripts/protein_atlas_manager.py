from manager import Manager


class ProteinAtlas(Manager):
    """
    A manager class to handle tasks related to fetching protein data from the Human Protein Atlas.

    Methods
    -------
    create_instance(uniprotID):
        Initializes the instance with the appropriate Protein Atlas API URL using the provided UniProt ID.

    execute():
        Executes the process of retrieving the protein data from the Protein Atlas.

    get_data():
        Retrieves and processes the protein data from the Protein Atlas API.
    """

    def create_instance(self, uniprotID):
        """
        Initializes the instance with the appropriate Protein Atlas API URL using the provided UniProt ID.

        Parameters
        ----------
        uniprotID : str
            The UniProt ID for the protein of interest.
        """
        self.uniprotId = uniprotID
        self.url = f"https://www.proteinatlas.org/api/search_download.php?search={uniprotID}&columns=chr,chrp,pc,upbp,up_mf&compress=no&format=json"

    def execute(self):
        """
        Executes the process of retrieving the protein data from the Protein Atlas.

        Returns
        -------
        dict
            A dictionary containing the retrieved protein data.
        """
        return self.get_data()

    def get_data(self):
        """
        Retrieves and processes the protein data from the Protein Atlas API.

        Returns
        -------
        dict
            A dictionary containing the processed protein data with an added URL for more information.
        """
        # Fetch data from the API
        rawDict = self.get_api_data(
            self.url, "Protein Atlas data retrieved", JSON=True
        )[0]
        # Add a URL to the dictionary for more information about the protein
        rawDict.update({"URL": f"https://www.proteinatlas.org/search/{self.uniprotId}"})
        return rawDict
