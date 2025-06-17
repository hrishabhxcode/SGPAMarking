from flask import Flask, render_template, request, send_file


app = Flask(__name__)

# Grade to weight mapping
grade_weights = {
    'S': 10,
    'A': 9,
    'B': 8,
    'C': 7,
    'D': 6,
    'E': 5,
    'U': 0,
    'AB': 0
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    grades = request.form.getlist('grade')
    credits = request.form.getlist('credit')
    regno = request.form.get('regno')

    total_score = 0
    total_credits = 0
    suggestions = []
    detailed_data = []

    for grade, credit in zip(grades, credits):
        try:
            weight = grade_weights[grade.upper()]
            credit = float(credit)
            total_score += weight * credit
            total_credits += credit
            detailed_data.append((grade.upper(), credit, weight))

            if grade.upper() in ['C', 'D', 'E', 'U', 'AB']:
                suggestions.append(f"Improve in subject with grade '{grade.upper()}'")
        except (KeyError, ValueError):
            continue

    cgpa = round(total_score / total_credits, 2) if total_credits > 0 else 0
    return render_template('index.html', cgpa=cgpa, data=zip(grades, credits), detailed_data=detailed_data, suggestions=set(suggestions), regno=regno)

@app.route('/export', methods=['POST'])
def export():
    grades = request.form.getlist('grade')
    credits = request.form.getlist('credit')
    regno = request.form.get('regno')

    total_score = 0
    total_credits = 0
    detailed_data = []

    for grade, credit in zip(grades, credits):
        try:
            weight = grade_weights[grade.upper()]
            credit = float(credit)
            total_score += weight * credit
            total_credits += credit
            detailed_data.append((grade.upper(), credit, weight))
        except (KeyError, ValueError):
            continue

    cgpa = round(total_score / total_credits, 2) if total_credits > 0 else 0

    rendered = render_template('report.html', cgpa=cgpa, detailed_data=detailed_data, regno=regno)



if __name__ == '__main__':
    app.run(debug=True)
