from flask import Flask, render_template, jsonify, request  # ← Добавили request!
import random
from datetime import datetime
import json
import os

if 'VERCEL' in os.environ:
    app.static_folder = os.path.join(os.path.dirname(__file__), 'static')
    app.template_folder = os.path.dirname(__file__)

app = Flask(__name__)

# Файл для хранения целей
GOALS_FILE = 'user_goals.json'

# Загружаем цитаты
with open('quotes.json', 'r', encoding='utf-8') as f:
    quotes = json.load(f)


def load_goals():
    if os.path.exists(GOALS_FILE):
        with open(GOALS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"weekly_goals": [], "daily_goals": []}


def save_goals(goals):
    with open(GOALS_FILE, 'w', encoding='utf-8') as f:
        json.dump(goals, f, ensure_ascii=False, indent=2)


def get_greeting():
    hour = datetime.now().hour
    if hour < 12:
        return "Доброе утро, стратег"
    elif hour < 18:
        return "Добрый день, лидер"
    else:
        return "Добрый вечер, CEO"


@app.route('/')
def dashboard():
    return render_template('index.html')


@app.route('/api/data')
def get_data():
    goals_data = load_goals()

    # Прогресс недельных целей
    weekly_completed = sum(1 for g in goals_data['weekly_goals'] if g['completed'])
    weekly_total = len(goals_data['weekly_goals'])
    weekly_progress = int((weekly_completed / weekly_total * 100)) if weekly_total > 0 else 0

    # Прогресс дневных целей
    daily_completed = sum(1 for g in goals_data['daily_goals'] if g['completed'])
    daily_total = len(goals_data['daily_goals'])
    daily_progress = int((daily_completed / daily_total * 100)) if daily_total > 0 else 0

    return jsonify({
        'greeting': get_greeting(),
        'quote': random.choice(quotes),
        'date': datetime.now().strftime("%A, %d %B"),
        'weekly_progress': weekly_progress,
        'daily_progress': daily_progress,
        'weekly_goals': goals_data['weekly_goals'],
        'daily_goals': goals_data['daily_goals']
    })


@app.route('/api/add-goal', methods=['POST'])
def add_goal():
    data = request.json
    goal_type = data.get('type', 'weekly')  # 'weekly' или 'daily'
    text = data.get('text', '').strip()

    if not text:
        return jsonify({'error': 'Текст цели не может быть пустым'}), 400

    goals_data = load_goals()

    # Создаём новую цель
    new_goal = {
        "id": int(datetime.now().timestamp() * 1000),  # уникальный ID
        "text": text,
        "completed": False,
        "created_at": datetime.now().isoformat()
    }

    goals_data[f'{goal_type}_goals'].append(new_goal)
    save_goals(goals_data)

    return jsonify({'success': True, 'goal': new_goal})


@app.route('/api/toggle/<int:goal_id>', methods=['POST'])
def toggle_goal(goal_id):
    goals_data = load_goals()

    # Ищем цель в weekly и daily
    found = False
    for goal_type in ['weekly_goals', 'daily_goals']:
        for goal in goals_data[goal_type]:
            if goal['id'] == goal_id:
                goal['completed'] = not goal['completed']
                found = True
                break
        if found:
            break

    if found:
        save_goals(goals_data)
        return jsonify({'success': True})

    return jsonify({'error': 'Цель не найдена'}), 404


@app.route('/api/delete/<int:goal_id>', methods=['POST'])
def delete_goal(goal_id):
    goals_data = load_goals()

    for goal_type in ['weekly_goals', 'daily_goals']:
        goals_data[goal_type] = [g for g in goals_data[goal_type] if g['id'] != goal_id]

    save_goals(goals_data)
    return jsonify({'success': True})


if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    # ВАЖНО: host='0.0.0.0' а не 127.0.0.1
    app.run(host='0.0.0.0', port=port, debug=False)
