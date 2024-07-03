from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    Image,
    Frame,
    KeepInFrame,
    KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
import logging, os
from pathlib import Path


class PDFGenerator:
    """
    A class to generate a PDF report based on various protein-related data.

    Attributes:
        filename (str): The name of the output PDF file.
        styles (StyleSheet1): The stylesheet for the PDF.
        doc (SimpleDocTemplate): The document template for the PDF.
        uniprot_data (dict): Data from UniProt.
        protein_atlas_data (dict): Data from the Human Protein Atlas.
        genome_alliance_data (dict): Data from the Alliance of Genome Resources.
        disease_result_data (dict): Disease association data.
        pathway_data (list): Data on pathways.
        pathway_summary (str): AI-generated summary of pathways.

    Methods:
        custom_styles(): Adds custom styles to the stylesheet.
        add_section(elements, paraStyle="MyLeftIndentParagraph", headertext="", *paragraph_texts): Adds a section with a header and paragraphs to the elements list.
        create_cover_page(c): Creates the cover page of the PDF.
        on_first_page(canvas, doc): Callback for the first page.
        generate_pdf(): Generates the PDF document.
        create_basic_info_pages(elements): Adds basic information pages to the PDF.
        create_disease_association_pages(elements): Adds disease association pages to the PDF.
        create_NV_M_section(elements): Adds the natural variants and mutagenesis section to the PDF.
        parse_html(html_text): Parses HTML text for the pathways section.
        create_pathway_section(elements): Adds the pathway section to the PDF.
        create_citations_section(elements): Adds the citations section to the PDF.
    """

    def __init__(
        self,
        filename,
        uniprot_data,
        protein_atlas_data,
        genome_alliance_data,
        disease_result_data,
        pathway_data,
        ai_text,
    ):
        """
        Initializes the PDFGenerator with the given data and filename.

        Args:
            filename (str): The name of the output PDF file.
            uniprot_data (dict): Data from UniProt for the protein.
            protein_atlas_data (dict): Data from the Protein Atlas.
            genome_alliance_data (dict): Data from the Genome Alliance.
            disease_result_data (dict): Data regarding disease associations.
            pathway_data (list): List of pathways.
            ai_text (dict): AI-generated text summaries.
        """

        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))  # Get the parent directory

        # Create the output filename in the parent directory
        self.filename = os.path.join(parent_dir, filename)

        self.styles = getSampleStyleSheet()
        self.custom_styles()
        self.doc = SimpleDocTemplate(self.filename, pagesize=letter)
        self.uniprot_data = uniprot_data
        self.protein_atlas_data = protein_atlas_data
        self.genome_alliance_data = genome_alliance_data
        self.disease_result_data = disease_result_data
        self.pathway_data = pathway_data
        self.pathway_summary = ai_text["pathway_summary"]

    def custom_styles(self):
        """
        Registers custom fonts and defines custom styles for the PDF.
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))

        self.title_font_path = os.path.join(
            current_dir, "..", "Fonts", "Lexend-Regular.ttf"
        )
        self.normal_font_path = os.path.join(
            current_dir, "..", "Fonts", "Lexend-Light.ttf"
        )
        self.bold_font_path = os.path.join(
            current_dir, "..", "Fonts", "Lexend-Bold.ttf"
        )

        pdfmetrics.registerFont(TTFont("Lexend-Regular", self.title_font_path))
        pdfmetrics.registerFont(TTFont("Lexend-Light", self.normal_font_path))
        pdfmetrics.registerFont(TTFont("Lexend-Bold", self.bold_font_path))

        self.styles.add(
            ParagraphStyle(
                name="MyTitle",
                fontName="Lexend-Regular",
                fontSize=30,
                textColor=(
                    22 / 255.0,
                    171 / 255.0,
                    229 / 255.0,
                ),  # RGB tuple normalized to 0-1
                spaceAfter=20,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="MySubtitle",
                fontName="Lexend-Regular",
                fontSize=20,
                textColor=(
                    48 / 255.0,
                    182 / 255.0,
                    131 / 255.0,
                ),  # RGB tuple normalized to 0-1
                spaceAfter=20,
                alignment=2,
                leading=30,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="MyHeader", fontName="Lexend-Regular", fontSize=20, spaceAfter=15
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="MyParagraph",
                fontName="Lexend-Light",
                fontSize=11,
                spaceAfter=10,
                leading=15,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="MyLeftIndentParagraph",
                fontName="Lexend-Light",
                fontSize=11,
                spaceAfter=10,
                leading=15,
                firstLineIndent=20,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="BulletPoints",
                bulletIndent=10,
                bulletColor=colors.black,
                textColor=colors.black,
                fontName="Lexend-Light",
                bulletFontName="Lexend-Light",
                fontSize=11,
                leading=15,
                leftIndent=20,
                spaceAfter=7,
                bulletText="•",
            )
        )

    def add_section(
        self,
        elements,
        paraStyle="MyLeftIndentParagraph",
        headertext="",
        *paragraph_texts,
    ):
        """
        Adds a header and paragraphs to the elements list.

        :param elements: List to which elements will be added.
        :param paraStyle: Style to be applied to paragraphs.
        :param headertext: Optional header text. No header will be displayed if this is blank.
        :param paragraph_texts: Any number of paragraph text strings.
        """
        try:
            temp_elements = []

            if headertext:
                header = Paragraph(headertext, self.styles["MyHeader"])
                temp_elements.append(header)

            for text in paragraph_texts:
                paragraph = Paragraph(text, self.styles[paraStyle])
                temp_elements.append(paragraph)

            elements.extend(temp_elements)
        except Exception as er:
            logging.warning(f"Could not add {headertext} section due to {er}")

    def create_cover_page(self, c):
        """
        Creates the cover page with title, subtitle, and images.

        Args:
            c (canvas.Canvas): The canvas object to draw on.
        """

        width, height = letter

        # Add cover image as background
        current_dir = os.path.dirname(os.path.abspath(__file__))
        img_path = os.path.join(current_dir, "..", "Graphics", "Cover Graphic.png")
        c.drawImage(img_path, 0, 0, width=width, height=height)

        # Overlay title text on top of the background image
        title_style = self.styles["MyTitle"]
        c.setFont(title_style.fontName, title_style.fontSize)
        c.setFillColorRGB(*title_style.textColor)

        title_text = "Protein Analysis Report"
        c.drawString((width) - 5.5 * inch, height - 4 * inch, title_text)

        # Add subtitle below the title
        subtitle_style = self.styles["MySubtitle"]
        subtitle_text = self.uniprot_data["fullName"].capitalize()
        subtitle_paragraph = Paragraph(subtitle_text, subtitle_style)

        # Create a frame to contain the subtitle
        frame_width = 5 * inch
        frame = Frame(
            width - frame_width - 0.75 * inch,
            height - 5 * inch,
            frame_width,
            60,
            showBoundary=0,
        )
        frame.addFromList([KeepInFrame(frame_width, 40, [subtitle_paragraph])], c)

        # Add the protein image
        img_path = os.path.join(current_dir, "..", "Graphics", "Protein_image.png")
        c.drawImage(img_path, 3.5 * inch, 1 * inch, width=5 * inch, height=5 * inch)

    def on_first_page(self, canvas, doc):
        """
        Handles the drawing of elements on the first page (cover page).

        Args:
            canvas (canvas.Canvas): The canvas object to draw on.
            doc (SimpleDocTemplate): The document object.
        """
        self.create_cover_page(canvas)

    def generate_pdf(self):
        """
        Generates the PDF by adding all necessary sections and elements.
        """

        elements = []

        # Add cover page first
        elements.append(PageBreak())

        # Add content pages
        self.create_basic_info_pages(elements)
        self.create_disease_association_pages(elements)
        self.create_NV_M_section(elements)
        self.create_pathway_section(elements)
        self.create_citations_section(elements)

        # Build document with the first page handler for cover page
        self.doc.build(elements, onFirstPage=self.on_first_page)
        logging.info("PDF Created Successfully")

    def create_basic_info_pages(self, elements):
        """
        Adds the basic information pages to the PDF elements.

        Args:
            elements (list): List to which elements will be added.
        """

        # Core info section
        header = Paragraph("Core Info", self.styles["MyHeader"])
        elements.append(header)

        biological_process_str = "None found"
        molecular_function_str = "None found"

        try:
            biological_process_str = ", ".join(
                self.protein_atlas_data["Biological process"]
            )
        except Exception as er:
            logging.info(f"No biological processes found due to {er}")

        try:
            molecular_function_str = ", ".join(
                self.protein_atlas_data["Molecular function"]
            )
        except Exception as e:
            logging.info(f"No molecular functions found due to {er}")

        if self.uniprot_data["cofactors"] == "":
            self.uniprot_data["cofactors"] = "None"

        core_info_text = (
            f"Protein Name: {self.uniprot_data['fullName']}<br/>"
            f"Gene: {self.uniprot_data['geneName']}<br/>"
            f"Uniprot ID: {self.uniprot_data['primaryAccession']}<br/>"
            f"Amino Acid length: {self.uniprot_data['sequence']['length']}<br/>"
            f"Cofactor(s): {self.uniprot_data['cofactors']}<br/>"
            f"Molecular Processes: {molecular_function_str}<br/>"
            f"Biological processes: {biological_process_str}<br/>"
            f"Found on Chromosome {self.protein_atlas_data['Chromosome']}"
        )

        core_info_paragraph = Paragraph(core_info_text, self.styles["MyParagraph"])
        elements.append(core_info_paragraph)

        # Executive Summary section
        self.add_section(
            elements,
            "MyLeftIndentParagraph",
            "",
            self.genome_alliance_data["geneSynopsis"],
        )

        # Add protein expression section
        self.add_section(
            elements,
            "MyLeftIndentParagraph",
            "Protein Expression",
            self.uniprot_data["tissue_specific_expression"],
            self.uniprot_data["inductive_expression"],
        )

    def create_disease_association_pages(self, elements):
        """
        Adds the disease association pages to the PDF elements.

        Args:
            elements (list): List to which elements will be added.
        """

        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Add header and image together, ensure they stay together on a page
        header_and_image = []
        header_and_image.append(
            Paragraph("Disease Associations", self.styles["MyHeader"])
        )

        # Add image
        img_path = os.path.join(
            current_dir, "..", "Graphics", "disease_annotations_plot.png"
        )
        img = Image(img_path, width=7 * inch, height=4 * inch, kind="proportional")
        header_and_image.append(img)

        elements.append(KeepTogether(header_and_image))

        marker_for_str = ", ".join(
            entry["diseaseName"] for entry in self.disease_result_data["marker in"]
        )

        marker_for_paragraph = Paragraph(
            "This gene is a marker for: " + marker_for_str,
            self.styles["MyLeftIndentParagraph"],
        )
        elements.append(marker_for_paragraph)

        implicated_in_str = ", ".join(
            entry["diseaseName"] for entry in self.disease_result_data["implicated in"]
        )

        implicated_in_paragraph = Paragraph(
            "This gene is implicated in: " + implicated_in_str,
            self.styles["MyLeftIndentParagraph"],
        )
        elements.append(implicated_in_paragraph)

    def create_NV_M_section(self, elements):
        """
        Adds the Natural Variants & Mutagenesis section to the PDF elements.

        Args:
            elements (list): List to which elements will be added.
        """

        current_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(current_dir, "..", "Graphics", "variations_plot.png")
        image_path = Path(image_path)

        if image_path.is_file():
            header_and_image = []
            # Natural Variants & mutagenesis
            header = Paragraph(
                f"Natural Variants & Mutagenesis", self.styles["MyHeader"]
            )
            header_and_image.append(header)
            # Add image
            img = Image(
                image_path, width=7 * inch, height=4 * inch, kind="proportional"
            )
            header_and_image.append(img)

            elements.append(KeepTogether(header_and_image))
        else:
            logging.info("Natural Variant graph not produced")

    def parse_html(self, html_text):
        """
        Parses HTML text into a list of Paragraph objects.

        Args:
            html_text (str): The HTML text to parse.

        Returns:
            list: List of Paragraph objects.
        """

        paragraphs = html_text.split("</p>")
        parsed_paragraphs = []
        for para in paragraphs:
            if "<strong>" in para:
                parts = para.split("<strong>")
                parsed_text = parts[0]
                for part in parts[1:]:
                    bold_text, rest = part.split("</strong>")
                    parsed_text += (
                        f'<font name="Lexend-Regular">{bold_text}</font>{rest}'
                    )
                para = parsed_text
            para = para + "</p>"  # Add the closing tag back
            parsed_paragraphs.append(
                Paragraph(para, self.styles["MyLeftIndentParagraph"])
            )
        return parsed_paragraphs

    def create_pathway_section(self, elements):
        """
        Adds the pathway section to the PDF elements.

        Args:
            elements (list): List to which elements will be added.
        """

        # Pathway section
        header = Paragraph("Pathways", self.styles["MyHeader"])
        elements.append(header)

        parsed_paragraphs = self.parse_html(self.pathway_summary)
        elements.extend(parsed_paragraphs)

        # Intro
        summary_paragraph = Paragraph(
            "Here is the full list of pathways (click for more info): ",
            self.styles["MyParagraph"],
        )
        elements.append(summary_paragraph)

        # Add bullet points
        bullet_point_style = self.styles["BulletPoints"]
        for point in self.pathway_data:
            name_with_link = f'<a href="{point["Url"]}">{point["Name"]}</a>'
            elements.append(Paragraph(name_with_link, bullet_point_style))

    def create_citations_section(self, elements):
        """
        Adds the citations section to the PDF elements.

        Args:
            elements (list): List to which elements will be added.
        """
        elements.append(PageBreak())
        # Citations section
        header = Paragraph("Citations", self.styles["MyHeader"])
        elements.append(header)

        citations = [
            {
                "Name": "Uniprot",
                "Url": f"https://www.uniprot.org/uniprotkb/{self.uniprot_data['primaryAccession']}",
            },
            {
                "Name": "Protein Atlas",
                "Url": f"https://www.proteinatlas.org/search/{self.uniprot_data['primaryAccession']}",
            },
            {
                "Name": "AlphaFold",
                "Url": f"https://alphafold.ebi.ac.uk/entry/{self.uniprot_data['primaryAccession']}",
            },
            {
                "Name": "Alliance of Genome Resources",
                "Url": f"https://www.alliancegenome.org/gene/{self.genome_alliance_data['id']}",
            },
        ]

        # Add each citation as a clickable hyperlink
        for citation in citations:
            name_with_link = (
                f'<a href="{citation["Url"]}">{citation["Name"]}: {citation["Url"]}</a>'
            )
            elements.append(Paragraph(name_with_link, self.styles["MyParagraph"]))
