from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import pandas as pd
import os
import uuid
from datetime import datetime
import tempfile
from pathlib import Path
import logging
import json

# Import your existing modules
from src.config import REQUIRED_COLUMNS
from src.processing import load_and_clean, summarize_data
from src.report_writer import write_report

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure app
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///document_processor.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'

# Create folders
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Initialize database
db = SQLAlchemy(app)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Database Models
class ProcessingJob(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    filename = db.Column(db.String(255))
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='processing')
    output_file = db.Column(db.String(255))
    error_message = db.Column(db.Text)
    summary_data = db.relationship('SummaryData', backref='job', lazy=True, cascade='all, delete-orphan')
    account_data = db.relationship('AccountData', backref='job', lazy=True, cascade='all, delete-orphan')


class SummaryData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.String(36), db.ForeignKey('processing_job.id'))
    company = db.Column(db.String(255))
    account = db.Column(db.String(255))
    document_currency = db.Column(db.String(50))
    local_currency = db.Column(db.String(50))
    amount_doc_curr = db.Column(db.Float)
    amount_local_curr = db.Column(db.Float)


class AccountData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.String(36), db.ForeignKey('processing_job.id'))
    account = db.Column(db.String(255))
    company = db.Column(db.String(255))
    document_date = db.Column(db.Date)
    document_currency = db.Column(db.String(50))
    local_currency = db.Column(db.String(50))
    amount_doc_curr = db.Column(db.Float)
    amount_local_curr = db.Column(db.Float)
    doc_ageing = db.Column(db.Integer)  # Days since document date


# Create tables
with app.app_context():
    db.create_all()


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ['xls', 'xlsx']


