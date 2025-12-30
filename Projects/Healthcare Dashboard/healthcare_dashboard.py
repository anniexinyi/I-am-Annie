import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import plotly.express as px
patient_df = pd.read_csv('/patient.csv')
labtest_df = pd.read_csv('/Labtest.csv')
test_df = pd.read_csv('/Test.csv')
prescription_df = pd.read_csv('/Prescription.csv')
drug_df = pd.read_csv('/Drug.csv')
admission_df = pd.read_csv('/Admission.csv')
room_df = pd.read_csv('/Room.csv')
history_df = pd.read_csv('/Patienthistory.csv')
labtest_merged = labtest_df.merge(patient_df, on='P_ID', how='left')
import math
# Filter positive and negative tests
positive_tests = labtest_merged[labtest_merged['testresult'] == 'Positive']
negative_tests = labtest_merged[labtest_merged['testresult'] == 'Negative']

# Count by department
dept_pos_counts = positive_tests['PatientDepartment'].value_counts()
dept_neg_counts = negative_tests['PatientDepartment'].value_counts()

# Combine into one DataFrame
dept_comparison = pd.DataFrame({
    'Positive': dept_pos_counts,
    'Negative': dept_neg_counts
}).fillna(0)

# Departments and layout
departments = dept_comparison.index.tolist()
n = len(departments)
cols = 3
rows = math.ceil(n / cols)

fig, axes = plt.subplots(rows, cols, figsize=(cols * 4, rows * 4))
axes = axes.flatten()
colors = ['lightblue', 'salmon']  # Positive, Negative

# Create pie chart for each department
for i, dept in enumerate(departments):
    data = dept_comparison.loc[dept]
    
    wedges, _, autotexts = axes[i].pie(
        data,
        labels=None,  # No external labels
        autopct='%1.1f%%',  # Percent inside
        startangle=90,
        colors=colors,
        textprops={'fontsize': 9, 'color': 'black'}
    )
    
    axes[i].set_title(dept, fontsize=11)

# Remove unused subplots
for j in range(i + 1, len(axes)):
    fig.delaxes(axes[j])

# Add a single unified legend
legend_labels = [
    mpatches.Patch(color='lightblue', label='Positive'),
    mpatches.Patch(color='salmon', label='Negative')
]
fig.legend(handles=legend_labels, loc='upper right', fontsize=10)

# Title and layout
plt.suptitle('Test Result Distribution by Department', fontsize=14)
plt.tight_layout(rect=[0, 0.03, 0.95, 0.95])
plt.show()
# Count all prescribed drugs (only 4 expected)
drug_counts = drug_df['drugname'].value_counts()

# Labels and values
labels = drug_counts.index
sizes = drug_counts.values

# Donut colors
colors = plt.cm.Set2(range(len(sizes)))

# Plot
fig, ax = plt.subplots(figsize=(6, 6))
wedges, texts, autotexts = ax.pie(
    sizes,
    labels=labels,
    autopct='%d',  # Show raw count
    startangle=90,
    colors=colors,
    textprops={'fontsize': 10},
    wedgeprops=dict(width=0.4)  # Makes it a donut
)

# Add center white circle
centre_circle = plt.Circle((0, 0), 0.70, fc='white')
fig.gca().add_artist(centre_circle)

# Title
plt.title('Prescribed Drugs Distribution', fontsize=14)
plt.tight_layout()
plt.show()
# -- Table: Recent Patient History
history_df['PatienthistoryDate'] = pd.to_datetime(history_df['PatienthistoryDate'])
recent_notes = history_df.sort_values(by='PatienthistoryDate', ascending=False).head(10)
print("\nRecent Patient Notes:")
print(recent_notes[['P_ID', 'D_ID', 'N_ID', 'Patienthistorynote', 'PatienthistoryDate']])
note_counts = history_df['Patienthistorynote'].value_counts()
print(note_counts)
# Data from the patient history note
categories = ['Emergency Visit', 'Routine Checkup', 'General Consultation']
counts = [214, 165, 114]

