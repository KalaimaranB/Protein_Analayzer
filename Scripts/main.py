from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import re
from Bio import Entrez

app = Flask(__name__)
CORS(app)

# Route to serve the HTML form
@app.route('/')
def form():
    return render_template('index.html')

# Route to fetch information from NCBI protein page
@app.route('/protein_info', methods=['POST'])
def protein_info():
    try:
        # Get the URL parameter from the request
        url = request.form.get('url')

        PID = re.search(r"protein/([A-Z0-9]+(?:\.[0-9]+)?)",url)
        info = find_protein_info(PID[1])
        print(info)
        #print(info.seq)
        
        return render_template('result.html', result=info)
    
    except requests.exceptions.RequestException as e:
        return render_template('result.html', result=f"Error fetching protein information: {str(e)}")


def find_protein_info(PID):
    # Provide your email for Entrez
    Entrez.email = "kalaimaranb25@gmail.com"

    # Fetch the protein record
    handle = Entrez.efetch(db="protein", id=PID, rettype="gb", retmode="text")
    record = handle.read()
    handle.close()

    # To parse specific details, you might need to use BioPython's SeqIO for more structured access
    from Bio import SeqIO
    from io import StringIO

    # Parse the GenBank record
    record = SeqIO.read(StringIO(record), "genbank")
    return record
                                                    

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
