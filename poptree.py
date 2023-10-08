import pandas as pd
import streamlit as st
import plotly.figure_factory as ff
from scipy.cluster.hierarchy import linkage, dendrogram

# Initialize session state
if 'selected_pop' not in st.session_state:
    st.session_state['selected_pop'] = None
if 'cluster_index' not in st.session_state:
    st.session_state['cluster_index'] = 0

st.set_page_config(layout="wide", page_title="PopTree", page_icon="🌳")
st.header('Pop:green[Tree]')

# Dictionary to map displayed names to actual file names
file_name_mapping = {
    "Modern Era": "Modern Ancestry.txt",
    "Mesolithic and Neolithic": "Mesolithic and Neolithic.txt",
    "Bronze Age": "Bronze Age.txt",
    "Iron Age": "Iron Age.txt",
    "Migration Period": "Migration Period.txt",
    "Middle Ages": "Middle Ages.txt",
}

# Multiselect for choosing time periods
selected_time_periods = st.multiselect("Time Period:", list(file_name_mapping.keys()), default=["Modern Era"])

# Load data from selected files into a Pandas DataFrame, skipping the first row
selected_files = [file_name_mapping[time_period] for time_period in selected_time_periods]
data = pd.concat([pd.read_csv(file, index_col=0, header=None) for file in selected_files])
# Remove duplicate rows based on data after the first comma
data = data.drop_duplicates(keep='first')




# Check if the selected population exists in the current data
if st.session_state['selected_pop'] is None or st.session_state['selected_pop'] not in data.index:
    st.session_state['selected_pop'] = data.index[0]
    st.session_state['cluster_index'] = 0

# Compute the linkage matrix using Ward's method
Z = linkage(data, method='ward')

# Get the branches of the dendrogram
def get_tree_branches(Z, data):
    n = len(data)
    branches = []
    for i in range(n-1):
        branch = []
        for j in range(2):
            if Z[i, j] < n:
                branch.append(data.index[int(Z[i, j])])
            else:
                branch += branches[int(Z[i, j] - n)]
        branches.append(branch)
    return branches

# Get the selected population from the session state
selected_pop = st.selectbox("Populations:", data.index, index=data.index.get_loc(st.session_state['selected_pop']))

# Update the selected population in the session state
if selected_pop != st.session_state['selected_pop']:
    st.session_state['selected_pop'] = selected_pop
    st.session_state['cluster_index'] = 0
    st.rerun()
    

# Find the branches that contain the selected population
pop_branches = []
for branch in get_tree_branches(Z, data):
    if selected_pop in branch:
        pop_branches.append(branch)

# Display the selected population and its clusters
if pop_branches:
    cluster_index = st.session_state['cluster_index']
    branch_text = ", ".join(pop_branches[cluster_index])

    # Move to the next and previous clusters
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("«", help="Previous") and cluster_index > 0:
            st.session_state['cluster_index'] -= 1
            st.rerun()

    with col2:
        if st.button("»", help="Next") and cluster_index < len(pop_branches) - 1:
            st.session_state['cluster_index'] += 1
            st.rerun()

    # Go back to the first cluster
    with col3:
        if cluster_index > 0:
            if st.button("↺", help="Reset"):
                st.session_state['cluster_index'] = 0
                st.rerun()

    # Create a Plotly figure for the dendrogram of the current cluster
    with st.spinner("Creating Dendrogram..."):
        current_cluster_data = data.loc[pop_branches[cluster_index]]
        # Create custom labels with population names
        custom_labels = current_cluster_data.index.tolist()
        height = max(20 * len(custom_labels), 500)
        fig = ff.create_dendrogram(
            current_cluster_data,
            orientation="right",
            labels=custom_labels,
            linkagefun=lambda x: linkage(x.T, method="ward"),  # Transpose the data for linkage
        )
        fig.update_layout(height=500, width=800)
        fig.update_layout(height=height, yaxis={'side': 'right'})
        fig.update_yaxes(automargin=True, range=[0, len(custom_labels)*10])

        # Display the Plotly figure using st.plotly_chart
        st.plotly_chart(fig, theme=None, use_container_width=True)
