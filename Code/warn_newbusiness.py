#WARN Notices and New Business Formation
#"Do localized layoffs (detected via WARN) act as a catalyst for regional startup clusters, or do they lead to 'Brain Drain' where talent leaves the city?"

#Load latest WARN notice data from Big Local News
import pandas as pd
#url = "https://storage.googleapis.com/bln_prod/project/bdc96e51-d30a-4ea7-868b-8db87dc34582/integrated.csv?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Credential=bln-storage%40big-local-news-267923.iam.gserviceaccount.com%2F20260418%2Fauto%2Fstorage%2Fgoog4_request&X-Goog-Date=20260418T110659Z&X-Goog-Expires=86400&X-Goog-SignedHeaders=host&X-Goog-Signature=5a554d5f4b0f1a8b6cfd51a0b2c9df6eee28799ad00cf24b9e6b866bae65ff9dc4c61e8c5946a146d2fb118591cd8c226d4da37a4faf7a0f67ad4baf02a50035cbe1f53b5948061431432a1f9fbc56adcbf3b56c037a4b24a6f2a164f1674065c63a534d45293f31a6e954b7ec67587c874ef5a4b38578d139f181e7c9d334ef3343eadd2e693ce7d8b92ac6936dd352eee678332b6f7cb737759916abaf1db80b2c6a845bcb3f85293a366157ec536196cc9a469c63c01ca81ccd13f42fd6954d0f3fdff1f99c798b29a9db7b2cc572e15ffbfbe33cc73f874c8ea785ca7de4809eee421c6d1c44f0d7b776c18931a698414c2d8aa5262468744c775c98697e"
#df = pd.read_csv(url, low_memory=False)
df = pd.read_csv("Data/WARN_notices_4182026.csv")


#Company Name Normalization
#Convert all to lowercase, remove Company, Inc., punctuation, Holdings, Corp
suffixes = r'\b(company|inc|holdings|corp|corporation|llc|ltd|limited)\b'
df_warn['company_clean'] = (
    df_warn['company']
    .str.lower()                               # Convert to lowercase
    .str.replace(r'[^\w\s]', '', regex=True)  # Remove all punctuation
    .str.replace(suffixes, '', regex=True)     # Remove the specific words
    .str.replace(r'\s+', ' ', regex=True)      # Replace multiple spaces with one space
    .str.strip()                               # Remove leading/trailing whitespace
)
print(df_warn[['company', 'company_clean']].head(20))

# Ensure date is a datetime object
df_warn['notice_date'] = pd.to_datetime(df_warn['notice_date'])

#Duplicate Elimination
# 1. Verify columns exist to avoid KeyError
actual_cols = [c for c in id_columns if c in df_warn.columns]

# 2. Convert to string/numeric to ensure hashability and consistent comparison
# This prevents "2026-01-01" (str) being treated differently than 2026-01-01 (datetime)
temp_df = df_warn.copy()
for col in actual_cols:
    if col == 'jobs':
        temp_df[col] = pd.to_numeric(temp_df[col], errors='coerce')
    else:
        temp_df[col] = temp_df[col].astype(str).str.lower().str.strip()

# 3. Drop duplicates based on the standardized temp_df
df_warn = df_warn.loc[temp_df.drop_duplicates(subset=actual_cols, keep='first').index]

print(f"Duplicates removed. Remaining records: {len(df_warn)}")

#Eliminate Records Missing Worker Counts
df_warn = df_warn.dropna(subset=['jobs'])

# Create a YYYY-MM string to match Census 'time' format
df_warn['month_str'] = df_warn['notice_date'].dt.strftime('%Y-%m')

# Aggregate: Sum the workers laid off per state/month
# Also count the number of unique companies (notices)
df_warn['state'] = df_warn['postal_code']
warn_monthly = df_warn.groupby(['state', 'month_str']).agg(
    total_layoffs=('jobs', 'sum'),
    notice_count=('company_clean', 'count')
).reset_index()

print(warn_monthly.head(50))

#Download the BFS Data
#bfs_url = "https://www.census.gov/econ/bfs/csv/bfs_monthly.csv"
df_bfs = pd.read_csv("Data/bfs_monthly.csv")

# To look at just the most recent "High-Propensity" applications (HBA)
# This is the series most likely to correlate with layoffs and hiring
df_hba = df_bfs[df_bfs['series'] == 'BA_HBA']

# Identify the month columns (jan, feb, mar, etc.)
month_cols = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

# Transform from Wide to Long
df_hba_long = pd.melt(
    df_hba, 
    id_vars=['year', 'state', 'series'], 
    value_vars=month_cols,
    var_name='month_label', 
    value_name='new_business_apps'
)

