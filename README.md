# EECS4312_W26_SpecChain

## instructions:
Please update to include: 
- App name
- Data collection method
- Original dataset
- Final cleaned dataset
- Exact commands to run pipeline

# example

Application: [Fitness Tracking App]

Dataset:
- reviews_raw.jsonl contains the collected reviews scraped from app store sources.
- reviews_clean.jsonl contains the cleaned dataset after preprocessing.
- The cleaned dataset contains 1169 reviews.

Repository Structure:
- data/ contains datasets and review groups
- personas/ contains persona files
- spec/ contains specifications
- tests/ contains validation tests
- metrics/ contains all metric files
- src/ contains executable Python scripts
- reflection/ contains the final reflection

How to Run:
1. python src/00_validate_repo.py
2. python src/run_all.py
3. Open metrics/metrics_summary.json for comparison results