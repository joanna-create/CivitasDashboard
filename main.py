import os
import pickle
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st


# Load saved projects
def load_projects():
    try:
        with open("projects.pkl", "rb") as file:
            return pickle.load(file)
    except FileNotFoundError:
        return []


# Save projects to a file
def save_projects(projects):
    with open("projects.pkl", "wb") as file:
        pickle.dump(projects, file)


# Enhanced Project Progress Calculation
def update_progress(project):
    total_elements = len(project["elements_progress"])
    if total_elements == 0:
        return 0
    weighted_sum = sum(progress["progress"] * progress["weight"] for progress in project["elements_progress"].values())
    total_weight = sum(progress["weight"] for progress in project["elements_progress"].values())
    return round(weighted_sum / total_weight, 2) if total_weight > 0 else 0


# Register New Project
# Register New Project
def register_project(projects, inputs):
    try:
        project_name = inputs["Project Name"]
        project_id = inputs["Project ID"]
        client_name = inputs["Client Name"]
        start_date = datetime.strptime(inputs["Start Date"], "%Y-%m-%d").date()
        end_date = datetime.strptime(inputs["End Date"], "%Y-%m-%d").date()

        if end_date < start_date:
            raise ValueError("End date cannot be earlier than start date.")

        # Budget validation and formatting
        try:
            budget = float(inputs["Budget (RM)"])
            if budget <= 0:
                raise ValueError("Budget must be a positive number.")
            budget = round(budget, 2)  # Ensure the budget is rounded to two decimal places
        except ValueError:
            st.error("Please enter a valid budget amount (positive number).")
            return

        project = {
            "name": project_name,
            "id": project_id,
            "client": client_name,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "budget": budget,  # Store budget with two decimal places
            "progress": 0,
            "task_list": [],
            "interim_claims": [],
            "reports": [],
            "elements_progress": {}
        }
        projects.append(project)
        save_projects(projects)
        st.success(f"Project '{project_name}' registered successfully!")
    except ValueError as ve:
        st.error(f"Input Error: {ve}")
    except Exception as e:
        st.error(f"Unexpected error: {e}")


# Display project progress with a better chart
def plot_project_progress(project):
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(['Progress'], [project['progress']], color="#4C9F70")  # Green color
    ax.set_xlim(0, 100)
    ax.set_xlabel('Progress (%)', fontsize=12, color='black')
    ax.set_title(f"Project Progress for {project['name']}", fontsize=14, color='#2C3E50')
    ax.text(10, 0, f"{project['progress']}%", va="center", ha="left", fontsize=12, color="white")
    st.pyplot(fig)


# Task Management
def manage_tasks(projects, project_id):
    for project in projects:
        if project["id"] == project_id:
            st.subheader("Manage Tasks")
            task_name = st.text_input("Task Name")
            task_status = st.selectbox("Task Status", ["Not Started", "In Progress", "Completed"])
            assignee = st.text_input("Assign to (Team Member)")
            task_deadline = st.date_input("Deadline")

            if st.button("Add Task", key="add_task"):
                task = {
                    "task_name": task_name,
                    "status": task_status,
                    "assignee": assignee,
                    "deadline": task_deadline
                }
                project["task_list"].append(task)
                save_projects(projects)
                st.success(f"Task '{task_name}' added to project '{project['name']}'")

            # Show existing tasks with status
            st.subheader("Current Tasks")
            if project["task_list"]:
                tasks_df = pd.DataFrame(project["task_list"])
                st.write(tasks_df)
            else:
                st.write("No tasks available yet.")


# Manage interim claims
def manage_interim_claims(projects, project_id):
    for project in projects:
        if project["id"] == project_id:
            st.subheader("Manage Interim Claims")
            claim_amount = st.number_input("Interim Claim Amount (RM)", min_value=0.0, step=0.01)
            claim_date = st.date_input("Claim Date")
            claim_status = st.selectbox("Claim Status", ["Pending", "Approved", "Rejected"])

            if st.button("Add Interim Claim", key="add_claim"):
                if claim_amount > project["budget"]:
                    st.error("Claim amount exceeds the remaining budget!")
                else:
                    claim = {"amount": claim_amount, "date": claim_date, "status": claim_status}
                    project["interim_claims"].append(claim)
                    project['budget'] -= claim_amount
                    save_projects(projects)
                    st.success(f"Interim Claim of RM{claim_amount} added to project '{project['name']}'")

            # Display claims with status
            st.subheader("Interim Claims")
            if project["interim_claims"]:
                claims_df = pd.DataFrame(project["interim_claims"])
                st.write(claims_df)
            else:
                st.write("No claims available yet.")

            # Update Claim Status
            st.subheader("Update Claim Status")
            claim_to_update = st.selectbox("Select Claim to Update", range(len(project["interim_claims"])))
            if claim_to_update is not None:
                updated_status = st.selectbox("New Status", ["Pending", "Approved", "Rejected"])
                if st.button("Update Status"):
                    project["interim_claims"][claim_to_update]["status"] = updated_status
                    save_projects(projects)
                    st.success(f"Claim status updated to '{updated_status}'.")


