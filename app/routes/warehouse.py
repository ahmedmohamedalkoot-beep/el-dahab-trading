from flask import Blueprint

warehouse_bp = Blueprint('warehouse', __name__, url_prefix='/warehouse')

# سيتم إضافة المسارات هنا عند الحاجة