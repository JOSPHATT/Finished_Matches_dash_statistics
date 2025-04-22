import streamlit as st
import pandas as pd
import plotly.express as px
import os


def load_data(file_path):
    """
    Load data from the CSV file if it exists.
    """
    if os.path.exists(file_path):
        try:
            data = pd.read_csv(file_path)
            return data
        except Exception as e:
            st.error(f"Error loading the data: {e}")
            return None
    else:
        st.error("The data file does not exist. Please ensure the script to generate 'team_statistics.csv' has been run.")
        return None


def main():
    st.title("Team Statistics Dashboard")
    st.markdown("This dashboard displays interactive charts based on team statistics.")

    # File path for the generated CSV
    file_path = "team_statistics.csv"

    # Load data
    data = load_data(file_path)
    if data is None:
        return

    # Filter the top 15 teams by matches played
    data['matches_played'] = data['matches_played'].fillna(0)  # Handle missing values
    top_teams = data.nlargest(15, 'matches_played')  # Select top 15 teams
    top_teams_list = top_teams["TEAM"].tolist()

    # Sidebar for filtering options
    st.sidebar.title("Filter Options")
    selected_team = st.sidebar.selectbox("Select a Team", options=["All"] + top_teams_list)

    # Filter data based on the selected team
    if selected_team != "All":
        filtered_data = data[data["TEAM"] == selected_team]
    else:
        filtered_data = data[data["TEAM"].isin(top_teams_list)]

    # Display filtered data as a table
    st.subheader("Filtered Data")
    st.dataframe(filtered_data)

    # Display various charts
    st.subheader("Charts")

    # Win Rate Distribution
    st.markdown("### Win Rate Distribution")
    fig2 = px.bar(
        filtered_data,
        x="TEAM",
        y="scoring_strength",
        color="TEAM",
        title="scoring strength Distribution",
        labels={"scoring_strength": "Scoring Strength (%)"},
    )
    st.plotly_chart(fig1)

    # Win Rate Distribution
    st.markdown("### Win Rate Distribution")
    fig2 = px.bar(
        filtered_data,
        x="TEAM",
        y="win_rate",
        color="TEAM",
        title="Win Rate Distribution",
        labels={"win_rate": "Win Rate (%)"},
    )
    st.plotly_chart(fig2)

    # Goals Scored Per Match
    st.markdown("### Goals Scored Per Match")
    fig3 = px.line(
        filtered_data,
        x="TEAM",
        y="goals_scored_per_match",
        title="Goals Scored Per Match",
        labels={"goals_scored_per_match": "Goals Scored Per Match"},
    )
    st.plotly_chart(fig3)

    # Custom chart options
    st.sidebar.title("Custom Chart Options")
    chart_type = st.sidebar.selectbox("Select Chart Type", ["Bar Chart", "Line Chart", "Scatter Plot"])
    stat_column = st.sidebar.selectbox(
        "Select Statistic",
        options=["goals_for", "goals_against", "win_rate", "loss_rate", "draw_rate"],
        index=0,
    )

    st.markdown(f"### Custom Chart: {chart_type}")
    if chart_type == "Bar Chart":
        fig4 = px.bar(
            filtered_data,
            x="TEAM",
            y=stat_column,
            color="TEAM",
            title=f"{stat_column.replace('_', ' ').title()} Distribution",
        )
    elif chart_type == "Line Chart":
        fig4 = px.line(
            filtered_data,
            x="TEAM",
            y=stat_column,
            title=f"{stat_column.replace('_', ' ').title()} Over Teams",
        )
    else:  # Scatter Plot
        fig4 = px.scatter(
            filtered_data,
            x="TEAM",
            y=stat_column,
            size="goal_difference",
            color="TEAM",
            title=f"{stat_column.replace('_', ' ').title()} Scatter Plot",
        )
    st.plotly_chart(fig4)


if __name__ == "__main__":
    main()
