# GoRules Business Hours PoC

This repo contains two small Streamlit proof-of-concept apps that evaluate business hours using GoRules (zen engine). Both use a 2026 public holiday list and a weekday/time business-hours table.

## Two approaches

### PoC1 = two separate decisions (app-level switch)
- Files: `streamlit_app.py`, `rules/business_hours.jdm.json`, `rules/public_holidays.jdm.json`
- Flow:
  1) Evaluate **Public Holidays** decision with `{ date }`.
  2) If a holiday is found, return **"we are closed on this public holiday"**.
  3) Otherwise evaluate **Business Hours** with `{ day_of_week, minutes }`.
- The "switch" logic is in Python (the Streamlit app decides which result to show).

### PoC2 = single JDM with two tables (model-level switch)
- Files: `streamlit_app2.py`, `rules/combined_business_and_holidays.jdm.json`
- Flow:
  1) One decision call sends `{ date, day_of_week, minutes }`.
  2) The model evaluates **Public Holidays** and **Business Hours** in the same graph.
  3) An **expression node** (?Final Message?) chooses the holiday result if `is_holiday == true`, otherwise uses the business-hours message.
- The "switch" logic is inside the JDM model rather than the app.

## Business hours rules
- Mon-Wed: 08:00?17:00
- Thu: 08:00?21:00
- Fri: 08:00?15:00
- Sat/Sun: closed

## Data files
- `data/2026_pubhol_QLD.csv` - public holidays (date, day, holiday name, location)
- `data/business_hours.csv` - lookup table for hours
- `data/decision_log.csv` - appended log of each evaluation

## Run
1) Create/activate your virtual environment (e.g., `gorules`).
2) Install deps:
   ```
   pip install -r requirements.txt
   ```
3) Run either app:
   ```
   streamlit run streamlit_app.py
   # or
   streamlit run streamlit_app2.py
   ```

## JDM editor (Docker)
If you want a local visual editor/simulator for JDM files, you can run the official GoRules editor container:
```
docker run -p 3000:3000 --platform=linux/amd64 gorules/editor
```
There is also an online version here https://editor.gorules.io/ 


## Notes
- Both apps allow a random 2026 date/time or a manual input.
- For PoC2, the decision split happens inside `rules/combined_business_and_holidays.jdm.json` in the **"Final Message"** expression node.