# Create the bar plot
plt.figure(figsize=(8, 5))
bars = plt.bar(categories, counts, color='skyblue')
plt.title('Patient History Note Counts')
plt.xlabel('Visit Type')
plt.ylabel('Count')
plt.grid(axis='y', linestyle='--', alpha=0.7)

# Add count labels in the center of bars
for bar in bars:
    yval = bar.get_height()
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        yval / 2,  # Midpoint of bar height
        f'{int(yval)}',
        ha='center',
        va='center',
        fontsize=11,
        color='black'
    )

plt.tight_layout()
plt.show()

# ------------------ Health Dashboard ------------------

import pandas as pd
import matplotlib.pyplot as plt
import math
from IPython.display import display, HTML

# Title
plt.figure(figsize=(10, 1))
plt.text(0.5, 0.5, 'Health Dashboard', fontsize=20, ha='center', va='center')
plt.axis('off')
plt.tight_layout()
plt.show()

# ------------------ 1. Recent Patient Notes -----------------

# Tag generator function for dashboard display
def generate_tags(note):
    tags = []
    note_lower = note.lower()
    if "general consultation" in note_lower:
        tags.append("<span style='color: #2a9d8f; font-weight: bold;'>🟦 General Consultation</span>")
    if "routine checkup" in note_lower:
        tags.append("<span style='color: #264653; font-weight: bold;'>🟨 Routine Checkup</span>")
    if "emergency visit" in note_lower:
        tags.append("<span style='color: #e76f51; font-weight: bold;'>🔴 Emergency Visit</span>")
    return " ".join(tags)

# Ensure the date column is in datetime format
history_df['PatienthistoryDate'] = pd.to_datetime(history_df['PatienthistoryDate'])

# Sort and select the 10 most recent notes
recent_notes = history_df.sort_values(by='PatienthistoryDate', ascending=False).head(10).copy()

# Generate tags
recent_notes['Tags'] = recent_notes['Patienthistorynote'].apply(generate_tags)

# Reorder columns so tags appear before the patient note
display_df = recent_notes[['P_ID', 'D_ID', 'N_ID', 'PatienthistoryDate', 'Tags']]

# Convert to HTML, ensuring tags render properly
html_table = display_df.to_html(index=False, escape=False)

# Display in a nicely formatted HTML block
display(HTML(f"""
<div style='text-align: center; font-family: Arial, sans-serif;'>
    <h3>Recent Patient Notes</h3>
    <div style='display: inline-block; text-align: left; border: 1px solid #ccc; padding: 15px; border-radius: 10px;'>
        {html_table}
    </div>
</div>
"""))


# ------------------ 2. Yearly Admissions and Visit Types ------------------

import pandas as pd
import matplotlib.pyplot as plt

# Step 1: Convert 'AdmissionDate' to datetime
admission_df['AdmissionDate'] = pd.to_datetime(admission_df['AdmissionDate'], errors='coerce')

# Step 2: Create a 'Trimester' label based on the month
def get_trimester_label(date):
    if pd.isnull(date):
        return None
    month = date.month
    if 1 == month:
        return '2025-1'
    elif 2 == month:
        return '2025-2'
    else:
        return '2025-3'

admission_df['Trimester'] = admission_df['AdmissionDate'].apply(get_trimester_label)

# Step 3: Group by 'Trimester' and count admissions
trimester_admissions = admission_df['Trimester'].value_counts().sort_index()

# Step 4: Plot the line chart
plt.figure(figsize=(8, 5))
plt.plot(trimester_admissions.index, trimester_admissions.values, marker='o', color='teal', linewidth=2)

# Add count labels
for x, y in zip(trimester_admissions.index, trimester_admissions.values):
    plt.text(x, y + 3, str(y), ha='center', va='bottom', fontsize=10, color='black')

