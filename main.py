import pandas as pd
import plotly.express as px
import streamlit as st
import os
import time
import watchdog 
import filelock


def update_data_to_csv():
    data_url = 'https://raw.githubusercontent.com/JOSPHATT/Finished_Matches/refs/heads/main/Finished_matches.csv'
    df = pd.read_csv(data_url)

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
    
# Function to monitor the CSV file for changes
def wait_for_csv_update(file_path, check_interval=60):
    """
    Waits for the CSV file to be updated by monitoring its modification time.
    :param file_path: Path to the CSV file to monitor.
    :param check_interval: Time interval (in seconds) to check for updates.
    """
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}. Waiting for it to be created...")
        while not os.path.exists(file_path):
            time.sleep(check_interval)
        print(f"File created: {file_path}")

    last_mod_time = os.path.getmtime(file_path)
    print(f"Monitoring changes to {file_path}...")

    while True:
        current_mod_time = os.path.getmtime(file_path)
        if current_mod_time != last_mod_time:
            print(f"File updated: {file_path}")
            break
        time.sleep(check_interval)

# Function to preprocess the data
def preprocess_data(file_path):
    # Load the CSV file
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
        return None

    # Ensure the data is clean and has all required columns
    df = df.drop_duplicates()
    df_numeric = df.select_dtypes(include=['float64', 'int64'])
    df[df_numeric.columns] = df_numeric.fillna(df_numeric.median())
    df_categorical = df.select_dtypes(include=['object'])
    for col in df_categorical.columns:
        df[col] = df[col].fillna(df[col].mode()[0])

    return df

# Streamlit dashboard function
def generate_streamlit_dashboard(file_path):
    """
    Streamlit dashboard for visualizing team statistics.
    :param file_path: Path to the CSV file containing team statistics.
    """
    st.title("Football Team Performance Dashboard")
    st.markdown("Analyze and visualize football team performance dynamically.")

    # Load and preprocess data
    df = preprocess_data(file_path)

    # Sidebar filters
    st.sidebar.header("Filters")
    num_teams = st.sidebar.slider("Number of top teams to display", min_value=5, max_value=30, value=15, step=1)
    stat_to_visualize = st.sidebar.selectbox(
        "Statistic to visualize",
        [
            "Scoring Strength",
            "Goal Difference",
            "Goals Scored per Match",
            "Goals Conceded per Match",
            "Win Rate",
            "Draw Rate",
            "Loss Rate",
        ],
    )

    # Map statistic names to columns
    stat_column_map = {
        "Scoring Strength": "scoring_strength",
        "Goal Difference": "goal_difference",
        "Goals Scored per Match": "goals_scored_per_match",
        "Goals Conceded per Match": "goals_conceded_per_match",
        "Win Rate": "win_rate",
        "Draw Rate": "draw_rate",
        "Loss Rate": "loss_rate",
    }
    stat_column = stat_column_map[stat_to_visualize]

    # Filter top teams
    top_teams = df.sort_values(by="matches_played", ascending=False).head(num_teams)

    # Generate visualization
    fig = px.bar(
        top_teams,
        x="TEAM",
        y=stat_column,
        title=f"Top {num_teams} Teams: Matches Played vs {stat_to_visualize}",
        labels={stat_column: stat_to_visualize},
        text="matches_played",
    )

    # Display visualization
    st.plotly_chart(fig)

if __name__ == "__main__":
    
    update_data_to_csv()
    # Path to the CSV file
    csv_file_path = 'team_statistics.csv'

    # Wait for the CSV file to be updated or created
    wait_for_csv_update(csv_file_path)

    # Launch the Streamlit dashboard
    generate_streamlit_dashboard(csv_file_path)
   
