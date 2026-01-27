# GoRules Logic Notes

This doc highlights the **logic differences** between the two apps and where the decision ?split? happens.

## PoC1 (two decisions, app?level switch)
Files:
- `streamlit_app.py`
- `rules/public_holidays.jdm.json`
- `rules/business_hours.jdm.json`

Logic:
- The Streamlit app evaluates **public holidays first** and only evaluates business hours if no holiday message is returned.
- The ?switch? happens **in Python**.

Code (PoC1):
```python
holiday_result = holiday_decision.evaluate(holiday_input)
holiday_message = holiday_result.get("result", {}).get("message", "")

if holiday_message:
    final_message = holiday_message
else:
    result = business_decision.evaluate(business_input)
    final_message = result.get("result", {}).get("message", "")
```

## PoC2 (single JDM, model?level switch)
Files:
- `streamlit_app2.py`
- `rules/combined_business_and_holidays.jdm.json`

Logic:
- The Streamlit app makes **one** decision call.
- The **JDM model** contains two decision tables (Public Holidays + Business Hours).
- An **expression node** decides which message to return based on `is_holiday`.
- The ?switch? happens **inside the JDM** (not in Python).

Code (PoC2):
```python
result = decision.evaluate(gorules_input)
message = result.get("result", {}).get("message", "")
```

JDM expression node (PoC2):
```json
{
  "type": "expressionNode",
  "name": "Final Message",
  "content": {
    "expressions": [
      {
        "key": "message",
        "value": "$nodes[\"Public Holidays\"].is_holiday == true ? $nodes[\"Public Holidays\"].message : $nodes[\"Business Hours\"].message"
      }
    ]
  }
}
```

## Summary
- **PoC1**: two JDMs + Python decides which output to use.
- **PoC2**: one JDM + GoRules decides which output to use.
