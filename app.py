import streamlit as st
import pandas as pd
import plotly.express as px

# Set page title
st.title("India Unemployment Dashboard")

# Load the unemployment data
@st.cache_data
def load_data():
    try:
        # Read CSV file from project folder
        df = pd.read_csv('unemployment.csv')
        
        # Clean column names - convert to lowercase with underscores
        df.columns = df.columns.str.lower().str.replace(' ', '_').str.replace('-', '_')
        
        # Remove rows with missing values
        df = df.dropna()
        
        # Convert date column to datetime
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
        
        return df
    except FileNotFoundError:
        st.error("unemployment.csv file not found. Please ensure the file exists in the project folder.")
        return None
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

# Load the data
data = load_data()

# Check if data loaded successfully
if data is not None:
    # Get list of states for dropdown
    states = sorted(data['region'].unique()) if 'region' in data.columns else []
    
    if states:
        # Sidebar for filters
        st.sidebar.header("Filters")
        
        # State selection dropdown
        selected_state = st.sidebar.selectbox("Select a State:", states)
        
        # Date range filter (if date column exists)
        if 'date' in data.columns:
            min_date = data['date'].min()
            max_date = data['date'].max()
            
            # Date range selector
            date_range = st.sidebar.date_input(
                "Select Date Range:",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
            
            # Apply date filter if two dates selected
            if len(date_range) == 2:
                start_date, end_date = date_range
                filtered_data = data[(data['date'] >= pd.to_datetime(start_date)) & 
                                    (data['date'] <= pd.to_datetime(end_date))]
            else:
                filtered_data = data
        else:
            filtered_data = data
        
        # Filter data for selected state
        state_data = filtered_data[filtered_data['region'] == selected_state].copy()
        
        # Multi-state comparison option
        st.sidebar.header("Multi-State Comparison")
        compare_states = st.sidebar.multiselect(
            "Select states to compare:",
            options=[s for s in states if s != selected_state],
            default=[]
        )
        
        # Main content area
        # Display table preview (first 5 rows)
        st.subheader(f"Data Preview for {selected_state}")
        st.dataframe(state_data.head())
        
        # Download button for filtered data
        csv = state_data.to_csv(index=False)
        st.download_button(
            label="Download Filtered Data as CSV",
            data=csv,
            file_name=f"unemployment_{selected_state}.csv",
            mime="text/csv"
        )
        
        # Calculate and display metrics in columns
        if 'unemployment_rate' in state_data.columns:
            st.subheader("Key Metrics")
            
            # Create columns for metrics
            col1, col2, col3 = st.columns(3)
            
            # Average unemployment rate
            avg_unemployment = state_data['unemployment_rate'].mean()
            col1.metric("Avg Unemployment Rate", f"{avg_unemployment:.2f}%")
            
            # Average labour participation rate (if available)
            if 'labour_participation_rate' in state_data.columns:
                avg_labour = state_data['labour_participation_rate'].mean()
                col2.metric("Avg Labour Participation", f"{avg_labour:.2f}%")
            
            # Average employed count (if available)
            if 'estimated_employed' in state_data.columns:
                avg_employed = state_data['estimated_employed'].mean()
                col3.metric("Avg Employed", f"{avg_employed:,.0f}")
            
            # Summary statistics dashboard
            st.subheader("Summary Statistics")
            
            # Create columns for summary stats
            stat_col1, stat_col2, stat_col3 = st.columns(3)
            
            # Min, Max, Median for unemployment rate
            min_unemp = state_data['unemployment_rate'].min()
            max_unemp = state_data['unemployment_rate'].max()
            median_unemp = state_data['unemployment_rate'].median()
            
            stat_col1.metric("Min Unemployment Rate", f"{min_unemp:.2f}%")
            stat_col2.metric("Max Unemployment Rate", f"{max_unemp:.2f}%")
            stat_col3.metric("Median Unemployment Rate", f"{median_unemp:.2f}%")
            
            # Create line chart of unemployment rate over time
            st.subheader("Unemployment Rate Trend")
            
            # Check if date column exists for time series
            if 'date' in state_data.columns:
                # Sort by date for proper line chart
                chart_data = state_data.sort_values('date')
                
                # Create line chart using plotly
                fig = px.line(chart_data, 
                             x='date', 
                             y='unemployment_rate',
                             title=f'Unemployment Rate Over Time - {selected_state}')
                
                fig.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Unemployment Rate (%)"
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                # If no date column, create simple line chart with index
                fig = px.line(state_data.reset_index(), 
                             x='index', 
                             y='unemployment_rate',
                             title=f'Unemployment Rate - {selected_state}')
                
                fig.update_layout(
                    xaxis_title="Data Point",
                    yaxis_title="Unemployment Rate (%)"
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Additional metrics charts (if columns exist)
            if 'labour_participation_rate' in state_data.columns and 'date' in state_data.columns:
                st.subheader("Labour Participation Rate Trend")
                
                chart_data = state_data.sort_values('date')
                fig2 = px.line(chart_data, 
                              x='date', 
                              y='labour_participation_rate',
                              title=f'Labour Participation Rate Over Time - {selected_state}')
                
                fig2.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Labour Participation Rate (%)"
                )
                
                st.plotly_chart(fig2, use_container_width=True)
            
            # Multi-state comparison charts
            if compare_states:
                st.subheader("Multi-State Comparison")
                
                # Prepare comparison data
                comparison_data = filtered_data[filtered_data['region'].isin([selected_state] + compare_states)].copy()
                
                if 'date' in comparison_data.columns:
                    comparison_data = comparison_data.sort_values('date')
                    
                    # Create side-by-side charts for each state
                    all_states = [selected_state] + compare_states
                    
                    # Create individual chart for each state (2 charts per row)
                    for idx, state in enumerate(all_states):
                        # Create new row of columns every 2 charts
                        if idx % 2 == 0:
                            chart_cols = st.columns(2)
                        
                        state_chart_data = comparison_data[comparison_data['region'] == state]
                        
                        fig = px.line(state_chart_data, 
                                     x='date', 
                                     y='unemployment_rate',
                                     title=f'{state}')
                        
                        fig.update_layout(
                            xaxis_title="Date",
                            yaxis_title="Unemployment Rate (%)"
                        )
                        
                        # Place chart in left (0) or right (1) column
                        col_idx = idx % 2
                        chart_cols[col_idx].plotly_chart(fig, use_container_width=True)
                    
                    # Show comparison table with average rates (outside column context)
                    st.subheader("Average Unemployment Rates by State")
                    
                    comparison_summary = comparison_data.groupby('region')['unemployment_rate'].mean().reset_index()
                    comparison_summary.columns = ['State', 'Average Unemployment Rate (%)']
                    comparison_summary = comparison_summary.sort_values('Average Unemployment Rate (%)', ascending=False)
                    
                    st.dataframe(comparison_summary)
        else:
            st.error("Unemployment rate column not found in the data.")
    else:
        st.error("No states found in the data. Please check if 'region' column exists.")
else:
    st.info("Please ensure unemployment.csv file is available in the project folder.")
