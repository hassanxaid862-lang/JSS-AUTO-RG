```python
import os
import json
import pandas as pd

BASE_DIR = "data"

# Ensure base directory exists
os.makedirs(BASE_DIR, exist_ok=True)

# ===============================
# INIT USER DATABASE
# ===============================
def init_user_database(user_id):
    user_path = os.path.join(BASE_DIR, user_id)
    os.makedirs(user_path, exist_ok=True)

# ===============================
# GET FILE PATH
# ===============================
def get_file_path(user_id, grade):
    return os.path.join(BASE_DIR, user_id, f"{grade}.json")

# ===============================
# SAVE DATA
# ===============================
def save_to_cloud_db(df, grade, user_id):
    try:
        path = get_file_path(user_id, grade)

        records = df.to_dict(orient="records")

        # Load existing data
        existing = []
        if os.path.exists(path):
            with open(path, "r") as f:
                existing = json.load(f)

        # Prevent duplicates
        existing_ids = {e["Assessment Number"] for e in existing}
        new_records = [r for r in records if r["Assessment Number"] not in existing_ids]

        existing.extend(new_records)

        with open(path, "w") as f:
            json.dump(existing, f, indent=4)

        return True, f"{len(new_records)} records saved"

    except Exception as e:
        return False, str(e)

# ===============================
# GET LEARNERS
# ===============================
def get_learners(user_id, grade):
    path = get_file_path(user_id, grade)

    if not os.path.exists(path):
        return []

    with open(path, "r") as f:
        data = json.load(f)

    learners = []
    for entry in data:
        learners.append({
            "name": entry.get("Learner's Name"),
            "assmt_no": entry.get("Assessment Number"),
            "grade": entry.get("Grade"),
            "marks": {
                k: float(v) for k, v in entry.items()
                if k not in ["Learner's Name", "Assessment Number", "Grade"]
            }
        })

    return learners

# ===============================
# UPDATE MARKS
# ===============================
def update_learner_marks(user_id, learner_id, new_marks):
    try:
        assmt_no, grade = learner_id.split("_")
        path = get_file_path(user_id, grade)

        if not os.path.exists(path):
            return False, "No data found"

        with open(path, "r") as f:
            data = json.load(f)

        updated = False
        for entry in data:
            if entry["Assessment Number"] == assmt_no:
                entry.update(new_marks)
                updated = True

        if not updated:
            return False, "Learner not found"

        with open(path, "w") as f:
            json.dump(data, f, indent=4)

        return True, "Marks updated successfully"

    except Exception as e:
        return False, str(e)

# ===============================
# DELETE LEARNER
# ===============================
def delete_learner(user_id, learner_id):
    try:
        assmt_no, grade = learner_id.split("_")
        path = get_file_path(user_id, grade)

        if not os.path.exists(path):
            return False, "No data found"

        with open(path, "r") as f:
            data = json.load(f)

        new_data = [d for d in data if d["Assessment Number"] != assmt_no]

        with open(path, "w") as f:
            json.dump(new_data, f, indent=4)

        return True, "Learner deleted successfully"

    except Exception as e:
        return False, str(e)

# ===============================
# USER SETTINGS (BASIC)
# ===============================
def get_user_settings(user_id):
    return {}

def update_user_settings(user_id, settings):
    return True, "Settings saved"

# ===============================
# GET GRADES
# ===============================
def get_grades(user_id):
    user_path = os.path.join(BASE_DIR, user_id)

    if not os.path.exists(user_path):
        return []

    files = os.listdir(user_path)
    return [f.replace(".json", "") for f in files if f.endswith(".json")]

# ===============================
# EXPORT DATA
# ===============================
def export_grade_data(user_id, grade):
    path = get_file_path(user_id, grade)

    if not os.path.exists(path):
        return pd.DataFrame()

    with open(path, "r") as f:
        data = json.load(f)

    return pd.DataFrame(data)

# ===============================
# PLACEHOLDER (for compatibility)
# ===============================
def get_firebase_db():
    return None
```