# Labels and title
plt.title('Admissions by Trimester (2025)', fontsize=16)
plt.xlabel('Trimester', fontsize=12)
plt.ylabel('Number of Admissions', fontsize=12)
plt.ylim(50, 100)  # <-- Set vertical axis limits
plt.grid(True, linestyle='--', alpha=0.5)

plt.tight_layout()
plt.show()


# Data from the patient history note
categories = ['Emergency Visit', 'Routine Checkup', 'General Consultation']
counts = [214, 165, 114]

# Create the bar plot
plt.figure(figsize=(8, 5))
bars = plt.bar(categories, counts, color='skyblue')
plt.title('Patient History Note Counts')
plt.xlabel('Visit Type')
plt.ylabel('Count')
plt.grid(axis='y', linestyle='--', alpha=0.7)

# Add count labels in the center of bars
for bar in bars:
    yval = bar.get_height()
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        yval / 2,  # Midpoint of bar height
        f'{int(yval)}',
        ha='center',
        va='center',
        fontsize=11,
        color='black'
    )

plt.tight_layout()
plt.show()


# ------------------ 3. Departmental test results ------------------

# Filter positive and negative tests
positive_tests = labtest_merged[labtest_merged['testresult'] == 'Positive']
negative_tests = labtest_merged[labtest_merged['testresult'] == 'Negative']

# Count by department
dept_pos_counts = positive_tests['PatientDepartment'].value_counts()
dept_neg_counts = negative_tests['PatientDepartment'].value_counts()

# Combine into one DataFrame
dept_comparison = pd.DataFrame({
    'Positive': dept_pos_counts,
    'Negative': dept_neg_counts
}).fillna(0)

# Departments and layout
departments = dept_comparison.index.tolist()
n = len(departments)
cols = 3
rows = math.ceil(n / cols)

fig, axes = plt.subplots(rows, cols, figsize=(cols * 4, rows * 4))
axes = axes.flatten()
colors = ['lightblue', 'salmon']  # Positive, Negative

# Create pie chart for each department
for i, dept in enumerate(departments):
    data = dept_comparison.loc[dept]
    
    wedges, _, autotexts = axes[i].pie(
        data,
        labels=None,  # No external labels
        autopct='%1.1f%%',  # Percent inside
        startangle=90,
        colors=colors,
        textprops={'fontsize': 11, 'color': 'black'}
    )
    
    axes[i].set_title(dept, fontsize=11)

# Remove unused subplots
for j in range(i + 1, len(axes)):
    fig.delaxes(axes[j])

# Add a single unified legend
legend_labels = [
    mpatches.Patch(color='lightblue', label='Positive'),
    mpatches.Patch(color='salmon', label='Negative')
]
fig.legend(handles=legend_labels, loc='upper right', fontsize=10)

# Title and layout
plt.suptitle('Test Result Distribution by Department', fontsize=14)
plt.tight_layout(rect=[0, 0.03, 0.95, 0.95])
plt.show()

# ------------------ 3. Donut Chart - Prescribed Drugs ------------------

drug_data = pd.DataFrame({
    'Drug': ['Tenofovir', 'Lorazepam', 'Tamiflu', 'Naltrexone'],
    'Count': [38, 21, 20,20]
})

fig, ax = plt.subplots(figsize=(6, 6))
colors = ['#2a9d8f', '#e9c46a', '#f4a261', '#e76f51']
wedges, texts = ax.pie(
    drug_data['Count'], 
    labels=[f"{drug} ({count})" for drug, count in zip(drug_data['Drug'], drug_data['Count'])],
    startangle=90,
    colors=colors,
    textprops={'fontsize': 11, 'color': 'black'}
)
centre_circle = plt.Circle((0,0),0.65,fc='white')
fig.gca().add_artist(centre_circle)
ax.set_title(' Prescribed Drugs', fontsize=12, color='#264653')
plt.tight_layout()
plt.show()