# Map abbreviations to numbers
month_map = {
    'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04', 'may': '05', 'jun': '06',
    'jul': '07', 'aug': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
}

df_hba_long['month_num'] = df_hba_long['month_label'].str.lower().map(month_map)

# Create the final join key
df_hba_long['month_str'] = df_hba_long['year'].astype(str) + '-' + df_hba_long['month_num']

# Ensure column names match for the merge
df_hba_long = df_hba_long.rename(columns={'geo': 'state', 'time': 'month_str', 'val': 'new_business_apps'})

# The Merge
final_df = pd.merge(
    warn_monthly, 
    df_hba_long, 
    on=['state', 'month_str'], 
    how='inner'
)

# Group by state and calculate the correlation between layoffs and new apps
correlations = final_df.groupby('state').apply(
    lambda x: x['total_layoffs'].corr(x['new_business_apps'])
).sort_values(ascending=False)

print("Top 10 States with strongest Layoff-to-Startup correlation:")
print(correlations.head(10)) #DC has highest correlation

# Create a 1-month lag for layoffs - these are "Day Zero" entrepreneurs who took WARN notice as their final push
final_df['layoffs_lag1'] = final_df.groupby('state')['total_layoffs'].shift(1)

# Check correlation with the lag
lagged_corr = final_df['layoffs_lag1'].corr(final_df['new_business_apps'])
print(f"National Correlation with 1-month lag: {lagged_corr:.3f}") #lagged correlation is stronger than the immediate correlation

lagged_correlations = final_df.groupby('state').apply(
    lambda x: x['layoffs_lag1'].corr(x['new_business_apps'])
).sort_values(ascending=False)

print(lagged_correlations.head(10))

# Testing lags from 1 to 14 months - theory is that 3-6 months will capture people pivoting to their plan B 
#(entrepreneurship) and 6+ months captures strategic entrepreneurship
for i in range(1, 15):
    final_df[f'lag_{i}'] = final_df.groupby('state')['total_layoffs'].shift(i)
    correlation = final_df[f'lag_{i}'].corr(final_df['new_business_apps'])
    print(f"Correlation at {i} month(s) lag: {correlation:.3f}")

#correlation peaks at 9 months (0.252) and starts to decline

#Which state has the highest correlation at 9 months?
# Calculate correlation at 9-month lag for every state
final_df['layoffs_lag9'] = final_df.groupby('state')['total_layoffs'].shift(9)

# Group by state and calculate correlation
state_rankings = final_df.groupby('state').apply(
    lambda x: x['layoffs_lag9'].corr(x['new_business_apps'])
).sort_values(ascending=False)

print("Top 10 States where Layoffs most reliably predict Startups (9-mo lag):")
print(state_rankings.head(10))



#Get lowest correlation states
lowest_corr = state_rankings.sort_values(ascending=True).head(10)

print("States with the LOWEST 'Layoff-to-Startup' Correlation (9-mo lag):")
print(lowest_corr)

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# 1. Ensure columns are numeric
final_df['new_business_apps'] = pd.to_numeric(final_df['new_business_apps'], errors='coerce')
final_df['total_layoffs'] = pd.to_numeric(final_df['total_layoffs'], errors='coerce')

# 2. Create the lagged column (Move layoffs forward by 9 months)
final_df['layoffs_lagged_9mo'] = final_df.groupby('state')['total_layoffs'].shift(9)

def plot_dual_axis(state_code, ax_obj):
    # Filter and drop NaNs so the lines are continuous
    df_state = final_df[final_df['state'] == state_code].sort_values('month_str').dropna(subset=['layoffs_lagged_9mo', 'new_business_apps'])
    
    # Primary Axis: Business Apps
    ax_obj.plot(df_state['month_str'], df_state['new_business_apps'], color='tab:blue', label='New Business Apps', linewidth=2)
    ax_obj.set_ylabel('New Business Apps', color='tab:blue', fontsize=12)
    ax_obj.tick_params(axis='y', labelcolor='tab:blue')
    
    # Secondary Axis: Layoffs (from 9 months ago)
    ax2 = ax_obj.twinx()
    ax2.plot(df_state['month_str'], df_state['layoffs_lagged_9mo'], color='tab:orange', label='Layoffs (9mo Lag)', linestyle='--')
    ax2.set_ylabel('Layoffs (9mo ago)', color='tab:orange', fontsize=12)
    ax2.tick_params(axis='y', labelcolor='tab:orange')
    
    ax_obj.set_title(f'9-Month Relationship: {state_code}', fontsize=14)
    ax_obj.xaxis.set_major_locator(ticker.MaxNLocator(10))
    plt.setp(ax_obj.get_xticklabels(), rotation=45)

