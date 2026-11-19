# BactoMut

**A Bacterial Protein Mutation Impact Prediction System**

BactoMut is a local, beginner-friendly academic project for analyzing single amino-acid substitutions in TEM-1 beta-lactamase. It trains regression models on genuine deep-mutational-scanning records and estimates the dataset-specific experimental mutation-effect score.

[Click here to open the project demo video](https://drive.google.com/file/d/1vhrr58d-8phgcuFsm9ygkjeRSHFlNylK/view?usp=drivesdk)

> **Scope:** These models estimate a specific TEM-1 assay score. They do not predict bacterial survival, clinical pathogenicity, antibiotic resistance, patient outcomes, or the effect of mutations in other proteins. A prediction is computational, not experimentally confirmed.

## Objectives and features

- Accept a protein sequence or a single-record FASTA file.
- Parse and validate a single substitution such as `V42A`; reject unsupported mutation forms, invalid residues, out-of-range positions, and reference mismatches.
- Extract BLOSUM62, residue molecular-weight, Kyte-Doolittle hydrophobicity, approximate pH-7 charge, position, and local sequence-context features.
- Train and compare Random Forest, Decision Tree, and Linear Regression on the official dataset stages.
- Report MAE, RMSE, R², and Spearman rank correlation calculated from held-out labels.
- Explore the live dataset and show genuine observed scores, mutation distributions, and model outputs.
- Generate a downloadable PDF research report.
- Run locally with Streamlit; no deployment or hosting configuration is included.

## Dataset and scientific basis

The primary dataset is [SaProtHub/Dataset-BLAT_ECOLX](https://huggingface.co/datasets/SaProtHub/Dataset-BLAT_ECOLX), loaded with the Hugging Face `datasets` library. Its observed schema is:

| Column | Meaning |
|---|---|
| `protein` | 286-aa TEM-1 protein-variant sequence |
| `label` | Experimental deep-mutational-scanning mutation-effect score |
| `stage` | Official `train`, `valid`, or `test` stage |

The dataset card reports 4,366 train, 575 validation, and 527 test examples. The `stage` column is inside the dataset's sole published `train` split. The mutation is not a separate source column: preprocessing derives it by comparing each sequence to the verified reference and retains only exactly one-substitution records. It does not create labels.

The dataset card declares the score's wild-type reference as **1.0**, with values above 1 described as higher fitness than wild type. In the inspected release, the 5,468 sequences were 286 residues long and labels ranged from 0.0008 to 2.9024. The exact wild-type sequence appears in 271 source records (225 train, 23 validation, 23 test); these are replicate assay scores, not all exactly 1.0. After removing 10 exact duplicate training records, the 215 unique training-stage wild-type scores have a mean of about 1.0239 (SD 0.1974). BactoMut uses 1.0, the dataset-card normalized reference, for its primary score difference, and displays the training-only empirical mean separately as a secondary comparison. No general harmful/beneficial cutoff is applied.

Reference: [UniProt P62593, BLAT_ECOLX](https://rest.uniprot.org/uniprotkb/P62593.fasta). Dataset license: MIT, as declared by its Hugging Face card. The dataset card cites *Deep generative models of genetic variation capture the effects of mutations*, Nature Methods (2018), [doi:10.1038/s41592-018-0138-4](https://doi.org/10.1038/s41592-018-0138-4). [ProteinGym](https://proteingym.org/) is a related resource for benchmark context; its assays are not merged into this project.

Dataset limitations include assay-specific measurements, sequence-level rather than clinical outcomes, replicate variability in the observed wild-type scores, and repeated source records. Ten exact duplicate training records are excluded from the empirical wild-type reference summary. The wild-type sequence records are not treated as mutation examples. Training collapses repeated mutation measurements within a stage by their mean; an identical sequence in an earlier stage is excluded from later evaluation to reduce leakage. Exclusion counts are written to model metadata. Official stage membership is not reassigned.

## Technologies

Python 3, Biopython, Pandas, NumPy, Hugging Face Datasets, scikit-learn, Random Forest Regressor, Decision Tree Regressor, Linear Regression, Streamlit, Matplotlib, Plotly, ReportLab, and Joblib.

## Project architecture

```text
BactoMut-AI/
├── app.py
├── api_server.py
├── requirements.txt
├── README.md
├── .gitignore
├── data/
│   ├── raw/                 # Reference FASTA; source dataset is loaded through Datasets
│   └── processed/           # Generated processed records
├── models/                  # Generated models, preprocessing, and evaluation metadata
├── src/
│   ├── dataset_loader.py
│   ├── preprocessing.py
│   ├── mutation_analysis.py
│   ├── feature_extraction.py
│   ├── model_training.py
│   ├── prediction.py
│   ├── visualization.py
│   ├── report_generator.py
│   ├── reference.py
│   └── ui.py
├── pages/
│   ├── 0_Home.py
│   ├── 1_Mutation_Analysis.py
│   ├── 2_AI_Prediction.py
│   ├── 3_Dataset_Explorer.py
│   ├── 4_Model_Performance.py
│   └── 5_Research_Report.py
├── tests/
└── notebooks/
    └── model_experimentation.ipynb
```

The home page uses Streamlit's top navigation for the research sections. The local
Streamlit deploy control and default sidebar navigation are hidden through
`.streamlit/config.toml`; the application is intended for local use only.

## Installation and local execution

Use Python 3.10 or later (Python 3.11 is a suitable choice) in a virtual environment. Training and first-time dataset exploration need internet access to Hugging Face.

```powershell
cd BactoMut-AI
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m src.model_training
streamlit run app.py
```

The required app launch commands are `pip install -r requirements.txt` and `streamlit run app.py`. Models are not fabricated or silently generated by the UI: train them with `python -m src.model_training`. The command downloads the dataset using Hugging Face Datasets, validates and preprocesses actual records, saves the processed data, fits the three models, computes validation/test metrics, and writes:

- `models/random_forest.pkl`
- `models/decision_tree.pkl`
- `models/linear_regression.pkl`
- `models/preprocessing.pkl`
- `models/model_metadata.json`

Hugging Face Datasets may cache its downloaded source files outside this project. Generated data under `data/processed/` is ignored by Git; trained model files and their calculated metadata are written to `models/`.

## Local API and Postman

Start the API in a second terminal from the project directory:

```powershell
python api_server.py
```

The API binds only to `127.0.0.1` and does not expose a public or hosted endpoint. In Postman, create a **POST** request to `http://127.0.0.1:8000/predict`, select **Body → raw → JSON**, and send:

```json
{
  "mutation": "M1I",
  "model": "Random Forest"
}
```

If `sequence` is omitted, the API uses the bundled TEM-1 wild-type reference. To use a mutant sequence, provide its `sequence` and omit `mutation` so the app infers the substitution:

```json
{
  "sequence": "PASTE_A_SINGLE_MUTANT_TEM1_SEQUENCE_HERE",
  "model": "Random Forest"
}
```

Replace the example string with an actual protein sequence (do not include placeholder text). An optional `mutation` can be included with a mutant sequence only if it matches the inferred wild-type substitution. Supported models are `Random Forest`, `Decision Tree`, and `Linear Regression`. The JSON response includes the inferred mutation, predicted assay score, wild-type references, and extracted features. `GET http://127.0.0.1:8000/health` checks service/model availability; `GET http://127.0.0.1:8000/models` lists available models. The API needs the trained model files described above.

## Using the application

1. Run the app locally and choose **Mutation Analysis** to enter a sequence or upload one FASTA record.
2. Provide one substitution, e.g. `V42A`. The notation describes the change from wild type to mutant.
3. Use **AI Prediction** to select a trained model. Enter the TEM-1 reference and mutation, or paste a single-mutant TEM-1 sequence/contiguous reference fragment and leave the mutation field blank for automatic inference. A fragment must align uniquely to the reference. If a sequence and mutation are both provided, they must agree.
4. Review the dataset-defined wild-type reference and the score difference. A score above or below 1 reflects the dataset's target definition only.
5. Use **Dataset Explorer** and **Model Performance** for source observations and calculated held-out metrics.
6. Use **Research Report** to generate and download a PDF.

## Feature and modeling methodology

Training mutations are derived from the published sequence and compared to the UniProt reference. The same feature extractor and fixed column schema are used at training and prediction. Categorical residue/context fields are one-hot encoded; numeric fields are median-imputed and standardized using training data. No target-derived feature is included.

Only the official `train` stage is used to fit models. The official `valid` and `test` stages are kept separate for evaluation. Identical sequences repeated within a stage are averaged; sequences appearing in an earlier stage are excluded from later-stage evaluation. No split is randomized or reassigned. Random Forest is the primary model; Decision Tree and Linear Regression are comparisons. Model hyperparameters are fixed in the training code; test metrics are not used to select them.

Metrics are Mean Absolute Error (MAE), Root Mean Squared Error (RMSE), R², and Spearman rank correlation, calculated from each official held-out stage. Tree-model feature importance is impurity-based, not causal. Results depend on this dataset, feature representation, and training procedure; no performance value is hardcoded.

## Tests

Run:

```powershell
pytest
```

Tests cover mutation notation and residue validation, sequence/FASTA validation, feature extraction, dataset schema/auditing, model loading and prediction, and PDF creation. Model training itself requires network access to the genuine dataset.

## References

- SaProtHub, [Dataset-BLAT_ECOLX](https://huggingface.co/datasets/SaProtHub/Dataset-BLAT_ECOLX), MIT license declared in dataset card.
- UniProt, [P62593, TEM beta-lactamase](https://www.uniprot.org/uniprotkb/P62593/entry).
- Riesselman AJ et al. [Deep generative models of genetic variation capture the effects of mutations](https://doi.org/10.1038/s41592-018-0138-4). *Nature Methods* (2018).
- [ProteinGym](https://proteingym.org/), an additional resource for protein variant benchmark context; no ProteinGym assay data is combined here.

## Developer

Developed by Afifa Kounain.
