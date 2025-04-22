import pandas as pd
import os
import time


def update_data_to_csv():
    data_url = 'https://raw.githubusercontent.com/JOSPHATT/Finished_Matches/refs/heads/main/Finished_matches.csv'
    
    try:
        # Fetch and load the data
        df = pd.read_csv(data_url)
    except Exception as e:
        print(f"Error fetching or reading data from the URL: {e}")
        return

    try:
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
    except Exception as e:
        print(f"Error during data preparation: {e}")
        return

    try:
        # Process home data
        home_df = df[['HOME', 'home_team_goal', 'away_team_goal']].copy()
        home_df.columns = ['TEAM', 'goals_for', 'goals_against']
        home_df['matches_played'] = 1
        home_df['matches_won'] = (home_df['goals_for'] > home_df['goals_against']).astype(int)
        home_df['matches_drawn'] = (home_df['goals_for'] == home_df['goals_against']).astype(int)
        home_df['matches_lost'] = (home_df['goals_for'] < home_df['goals_against']).astype(int)

        # Process away data
        away_df = df[['AWAY', 'away_team_goal', 'home_team_goal']].copy()
        away_df.columns = ['TEAM', 'goals_for', 'goals_against']
        away_df['matches_played'] = 1
        away_df['matches_won'] = (away_df['goals_for'] > away_df['goals_against']).astype(int)
        away_df['matches_drawn'] = (away_df['goals_for'] == away_df['goals_against']).astype(int)
        away_df['matches_lost'] = (away_df['goals_for'] < away_df['goals_against']).astype(int)

        # Combine home and away data
        team_df = pd.concat([home_df, away_df])
        team_stats = team_df.groupby('TEAM').sum().reset_index()
        team_stats['goal_difference'] = team_stats['goals_for'] - team_stats['goals_against']
        team_stats['goals_scored_per_match'] = team_stats['goals_for'] / team_stats['matches_played']
        team_stats['goals_conceded_per_match'] = team_stats['goals_against'] / team_stats['matches_played']
        team_stats['goal_difference_per_match'] = team_stats['goal_difference'] / team_stats['matches_played']
        team_stats['win_rate'] = (team_stats['matches_won'] / team_stats['matches_played']) * 100
        team_stats['draw_rate'] = (team_stats['matches_drawn'] / team_stats['matches_played']) * 100
        team_stats['loss_rate'] = (team_stats['matches_lost'] / team_stats['matches_played']) * 100
        team_stats['scoring_strength'] = team_stats['goals_scored_per_match'] + (0.5 * team_stats['goal_difference_per_match'])
    except Exception as e:
        print(f"Error during data processing: {e}")
        return

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