# Execute the plot
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12))
plot_dual_axis('DC', ax1)
plot_dual_axis('ID', ax2)

plt.tight_layout()
plt.show()

#looks like trend in DC is being driven by COVID-era layoffs

#try a split-sample to see if trend holds up for the last 2 years
# 1. Create a Post-COVID filter (e.g., everything from 2024 onwards)
df_recent = final_df[final_df['year'] >= 2024].copy()

# 2. Calculate the 9-month lag correlation for DC in just the recent period
recent_dc = df_recent[df_recent['state'] == 'DC']
recent_corr = recent_dc['layoffs_lagged_9mo'].corr(recent_dc['new_business_apps'])

print(f"DC Correlation (Full Period): {state_rankings['DC']:.3f}")
print(f"DC Correlation (2024-2026): {recent_corr:.3f}")
#Correlation is negative in DC post-COVID

#This could be spurious - check growth rates and compare those to see if the correlation remains
# Calculate month-over-month growth to remove the "COVID trend"
final_df['apps_pct_change'] = final_df.groupby('state')['new_business_apps'].pct_change()
final_df['layoffs_pct_change_lag9'] = final_df.groupby('state')['total_layoffs'].pct_change().shift(9)

# Re-run correlation on the changes to check whether this is driven by correlated growth rates
dc_growth_corr = final_df[final_df['state'] == 'DC']['layoffs_pct_change_lag9'].corr(
    final_df[final_df['state'] == 'DC']['apps_pct_change']
)
print(f"DC Growth-to-Growth Correlation: {dc_growth_corr:.3f}")
#Correlation is gone - the relationship was entirely driven by COVID-era shocks


###Analysis on Post-pandemic period to see if any relationship exists
# 1. Filter for the "Stable" Post-Pandemic period
# (Assuming your month_str is formatted YYYY-MM)
df_stable = final_df[final_df['month_str'] >= '2023-01'].copy()

#check out lags again
for i in range(1, 15):
    df_stable[f'lag_{i}'] = df_stable.groupby('state')['total_layoffs'].shift(i)
    correlation = df_stable[f'lag_{i}'].corr(df_stable['new_business_apps'])
    print(f"Correlation at {i} month(s) lag: {correlation:.3f}")
#highest corr is at 12 months

import numpy as np

# 1. Replace 'inf' with NaN so we can drop them all at once
df_stable = df_stable.replace([np.inf, -np.inf], np.nan)

# 2. Drop rows where either our X or Y variable is missing
# This ensures we are only correlating months where we have BOTH data points
clean_growth = df_stable.dropna(subset=['layoffs_pct_change_lag9', 'apps_pct_change'])

# 3. Re-run the correlation
stable_growth_corr = clean_growth['layoffs_pct_change_lag9'].corr(clean_growth['apps_pct_change'])

print(f"Cleaned Stable Growth Correlation: {stable_growth_corr:.3f}") #near 0, means that the month correlation was noise

# Aggregate to Quarter to filter out month to month noise
df_stable['quarter'] = pd.to_datetime(df_stable['month_str']).dt.to_period('Q')
quarterly = df_stable.groupby(['state', 'quarter'])[['total_layoffs', 'new_business_apps']].sum().reset_index()

# Run the 3-quarter lag (approx 9 months)
quarterly['layoffs_lag3'] = quarterly.groupby('state')['total_layoffs'].shift(3)
q_corr = quarterly['layoffs_lag3'].corr(quarterly['new_business_apps'])

print(f"Quarterly Correlation (3-Quarter Lag): {q_corr:.3f}")
#correlation is back (0.6) - tells us that a strong correlation between layoffs and entrepreneurship exist, 
# it just isnt perfectly individual month to month

#Run an OLS regression and see what the 9-month lag coefficient is and whether it is statistically significant or not
import statsmodels.api as sm

# Drop NaNs from the lag
df_reg = quarterly.dropna(subset=['layoffs_lag3', 'new_business_apps'])

# Define the variables
# X is the predictor (Layoffs from 3 quarters ago)
# Y is the target (Current Business Apps)
X = df_reg['layoffs_lag3']
y = df_reg['new_business_apps']

# Define the model
X = sm.add_constant(X)
model = sm.OLS(y, X).fit()

# Results
print(model.summary())
#9 month lag is statistically significant (99%)
#every 1 layoff predicts 2.3 new businesses (multiplier effect, 
# maybe a big layoff at google inspires others at other companies to pursue entrepreneurship)


#Which states have higher multipliers?
import statsmodels.api as sm

