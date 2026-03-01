# ============================================================
# DATA EXPORT MODULE
# ============================================================

import csv
import json
from io import StringIO, BytesIO
from datetime import datetime
import tempfile
import os

class DataExporter:
    """Export data in various formats"""
    
    @staticmethod
    def export_to_csv(data, filename='export.csv'):
        """Export data to CSV format"""
        if not data or len(data) == 0:
            return None
        
        # Use StringIO to create in-memory file
        output = StringIO()
        
        # Get headers from first item
        headers = list(data[0].keys()) if isinstance(data[0], dict) else list(range(len(data[0])))
        
        writer = csv.DictWriter(output, fieldnames=headers) if isinstance(data[0], dict) else csv.writer(output)
        
        # Write headers
        writer.writeheader() if isinstance(data[0], dict) else writer.writerow(headers)
        
        # Write data
        writer.writerows(data)
        
        # Get the CSV content
        csv_content = output.getvalue()
        output.close()
        
        return csv_content
    
    @staticmethod
    def export_to_json(data, filename='export.json', pretty=True):
        """Export data to JSON format"""
        if pretty:
            return json.dumps(data, indent=2, default=str)
        else:
            return json.dumps(data, default=str)
    
    @staticmethod
    def export_threats_to_csv(threats):
        """Export threat data to CSV"""
        csv_data = []
        for threat in threats:
            csv_data.append({
                'Timestamp': threat.get('timestamp', ''),
                'Type': threat.get('type', ''),
                'Severity': threat.get('severity', ''),
                'Source': threat.get('source', ''),
                'Destination': threat.get('destination', ''),
                'Country': threat.get('country_name', ''),
                'Status': threat.get('status', ''),
                'Confidence': threat.get('confidence', '')
            })
        return DataExporter.export_to_csv(csv_data)
    
    @staticmethod
    def export_users_to_csv(users):
        """Export user data to CSV"""
        csv_data = []
        for user in users:
            csv_data.append({
                'ID': user.get('id', ''),
                'Username': user.get('username', ''),
                'Email': user.get('email', ''),
                'Role': user.get('role', ''),
                'Status': 'Active' if user.get('is_active', True) else 'Inactive',
                'Created': user.get('created_at', ''),
                'Last Login': user.get('last_login', 'Never')
            })
        return DataExporter.export_to_csv(csv_data)
    
    @staticmethod
    def export_report(report_data, format='json'):
        """Export comprehensive report"""
        if format == 'json':
            return DataExporter.export_to_json(report_data, pretty=True)
        elif format == 'csv':
            # Flatten nested data for CSV
            flattened_data = []
            if isinstance(report_data, dict):
                for key, value in report_data.items():
                    if isinstance(value, (list, dict)):
                        value = json.dumps(value)
                    flattened_data.append({'Key': key, 'Value': value})
            return DataExporter.export_to_csv(flattened_data)
        return None


class ReportGenerator:
    """Generate comprehensive reports"""
    
    @staticmethod
    def generate_threat_report(threats, start_date=None, end_date=None):
        """Generate threat analysis report"""
        report = {
            'report_type': 'Threat Analysis',
            'generated_at': datetime.now().isoformat(),
            'period': {
                'start': start_date,
                'end': end_date
            },
            'summary': {
                'total_threats': len(threats),
                'critical_count': sum(1 for t in threats if t.get('severity') == 'Critical'),
                'high_count': sum(1 for t in threats if t.get('severity') == 'High'),
                'medium_count': sum(1 for t in threats if t.get('severity') == 'Medium'),
                'low_count': sum(1 for t in threats if t.get('severity') == 'Low'),
            },
            'threat_types': {},
            'top_sources': {},
            'threat_details': threats
        }
        
        # Count by threat type
        for threat in threats:
            threat_type = threat.get('type', 'Unknown')
            report['threat_types'][threat_type] = report['threat_types'].get(threat_type, 0) + 1
        
        # Count by source
        for threat in threats:
            source = threat.get('source', 'Unknown')
            report['top_sources'][source] = report['top_sources'].get(source, 0) + 1
        
        # Sort top sources
        report['top_sources'] = dict(
            sorted(report['top_sources'].items(), key=lambda x: x[1], reverse=True)[:10]
        )
        
        return report
    
    @staticmethod
    def generate_user_report(users):
        """Generate user management report"""
        report = {
            'report_type': 'User Management',
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_users': len(users),
                'active_users': sum(1 for u in users if u.get('is_active', True)),
                'inactive_users': sum(1 for u in users if not u.get('is_active', True)),
                'admins': sum(1 for u in users if u.get('role') == 'admin'),
                'analysts': sum(1 for u in users if u.get('role') == 'analyst')
            },
            'users': users
        }
        return report
    
    @staticmethod
    def generate_performance_report(metrics):
        """Generate performance report"""
        report = {
            'report_type': 'Performance Metrics',
            'generated_at': datetime.now().isoformat(),
            'metrics': metrics,
            'summary': {
                'total_requests': metrics.get('total_requests', 0),
                'total_errors': metrics.get('total_errors', 0),
                'error_rate': (metrics.get('total_errors', 0) / max(metrics.get('total_requests', 1), 1)) * 100,
                'slow_requests': len(metrics.get('slow_requests', [])),
                'endpoints_monitored': len(metrics.get('endpoint_stats', {}))
            }
        }
        return report
    
    @staticmethod
    def generate_compliance_report(users, threats):
        """Generate compliance report"""
        report = {
            'report_type': 'Compliance',
            'generated_at': datetime.now().isoformat(),
            'audit_summary': {
                'total_users': len(users),
                'verified_users': sum(1 for u in users if u.get('email_verified', False)),
                'users_with_oauth': sum(1 for u in users if u.get('oauth_provider')),
                'password_secured_accounts': len([u for u in users if u.get('password')])
            },
            'security_summary': {
                'total_threats': len(threats),
                'blocked_threats': sum(1 for t in threats if t.get('status') == 'Blocked'),
                'detected_threats': sum(1 for t in threats if t.get('status') == 'Detected'),
                'critical_threats': sum(1 for t in threats if t.get('severity') == 'Critical')
            },
            'recommendations': [
                'Enable 2FA for all admin accounts',
                'Regularly review and update access permissions',
                'Monitor unusual login patterns',
                'Maintain regular security audits'
            ]
        }
        return report


class ScheduledReports:
    """Handle scheduled report generation"""
    
    REPORT_TYPES = {
        'daily': 24,
        'weekly': 7 * 24,
        'monthly': 30 * 24
    }
    
    def __init__(self):
        self.scheduled_reports = {}
        self.generated_reports = []
    
    def schedule_report(self, report_type, frequency, recipients=None):
        """Schedule a report for automatic generation"""
        report_id = f"{report_type}_{datetime.now().timestamp()}"
        self.scheduled_reports[report_id] = {
            'type': report_type,
            'frequency': frequency,
            'recipients': recipients or [],
            'created_at': datetime.now().isoformat(),
            'next_run': datetime.now().isoformat()
        }
        return report_id
    
    def get_scheduled_reports(self):
        """Get all scheduled reports"""
        return list(self.scheduled_reports.values())
    
    def get_past_reports(self, limit=10):
        """Get recently generated reports"""
        return self.generated_reports[-limit:]