# Display Total Claims
def display_total_claims(project):
    total_claims = sum(claim["amount"] for claim in project["interim_claims"])
    st.write(f"**Total Claims Submitted (RM):** RM{total_claims:.2f}")  # Display total claims with 2 decimal places
    st.write(f"**Remaining Budget (RM):** RM{project['budget']:.2f}")  # Display budget with 2 decimal places


# File Upload and Preview
def upload_project_document(projects, project_id, document_file):
    try:
        for project in projects:
            if project["id"] == project_id:
                document_name = document_file.name
                document_path = f"project_docs/{project_id}/{document_name}"
                os.makedirs(os.path.dirname(document_path), exist_ok=True)
                with open(document_path, "wb") as file:
                    file.write(document_file.getbuffer())
                project["reports"].append(document_path)
                save_projects(projects)
                st.success(f"Document '{document_name}' uploaded successfully!")

                # File preview
                if document_file.type == "application/pdf":
                    st.write("**PDF Preview:**")
                    with open(document_path, "rb") as file:
                        st.download_button("Download PDF", file, document_name)
                elif document_file.type.startswith("image/"):
                    st.image(document_path, caption=document_name)

    except Exception as e:
        st.error(f"Error uploading document: {e}")


# Main Streamlit App
def main():
    st.set_page_config(page_title="Construction Project Dashboard", layout="wide", page_icon="🏗️")

    st.title("🏗️ **Construction Project Dashboard**")
    st.markdown("<hr>", unsafe_allow_html=True)

    # Sidebar style improvements
    st.sidebar.markdown("<h3 style='color:#2C3E50;'>Navigation</h3>", unsafe_allow_html=True)
    menu = ["Home", "Register Project", "View Projects", "Tasks", "Interim Claims", "Documents"]
    choice = st.sidebar.radio("Select an Option", menu)

    # Load projects
    projects = load_projects()

    if choice == "Home":
        st.write("Welcome to the Civitas Dashboard! Your one-stop solution for project management.")

    elif choice == "Register Project":
        st.subheader("Register New Project")
        with st.form(key="register_form"):
            project_name = st.text_input("Project Name")
            project_id = st.text_input("Project ID")
            client_name = st.text_input("Client Name")
            start_date = st.date_input("Start Date")
            end_date = st.date_input("End Date")
            budget = st.text_input("Budget (RM)")

            submit_button = st.form_submit_button("Register Project")
            if submit_button:
                inputs = {
                    "Project Name": project_name,
                    "Project ID": project_id,
                    "Client Name": client_name,
                    "Start Date": str(start_date),
                    "End Date": str(end_date),
                    "Budget (RM)": budget
                }
                register_project(projects, inputs)


# View Projects section (Display the budget in two decimal places)

    elif choice == "View Projects":

        st.subheader("Existing Projects")

        project_ids = [project["id"] for project in projects]

        selected_project_id = st.selectbox("Select a Project", project_ids)

        if selected_project_id:
            selected_project = next(project for project in projects if project["id"] == selected_project_id)

            st.write(f"**Project Name**: {selected_project['name']}")

            st.write(f"**Client**: {selected_project['client']}")

            st.write(f"**Start Date**: {selected_project['start_date']}")

            st.write(f"**End Date**: {selected_project['end_date']}")

            st.write(f"**Budget**: RM{selected_project['budget']:.2f}")  # Display the budget in 2 decimal places

            st.write(f"**Progress**: {selected_project['progress']}%")

            plot_project_progress(selected_project)

            display_total_claims(selected_project)

    elif choice == "Tasks":
        project_ids = [project["id"] for project in projects]
        selected_project_id = st.selectbox("Select Project for Task Management", project_ids)
        if selected_project_id:
            manage_tasks(projects, selected_project_id)

    elif choice == "Interim Claims":
        project_ids = [project["id"] for project in projects]
        selected_project_id = st.selectbox("Select Project for Claims Management", project_ids)
        if selected_project_id:
            manage_interim_claims(projects, selected_project_id)

    elif choice == "Documents":
        project_ids = [project["id"] for project in projects]
        selected_project_id = st.selectbox("Select Project for Document Upload", project_ids)
        document_file = st.file_uploader("Upload Document", type=["pdf", "docx", "jpg", "png"])
        if document_file:
            upload_project_document(projects, selected_project_id, document_file)

    save_projects(projects)


if __name__ == '__main__':
    main()
