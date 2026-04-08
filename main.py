import streamlit as st
import json
import time
from google import genai
from google.genai import types

def extract_data_with_ai(pdf_file, api_key):
    """
    Extraheert data uit de PDF met de Gemini 2.5 Flash API.
    Inclusief automatische retry bij een 503 error.
    """
    max_retries = 10
    for attempt in range(max_retries):
        try:
            # Initialiseer de Client
            client = genai.Client(api_key=api_key)
            
            # Gebruik de stabiele modelnaam
            model_id = "gemini-2.5-pro"
            #model_id ="gemini-3-flash-preview"
            # Lees de PDF in als bytes
            pdf_bytes = pdf_file.read()
            pdf_file.seek(0) 

            prompt = """
            Analyseer deze installatiehandleiding en extraheer de technische informatie exact in de volgende JSON structuur.
        Focus op: Merk, Model, Contactinformatie, Apparaattype (CV/WP/Hybride), Storingen, Afstel-protocol, Warmtepomp-specificaties, Testmodus, Bedrijfstoestanden/Statuscodes, afbeeldingen van componenten en de onderdelenlijst.
        Focus op: Merk, Model, Telefoonnummer, Whatsapp, Apparaattype (CV/WP/Hybride), Storingen, Afstel-protocol, Gas-specificaties, Warmtepomp-specificaties, Testmodus, Bedrijfstoestanden/Statuscodes, afbeeldingen van componenten, de onderdelenlijst en onderdelenkoffers.
        Belangrijk:
        - Bepaal het type apparaat: Als het een CV-ketel is, gebruik "CV-Ketel". Als het een warmtepomp of hybride systeem is, gebruik "Warmtepomp".
        - Zoek naar het telefoonnummer van de fabrikant. Geef prioriteit aan het professionele/technische servicenummer voor installateurs. Gebruik het algemene nummer alleen als er geen specifiek vaknummer wordt vermeld.
        - Testmodus: Zoek naar informatie over hoe de testmodus, schoorsteenvegerfunctie of het testprogramma geactiveerd en gedeactiveerd kan worden.
        - Bedrijfstoestanden/Statuscodes: Zoek naar de tabel met statuscodes of bedrijfstoestanden. Dit zijn vaak codes (bijv. 0, 1, 10, A, H) die aangeven wat het toestel op dat moment doet (bijv. "Ruststand", "Na-draaien pomp", "CV-bedrijf").
        - Voor CV-ketels en Hybride: Scan het document zeer grondig op tabellen met O2, CO2 en verbrandingswaarden. Zoek specifiek naar secties met titels als 'Rookgasanalyse', 'Afstelling', 'Controle verbranding', 'Verbrandingswaarden' of 'Instellen van de gas-luchtverhouding'. 
        - Tabelherkenning: Let op tabelkoppen die kolommen bevatten voor 'Gastype', 'CO2 (%)', 'O2 (%)' of 'p (Pa/mbar)'. Deze tabellen bevinden zich vaak in de hoofdstukken 'Inbedrijfstelling', 'Gasinstellingen' of 'Onderhoud'.
        - Extractie details: Geef de naam van het gastype inclusief beschrijving (bijv. "G25.3 (Aardgas NL)"). Geef O2/CO2 weer als een bereik [min, max]. Zoek ook de gasluchtverhouding (p-verschildruk) en geef deze weer in zowel Pascal (Pa) als millibar (mbar). Als er maar één eenheid in de tekst staat, reken de andere dan om (1 mbar = 100 Pa). Zoek ook de correctiefactoren/offsets (factor, offset_O2, offset_CO2). Sorteer de `gastype_data` lijst zo dat het gastype voor Nederland (G25.3, G25, 2E of 2K) ALTIJD als eerste staat.
        - Controleer of het toestel beschikt over automatische kalibratie van het gasblok (bijv. elektronische gas-luchtkoppeling). Beschrijf dit kort indien aanwezig en hoe de automatsche calbratie te activeren.
        - Voor Warmtepompen en Hybride: Extraheer vermogen (kW), COP, SCOP, koudemiddel type (bijv. R32, R290) en geluidsvermogen.
        - Onderdelen: Als er een onderdelenlijst of lijst met reserveonderdelen aanwezig is, extraheer deze dan volledig met het artikelnummer en de omschrijving.
        - Onderdelenkoffers: Extraheer ook een complete lijst van 'onderdelenkoffers' of 'servicekoffers'. Groepeer deze per 'keteltype' indien gespecificeerd. Voor elke koffer, extraheer de naam, een korte omschrijving (indien aanwezig) en de volledige inhoud met artikelnummer en omschrijving. Als een koffer niet specifiek aan een keteltype is gekoppeld, gebruik dan "Algemeen".
        - Afbeeldingen: Identificeer waar afbeeldingen van het gasblok, de bediening (knoppen/knoppenpaneel) en het display zich bevinden. Geef een korte beschrijving of het paginanummer.        
        - Extraheer de volledige storingslijst en parameters met fabriekswaarden.
        
        Retourneer ALLEEN de JSON. Geen extra tekst of markdown.
        
        Structuur:
        {
          "merk": "string",
          "model": "string",
          "telefoonnummer": "string",
          "whatsapp": "string",
          "apparaattype": "string",
          "categorie": "CV-Ketel | Warmtepomp",
          "afstel_protocol": {
            "titel": "string",
            "automatische_kalibratie": {
              "aanwezig": boolean,
              "beschrijving": "string"
            },
            "hooglast_activatie": "string",
            "laaglast_activatie": "string",
            "gasblok_afbeelding": "string",
            "bediening_afbeelding": "string",
            "display_afbeelding": "string",
            "instelling_uitleg": "string"
            "afsluit_uitleg": "string"
          },          
          "gas_specificaties": {
            "gastype_data": [
              {
                "naam": "string",
                "hooglast_O2_bereik": [number, number],
                "hooglast_CO2_bereik": [number, number],
                "laaglast_O2_bereik": [number, number],
                "laaglast_CO2_bereik": [number, number],
                "hooglast_gasluchtverhouding": {
                  "pa": {"min": number, "nom": number, "max": number},
                  "mbar": {"min": number, "nom": number, "max": number}
                },
                "laaglast_gasluchtverhouding": {
                  "pa": {"min": number, "nom": number, "max": number},
                  "mbar": {"min": number, "nom": number, "max": number}
                },
                "berekening": { "factor": number, "offset_O2": number, "offset_CO2": number }
              }
            ]
          },
          "warmtepomp_details": {
            "thermisch_vermogen_kw": "string",
            "cop": "string",
            "scop": "string",
            "koudemiddel": "string",
            "geluidsvermogen_buiten_db": "string"
          },
          "testmodus": {
            "beschrijving": "string",
            "activatie": "string",
            "deactivatie": "string"
          },
          "bedrijfstoestanden": [{"code": "string", "omschrijving": "string"}],
          "parameters": [{"nummer": "string", "omschrijving": "string", "fabriek": "string", "info": "string"}],
          "storingen": [{"code": "string", "omschrijving": "string", "oplossing": "string"}],
          "onderdelen": [{"artikelnummer": "string", "omschrijving": "string"}],
          "onderdelenkoffers": [
            {
              "keteltype": "string",
              "koffers": [
                {
                  "naam": "string",
                  "omschrijving": "string",
                  "inhoud": [
                    {"artikelnummer": "string", "omschrijving": "string"}
                  ]
                }
              ]
            }
          ],
          "gasblok_afbeelding": "string",
          "bediening_afbeelding": "string",
          "display_afbeelding": "string"
        }
            """

            # Verstuur de aanroep naar Gemini
            response = client.models.generate_content(
                model=model_id,
                contents=[
                    types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
                    prompt
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )

            # Resultaat verwerken
            if response.text:
                clean_json = response.text.replace("```json", "").replace("```", "").strip()
                return json.loads(clean_json)

        except Exception as e:
            # Controleer op 503 Service Unavailable error
            if "503" in str(e) and attempt < max_retries - 1:
                st.info(f"⏳ De AI-server is momenteel erg druk (Status 503). We proberen het automatisch opnieuw... (Poging {attempt + 1} van {max_retries})")
                time.sleep(3)
                continue
            st.error(f"Fout bij AI-verwerking: {e}")
            return None
    return None

def main():
    st.set_page_config(layout="wide", page_title="CV-Data Extractor")
    
    st.title("🛠️ CV-Handleiding Data Extractor")
    st.markdown("Extraheer technische data direct uit PDF-handleidingen met AI.")
    
    # API Key invoer in de zijbalk
    st.sidebar.header("Configuratie")
    api_key = st.sidebar.text_input("Gemini API Key", type="password", help="Voer hier je Google Gemini API key in.")
    
    uploaded_file = st.file_uploader("Upload de handleiding (PDF)", type="pdf")

    if uploaded_file:
        st.success(f"Bestand '{uploaded_file.name}' succesvol geladen.")
        
        if st.button("Start AI Analyse"):
            if not api_key:
                st.error("Voer a.u.b. eerst een API-sleutel in de zijbalk in.")
                return
            with st.spinner("Gemini analyseert het document... dit kan 10-20 seconden duren."):
                result = extract_data_with_ai(uploaded_file, api_key)
                
                if result:
                    st.subheader("Gevonden Gegevens")
                    st.json(result)
                    
                    # Download knop
                    json_str = json.dumps(result, indent=4, ensure_ascii=False)

                    # Construct filename based on 'merk' and 'model' from the result
                    merk = result.get("merk", "").replace(" ", "_").replace("/", "_")
                    model = result.get("model", "").replace(" ", "_").replace("/", "_")

                    if merk and model:
                        download_filename = f"{merk}_{model}.json"
                    else:
                        download_filename = f"data_{uploaded_file.name.replace('.pdf', '')}.json"

                    st.download_button( 
                        label="Download JSON Bestand",
                        data=json_str, 
                        file_name=download_filename,
                        mime="application/json"
                    )

if __name__ == "__main__":
    main()