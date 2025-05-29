import streamlit as st
import sqlite3
from datetime import datetime, date, timedelta
import random
import calendar

DB_NAME = "tasks.db"

# ---------- DB Setup with Migration ----------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            task TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Not Done',
            due_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS food_planner (
            id INTEGER PRIMARY KEY,
            food TEXT NOT NULL,
            plan_date TEXT NOT NULL,
            meal_type TEXT NOT NULL DEFAULT 'Unknown'
        )
    ''')
    # Modified custom_foods table to include image_url
    c.execute('''
        CREATE TABLE IF NOT EXISTS custom_foods (
            id INTEGER PRIMARY KEY,
            food TEXT NOT NULL,
            meal_type TEXT NOT NULL,
            image_url TEXT
        )
    ''')

    # Add image_url column if it doesn't exist (migration)
    try:
        c.execute("ALTER TABLE custom_foods ADD COLUMN image_url TEXT")
    except sqlite3.OperationalError:
        pass # Column already exists, safe to ignore

    conn.commit()
    conn.close()

# ---------- Task Functions (No Change) ----------
def add_task(task, due_date):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute('INSERT INTO tasks (task, status, due_date) VALUES (?, ?, ?)', (task, "Not Done", due_date))

def get_tasks():
    with sqlite3.connect(DB_NAME) as conn:
        return conn.execute('SELECT id, task, status, due_date FROM tasks ORDER BY created_at DESC').fetchall()

def get_tasks_by_date(target_date):
    with sqlite3.connect(DB_NAME) as conn:
        return conn.execute('SELECT id, task, status, due_date FROM tasks WHERE due_date = ?', (target_date,)).fetchall()

def update_task_status(task_id, new_status):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute('UPDATE tasks SET status = ? WHERE id = ?', (new_status, task_id))

def delete_task(task_id):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute('DELETE FROM tasks WHERE id = ?', (task_id,))

# ---------- Food Planner Functions (Modified) ----------
def add_food(food, plan_date, meal_type):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute('INSERT INTO food_planner (food, plan_date, meal_type) VALUES (?, ?, ?)', (food, plan_date, meal_type))

def get_foods_by_date(plan_date):
    with sqlite3.connect(DB_NAME) as conn:
        # Order by meal_type to get desired sorting (e.g., Breakfast, Lunch, Dinner)
        return conn.execute('SELECT id, food, meal_type FROM food_planner WHERE plan_date = ? ORDER BY meal_type', (plan_date,)).fetchall()

def delete_food(food_id):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute('DELETE FROM food_planner WHERE id = ?', (food_id,))

def add_custom_food(food, meal_type, image_url=None):
    with sqlite3.connect(DB_NAME) as conn:
        # Ensure image_url is stored as None if empty string
        final_image_url = image_url if image_url and image_url.strip() else None
        conn.execute('INSERT INTO custom_foods (food, meal_type, image_url) VALUES (?, ?, ?)', (food.strip(), meal_type, final_image_url))

def get_custom_foods(meal_type=None): # Modified to allow fetching all custom foods or by type
    with sqlite3.connect(DB_NAME) as conn:
        if meal_type:
            # Returns (food, image_url) tuples
            return conn.execute('SELECT food, image_url FROM custom_foods WHERE meal_type = ?', (meal_type,)).fetchall()
        else:
            return conn.execute('SELECT id, food, meal_type, image_url FROM custom_foods').fetchall()

def delete_custom_food(food_id):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute('DELETE FROM custom_foods WHERE id = ?', (food_id,))

# ---------- Helper (No Change) ----------
def trigger_rerun():
    st.session_state.rerun_toggle = not st.session_state.get("rerun_toggle", False)


# ---------- UI Mode ----------
st.set_page_config(page_title="Personal Planner", layout="centered", initial_sidebar_state="expanded")
init_db()

# Define meal_types globally so it's accessible everywhere
meal_types = ["Breakfast", "Lunch", "Dinner"]

# Theme Selector
theme = st.sidebar.selectbox("🎨 Select Theme", ["Dark 🌙", "Light ☀️", "Blue 💙", "Red ❤️", "Yellow 💛", "Green 💚"])

theme_styles = {
    "Dark 🌙": {
        "bg": "#0e1117", "text": "white", "sidebar": "#161b22", "accent": "#58a6ff", "done": "#238636", "info_bg": "#1e2838", "warning_bg": "#3d2a13"
    },
    "Light ☀️": {
        "bg": "#f5f5f5", "text": "#333", "sidebar": "#eeeeee", "accent": "#0a58ca", "done": "#28a745", "info_bg": "#e0f2f7", "warning_bg": "#fff3cd"
    },
    "Blue 💙": {
        "bg": "#e0f0ff", "text": "#003366", "sidebar": "#cce5ff", "accent": "#004085", "done": "#007bff", "info_bg": "#b3e0ff", "warning_bg": "#ffeeba"
    },
    "Red ❤️": {
        "bg": "#ffe6e6", "text": "#660000", "sidebar": "#ffcccc", "accent": "#cc0000", "done": "#e60000", "info_bg": "#ffcce0", "warning_bg": "#ffe0b2"
    },
    "Yellow 💛": {
        "bg": "#fff8e1", "text": "#665c00", "sidebar": "#fff3cd", "accent": "#ffcc00", "done": "#e6b800", "info_bg": "#fff9c4", "warning_bg": "#ffecb3"
    },
    "Green 💚": {
        "bg": "#e6ffed", "text": "#004d00", "sidebar": "#ccffdd", "accent": "#008000", "done": "#00cc66", "info_bg": "#c8e6c9", "warning_bg": "#ffecb3"
    }
}

style = theme_styles[theme]

# Color for nav text: white only if dark mode else black
nav_text_color = "white" if theme == "Dark 🌙" else "black"
# Adjusted accent color for info/warning boxes to be more readable
info_accent_color = style['accent']
warning_accent_color = style['accent']

custom_css = f"""
<style>
body {{
    background-color: {style['bg']};
    color: {style['text']};
}}
[data-testid="stSidebar"] {{
    background-color: {style['sidebar']};
    color: {nav_text_color} !important;
}}
h1, h2, h3, h4, h5, h6, .st-emotion-cache-10trblm, .st-emotion-cache-1avcm0n {{
    color: {style['accent']} !important;
}}
button[kind="primary"] {{
    background-color: {style['done']};
    color: white;
}}
/* General button styling */
.stButton > button {{
    background-color: {style['accent']};
    color: white;
    border-radius: 5px;
    border: none;
    padding: 8px 15px;
    cursor: pointer;
    transition: background-color 0.2s ease-in-out;
}}
.stButton > button:hover {{
    background-color: {style['accent']}da; /* Slightly darker on hover */
}}

/* Streamlit info/warning boxes */
.stAlert > div {{
    background-color: {style['info_bg']} !important;
    color: {style['text']} !important;
    border-left: 5px solid {info_accent_color} !important;
}}
.stAlert [data-testid="stMarkdownContainer"] p {{
    color: {style['text']} !important;
}}
.stAlert [data-testid="stMarkdownContainer"] strong {{
    color: {info_accent_color} !important; /* For info box title/strong text */
}}

/* Specific overrides for sidebar navigation text (radio buttons) */
[data-testid="stSidebar"] [data-testid="stRadio"] label {{
    color: {nav_text_color} !important;
    padding: 8px 15px;
    margin: 5px 0;
    border-radius: 8px;
    transition: background-color 0.2s ease-in-out;
    font-size: 1.1em;
    font-weight: bold;
}}

/* Hover effect for radio buttons */
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {{
    background-color: rgba(255, 255, 255, 0.1);
}}

/* Style for the selected radio button */
[data-testid="stSidebar"] [data-testid="stRadio"] input:checked + div {{
    background-color: {style['accent']} !important;
    color: white !important;
    border-radius: 8px;
}}

/* Ensure the text within the selected radio button is white */
[data-testid="stSidebar"] [data-testid="stRadio"] input:checked + div > .st-emotion-cache-1v0mbdj span,
[data-testid="stSidebar"] [data-testid="stRadio"] input:checked + div > .st-emotion-cache-1v0mbdj div,
[data-testid="stSidebar"] [data-testid="stRadio"] input:checked + div > label > p {{
    color: white !important;
}}

/* Target the div elements that contain the actual text inside the labels */
[data-testid="stSidebar"] [data-testid="stRadio"] label > div {{
    color: {nav_text_color} !important;
}}
/* Sometimes text is wrapped in a p tag, target that too */
[data-testid="stSidebar"] [data-testid="stRadio"] label p {{
    color: {nav_text_color} !important;
}}

/* More general rule for any text inside the sidebar to ensure consistency */
[data-testid="stSidebar"] .st-emotion-cache-1aumxhk,
[data-testid="stSidebar"] .st-emotion-cache-1v0mbdj {{
    color: {nav_text_color} !important;
}}

/* Style for task/meal items in lists */
.task-item, .meal-item {{
    padding: 8px;
    border-left: 4px solid;
    margin-bottom: 5px;
    border-radius: 4px;
}}
.task-overdue {{
    border-color: #ff4d4d;
    background-color: rgba(255, 77, 77, 0.1);
}}
.task-not-done {{
    border-color: #999;
    background-color: rgba(153, 153, 153, 0.1);
}}
.task-done {{
    border-color: {style['done']};
    background-color: rgba({int(style['done'][1:3], 16)}, {int(style['done'][3:5], 16)}, {int(style['done'][5:7], 16)}, 0.1);
}}

/* Calendar day styling */
.calendar-day {{
    background-color: #eeeeee;
    border-radius: 8px;
    padding: 8px;
    text-align: center;
    font-weight: bold;
    color: #222;
    user-select: none;
    cursor: pointer;
    transition: all 0.1s ease-in-out;
    border: 1px solid transparent; /* for hover effect */
}}
.calendar-day:hover {{
    border: 1px solid {style['accent']};
    box-shadow: 0 0 5px rgba({int(style['accent'][1:3], 16)}, {int(style['accent'][3:5], 16)}, {int(style['accent'][5:7], 16)}, 0.5);
}}
.calendar-day.has-task {{
    background-color: #ff9999; /* red-ish */
    color: {style['text']};
}}
.calendar-day.has-meal {{
    background-color: #99ff99; /* green-ish */
    color: {style['text']};
}}
.calendar-day.has-both {{
    background-color: #a186f0; /* purple-ish */
    color: {style['text']};
}}
.calendar-day.current-day {{
    border: 2px solid {style['accent']};
    box-shadow: 0 0 8px rgba({int(style['accent'][1:3], 16)}, {int(style['accent'][3:5], 16)}, {int(style['accent'][5:7], 16)}, 0.7);
}}

</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# Main App Title and Current Date/Time
st.markdown(
    f"<h1 style='text-align: center; color: {style['accent']}; margin-bottom: 0px;'>✨ Your Personal Planner ✨</h1>",
    unsafe_allow_html=True
)
st.markdown(
    f"<div style='text-align: center; font-size: 1.1em; color: {style['text']}; margin-bottom: 20px;'>{datetime.now().strftime('%A, %B %d, %Y — %I:%M:%S %p')}</div>",
    unsafe_allow_html=True
)

# Navigation
page = st.sidebar.radio("📚 Navigate", ["To-Do List", "Food Spinner", "Custom Foods", "Calendar 📅"])


if page == "To-Do List":
    st.subheader("📋 Your Tasks")

    st.markdown("---")
    st.subheader("➕ Add a New Task")
    with st.form("add_task_form", clear_on_submit=True):
        task_input = st.text_input("What's on your mind?", placeholder="e.g., Buy groceries, Finish report...")
        due_date = st.date_input("Due Date", value=date.today())
        if st.form_submit_button("Add Task", use_container_width=True):
            if task_input.strip():
                add_task(task_input.strip(), due_date.isoformat())
                st.success("Task added successfully!")
                trigger_rerun()
            else:
                st.warning("Please enter a valid task description.")

    st.markdown("---")
    st.subheader("🔎 Filter Tasks by Date")
    filter_date = st.date_input("Show tasks due on", value=None, key="task_filter_date")

    st.markdown("---")
    st.subheader("⚡ Pending Tasks")
    tasks = get_tasks()
    if filter_date:
        tasks_to_display = [t for t in tasks if t[3] == filter_date.isoformat()]
    else:
        tasks_to_display = tasks

    not_done_tasks = [t for t in tasks_to_display if t[2] == "Not Done"]

    if not_done_tasks:
        for task_id, task, status, due in not_done_tasks:
            is_overdue = (status == "Not Done" and due and date.fromisoformat(due) < date.today())
            task_class = "task-overdue" if is_overdue else "task-not-done"
            
            col1, col2, col3 = st.columns([6, 2, 2])
            with col1:
                st.markdown(f"<div class='task-item {task_class}'><b>{task}</b><br><small>Due: {due}</small></div>", unsafe_allow_html=True)
            with col2:
                if st.button("✅ Done", key=f"done{task_id}", use_container_width=True):
                    update_task_status(task_id, "Done")
                    st.balloons() # Confetti!
                    trigger_rerun()
            with col3:
                if st.button("🗑️", key=f"del_not_done_{task_id}", use_container_width=True):
                    delete_task(task_id)
                    trigger_rerun()
    else:
        st.info("No pending tasks. Great job, or perhaps add a new one?")

    st.markdown("---")
    st.subheader("✅ Completed Tasks")
    done_tasks = [t for t in tasks_to_display if t[2] == "Done"]
    if done_tasks:
        for task_id, task, status, due in done_tasks:
            task_class = "task-done"
            col1, col2 = st.columns([8, 2])
            with col1:
                st.markdown(f"<div class='task-item {task_class}'><b>{task}</b><br><small>Due: {due}</small></div>", unsafe_allow_html=True)
            with col2:
                if st.button("🗑️", key=f"del_done_{task_id}", use_container_width=True):
                    delete_task(task_id)
                    trigger_rerun()
    else:
        st.info("No completed tasks yet.")


elif page == "Food Spinner":
    st.subheader("🍽️ Plan Your Meals!")

    plan_date = st.date_input("Select Date for Meal Plan", value=date.today(), key="food_plan_date")
    selected_meal = st.selectbox("Meal Type for Spinning", meal_types, key="spinner_meal_type")

    # Dictionary of default foods with reliable example image URLs
    default_foods_with_images = {
        "Breakfast": [
            {"food": "Pancakes", "image_url": "https://upload.wikimedia.org/wikipedia/commons/4/43/Blueberry_pancakes_%283%29.jpg"},
            {"food": "Cereal", "image_url": "https://th.bing.com/th/id/OIP.5lxR-uEQfDdKXC3Z2nRuhgHaGa?rs=1&pid=ImgDetMain"},
            {"food": "Omelette", "image_url": "https://www.sweetashoney.co/wp-content/uploads/Omelette-2-1024x640.jpg"},
            {"food": "Toast", "image_url": "https://www.thespruceeats.com/thmb/ucRM--oMpuYbTO7O3gOiB8LaTvo=/5190x4062/filters:fill(auto,1)/French-Toast-58addf8e5f9b58a3c9d41348.jpg"},
            {"food": "Smoothie", "image_url": "https://tatyanaseverydayfood.com/wp-content/uploads/2015/01/Fruit-Smoothie.jpg"}
        ],
        "Lunch": [
            {"food": "Sandwich", "image_url": "https://www.maggi.ph/sites/default/files/styles/image_744_x_419/public/srh_recipes/91afe3a3615aaa162847dc3fdcdda2da.jpg?h=476030cb&itok=xKWGntHo"},
            {"food": "Salad", "image_url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQND_ziEJuzn-YxmIuwKaWTB17XPtQs8-UKTFULGlyZEi3BL4jSnnlzqBo71jVA3DbrwrM&usqp=CAU"},
            {"food": "Burger", "image_url": "https://www.ajinomoto.com.my/sites/default/files/content/recipe/image/2022-09/Malaysian-Classic-Street-Burger-new.jpg"},
            {"food": "Noodles", "image_url": "https://pinchandswirl.com/wp-content/uploads/2022/11/Garlic-Butter-Noodles_sq.jpg"},
            {"food": "Sushi", "image_url": "https://i.shgcdn.com/170776f5-8678-4b7b-aba7-9157fd1b5aab/-/format/auto/-/preview/3000x3000/-/quality/lighter/"}
        ],
        "Dinner": [
            {"food": "Pizza", "image_url": "https://images.ctfassets.net/j8tkpy1gjhi5/5OvVmigx6VIUsyoKz1EHUs/b8173b7dcfbd6da341ce11bcebfa86ea/Salami-pizza-hero.jpg?w=768&q=90&fm=webp"},
            {"food": "Pasta", "image_url": "https://ministryofcurry.com/wp-content/uploads/2018/07/Pasta-with-Creamy-Tomato-Sauce-1.jpg"},
            {"food": "Steak", "image_url": "https://thebigmansworld.com/wp-content/uploads/2023/07/sirloin-steak-recipe.jpg"},
            {"food": "Rice Bowl", "image_url": "https://cdn.loveandlemons.com/wp-content/uploads/2020/03/bibimbap-recipe.jpg"},
            {"food": "Soup", "image_url": "https://www.tasteofhome.com/wp-content/uploads/2018/01/exps7965_HSC143552A08_07_5b.jpg"}
        ]
    }

    # Get custom foods. get_custom_foods now returns (food, image_url) tuples.
    custom_foods_raw = get_custom_foods(selected_meal)
    # Convert raw tuples into a list of dictionaries for consistent handling
    custom_foods_processed = [{"food": item[0], "image_url": item[1]} for item in custom_foods_raw]

    # Combine default and custom foods for the spinner
    all_foods_for_spinning = default_foods_with_images[selected_meal] + custom_foods_processed


    st.markdown("---")
    st.subheader(f"🎲 Spin for Your {selected_meal}!")
    # Initialize session state for the currently selected food (name and URL)
    if "current_food_selection" not in st.session_state:
        st.session_state.current_food_selection = None

    col_spin, col_save_reset = st.columns([1, 2])
    with col_spin:
        if st.button("🎲 Spin Wheel", use_container_width=True):
            if all_foods_for_spinning:
                st.session_state.current_food_selection = random.choice(all_foods_for_spinning)
            else:
                st.warning(f"Please add some {selected_meal} options first using 'Add Custom Food'.")

    if st.session_state.current_food_selection:
        selected_food_name = st.session_state.current_food_selection["food"]
        selected_food_image = st.session_state.current_food_selection["image_url"]

        st.markdown(f"### 🍽️ Selected: **{selected_food_name}**")
        if selected_food_image:
            st.image(selected_food_image, caption=f"Enjoy {selected_food_name}!", width=300)
        else:
            st.info("No image available for this food. Consider adding one in 'Custom Foods'!")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Save This Meal", key=f"save_spin_food", use_container_width=True):
                add_food(selected_food_name, plan_date.isoformat(), selected_meal)
                st.success(f"'{selected_food_name}' saved for {plan_date.strftime('%B %d')}!")
                st.session_state.current_food_selection = None # Reset selection after saving
                trigger_rerun() # Rerun to refresh the planned meals list
        with col2:
            if st.button("🔄 Spin Again", key=f"spin_again_food", use_container_width=True):
                if all_foods_for_spinning:
                    st.session_state.current_food_selection = random.choice(all_foods_for_spinning)
                else:
                    st.warning(f"No {selected_meal} options available to spin again.") # Should not happen if previous spin was successful

    st.markdown("---")
    st.subheader(f"📅 Meals Planned for {plan_date.strftime('%B %d, %Y')}")
    meals_for_date = get_foods_by_date(plan_date.isoformat())

    if meals_for_date:
        grouped_meals = {meal_type: [] for meal_type in meal_types}
        for food_id, food, meal_type in meals_for_date:
            grouped_meals[meal_type].append({"id": food_id, "food": food})

        for meal_type in meal_types:
            st.markdown(f"#### 🍴 {meal_type}")
            if grouped_meals[meal_type]:
                for meal_item in grouped_meals[meal_type]:
                    col1, col2 = st.columns([6, 1])
                    with col1:
                        st.markdown(f"<div class='meal-item'>- {meal_item['food']}</div>", unsafe_allow_html=True)
                    with col2:
                        if st.button("🗑️", key=f"delmeal{meal_item['id']}", use_container_width=True):
                            delete_food(meal_item['id'])
                            trigger_rerun()
            else:
                st.info(f"No {meal_type} planned. Spin one!")
    else:
        st.info(f"No meals planned for {plan_date.strftime('%B %d, %Y')}. Spin the wheel to get started!")

elif page == "Custom Foods":
    st.subheader("🍔 Manage Your Custom Foods")
    st.markdown("Add your favorite dishes to the spinner and even include an image!")

    st.markdown("---")
    st.subheader("➕ Add New Custom Food")
    with st.form("add_custom_food_form", clear_on_submit=True):
        custom_food_name = st.text_input("Food Name", placeholder="e.g., Homemade Lasagna")
        custom_meal_type = st.selectbox("Meal Type", meal_types, key="add_custom_meal_type")
        image_url = st.text_input("Image URL (Optional)", placeholder="Paste image link here...")

        if st.form_submit_button("Add Custom Food", use_container_width=True):
            if custom_food_name.strip():
                add_custom_food(custom_food_name.strip(), custom_meal_type, image_url.strip() if image_url else None)
                st.success(f"'{custom_food_name}' added to your custom foods!")
                trigger_rerun()
            else:
                st.warning("Please enter a food name.")

    st.markdown("---")
    st.subheader("My Custom Food List")
    all_custom_foods = get_custom_foods(meal_type=None) # Fetch all custom foods for display

    if all_custom_foods:
        # Group custom foods by meal type for better organization
        grouped_custom_foods = {mt: [] for mt in meal_types}
        for food_id, food_name, meal_type, img_url in all_custom_foods:
            grouped_custom_foods[meal_type].append({"id": food_id, "food": food_name, "image_url": img_url})

        for m_type in meal_types:
            if grouped_custom_foods[m_type]:
                st.markdown(f"#### 🍴 {m_type} Custom Foods")
                for item in grouped_custom_foods[m_type]:
                    col_food, col_img_preview, col_delete = st.columns([5, 3, 1])
                    with col_food:
                        st.markdown(f"- **{item['food']}**")
                    with col_img_preview:
                        if item['image_url']:
                            st.image(item['image_url'], width=100, caption="Preview")
                        else:
                            st.markdown("<small>No image</small>", unsafe_allow_html=True)
                    with col_delete:
                        if st.button("🗑️", key=f"del_custom_{item['id']}", use_container_width=True):
                            delete_custom_food(item['id'])
                            st.info(f"'{item['food']}' removed.")
                            trigger_rerun()
    else:
        st.info("No custom foods added yet. Use the form above to add your favorites!")


elif page == "Calendar 📅":
    st.subheader("📅 Monthly Overview")

    today = date.today()
    
    # Allow user to change month/year
    col_month, col_year = st.columns(2)
    with col_month:
        month = st.selectbox("Month", range(1, 13), index=today.month - 1, format_func=lambda x: calendar.month_name[x])
    with col_year:
        year = st.number_input("Year", min_value=1900, max_value=2100, value=today.year, step=1)

    cal = calendar.Calendar(firstweekday=0)  # Monday first

    tasks = get_tasks()
    tasks_dates = set(t[3] for t in tasks if t[3])

    with sqlite3.connect(DB_NAME) as conn:
        meals_dates = set(row[0] for row in conn.execute('SELECT DISTINCT plan_date FROM food_planner'))

    st.markdown(f"### {calendar.month_name[month]} {year}", unsafe_allow_html=True)

    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    cols = st.columns(7) # Changed to 7 columns for direct weekday layout
    for i, day in enumerate(weekdays):
        cols[i].markdown(f"**{day}**", unsafe_allow_html=True)


    weeks = cal.monthdayscalendar(year, month)

    # Store a potential clicked date
    if 'clicked_calendar_date' not in st.session_state:
        st.session_state.clicked_calendar_date = today

    for week in weeks:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].write("")  # empty cell
            else:
                current_day_date = date(year, month, day)
                date_str = current_day_date.isoformat()
                has_task = date_str in tasks_dates
                has_meal = date_str in meals_dates

                bg_class = "calendar-day"
                if has_task and has_meal:
                    bg_class += " has-both"
                elif has_task:
                    bg_class += " has-task"
                elif has_meal:
                    bg_class += " has-meal"

                if current_day_date == today:
                    bg_class += " current-day"

                # Use a button or a clickable div for interactivity
                # For simplicity in this structure, let's use a button, but CSS can make it look like a div.
                # A more advanced approach would involve custom components or JavaScript.
                # Here, we'll just use unique keys for buttons and update session state
                if cols[i].button(str(day), key=f"cal_day_{date_str}", help=f"Click to view details for {date_str}"):
                    st.session_state.clicked_calendar_date = current_day_date
                    # Trigger rerun to show details for the newly clicked date
                    trigger_rerun()
                
                # Apply custom CSS using markdown for the cell background and text styling
                # Note: This markdown won't apply to the button directly, but if you wanted a pure
                # display, you could use this HTML directly and replace the button.
                # For clickable calendar cells, Streamlit buttons are easiest.
                # The CSS for .calendar-day is applied to the button itself implicitly by Streamlit's rendering.
                
                # We'll re-render the button with custom styles if needed, or stick to the simple button
                # and let Streamlit's default styling work with the custom CSS.
                # The background colors are handled by the CSS classes (has-task, etc.) which Streamlit
                # applies if the button is within a markdown block with the class. This is tricky.
                # For robust styling of buttons as calendar cells, you'd usually create custom components
                # or use `st.markdown` with a hacky onclick, but let's try injecting style onto the button directly.

                # A more reliable way for background coloring *inside* the button
                # is not directly supported by Streamlit's button API, so the CSS classes
                # like .calendar-day are best efforts to style the button *container*.
                # Let's adjust the button's appearance via CSS:
                if has_task and has_meal:
                    button_style = "background-color: #a186f0; color: white; border: none; border-radius: 8px;"
                elif has_task:
                    button_style = "background-color: #ff9999; color: black; border: none; border-radius: 8px;"
                elif has_meal:
                    button_style = "background-color: #99ff99; color: black; border: none; border-radius: 8px;"
                else:
                    button_style = f"background-color: {style['sidebar']}; color: {style['text']}; border: 1px solid #ccc; border-radius: 8px;"

                if current_day_date == today:
                    button_style += f"border: 2px solid {style['accent']};"
                
                # Re-rendering the button with an embedded style is not how Streamlit works.
                # The best way to achieve the distinct colored cells for dates is to *not* use st.button
                # for the visual representation, but to use st.markdown with clickability via JS (complex)
                # or to use st.columns with st.empty() and then fill with a button *or* a markdown block based on click.
                # For simplicity for now, the existing `st.button` combined with the general CSS
                # targeting `stButton > button` and specific `.calendar-day` classes for the cell *container*
                # will give some visual feedback. The hover/border styles in CSS will also apply.

                # Let's try to pass an HTML string into a button's label to get colors directly.
                # This is tricky because button labels escape HTML by default.
                # Alternative: create clickable markdown divs.
                # For now, I'll keep the button and focus on the information display below.

    st.markdown("---")
    st.subheader(f"🔍 Details for {st.session_state.clicked_calendar_date.strftime('%A, %B %d, %Y')}")

    day_tasks = get_tasks_by_date(st.session_state.clicked_calendar_date.isoformat())
    day_meals = get_foods_by_date(st.session_state.clicked_calendar_date.isoformat())

    st.markdown("##### Tasks:")
    if day_tasks:
        for task_id, task, status, due in day_tasks:
            is_overdue = status == "Not Done" and date.fromisoformat(due) < date.today()
            task_class = "task-overdue" if is_overdue else ("task-done" if status == "Done" else "task-not-done")
            st.markdown(f"<div class='task-item {task_class}'><span style='font-weight:bold;'>{task}</span> (Status: {status})</div>", unsafe_allow_html=True)
    else:
        st.info("No tasks scheduled for this date.")

    st.markdown("##### Meals:")
    if day_meals:
        grouped_meals_calendar = {mt: [] for mt in meal_types}
        for _, food, meal_type in day_meals:
            grouped_meals_calendar[meal_type].append(food)

        for meal_type in meal_types:
            st.markdown(f"###### 🍴 {meal_type}:")
            if grouped_meals_calendar[meal_type]:
                for food_item in grouped_meals_calendar[meal_type]:
                    st.markdown(f"- {food_item}")
            else:
                st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp; _No {meal_type} planned._")
    else:
        st.info("No meals planned for this date.")
