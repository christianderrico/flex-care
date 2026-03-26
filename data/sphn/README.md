# Dataset Card for the SPHN Dataset (Swiss Personalized Health Network)

## Dataset Details

### Dataset Description

The **SPHN Dataset** is the core tabular artifact of the Swiss Personalized Health Network (SPHN) Semantic Interoperability Framework. It defines a curated set of clinical concepts — covering diagnoses, procedures, laboratory results, medications, vital signs, and more — together with their compositional relationships and bindings to international biomedical terminologies (SNOMED CT, LOINC, ICD-10-GM, ATC, CHOP, UCUM). The dataset serves as a human-readable source of truth from which the SPHN RDF Schema is automatically generated, enabling FAIR, semantically interoperable exchange of health-related data across Swiss university hospitals.

This repository contains a mapping artifact (`SPHN_to_FHIR Mapping - MIE 2023`) that bridges SPHN concepts to their corresponding FHIR (Fast Healthcare Interoperability Resources) equivalents, as presented at the Medical Informatics Europe (MIE) 2023 conference.

- **Curated by:** Data Coordination Center (DCC), SPHN — FAIR Data Team, SIB Swiss Institute of Bioinformatics (Personalized Health Informatics Group, PHI)
- **Funded by:** Swiss Personalized Health Network (SPHN), funded by the Swiss Federal Government through the Swiss National Science Foundation (SNSF)
- **Shared by:** BIH Center for Digital Health (BIH-CEI), Berlin Institute of Health at Charité; SIB Swiss Institute of Bioinformatics
- **Language(s) (NLP):** English (schema labels and definitions); clinical terminologies are multilingual (SNOMED CT, LOINC, ICD-10-GM in German)
- **License:** Creative Commons Attribution 4.0 International ([CC BY 4.0](https://creativecommons.org/licenses/by/4.0/))

### Dataset Sources

- **Repository (mapping artifact):** https://github.com/BIH-CEI/sphn-to-fhir-map
- **SPHN RDF Schema (official GitLab):** https://git.dcc.sib.swiss/sphn-semantic-framework/sphn-ontology
- **SPHN Semantic Framework documentation:** https://sphn-semantic-framework.readthedocs.io/en/latest/
- **SPHN Schema web browser:** https://www.biomedit.ch/rdf/sphn-ontology/sphn/2023/2
- **Paper (MIE 2023 mapping):** Klopfenstein S., Thun S., Crameri K., Stellmach C. — *Map of the Swiss Personalized Health Network Dataset to Fast Healthcare Interoperability Resources*. MIE 2023.
- **Paper (FAIRification framework):** Touré V. et al. — *FAIRification of health-related data using semantic web technologies in the Swiss Personalized Health Network*. Scientific Data, 2023. https://doi.org/10.1038/s41597-023-02028-y
- **Paper (Schema Forge):** Touré V. et al. — *The SPHN Schema Forge*. J Biomed Semant 16, 9 (2025). https://doi.org/10.1186/s13326-025-00330-9

---

## Uses

### Direct Use

The SPHN Dataset and its derived artifacts are intended for:

- **Secondary use of clinical routine data for research** — enabling federated analyses across Swiss university hospitals without centralizing patient-level data.
- **Semantic interoperability projects** — providing a standardized schema for representing EHR data as RDF knowledge graphs.
- **FHIR mapping and integration** — the mapping artifact in this repository enables translation of SPHN-structured data to FHIR resources, facilitating exchange with systems following HL7 FHIR standards.
- **Ontology and knowledge engineering** — the SPHN RDF Schema, derived from this dataset, can be reused as a reference for healthcare knowledge modeling.
- **FAIR data compliance** — organizations aiming to make health data Findable, Accessible, Interoperable, and Reusable (FAIR) can use SPHN as a reference framework.

### Out-of-Scope Use

- **Direct clinical decision support or patient care** — the SPHN Dataset is a semantic/interoperability standard, not a clinical decision tool.
- **Use outside the Swiss regulatory context without adaptation** — some terminological bindings (e.g., ICD-10-GM, CHOP) are specific to the Swiss/German health system and may require localization.
- **Training large language models without further curation** — the dataset is a schema definition, not a corpus of natural language text.
- **Substituting access to patient data** — this repository contains only the schema and mapping, not actual patient records.

---

## Dataset Structure

The primary artifact in this repository is an Excel workbook:

```
SPHN_to_FHIR Mapping - MIE 2023 - Klopfenstein and Stellmach.xlsx
```

It provides a concept-level crosswalk between the SPHN Dataset and FHIR, with columns covering:

| Column type | Description |
|---|---|
| SPHN Concept | The SPHN general concept name (maps to an RDF class) |
| SPHN composedOf | Properties/attributes of the concept |
| FHIR Resource / Profile | Corresponding FHIR resource or profile |
| FHIR element | Specific FHIR element path |
| Terminology binding | Codes from SNOMED CT, LOINC, ATC, ICD-10-GM, etc. |
| Notes | Mapping rationale and caveats |

The broader SPHN Dataset (outside this repository) is distributed as a versioned Excel spreadsheet through official SPHN/SIB channels, with the following key structural axes:

- **Concepts** (→ RDF classes): clinical entities such as `Diagnosis`, `LabResult`, `Medication`, `Procedure`, `VitalSign`, etc.
- **composedOf relations** (→ RDF object/data properties): compositional attributes linking concepts to values or sub-concepts.
- **Meaning bindings**: alignments to external ontologies (SNOMED CT, LOINC, GENO, SO, OBI, EFO).
- **Value sets**: enumerated sets of permissible values for specific properties.
- **Hierarchies**: parent–child relationships between concepts (e.g., `BilledDiagnosis` and `NursingDiagnosis` are subclasses of `Diagnosis`).

As of the 2026.1 release, the SPHN Federated Clinical Routine Dataset covers **more than 800,000 patients** across six Swiss university hospitals, holding over **12.5 billion RDF triples** mapped to **125 SPHN semantic concepts**.

---

## Dataset Creation

### Curation Rationale

The SPHN Dataset was designed to address the challenge of semantic heterogeneity in Swiss hospital data. Each university hospital uses different internal data models and coding practices. The SPHN initiative, funded by the Swiss Federal Government, created a national standard to enable federated secondary use of clinical routine data for research, without requiring centralization of sensitive patient information. The dataset prioritizes the FAIR principles and alignment with established international biomedical terminologies.

The SPHN-to-FHIR mapping artifact in this repository was created to extend interoperability beyond the Swiss context, enabling SPHN-structured data to be exchanged with systems following the HL7 FHIR standard, which is the dominant interoperability framework in clinical informatics internationally.

### Source Data

#### Data Collection and Processing

The SPHN Dataset is developed iteratively by the SPHN Data Coordination Center (DCC) FAIR Data Team at the SIB Swiss Institute of Bioinformatics, in collaboration with clinical informatics experts at the five Swiss university hospitals (Inselspital Bern, CHUV Lausanne, HUG Geneva, USB Basel, USZ Zurich) and cantonal hospitals. Each release cycle incorporates:

- Feedback from ongoing SPHN research projects and national data streams.
- New clinical concepts identified as relevant for cross-institutional research (e.g., cardiology, genomics, microbiology, nutrition).
- Updates to external terminology versions (SNOMED CT, LOINC, ICD-10-GM, ATC).
- Quality assurance via SHACL validation rules and SPARQL statistical queries.

The dataset is versioned (e.g., 2022.2, 2023.2, 2026.1) and each version is published together with a migration path from the previous release.

#### Who are the source data producers?

The SPHN Dataset schema is produced by the **SPHN Data Coordination Center (DCC)** — specifically its FAIR Data Team — hosted at the **SIB Swiss Institute of Bioinformatics**, Personalized Health Informatics Group (PHI). Clinical input is provided by data stewards and clinical informatics specialists at Swiss university hospitals participating in the SPHN initiative.

The SPHN-to-FHIR mapping in this repository was produced by **S. Klopfenstein** and **C. Stellmach** (BIH-CEI, Berlin Institute of Health at Charité), with contributions from **S. Thun** and **K. Crameri** (SIB), as a research output submitted to MIE 2023.

---

## Annotations

### Annotation Process

Each SPHN concept is annotated with:
- A human-readable `rdfs:label` and `skos:definition`.
- Optional alignment (`owl:equivalentClass`) to a SNOMED CT, LOINC, GENO, or SO concept (meaning binding).
- Hierarchical relationships (`rdfs:subClassOf`) where applicable.

Annotations are defined in the tabular SPHN Dataset and automatically translated to RDF via the **SPHN Schema Forge** web service, ensuring consistency across releases.

### Who are the annotators?

Annotations are produced and reviewed by the SPHN DCC FAIR Data Team (SIB Swiss Institute of Bioinformatics), with expert review from clinical domain specialists at SPHN member hospitals and research projects.

---

## Personal and Sensitive Information

The SPHN Dataset (this repository) contains **no patient data** — it is a schema definition and a concept-level mapping. It does not include any identifiable or re-identifiable personal health information.

Implementations of the SPHN framework that process actual clinical data operate under strict data protection rules aligned with the Swiss Federal Act on Data Protection (nFADP / revDSG) and relevant cantonal regulations. Patient data within the SPHN infrastructure is pseudonymized and stored locally at each hospital; it is never centralized. Access to real SPHN-compliant datasets requires formal data access agreements with the respective data providers and ethics approval.

---

## Bias, Risks, and Limitations

- **Swiss-specific design:** The SPHN Dataset is optimized for the Swiss healthcare context. Terminological bindings to ICD-10-GM and CHOP are specific to the Swiss/German system and may not transfer directly to other countries without adaptation.
- **Hospital coverage:** As of 2025, the SPHN Federated Clinical Routine Dataset covers six Swiss university hospitals. Community or primary care settings are not yet systematically included, which may introduce selection bias toward complex or hospitalized patients.
- **Mapping completeness:** The SPHN-to-FHIR mapping in this repository reflects the state of both standards as of MIE 2023. Subsequent releases of either SPHN or FHIR may introduce gaps or require updates.
- **Terminology licensing:** Full use of SNOMED CT requires an affiliate license (currently free for Swiss users). This may limit reproducibility for users outside Switzerland.
- **Schema evolution:** The SPHN Dataset is updated regularly. Downstream applications built on a specific version must account for migration paths between releases.
- **Not a patient cohort dataset:** This repository does not provide statistical summaries of any patient population; any inference about the characteristics of SPHN-covered patients should be drawn from published SPHN studies, not from this schema artifact.

### Recommendations

Users should be aware that the SPHN-to-FHIR mapping is a research artifact (MIE 2023 submission) and has not been validated as a production-grade implementation guide. For deployment in production systems, users are encouraged to consult the official SPHN documentation and engage with the SPHN DCC. Implementers outside Switzerland should verify compliance with local data protection regulations and terminology licensing requirements before using SPHN-derived artifacts.

---

## Citation

### BibTeX

```bibtex
@inproceedings{klopfenstein2023sphn,
  title     = {Map of the Swiss Personalized Health Network Dataset to Fast Healthcare Interoperability Resources},
  author    = {Klopfenstein, S. and Thun, S. and Crameri, K. and Stellmach, C.},
  booktitle = {Medical Informatics Europe (MIE 2023)},
  year      = {2023}
}

@article{toure2023fairification,
  title   = {FAIRification of health-related data using semantic web technologies in the Swiss Personalized Health Network},
  author  = {Tour{\'e}, Vasundra and others},
  journal = {Scientific Data},
  year    = {2023},
  doi     = {10.1038/s41597-023-02028-y}
}
```

### APA

Klopfenstein, S., Thun, S., Crameri, K., & Stellmach, C. (2023). *Map of the Swiss Personalized Health Network Dataset to Fast Healthcare Interoperability Resources*. Medical Informatics Europe (MIE 2023).

Touré, V., et al. (2023). FAIRification of health-related data using semantic web technologies in the Swiss Personalized Health Network. *Scientific Data*. https://doi.org/10.1038/s41597-023-02028-y

---

## Glossary

| Term | Definition |
|---|---|
| **SPHN** | Swiss Personalized Health Network — a national Swiss initiative for FAIR health data infrastructure |
| **DCC** | Data Coordination Center — the coordinating body for SPHN data standards, hosted at SIB |
| **SIB** | Swiss Institute of Bioinformatics |
| **FHIR** | Fast Healthcare Interoperability Resources — the HL7 standard for exchanging healthcare information electronically |
| **RDF** | Resource Description Framework — a W3C standard for representing structured data as subject–predicate–object triples |
| **SHACL** | Shapes Constraint Language — a W3C language for validating RDF graphs |
| **SPARQL** | SPARQL Protocol and RDF Query Language — a query language for RDF data |
| **SNOMED CT** | Systematized Nomenclature of Medicine – Clinical Terms — a comprehensive clinical terminology |
| **LOINC** | Logical Observation Identifiers Names and Codes — a standard for laboratory and clinical observations |
| **ICD-10-GM** | International Classification of Diseases, 10th revision, German Modification |
| **ATC** | Anatomical Therapeutic Chemical classification system for medications |
| **CHOP** | Swiss procedure classification (Schweizerische Operationsklassifikation) |
| **FAIR** | Findable, Accessible, Interoperable, Reusable — principles for scientific data management |
| **BIH-CEI** | Berlin Institute of Health Center for Digital Health, Charité – Universitätsmedizin Berlin |
| **Meaning binding** | An explicit alignment between an SPHN class and a concept in an external ontology (e.g., SNOMED CT) |

---

## More Information

- SPHN official website: https://sphn.ch
- SPHN Semantic Interoperability Framework documentation: https://sphn-semantic-framework.readthedocs.io/en/latest/
- SPHN RDF Schema browser: https://www.biomedit.ch/rdf/sphn-ontology/sphn/2023/2
- BioMedIT Portal (terminologies): https://portal.dcc.sib.swiss/
- Bioregistry entry: https://bioregistry.io/sphn

---

## Dataset Card Authors

S. Klopfenstein, S. Thun, K. Crameri, C. Stellmach (mapping artifact); SPHN DCC FAIR Data Team / SIB PHI Group (SPHN Dataset schema).

## Dataset Card Contact

For questions about the SPHN Dataset schema and RDF artifacts, contact the SPHN Data Coordination Center via https://sphn.ch.
For questions specific to this mapping repository, refer to the BIH-CEI GitHub organization: https://github.com/BIH-CEI.
