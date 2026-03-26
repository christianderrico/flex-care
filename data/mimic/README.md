# Dataset Card for MIMIC-IV

## Dataset Details

### Dataset Description

MIMIC-IV (Medical Information Mart for Intensive Care IV) is a large, freely accessible database of deidentified electronic health records (EHR) for patients admitted to the emergency department (ED) or an intensive care unit (ICU) at the Beth Israel Deaconess Medical Center (BIDMC) in Boston, Massachusetts, USA. The dataset covers admissions between 2008 and 2022 and contains data for over 65,000 ICU patients and over 200,000 ED patients. MIMIC-IV is the successor to MIMIC-III and adopts a modular architecture to highlight data provenance and facilitate both individual and combined use of disparate clinical data sources.

- **Curated by:** Alistair Johnson, Lucas Bulgarelli, Tom Pollard, Steven Horng, Leo Anthony Celi, Roger Mark — MIT Laboratory for Computational Physiology (MIT-LCP)
- **Funded by:** National Institute of Biomedical Imaging and Bioengineering (NIBIB), National Institutes of Health (NIH), grant number R01EB030362
- **Shared by:** PhysioNet / MIT Laboratory for Computational Physiology
- **Language(s) (NLP):** English (free-text clinical notes available in the separate MIMIC-IV-Note module)
- **License:** PhysioNet Credentialed Health Data License 1.5.0 — access is restricted to credentialed users who complete a data use agreement and a human subjects research training course. A publicly accessible demo subset (100 patients) is available under the Open Database License (ODbL) v1.0.

---

### Dataset Sources

- **Repository (PhysioNet, official):** https://physionet.org/content/mimiciv/
- **Documentation & code repository:** https://github.com/MIT-LCP/mimic-code
- **Paper:** Johnson, A.E.W., Bulgarelli, L., Shen, L. et al. *MIMIC-IV, a freely accessible electronic health record dataset.* Sci Data **10**, 1 (2023). https://doi.org/10.1038/s41597-022-01899-x
- **Demo (open-access subset):** https://physionet.org/content/mimic-iv-demo/

---

## Uses

### Direct Use

MIMIC-IV is intended to support a wide range of retrospective research studies and educational initiatives in clinical medicine, health informatics, and machine learning. Primary use cases include:

- **Predictive modeling:** in-hospital mortality prediction, ICU length-of-stay estimation, readmission risk, phenotype classification, sepsis onset prediction.
- **Clinical NLP:** information extraction from discharge summaries and radiology reports (via MIMIC-IV-Note).
- **Epidemiology:** retrospective cohort studies on disease incidence, treatment patterns, and outcomes.
- **Benchmarking:** evaluation of machine learning and AI models on real-world clinical data.
- **Education:** training healthcare professionals and data scientists in clinical data analysis.

### Out-of-Scope Use

- **Clinical decision support in production:** MIMIC-IV is a retrospective research resource and must **not** be used to inform real-time patient care decisions.
- **Re-identification:** any attempt to re-identify patients or link the data to external sources to recover protected health information (PHI) is strictly prohibited by the data use agreement.
- **Commercial exploitation without authorisation:** redistribution or commercial use is not permitted without explicit agreement with PhysioNet/MIT-LCP.
- **Derived dataset sharing outside PhysioNet:** any derivative dataset or trained model must be treated as sensitive information. If shared publicly, it must be hosted on PhysioNet under the same license as the source data.
- **Direct generalisation to non-US or non-tertiary care settings** without appropriate validation, given the single-centre, US academic medical centre origin of the data.

---

## Dataset Structure

MIMIC-IV adopts a relational structure with predefined relationships stored across tables and columns. Data are organised into three modules:

| Module | Description |
|--------|-------------|
| `hosp` | Hospital-wide EHR data: admissions, transfers, diagnoses (ICD-9/10), procedures, laboratory results, microbiology, medication prescriptions and administration (eMAR), provider orders, and billing codes (DRG, HCPCS). |
| `icu` | ICU-specific data sourced from the MetaVision clinical information system (iMDsoft): ICU stays (`icustays`), charted vital signs (`chartevents`), fluid inputs (`inputevents`), outputs (`outputevents`), procedures (`procedureevents`), and datetime events (`datetimeevents`). |
| `note` | Deidentified free-text clinical notes, including discharge summaries and radiology reports. Available as a separate PhysioNet project: [MIMIC-IV-Note](https://physionet.org/content/mimic-iv-note/). |

Tables within modules are linked by shared identifiers:

- `subject_id` — unique patient identifier (present in all tables)
- `hadm_id` — unique hospital admission identifier
- `stay_id` — unique ICU stay identifier (icu module)

Dates and times are shifted consistently per patient into a fictional future window (approximately 2100–2200) to prevent re-identification while preserving intra-patient temporal relationships.

Data are distributed as **comma-separated value (CSV) files** and are also accessible via **Google BigQuery** and as an **SQLite database**.

---

## Dataset Creation

### Curation Rationale

MIMIC-IV was created to address the critical shortage of openly accessible, real-world clinical datasets for research. Retrospectively collected EHR data offer valuable opportunities for knowledge discovery, algorithm development, and reproducible science. MIMIC-IV updates and expands MIMIC-III with contemporary data (2008–2022), a cleaner modular structure, and additional data elements, while maintaining the commitment to open credentialed access that has made the MIMIC series a cornerstone of clinical informatics research.

### Source Data

#### Data Collection and Processing

Data were collected from three source systems at BIDMC:

1. **Hospital-wide EHR** (custom system) — source of the `hosp` module.
2. **MetaVision ICU clinical information system** (iMDsoft) — source of the `icu` module.
3. **Emergency department information system** — source of MIMIC-IV-ED (a linked companion dataset).

The curation pipeline proceeded in three stages:

1. **Acquisition:** a master patient list was assembled from all medical record numbers corresponding to patients admitted to an ICU or ED between 2008 and 2022. All source tables were filtered to retain only those patients.
2. **Preparation:** tables were denormalised, audit trails were removed, and data were reorganised to facilitate retrospective analysis. Importantly, **no data cleaning was performed**, preserving the messy, real-world character of the dataset.
3. **Deidentification:** patient identifiers stipulated under the HIPAA Safe Harbor provision were removed and replaced with randomly generated integer identifiers (`subject_id`, `hadm_id`, `stay_id`). Structured columns were filtered using allow lists. Free-text fields were processed using a combination of rule-based algorithms and a neural network deidentification model; detected PHI was replaced with three consecutive underscores (`___`). Dates and times were shifted by a random integer offset (consistent within each patient) to remove seasonality and year information.

#### Who are the source data producers?

The source data were produced during routine clinical care at the **Beth Israel Deaconess Medical Center (BIDMC)**, a tertiary academic medical centre in Boston, Massachusetts, USA, affiliated with Harvard Medical School. Clinical staff — physicians, nurses, pharmacists, and other providers — generated the records as part of standard patient care. No additional data collection was performed specifically for research purposes.

---

### Annotations

#### Annotation process

MIMIC-IV does not contain prospective research annotations. Diagnoses and procedures are coded using standard clinical ontologies (ICD-9-CM / ICD-10-CM for diagnoses; ICD-9-PCS / ICD-10-PCS for procedures; DRG codes for billing) as assigned by hospital coding staff. Laboratory and microbiology results are recorded with LOINC-compatible item identifiers. Free-text notes in MIMIC-IV-Note are not annotated beyond deidentification.

#### Who are the annotators?

Clinical coding was performed by trained medical coders at BIDMC as part of standard hospital operations. Deidentification was performed by the MIT Laboratory for Computational Physiology.

---

### Personal and Sensitive Information

MIMIC-IV contains highly sensitive medical information, including diagnoses, treatments, laboratory results, vital signs, and — in MIMIC-IV-Note — free-text clinical narratives. All direct patient identifiers (name, date of birth, address, phone number, etc.) have been removed in accordance with the HIPAA Safe Harbor provision. Ages above 89 are obscured. Dates are time-shifted.

Despite deidentification, **re-identification risk cannot be completely eliminated** for rare conditions or unusual clinical trajectories. Access is therefore restricted to credentialed researchers who have completed a recognised human subjects research course (e.g., CITI "Data or Specimens Only Research") and signed a data use agreement. Any derived datasets or models must be treated as sensitive and shared only under equivalent access controls.

---

## Bias, Risks, and Limitations

- **Single-centre bias:** all data originate from a single US tertiary academic medical centre (BIDMC, Boston, MA). Patient demographics, care protocols, and coding practices may not be representative of other hospitals, health systems, or countries.
- **Demographic skew:** the patient population reflects the catchment area of BIDMC and may under-represent certain racial, ethnic, socioeconomic, or age groups. Models trained on MIMIC-IV may perform poorly on more diverse populations.
- **Missing data:** as a real-world dataset, MIMIC-IV contains substantial missingness. Values are missing not at random (MNAR) — the absence of a measurement often carries clinical meaning (e.g., a laboratory test not ordered because it was not deemed necessary).
- **Temporal shift:** dates are shifted into a fictional window (approximately 2100–2200). Absolute calendar-year analyses are not possible, though approximate cohort years can be inferred via `anchor_year_group`.
- **Coding and documentation variability:** ICD codes reflect billing practices as much as clinical reality. Free-text notes vary in structure and completeness across providers and time periods.
- **No causal structure:** MIMIC-IV is observational. Confounding by indication and selection bias are inherent; causal inference requires careful study design.
- **Access latency:** because access requires credentialing, the dataset is not suitable for rapid open benchmarks or fully reproducible public pipelines without a PhysioNet account.

---

## Recommendations

Users should be made aware of the risks, biases, and limitations described above. In particular:

- Models or findings derived from MIMIC-IV should be externally validated on independent datasets before any clinical application.
- Demographic fairness analyses are strongly recommended before deploying any MIMIC-derived model.
- Users should consult the [MIMIC Code Repository](https://github.com/MIT-LCP/mimic-code) for community-maintained preprocessing scripts, concept derivations, and reproducible analyses.
- Derived datasets and models must be shared on PhysioNet under the same data use agreement as the source data.

---

## Citation

### BibTeX

```bibtex
@article{johnson2023mimic,
  title     = {{MIMIC-IV}, a freely accessible electronic health record dataset},
  author    = {Johnson, Alistair E W and Bulgarelli, Lucas and Shen, Lu and
               Gayles, Alvin and Shammout, Ayad and Horng, Steven and
               Pollard, Tom J and Hao, Sicheng and Moody, Benjamin and
               Gow, Brian and Lehman, Li-wei H and Celi, Leo Anthony and
               Mark, Roger G},
  journal   = {Scientific Data},
  volume    = {10},
  number    = {1},
  pages     = {1},
  year      = {2023},
  publisher = {Nature Publishing Group},
  doi       = {10.1038/s41597-022-01899-x}
}
```

### PhysioNet platform citation (also required)

```bibtex
@article{goldberger2000physiobank,
  title   = {{PhysioBank}, {PhysioToolkit}, and {PhysioNet}:
             Components of a new research resource for complex physiologic signals},
  author  = {Goldberger, Ary L and Amaral, Luis A N and Glass, Leon and
             Hausdorff, Jeffrey M and Ivanov, Plamen Ch and Mark, Roger G and
             Mietus, Joseph E and Moody, George B and Peng, Chung-Kang and
             Stanley, H Eugene},
  journal = {Circulation},
  volume  = {101},
  number  = {23},
  pages   = {e215--e220},
  year    = {2000},
  doi     = {10.1161/01.CIR.101.23.e215}
}
```

### APA

Johnson, A. E. W., Bulgarelli, L., Shen, L., Gayles, A., Shammout, A., Horng, S., Pollard, T. J., Hao, S., Moody, B., Gow, B., Lehman, L.-W. H., Celi, L. A., & Mark, R. G. (2023). MIMIC-IV, a freely accessible electronic health record dataset. *Scientific Data*, *10*, 1. https://doi.org/10.1038/s41597-022-01899-x

---

## Glossary

| Term | Definition |
|------|-----------|
| **BIDMC** | Beth Israel Deaconess Medical Center, Boston, MA — the sole source hospital for MIMIC-IV. |
| **EHR** | Electronic Health Record — a digital record of a patient's medical history maintained by the care provider. |
| **ICU** | Intensive Care Unit — a specialist ward providing intensive monitoring and treatment to critically ill patients. |
| **ED** | Emergency Department. |
| **PHI** | Protected Health Information — any information that could be used to identify a patient, as defined by HIPAA. |
| **HIPAA** | Health Insurance Portability and Accountability Act (US, 1996) — sets standards for the protection of health information. |
| **ICD** | International Classification of Diseases — a standardised system for coding diagnoses and procedures (versions 9 and 10 are used in MIMIC-IV). |
| **DRG** | Diagnosis Related Group — a classification used for hospital billing. |
| **HCPCS** | Healthcare Common Procedure Coding System — a set of codes used for billing medical services. |
| **subject_id** | Deidentified unique integer identifier assigned to each patient. |
| **hadm_id** | Deidentified unique integer identifier assigned to each hospital admission. |
| **stay_id** | Deidentified unique integer identifier assigned to each ICU stay. |
| **anchor_year** | A fictional deidentified year (in the range 2100–2200) used to anchor patient timelines. |
| **anchor_year_group** | A three-year range (e.g., "2014–2016") indicating the approximate real period of a patient's admission. |

---

## More Information

- Full documentation: https://mimic.mit.edu/
- MIMIC Code Repository (SQL, Python): https://github.com/MIT-LCP/mimic-code
- Access request and credentialing: https://physionet.org/content/mimiciv/
- MIMIC-IV-Note (free-text clinical notes): https://physionet.org/content/mimic-iv-note/
- MIMIC-IV-ED (emergency department module): https://physionet.org/content/mimic-iv-ed/
- MIMIC-IV-ECG (electrocardiograms): https://physionet.org/content/mimic-iv-ecg/
- MIMIC-IV Clinical Database Demo (open-access, 100 patients): https://physionet.org/content/mimic-iv-demo/

---

## Dataset Card Authors

This dataset card was compiled from official PhysioNet documentation, the MIMIC-IV *Scientific Data* paper (Johnson et al., 2023), and the MIT-LCP MIMIC Code Repository. It is intended as a community resource and not an official publication of MIT-LCP or PhysioNet.

---

## Dataset Card Contact

For questions about data access, corrections, or issues: please open an issue on the [MIMIC Code Repository](https://github.com/MIT-LCP/mimic-code/issues) or contact PhysioNet via https://physionet.org/about/#contact_us.
