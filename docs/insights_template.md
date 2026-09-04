# Business Insights Template

Use this template only after executing the relevant SQL query or reviewing a Power BI visual. Replace every bracketed placeholder with evidence from the analysis. Do not convert correlation into a causal claim.

## Analysis scope

- Analysis period: `[start date]` to `[end date]`
- Data source: `[SQL file/query, workbook sheet, or Power BI visual]`
- Filters applied: `[filters or None]`
- Metric definition: `[link/name from kpi_definitions.md]`
- Data caveats: `[known limitation]`

## Finding 1

**Finding:**  
`[State one precise observation. Example: Store X has a lower gross margin than the company average.]`

**Evidence:**  
`[Give the executed values, comparison, period, sample size, and source query.]`

**Possible business impact:**  
`[Explain why the observation may matter. Keep uncertainty visible.]`

**Recommendation:**  
`[Suggest a proportionate next action or investigation.]`

**How to measure the result:**  
`[Name the KPI, expected direction, review date, and guardrail.]`

## Finding 2

**Finding:**  
`[Observation]`

**Evidence:**  
`[Executed values and source]`

**Possible business impact:**  
`[Impact]`

**Recommendation:**  
`[Action]`

**How to measure the result:**  
`[KPI and guardrail]`

## Finding 3

**Finding:**  
`[Observation]`

**Evidence:**  
`[Executed values and source]`

**Possible business impact:**  
`[Impact]`

**Recommendation:**  
`[Action]`

**How to measure the result:**  
`[KPI and guardrail]`

## Final checks before publishing

- [ ] The query was executed against the current database.
- [ ] The date range, filters, currency, and metric denominator are stated.
- [ ] Totals were reconciled to a second calculation or summary.
- [ ] Sales and returns were aggregated separately before calculating return rate.
- [ ] Partial months are labeled or excluded from comparisons.
- [ ] Recommendations are supported by evidence.
- [ ] Any causal language is removed unless a causal method was used.

