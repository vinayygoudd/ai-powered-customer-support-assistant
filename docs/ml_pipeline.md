# ML Pipeline

The project generates 2,400 synthetic-but-structured support records by default. The generator deliberately creates varied messages across six categories and four priorities so the complete training workflow is reproducible without depending on a third-party dataset.

## Preprocessing
Pandas loads the CSV. Missing required labels/messages are removed, text is normalized, whitespace is collapsed, and duplicate records are removed. NumPy is used for nullable resolution-time values during dataset creation.

## Feature extraction and models
Each target has an independent scikit-learn Pipeline:
`TfidfVectorizer(1-2 grams) -> LogisticRegression`.

The same fitted pipeline performs feature extraction and inference, preventing train/inference preprocessing drift.

## Evaluation
`python -m ml.evaluate` calculates accuracy, weighted precision, weighted recall, weighted F1, classification reports, and confusion matrices, then writes `data/processed/evaluation.json`. The repository does not claim fixed performance numbers; run evaluation after generating/training to obtain actual metrics.

## Limitations
The generated dataset is synthetic and may not represent a real production support distribution. Real deployment should retrain on reviewed historical tickets, monitor drift, calibrate confidence, and validate category/priority policies with domain owners.


## Benchmark interpretation
The generated data includes varied templates, contextual phrases, formatting variation, and a small amount of label noise. Evaluation reports a majority-class baseline as a sanity check. Neither the baseline nor model metrics should be interpreted as production performance because the dataset is synthetic.