def get_state_yield(group):
    # Ensure we have enough quarterly data points for a valid regression
    valid = group.dropna(subset=['layoffs_lag3', 'new_business_apps'])
    if len(valid) < 8:  # Requires at least 2 years of quarterly data
        return None
    
    X = sm.add_constant(valid['layoffs_lag3'])
    model = sm.OLS(valid['new_business_apps'], X).fit()
    return model.params['layoffs_lag3']

# Apply the regression to each state
state_yields = quarterly.groupby('state').apply(get_state_yield).dropna().sort_values(ascending=False)

print("Top 10 States: Highest Multiplier (Business Apps per Layoff)")
print(state_yields.head(10))

import matplotlib.pyplot as plt

# Plotting the Top 10 Yields
plt.figure(figsize=(12, 6))
state_yields.head(10).plot(kind='bar', color='#1a5276')
plt.title('Entrepreneurial Multiplier: New Business Apps per 1.0 Layoffs (9-Month Lag)', fontsize=14)
plt.ylabel('Multiplier (Beta)', fontsize=12)
plt.xlabel('State', fontsize=12)
plt.axhline(y=1.0, color='r', linestyle='--', label='1:1 Parity')
plt.legend()
plt.xticks(rotation=45)
plt.show()

print("\nBottom 10 States: Lowest Multiplier")
print(state_yields.tail(10))

#Get regression results by state to see where beta is higher and where r2 is lower (more random noise probably driving results)
import statsmodels.api as sm

def get_detailed_metrics(state_code):
    # Filter data for the specific state
    state_data = quarterly[quarterly['state'] == state_code].dropna(subset=['layoffs_lag3', 'new_business_apps'])
    
    if len(state_data) < 4:
        return "Insufficient Data", 0, 0
    
    # Run the OLS Regression
    X = sm.add_constant(state_data['layoffs_lag3'])
    model = sm.OLS(state_data['new_business_apps'], X).fit()
    
    return state_code, model.params['layoffs_lag3'], model.rsquared

# Get results for both
results = [get_detailed_metrics('VA'), get_detailed_metrics('CA')]

print(f"{'State':<6} | {'Multiplier (Beta)':<18} | {'R-squared':<10}")
print("-" * 40)
for state, beta, r2 in results:
    print(f"{state:<6} | {beta:<18.4f} | {r2:<10.4f}")

#CA R2 is super low (0.02) - meaning that layoffs are not well correlated with startup activity
#this makes sense - CA is where people go to form tech startups because that is where the investors are

#Southeast states are on the national WARN standard (500+ EEs or 50+ if over 33% of WF, so 
# implement regional pooling to see if any correlation is there)
# Create a Southeast Region filter
se_states = ['GA', 'NC', 'SC', 'AL', 'TN', 'MS']
df_se = quarterly[quarterly['state'].isin(se_states)].groupby('quarter').sum().reset_index()

# Run the 3-quarter lag regression on the WHOLE region
df_se['layoffs_lag3'] = df_se['total_layoffs'].shift(3)
se_reg = sm.OLS(df_se['new_business_apps'], sm.add_constant(df_se['layoffs_lag3']), missing='drop').fit()

print(f"Southeast Regional Multiplier: {se_reg.params['layoffs_lag3']:.4f}")
print(f"Southeast Regional R-Squared: {se_reg.rsquared:.4f}")

#plot virginia vs. california to show that one is pro cyclical and the other is counter cyclical
import matplotlib.pyplot as plt
import seaborn as sns

# Filter for the two comparison states
va_data = quarterly[quarterly['state'] == 'VA'].dropna(subset=['layoffs_lag3', 'new_business_apps'])
ca_data = quarterly[quarterly['state'] == 'CA'].dropna(subset=['layoffs_lag3', 'new_business_apps'])

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6), sharey=False)

# Plot Virginia
sns.regplot(data=va_data, x='layoffs_lag3', y='new_business_apps', ax=ax1, color='#1a5276')
ax1.set_title(f'Virginia: The Incubator\n(Beta: 2.53, R²: 0.25)', fontsize=14)
ax1.set_xlabel('Layoffs (t-3 Quarters)')
ax1.set_ylabel('New Business Apps')

# Plot California
sns.regplot(data=ca_data, x='layoffs_lag3', y='new_business_apps', ax=ax2, color='#922b21')
ax2.set_title(f'California: The Volatile Core\n(Beta: -0.97, R²: 0.03)', fontsize=14)
ax2.set_xlabel('Layoffs (t-3 Quarters)')
ax2.set_ylabel('') # Share Y or leave blank for clarity

plt.suptitle('Predictive Power of Layoffs on Entrepreneurship (2023-2026)', fontsize=16, y=1.05)
plt.tight_layout()
plt.show()
plt.savefig('Images/ca_vs_va_comparison.png', dpi=300, bbox_inches='tight')
