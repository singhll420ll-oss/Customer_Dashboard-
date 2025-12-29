import os
from datetime import datetime
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, upload_folder, prefix=''):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{prefix}_{timestamp}_{filename}"
        filepath = os.path.join(upload_folder, unique_filename)
        file.save(filepath)
        return unique_filename
    return None

def format_datetime(value, format='%d %b %Y, %H:%M'):
    if value:
        return value.strftime(format)
    return ''

def calculate_final_price(base_price, discount):
    try:
        return float(base_price) - float(discount)
    except:
        return float(base_price)
