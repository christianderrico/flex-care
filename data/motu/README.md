# Dataset Card for MOTU

## Dataset Description
The MOTU dataset provides FHIR-standardized clinical data on the rehabilitation pathways of trans-femoral amputation patients. It includes clinical features, mobility measurements, and prosthetic knee information from 1962 hospitalizations of 1006 patients. Data are available in CSV and FHIR formats.

**Curated by:** Valerio Antonio Arcobelli, Serena Moscato, Pierpaolo Palumbo, Alberto Marfoglia, Filippo Nardini, Pericle Randi, Angelo Davalli, Antonella Carbonaro, Lorenzo Chiari, Sabato Mellone

**Funded by:** Italian National Institute for Insurance against Accidents at Work (INAIL), MOTU and MOTU++ projects

**Language(s):** Italian / structured clinical data

**License:** Open access (Nature Scientific Data) – check reuse terms

**Dataset Sources:** INAIL Prosthesis Centre, Budrio, Italy

**Paper:** [Nature Scientific Data, 2024](https://www.nature.com/articles/s41597-024-03593-6)

## Uses

**Direct Use:**  
- Analyze rehabilitation pathways for trans-femoral amputation  
- Study factors affecting mobility and prosthetic adaptation  
- Research on prosthetic knee performance and safety  

**Out-of-Scope Use:**  
- Direct clinical diagnosis or therapy decisions without medical supervision  
- Generalizing to populations not represented (e.g., other amputation types)  

## Dataset Structure

- CSV and FHIR formats  
- 1962 hospitalizations of 1006 patients  
- Variables: clinical features, mobility parameters, prosthesis type, rehabilitation outcomes  

## Dataset Creation

**Curation Rationale:**  
Provide a structured and interoperable dataset for research on post-amputation rehabilitation, enabling real-world data sharing

**Source Data:**  
Clinical data collected during hospitalizations at the INAIL Prosthesis Centre (2011–2020)

**Data Collection and Processing:**  
Retrospective collection with informed consent; standardized using FHIR for interoperability

**Source Data Producers:**  
Medical and research staff at INAIL Prosthesis Centre, Budrio, Italy

## Personal and Sensitive Information
Patient data are anonymized; collection complies with the Declaration of Helsinki and ethical approval CE AVEC n. 380/2018/OSS/AUSLBO

## Bias, Risks, and Limitations
- Predominantly male patients (90.9%)  
- Only unilateral trans-femoral or knee-disarticulation amputations  
- Data limited to a single Italian center; generalizability may be limited  

## Recommendations
Users should be aware of gender bias, geographic limitations, and clinical specificity of the dataset

## Citation

**BibTeX:**  
```bibtex
@article{arcobelli2024fhir,
  title={FHIR-standardized data collection on the clinical rehabilitation pathway of trans-femoral amputation patients},
  author={Arcobelli, Valerio Antonio and Moscato, Serena and Palumbo, Pierpaolo and others},
  journal={Scientific Data},
  volume={11},
  number={806},
  year={2024},
  publisher={Nature Publishing Group}
}