def save_to_database(job_id, summary_df, account_data_dict):
    """Save processed data to database"""
    try:
        # Save summary data
        for _, row in summary_df.iterrows():
            summary_record = SummaryData(
                job_id=job_id,
                company=str(row['Comapany']),
                account=str(row['Account']),
                document_currency=str(row['Document currency']),
                local_currency=str(row['Local Currency']),
                amount_doc_curr=float(row['Amount in doc. curr.']),
                amount_local_curr=float(row['Amount in local currency'])
            )
            db.session.add(summary_record)

        # Save account-wise data
        for account, df in account_data_dict.items():
            for _, row in df.iterrows():
                # Calculate document ageing
                if pd.notna(row['Document Date']):
                    doc_date = pd.to_datetime(row['Document Date']).date()
                    ageing = (datetime.now().date() - doc_date).days
                else:
                    ageing = None

                account_record = AccountData(
                    job_id=job_id,
                    account=str(account),
                    company=str(row['Comapany']),
                    document_date=doc_date if pd.notna(row['Document Date']) else None,
                    document_currency=str(row['Document currency']),
                    local_currency=str(row['Local Currency']),
                    amount_doc_curr=float(row['Amount in doc. curr.']),
                    amount_local_curr=float(row['Amount in local currency']),
                    doc_ageing=ageing
                )
                db.session.add(account_record)

        db.session.commit()
        return True
    except Exception as e:
        logger.error(f"Database save error: {str(e)}")
        db.session.rollback()
        return False


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload and processing"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Only .xls and .xlsx files are allowed'}), 400

    try:
        # Generate unique job ID
        job_id = str(uuid.uuid4())

        # Save uploaded file
        filename = secure_filename(file.filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{job_id}_{filename}")
        file.save(input_path)

        # Create job record
        job = ProcessingJob(
            id=job_id,
            filename=filename,
            status='processing'
        )
        db.session.add(job)
        db.session.commit()

        # Process the file
        df = load_and_clean(input_path, REQUIRED_COLUMNS)
        if df is None or df.empty:
            job.status = 'failed'
            job.error_message = 'Failed to load valid data from file'
            db.session.commit()
            return jsonify({'error': 'Failed to process file', 'job_id': job_id}), 400

        # Summarize data
        summary_df, account_data_dict = summarize_data(df)

        # Generate output file
        output_filename = f"{job_id}_Final_Report.xlsx"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

        # Write report
        success = write_report(summary_df, account_data_dict, output_path)
        if not success:
            job.status = 'failed'
            job.error_message = 'Failed to generate report'
            db.session.commit()
            return jsonify({'error': 'Failed to generate report', 'job_id': job_id}), 500

        # Save to database
        if save_to_database(job_id, summary_df, account_data_dict):
            job.status = 'completed'
            job.output_file = output_filename
            db.session.commit()

            return jsonify({
                'message': 'File processed successfully',
                'job_id': job_id,
                'status': 'completed'
            }), 200
        else:
            job.status = 'failed'
            job.error_message = 'Failed to save data to database'
            db.session.commit()
            return jsonify({'error': 'Database error', 'job_id': job_id}), 500

    except Exception as e:
        logger.error(f"Processing error: {str(e)}", exc_info=True)
        if 'job' in locals():
            job.status = 'failed'
            job.error_message = str(e)
            db.session.commit()
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500


@app.route('/api/job/<job_id>/status', methods=['GET'])
def get_job_status(job_id):
    """Get processing job status"""
    job = ProcessingJob.query.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    return jsonify({
        'job_id': job.id,
        'status': job.status,
        'filename': job.filename,
        'upload_date': job.upload_date.isoformat() if job.upload_date else None,
        'error_message': job.error_message
    })


@app.route('/api/job/<job_id>/preview', methods=['GET'])
def get_preview(job_id):
    """Get preview data for display"""
    job = ProcessingJob.query.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    if job.status != 'completed':
        return jsonify({'error': 'Job not completed'}), 400

    # Get summary data
    summary_data = []
    for record in job.summary_data:
        summary_data.append({
            'company': record.company,
            'account': record.account,
            'document_currency': record.document_currency,
            'local_currency': record.local_currency,
            'amount_doc_curr': record.amount_doc_curr,
            'amount_local_curr': record.amount_local_curr
        })

    # Get account data (limited for preview)
    account_data = {}
    accounts = db.session.query(AccountData.account).filter_by(job_id=job_id).distinct().all()

    for (account,) in accounts:
        records = AccountData.query.filter_by(job_id=job_id, account=account).limit(10).all()
        account_data[account] = []
        for record in records:
            account_data[account].append({
                'company': record.company,
                'document_date': record.document_date.isoformat() if record.document_date else None,
                'document_currency': record.document_currency,
                'local_currency': record.local_currency,
                'amount_doc_curr': record.amount_doc_curr,
                'amount_local_curr': record.amount_local_curr,
                'doc_ageing': record.doc_ageing
            })

    # Get totals
    totals = db.session.query(
        db.func.sum(SummaryData.amount_doc_curr).label('total_doc_curr'),
        db.func.sum(SummaryData.amount_local_curr).label('total_local_curr')
    ).filter_by(job_id=job_id).first()

    return jsonify({
        'summary': summary_data,
        'accounts': account_data,
        'totals': {
            'total_doc_curr': totals.total_doc_curr if totals else 0,
            'total_local_curr': totals.total_local_curr if totals else 0
        },
        'account_count': len(accounts),
        'total_records': db.session.query(AccountData).filter_by(job_id=job_id).count()
    })


@app.route('/api/job/<job_id>/download', methods=['GET'])
def download_report(job_id):
    """Download processed report"""
    job = ProcessingJob.query.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    if job.status != 'completed':
        return jsonify({'error': 'Job not completed'}), 400

    if not job.output_file:
        return jsonify({'error': 'Output file not found'}), 404

    file_path = os.path.join(app.config['OUTPUT_FOLDER'], job.output_file)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found on server'}), 404

    return send_file(
        file_path,
        as_attachment=True,
        download_name=f"Report_{job.filename}",
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@app.route('/api/job/<job_id>/account/<account>', methods=['GET'])
def get_account_details(job_id, account):
    """Get detailed data for a specific account"""
    job = ProcessingJob.query.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    if job.status != 'completed':
        return jsonify({'error': 'Job not completed'}), 400

    # Pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    # Query account data
    query = AccountData.query.filter_by(job_id=job_id, account=account)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    records = []
    for record in pagination.items:
        records.append({
            'company': record.company,
            'document_date': record.document_date.isoformat() if record.document_date else None,
            'document_currency': record.document_currency,
            'local_currency': record.local_currency,
            'amount_doc_curr': record.amount_doc_curr,
            'amount_local_curr': record.amount_local_curr,
            'doc_ageing': record.doc_ageing
        })

    return jsonify({
        'account': account,
        'data': records,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages
        }
    })


@app.route('/api/jobs', methods=['GET'])
def list_jobs():
    """List all processing jobs"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    query = ProcessingJob.query.order_by(ProcessingJob.upload_date.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    jobs = []
    for job in pagination.items:
        jobs.append({
            'job_id': job.id,
            'filename': job.filename,
            'upload_date': job.upload_date.isoformat() if job.upload_date else None,
            'status': job.status
        })

    return jsonify({
        'jobs': jobs,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages
        }
    })


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})


if __name__ == '__main__':
    app.run(debug=True, port=5001)