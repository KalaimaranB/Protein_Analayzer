from uniprot_manager import UniProt
from protein_atlas_manager import ProteinAtlas
from genome_alliance_manager import GenomeAllianceManager
from alpha_fold_manager import Alpha_fold_manager
import time, json, os
from generate_pdf import PDFGenerator
from threading import Thread
from ai_results import AI_Generator

import time


def main():
    full_data_test("7XZZ_K")

def test_protein_atlas():
    PA_ID = "P04637"
    PAM = ProteinAtlas(PA_ID)
    pam_results = PAM.run()
    print(pam_results)


def test_genome_alliance():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    graphics_path = os.path.join(current_dir, "..", "Graphics")
    fonts_path = os.path.join(current_dir, "..", "Fonts")
    GAM = GenomeAllianceManager("P04637", 9606, fonts_path, graphics_path)
    GA_id = GAM.get_GA_id()
    gene_info = GAM.get_gene_info(GA_id)
    raw_disease_info = GAM.get_disease_info(GA_id)
    disease_results = GAM.process_disease_info(raw_disease_info)
    pathwayData = GAM.get_pathway_data(GA_id)
    GAM.produce_graph()


def test_uniprot():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    graphics_path = os.path.join(current_dir, "..", "Graphics")
    fonts_path = os.path.join(current_dir, "..", "Fonts")
    uniprot = UniProt("7XZZ_K", "Homo sapiens", fonts_path, graphics_path)
    uniprot_results = uniprot.execute()
    print(uniprot_results)


def pdf_test():

    # Open and read the JSON file
    with open("uniprot_manager_result.json", "r") as file:
        data1 = json.load(file)

    with open("PAM_result.json", "r") as file:
        data2 = json.load(file)

    with open("GAM_gene_info.json", "r") as file:
        data3 = json.load(file)

    with open("GAM_disease_info.json", "r") as file:
        data4 = json.load(file)

    with open("GAM_pathway_info.json", "r") as file:
        data5 = json.load(file)

    pathway_list = "Activation of NOXA and translocation to mitochondria, Activation of PUMA and translocation to mitochondria, Pre-NOTCH Transcription and Translation, Oxidative Stress Induced Senescence, Formation of Senescence-Associated Heterochromatin Foci (SAHF), Oncogene Induced Senescence, DNA Damage/Telomere Stress Induced Senescence, SUMOylation of transcription factors, Autodegradation of the E3 ubiquitin ligase COP1, Association of TriC/CCT with target proteins during biosynthesis, Pyroptosis, TP53 Regulates Metabolic Genes, Ub-specific processing proteases, Ovarian tumor domain proteases, Recruitment and ATM-mediated phosphorylation of repair and signaling proteins at DNA double strand breaks, Interleukin-4 and Interleukin-13 signaling, TP53 Regulates Transcription of DNA Repair Genes, TP53 Regulates Transcription of Genes Involved in Cytochrome C Release, TP53 regulates transcription of several additional cell death genes whose specific roles in p53-dependent apoptosis remain uncertain, TP53 Regulates Transcription of Caspase Activators and Caspases, TP53 Regulates Transcription of Death Receptors and Ligands, TP53 Regulates Transcription of Genes Involved in G2 Cell Cycle Arrest, TP53 regulates transcription of additional cell cycle genes whose exact role in the p53 pathway remain uncertain, TP53 Regulates Transcription of Genes Involved in G1 Cell Cycle Arrest, Regulation of TP53 Expression, Regulation of TP53 Activity through Phosphorylation, Regulation of TP53 Degradation, Regulation of TP53 Activity through Acetylation, Regulation of TP53 Activity through Association with Co-factors, Regulation of TP53 Activity through Methylation, PI5P Regulates TP53 Acetylation, G2/M DNA damage checkpoint, G2/M Checkpoints, Stabilization of p53, Transcriptional activation of cell cycle inhibitor p21, The role of GTSE1 in G2/M progression after G2 checkpoint, Transcriptional Regulation by VENTX, RUNX3 regulates CDKN1A transcription, Regulation of PTEN gene transcription, Loss of function of TP53 in cancer due to loss of tetramerization ability, Signaling by ALK fusions and activated point mutants, Regulation of NF-kappa B signaling, Zygotic genome activation (ZGA), Factors involved in megakaryocyte development and platelet production, PKR-mediated signaling"
    AIG = AI_Generator(pathway_list)
    results = AIG.get_summaries()

    pdf_generator = PDFGenerator(
        "Protein report.pdf", data1, data2, data3, data4, data5, results
    )
    pdf_generator.generate_pdf()


def full_data_test(key):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    graphics_path = os.path.join(current_dir, "..", "Graphics")
    fonts_path = os.path.join(current_dir, "..", "Fonts")

    st = time.time()
    uniprot = UniProt(key, "Homo sapiens", fonts_path, graphics_path)
    uniprot_results = uniprot.run()

    time.sleep(3)

    PA_ID = uniprot_results["primaryAccession"]
    PAM = ProteinAtlas(PA_ID)
    pam_results = PAM.run()

    time.sleep(3)

    AFM = Alpha_fold_manager(PA_ID)
    AFM.run()

    time.sleep(3)

    GAM = GenomeAllianceManager(
        PA_ID, uniprot_results["organismInfo"]["taxonId"], fonts_path, graphics_path
    )
    GAM_results = GAM.run()

    AIG = AI_Generator(GAM_results["pathway_names"])
    AI_sum = AIG.get_summaries()

    pdf_generator = PDFGenerator(
        "Protein report.pdf",
        uniprot_results,
        pam_results,
        GAM_results["gene_info"],
        GAM_results["disease_results"],
        GAM_results["pathway_data"],
        AI_sum,
    )

    pdf_generator.generate_pdf()

    et = time.time()
    elapsed_time = et - st
    print(f"The time taken for this to execute completely was: {elapsed_time}")


if __name__ == "__main__":
    main()
