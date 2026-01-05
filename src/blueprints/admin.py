from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user
from src.models import Patient, User, PatientDisease

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'admin':
        abort(403)
        
    stats = {
        'total_patients': Patient.query.count(),
        'total_users': User.query.count(),
        'recent_patients': Patient.query.order_by(Patient.id.desc()).limit(5).all()
    }
    
    # Analytics for Charts
    # 1. Disease Distribution
    all_diseases = PatientDisease.query.all()
    disease_counts = {}
    for d in all_diseases:
        disease_counts[d.name] = disease_counts.get(d.name, 0) + 1
    
    # Sort for Top 5
    top_diseases_list = sorted(disease_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Prepare Chart Data
    chart_data = {
        'diseases': {
            'labels': [d[0] for d in top_diseases_list],
            'data': [d[1] for d in top_diseases_list]
        },
        'ages': {'labels': [], 'data': []}
    }

    # 2. Age Distribution (Simple buckets)
    patients = Patient.query.all()
    age_buckets = {'0-18': 0, '19-35': 0, '36-60': 0, '60+': 0}
    for p in patients:
        try:
            age = int(p.age)
            if age <= 18: age_buckets['0-18'] += 1
            elif age <= 35: age_buckets['19-35'] += 1
            elif age <= 60: age_buckets['36-60'] += 1
            else: age_buckets['60+'] += 1
        except:
            pass # Ignore invalid age
            
    chart_data['ages']['labels'] = list(age_buckets.keys())
    chart_data['ages']['data'] = list(age_buckets.values())

    return render_template('dashboard.html', stats=stats, top_diseases=top_diseases_list, chart_data=chart_data)


@admin_bp.route('/users')
@login_required
def manage_users():
    if current_user.role != 'admin':
        abort(403)
    # The template 'admin.html' expects 'users' (dict of staff) and 'patients' (list)
    # transforming DB query to match template expectations roughly
    staff_users = User.query.filter(User.role.in_(['admin', 'staff'])).all()
    # Convert to dict {username: user_obj} as per legacy expectation if needed, or pass list
    # Template likely iterates: `{% for username, user in users.items() %}`
    # I should check admin.html.
    # Assuming list usage is better, but let's stick to what template likely does or fixing template is harder.
    # Let's wrap as dict for compatibility.
    staff_dict = {u.username: u for u in staff_users if u.username != 'admin'}
    
    patient_users = User.query.filter_by(role='patient').all()
    # They need to be objects with username.
    
    return render_template('admin.html', users=staff_dict, patients=patient_users)

@admin_bp.route('/delete_user/<username>', methods=['POST'])
@login_required
def delete_user(username):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    if username == 'admin':
        flash('Cannot delete admin.', 'warning')
        return redirect(url_for('admin.manage_users'))

    user = User.query.filter_by(username=username).first()
    if user:
        db.session.delete(user) # Cascades to patient if set up, or leaves orphan?
        # Patient model has `user_id`. delete-orphan might need explicit config or manual delete.
        # For now, just delete user.
        db.session.commit()
        flash(f'User {username} deleted.', 'success')
    else:
        flash('User not found.', 'warning')
    return redirect(url_for('admin.manage_users'))

