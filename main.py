
import pandas as pd
import plotly.express as px
import os


def csv_data():
    data_url = "https://raw.githubusercontent.com/JOSPHATT/Finished_Matches_dash_statistics/refs/heads/main/team_statistics.csv"

    try:
        # Fetch and load the data
        df = pd.read_csv(data_url)
    except Exception as e:
        print(f"Error fetching or reading data from the URL: {e}")
        return
    return df
    # Filter the top 15 teams by matches played

#print(csv_data())

#stream_data()
# %%
TOP_TEAMS=csv_data()


# Example: assuming 'TOP_TEAMS' is your existing DataFrame with one row per team
# and already contains the required columns

# Define model weights
a1 = 0.5  # goals_scored_per_match
a2 = 0.3  # goal_difference_per_match
a3 = 0.1  # win_rate
a4 = 0.4  # scoring_strength
b = 0.2   # bias term

# Calculate expected goals for each team
# The following columns were missing in the TOP_TEAMS DataFrame,
# they are now included from the stream_data function call.
TOP_TEAMS['expected_goals_next_match'] = (
    a1 * TOP_TEAMS['goals_scored_per_match'] +
    a2 * TOP_TEAMS['goal_difference_per_match'] +
    a3 * TOP_TEAMS['win_rate'] +
    a4 * TOP_TEAMS['scoring_strength'] +
    b
)

# Output preview
#print(TOP_TEAMS[['TEAM', 'expected_goals_next_match']])
# %%
def Previous_match():
    finished_games_url="https://raw.githubusercontent.com/JOSPHATT/Finished_Matches/refs/heads/main/Finished_matches.csv"

    try:
        # Fetch and load the data
        df = pd.read_csv(finished_games_url)
        # Data preparation
        df = df.drop_duplicates()
        df_numeric = df.select_dtypes(include=['float64', 'int64'])
        df[df_numeric.columns] = df_numeric.fillna(df_numeric.median())
        df_categorical = df.select_dtypes(include=['object'])
        for col in df_categorical.columns:
            df[col] = df[col].fillna(df[col].mode()[0])

        if 'H_GOALS' in df.columns and 'A_GOALS' in df.columns:
            df['home_team_goal'] = df['H_GOALS']
            df['away_team_goal'] = df['A_GOALS']

        # Process home data
        home_df = df[['HOME', 'home_team_goal']].copy()
        home_df.columns = ['TEAM', 'GOALS']

        # Process away data
        away_df = df[['AWAY', 'away_team_goal']].copy()
        away_df.columns = ['TEAM', 'GOALS']

        # Combine home and away data
        team_df = pd.concat([home_df, away_df])
        #team_stats = team_df.groupby('TEAM').sum().reset_index()
    except Exception as e:
        print(f"Error during data processing: {e}")
    return team_df
Previous_match_outcome=Previous_match()
#Previous_match_outcome

N_df = pd.DataFrame()
for team in TOP_TEAMS['TEAM']:
    prev_match = Previous_match_outcome.loc[Previous_match_outcome['TEAM'] == str(team)]
    prev_match = prev_match.tail(1)
    #PREV_match = prev_match['TEAM'].to_frame() #This line is the problem, it only creates a dataframe with TEAM column
    t = prev_match['TEAM']
    g = prev_match['GOALS']  #Now this should work, as prev_match has both TEAM and GOALS
    #print(t)
    # Append the data to the DataFrame instead of assigning directly
    N_df = pd.concat([N_df, pd.DataFrame({'TEAM': t, 'GOALS': g})], ignore_index=True)
#print(type(N_df))
TOP_TEAMS['Previous_goals']=N_df['GOALS'].tolist()
# %% [markdown]
#
# %%
#this should be run after the expected match is played and actual outcome recorded.
#gets the actual outcome, readjusts weights and computes outcome for next match
#TODOs: add a column for previous_match_actual_goals(get from livescores csv/script/code), use actual_goals as input for this function below

from sklearn.linear_model import LinearRegression
import numpy as np

def update_weights_and_predict(TOP_TEAMS, actual_goals_column):
    # Features used for prediction
    features = ['goals_scored_per_match', 'goal_difference_per_match', 'win_rate', 'scoring_strength']

    # Drop rows with missing values in the relevant columns
    data = TOP_TEAMS.dropna(subset=features + [actual_goals_column])

    # Prepare training data
    X = data[features].values
    y = data[actual_goals_column].values

    # Train linear regression model to fit actual goals
    model = LinearRegression()
    model.fit(X, y)

    # Get the new weights and bias
    new_weights = model.coef_
    new_bias = model.intercept_

    # Apply updated model to predict expected goals
    TOP_TEAMS['expected_goals_next_match'] = np.dot(TOP_TEAMS[features], new_weights) + new_bias

    # Optionally print new weights
    #print("Updated weights:", dict(zip(features, new_weights)))
    #print("Updated bias:", new_bias)
# Example usage:
# TOP_TEAMS = update_weights_and_predict(TOP_TEAMS, actual_goals_column='actual_goals_last_match')

def update_data_to_csv():
    TOP_TEAMS = update_weights_and_predict(TOP_TEAMS, actual_goals_column='Previous_goals')
    team_stats = TOP_TEAMS.drop(['expected', 'previous_goals'], axis=1)
    try:
        # Append to existing CSV in the repository
        output_file_path = 'team_statistics.csv'  # Path to the CSV file in the repository
        if os.path.exists(output_file_path):
            # Append to the existing CSV file
            existing_data = pd.read_csv(output_file_path)
            combined_data = pd.concat([existing_data, team_stats]).drop_duplicates().reset_index(drop=True)
            combined_data.to_csv(output_file_path, index=False)
        else:
            # Create the file if it doesn't exist
            team_stats.to_csv(output_file_path, index=False)
    except Exception as e:
        print(f"Error during file writing: {e}")
        return


if __name__ == "__main__":
    update_data_to_csv()
