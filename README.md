# warn_entrepreneurship


# The Entrepreneurial Lag: Predicting Business Formation via Labor Market ShocksExecutive 

# Summary
Does a layoff today predict a new business tomorrow? This project analyzes the relationship between WARN Act Layoff Notices and High-Propensity Business Applications (BFS) across the US from 2023–2026. While raw correlations suggest a strong link, this study employs OLS Regression and Quarterly Aggregation to reveal a "Geography of Resilience." I found that the "9-month incubation period" for new startups is highly predictable in "Incubator" states like Virginia, but the inverse is true for states like California and Washington.  

# Key Findings
The 231% Multiplier: At a national level, every 1,000 layoffs is associated with ~2,313 new business filings nine months later ($p < 0.001$).  This is not causal and additional work needs to be done to identify the causal link between layoffs and new business formation.  However, significant differences were found across geographies that provide signals about entrepreneurship in these areas.

## Geographic Divergence: 
1.  The Incubator (VA): High predictability ($R^2=0.25$). Layoffs are a mechanical leading indicator of growth.
2.  The Opportunity Hub (GA/NC): Low predictability ($R^2=0.07$). Entrepreneurship is driven by "Opportunity" rather than "Necessity," making traditional layoff data a poor predictor.  The state policies surrounding layoffs also mirror the federal standard, meaning that there are fewer WARN notices unless the scale of the layoffs is large.  More data is needed to understand drivers of entrepreneurship in these markets.
3.  The Volatile Core (CA/WA): Pro-cyclical. Layoffs act as a systemic shock that suppresses business formation rather than catalyzing it.Technical Methodology1. 

| State Type | Representative | Multiplier ($\beta$) | $R^2$ | Interpretation |
| :--- | :--- | :--- | :--- | :--- |
| **Incubator** | Virginia (VA) | 2.53 | 0.25 | Predictable talent recycling pipeline. |
| **Opportunity Hub** | Southeast (GA/NC)| 0.96 | 0.07 | Decoupled; growth is organic/non-necessity. |
| **Volatile Core** | California (CA) | -0.97 | 0.03 | Pro-cyclical; shocks suppress formation. |

# Data Sources
WARN Act Data: Cleaned and standardized regulatory filings (Mass Layoff Notices).Census Bureau BFS: Business Formation Statistics, filtered for "High-Propensity" applications (those likely to hire employees).
BFS Data: restricted sample to 

# Analysis Notes
Initially, a high correlation was observed ($r=0.36$) in DC, but further "Growth-to-Growth" testing (using percent changes) revealed this was an artifact of the COVID-19 recovery period. To find the true signal, I moved to Quarterly Aggregation To "denoise" the temporal jitter of government reporting cycles and restricted sample to the post-COVID period (2023-2026).  

OLS Regression was used to analyze the relationship between layoffs and new business formation and observe the strength of the relationship ($R^2$).

Negative Control: Conducted a first-difference (percent change) correlation check. In DC, growth-to-growth correlation collapsed from 0.36 to 0.063 when detrended, identifying the "COVID-period trend" as a confounding variable and necessitating the pivot to quarterly OLS modeling.

Handling Zero-Inflation & Reporting Gaps.  In "Federal Standard" states (GA, NC) where reporting thresholds are high (500+ employees), I employed Regional Pooling to capture latent signals that are otherwise lost in state-level noise. 

| Metric | Level Analysis | Growth-to-Growth | Aggregated OLS |
| :--- | :--- | :--- | :--- |
| **Raw Correlation** | 0.36 | 0.063 | 0.60 |
| **Findings** | High (Confounded) | Low (Noisy) | **High (Robust)** |
| **The "Why"** | Driven by COVID trends. | Monthly jitter hides signal. | Quarterly windows reveal the 9-month lag. |

# Strategic Implications for People Analytics
1.  Talent Recycling: In high-yield states, "People Leaders" should view layoffs as the start of a new talent ecosystem, not just a labor contraction.
2.  Alternative Data Necessity: The "Invisibility" of the Southern startup engine (low $R^2$ in GA/NC) proves that traditional government data is insufficient for tracking modern labor velocity.
3.  Resilience Modeling: Firms can use these multipliers to predict which regions will bounce back fastest after economic downturns.
  
# Tech Stack
Language: Python 3.13 
Libraries: pandas, statsmodels (OLS), numpy, matplotlib
Methodologies: Time-Series Lag Analysis, Detrending (First-Differencing), Regional Pooling.
