from datetime import datetime

class RiskAnalyzer:
    def __init__(self):
        pass

    def calculate_risks(self, patient):
        """
        Analyze patient data and return a list of potential risks.
        Returns: list of dicts {'condition': str, 'risk_level': str, 'probability': int, 'message': str}
        """
        risks = []
        try:
            age = int(patient.age)
        except:
            age = 0
            
        history_text = " ".join([v.diagnosis.lower() for v in patient.visits if v.diagnosis] + 
                                [d.disease_name.lower() for d in patient.diseases])
        
        # 1. Diabetes Risk
        # Factors: Age > 45, History of hypertension (simple keyword check for prototype)
        diabetes_prob = 10
        if age > 45: diabetes_prob += 20
        if age > 60: diabetes_prob += 15
        if 'blood pressure' in history_text or 'hypertension' in history_text: diabetes_prob += 25
        if 'obesity' in history_text or 'weight' in history_text: diabetes_prob += 30
        
        if diabetes_prob > 30:
            level = 'High' if diabetes_prob > 60 else 'Medium'
            risks.append({
                'condition': 'Type 2 Diabetes',
                'risk_level': level,
                'probability': min(diabetes_prob, 95),
                'message': 'Elevated risk due to age and history factors.'
            })

        # 2. Cardiovascular Risk
        cardio_prob = 5
        if age > 50: cardio_prob += 20
        if 'diabetes' in history_text: cardio_prob += 30
        if 'cholesterol' in history_text: cardio_prob += 25
        if 'chest pain' in history_text: cardio_prob += 20
        
        if cardio_prob > 30:
            level = 'High' if cardio_prob > 60 else 'Medium'
            risks.append({
                'condition': 'Cardiovascular Disease',
                'risk_level': level,
                'probability': min(cardio_prob, 95),
                'message': 'Consider monitoring heart health closely.'
            })

        # 3. Respiratory Issues (e.g. if 'cough' or 'asthma' present often)
        resp_count = history_text.count('cough') + history_text.count('breath') + history_text.count('asthma')
        if resp_count >= 2:
             risks.append({
                'condition': 'Chronic Respiratory Issue',
                'risk_level': 'Medium',
                'probability': 50 + (resp_count * 5),
                'message': 'Recurrent respiratory symptoms detected.'
            })

        return risks
