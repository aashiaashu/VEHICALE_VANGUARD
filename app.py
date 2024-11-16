from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
from dotenv import load_dotenv
import os
load_dotenv()
app = Flask(__name__)
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-pro')
def analyze_vehicle_data(data):
    """Analyze vehicle sensor data and return maintenance recommendations"""
    # Define normal operating ranges
    ranges = {
        'Oil Pressure': (20, 80),
        'Oil Temperature': (195, 220),
        'Oil Quality': (0, 100),
        'Brake Fluid Pressure': (300, 900),
        'Brake Pad Wear': (0, 100),
        'Brake Temperature': (150, 400),
        'Fuel Pressure': (40, 60),
        'O2 Sensor': (0, 1),
        'Fuel Temperature': (75, 95)
    }
    
    issues = []
    systems_affected = set()
    
    # Check each sensor reading
    for sensor, value in data.items():
        if sensor in ranges:
            min_val, max_val = ranges[sensor]
            if value < min_val or value > max_val:
                issues.append(f"{sensor}: {value} (Normal range: {min_val}-{max_val})")
                if 'Oil' in sensor:
                    systems_affected.add('Engine Oil System')
                elif 'Brake' in sensor:
                    systems_affected.add('Brake System')
                elif 'Fuel' in sensor or 'O2' in sensor:
                    systems_affected.add('Fuel System')

    return list(systems_affected), issues

def get_maintenance_strategy(systems_affected, issues):
    """Generate maintenance strategy using Gemini API with formatted output"""
    prompt = f"""
    As a vehicle maintenance expert, provide a maintenance strategy for a vehicle with these issues:
    Affected Systems: {', '.join(systems_affected)}
    Issues Detected: {', '.join(issues)}
    
    Format your response exactly as follows, using only plain text and bullet points (•):

    Maintenance Strategy:

    Immediate Actions Needed:
    • [List immediate actions for each affected system]

    Recommended Maintenance Schedule:

    Quarterly:
    • [2 points onquarterly maintenance tasks]

    Annually:
    • [2 points on annual maintenance tasks]

    Estimated Severity:
    [State severity level and brief explanation]

    Potential Consequences if Not Addressed:

    Brake System:
    • [2 Points on brake system consequences]

    Engine Oil System:
    • [2 points on engine consequences]

    Fuel System:
    • [2 points onfuel system consequences]

    Use only bullet points with • symbol, no special characters, no markdown, and maintain consistent formatting.
    """
    
    response = model.generate_content(prompt)
    return response.text

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = {
            'Oil Pressure': float(request.form['oil_pressure']),
            'Oil Temperature': float(request.form['oil_temperature']),
            'Oil Quality': float(request.form['oil_quality']),
            'Brake Fluid Pressure': float(request.form['brake_pressure']),
            'Brake Pad Wear': float(request.form['brake_pad_wear']),
            'Brake Temperature': float(request.form['brake_temperature']),
            'Fuel Pressure': float(request.form['fuel_pressure']),
            'O2 Sensor': float(request.form['o2_sensor']),
            'Fuel Temperature': float(request.form['fuel_temperature'])
        }
        
        systems_affected, issues = analyze_vehicle_data(data)
        
        if systems_affected:
            maintenance_strategy = get_maintenance_strategy(systems_affected, issues)
        else:
            maintenance_strategy = """
            Maintenance Strategy:

            All systems are operating within normal parameters.

            Recommended Maintenance Schedule:

            Weekly:
            • Check all fluid levels
            • Visual inspection of components

            Monthly:
            • Perform routine checks
            • Document sensor readings

            Continue following manufacturer's regular maintenance schedule.
            """
        
        return jsonify({
            'success': True,
            'systems_affected': list(systems_affected),
            'issues': issues,
            'maintenance_strategy': maintenance_strategy
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    app.run(debug=True)