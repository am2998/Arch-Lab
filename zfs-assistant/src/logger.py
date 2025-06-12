#!/usr/bin/env python3
"""
ZFS Assistant - Comprehensive Logging System
Handles logging for all ZFS operations including snapshots, system updates, backups, and maintenance
"""

import os
import json
import datetime
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from enum import Enum

# Import LOG_FILE constant from common
try:
    from .common import LOG_FILE
except ImportError:
    try:
        from common import LOG_FILE
    except ImportError:
        # Fallback if import fails
        LOG_FILE = "/var/log/zfs-assistant.log"

class OperationType(Enum):
    """Types of operations that can be logged"""
    SNAPSHOT_SCHEDULED = "snapshot_scheduled"
    SNAPSHOT_MANUAL = "snapshot_manual"
    SNAPSHOT_CLEANUP = "snapshot_cleanup"
    PACMAN_INTEGRATION = "pacman_integration"
    SYSTEM_UPDATE = "system_update"
    CACHE_CLEANUP = "cache_cleanup"
    ZFS_BACKUP = "zfs_backup"
    SYSTEM_MAINTENANCE = "system_maintenance"
    ORPHAN_CLEANUP = "orphan_cleanup"
    ROLLBACK = "rollback"
    CLONE = "clone"

class LogLevel(Enum):
    """Log levels for different types of messages"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    SUCCESS = "SUCCESS"

class ZFSLogger:
    """
    Comprehensive logging system for ZFS Assistant operations
    Creates structured logs with timestamps and operation-specific sections
    """    def __init__(self, log_file: str = None):
        """
        Initialize the logger
        
        Args:
            log_file: Path to the single log file (defaults to LOG_FILE constant)
        """
        if log_file is None:
            log_file = LOG_FILE
        self.log_file = Path(log_file)
        
        # Ensure the log directory exists
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Single unified log file for all operations
        self.main_log_file = self.log_file
        
        # Current operation context
        self.current_operation: Optional[Dict[str, Any]] = None
        
        # Setup standard Python logging
        self._setup_python_logging()
    
    def _setup_python_logging(self):
        """Setup standard Python logging for integration with existing code"""
        self.python_logger = logging.getLogger('zfs_assistant')
        self.python_logger.setLevel(logging.DEBUG)
        
        # Create formatter
        formatter = logging.Formatter(
            '[%(asctime)s] - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File handler for main log
        if not self.python_logger.handlers:
            file_handler = logging.FileHandler(self.main_log_file)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            self.python_logger.addHandler(file_handler)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        return datetime.datetime.now().isoformat()
    
    def _write_to_log(self, log_file: Path, content: str):
        """Write content to a specific log file"""
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(content + '\n')
        except Exception as e:
            # Fallback to main log if specific log fails
            with open(self.main_log_file, 'a', encoding='utf-8') as f:
                f.write(f"[{self._get_timestamp()}] LOG_ERROR: Failed to write to {log_file}: {e}\n")
                f.write(content + '\n')
    
    def _format_log_entry(self, level: LogLevel, message: str, operation_type: Optional[OperationType] = None, details: Optional[Dict[str, Any]] = None) -> str:
        """Format a log entry with timestamp and metadata"""
        timestamp = self._get_timestamp()
        entry_parts = [f"[{timestamp}]", f"[{level.value}]"]
        
        if operation_type:
            entry_parts.append(f"[{operation_type.value.upper()}]")
        
        entry_parts.append(message)
        
        log_entry = " ".join(entry_parts)
        
        if details:
            details_str = json.dumps(details, indent=2, default=str)
            log_entry += f"\nDetails: {details_str}"
        
        return log_entry
    
    def start_operation(self, operation_type: OperationType, description: str, details: Optional[Dict[str, Any]] = None):
        """
        Start logging a new operation
        
        Args:
            operation_type: Type of operation being started
            description: Human-readable description of the operation
            details: Additional details about the operation
        """
        start_time = datetime.datetime.now()
        
        self.current_operation = {
            'type': operation_type,
            'description': description,
            'start_time': start_time,
            'details': details or {},
            'log_entries': []
        }
        
        # Log operation start
        header = f"{'='*80}"
        start_msg = f"OPERATION STARTED: {description}"
        
        operation_details = {
            'operation_type': operation_type.value,
            'start_time': start_time.isoformat(),
            'details': details or {}
        }
        
        log_content = f"{header}\n{self._format_log_entry(LogLevel.INFO, start_msg, operation_type, operation_details)}\n{header}"
          # Write to main log
        self._write_to_log(self.main_log_file, log_content)
        
        # Log to Python logger
        self.python_logger.info(f"Started operation: {description}")
    
    def log_message(self, level: LogLevel, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Log a message within the current operation
        
        Args:
            level: Log level
            message: Message to log
            details: Additional details
        """
        operation_type = self.current_operation['type'] if self.current_operation else None
        
        log_entry = self._format_log_entry(level, message, operation_type, details)
        
        # Add to current operation log entries
        if self.current_operation:
            self.current_operation['log_entries'].append({
                'timestamp': self._get_timestamp(),
                'level': level.value,
                'message': message,
                'details': details or {}
            })
          # Write to main log
        self._write_to_log(self.main_log_file, log_entry)
        
        # Log to Python logger
        python_level = getattr(logging, level.value, logging.INFO)
        self.python_logger.log(python_level, message)
    
    def end_operation(self, success: bool, summary: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        """
        End the current operation and log summary
        
        Args:
            success: Whether the operation was successful
            summary: Optional summary message
            details: Additional details about the operation result
        """
        if not self.current_operation:
            self.log_message(LogLevel.WARNING, "Attempted to end operation but no operation was started")
            return
        
        end_time = datetime.datetime.now()
        duration = end_time - self.current_operation['start_time']
        
        operation_type = self.current_operation['type']
        operation_desc = self.current_operation['description']
        
        # Determine result level and message
        if success:
            result_level = LogLevel.SUCCESS
            result_status = "COMPLETED SUCCESSFULLY"
        else:
            result_level = LogLevel.ERROR
            result_status = "FAILED"
        
        end_msg = f"OPERATION {result_status}: {operation_desc}"
        
        operation_summary = {
            'operation_type': operation_type.value,
            'description': operation_desc,
            'start_time': self.current_operation['start_time'].isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': duration.total_seconds(),
            'success': success,
            'summary': summary,
            'details': details or {},
            'log_entries_count': len(self.current_operation['log_entries'])
        }
        
        # Log operation end
        footer = f"{'='*80}"
        duration_msg = f"Duration: {duration}"
        
        log_content = f"{self._format_log_entry(result_level, end_msg, operation_type, operation_summary)}\n{duration_msg}\n{footer}\n"
          # Write to main log
        self._write_to_log(self.main_log_file, log_content)
        
        # Log to Python logger
        python_level = logging.INFO if success else logging.ERROR
        self.python_logger.log(python_level, f"Ended operation: {operation_desc} - {result_status} (Duration: {duration})")
        
        # Clear current operation
        self.current_operation = None
    
    def log_snapshot_operation(self, operation: str, dataset: str, snapshot_name: str, success: bool, details: Optional[Dict[str, Any]] = None):
        """
        Log a specific snapshot operation
        
        Args:
            operation: Type of snapshot operation (create, delete, rollback, etc.)
            dataset: ZFS dataset name
            snapshot_name: Name of the snapshot
            success: Whether operation was successful
            details: Additional operation details
        """
        level = LogLevel.SUCCESS if success else LogLevel.ERROR
        message = f"Snapshot {operation}: {dataset}@{snapshot_name}"
        
        operation_details = {
            'operation': operation,
            'dataset': dataset,
            'snapshot_name': snapshot_name,
            'full_snapshot_name': f"{dataset}@{snapshot_name}",
            'success': success
        }
        
        if details:
            operation_details.update(details)
        
        self.log_message(level, message, operation_details)
    
    def log_system_command(self, command: List[str], success: bool, output: Optional[str] = None, error: Optional[str] = None):
        """
        Log execution of a system command
        
        Args:
            command: Command that was executed
            success: Whether command succeeded
            output: Command output
            error: Error message if any
        """
        level = LogLevel.SUCCESS if success else LogLevel.ERROR
        command_str = " ".join(command)
        message = f"System command: {command_str}"
        
        command_details = {
            'command': command,
            'command_string': command_str,
            'success': success,
            'output': output,
            'error': error
        }
        
        self.log_message(level, message, command_details)
    
    def log_backup_operation(self, source_dataset: str, target_pool: str, backup_type: str, success: bool, details: Optional[Dict[str, Any]] = None):
        """
        Log a ZFS backup operation
        
        Args:
            source_dataset: Source dataset being backed up
            target_pool: Target pool for backup
            backup_type: Type of backup (full, incremental)
            success: Whether backup succeeded
            details: Additional backup details
        """
        level = LogLevel.SUCCESS if success else LogLevel.ERROR
        message = f"ZFS backup ({backup_type}): {source_dataset} -> {target_pool}"
        
        backup_details = {
            'source_dataset': source_dataset,
            'target_pool': target_pool,
            'backup_type': backup_type,
            'success': success
        }
        
        if details:
            backup_details.update(details)
        
        self.log_message(level, message, backup_details)
      def get_operation_logs(self, operation_type: OperationType, limit: Optional[int] = None) -> List[str]:
        """
        Get recent log entries for a specific operation type
        
        Args:
            operation_type: Type of operation to get logs for
            limit: Maximum number of log entries to return
            
        Returns:
            List of log entries
        """
        if not self.main_log_file.exists():
            return []
        
        try:
            with open(self.main_log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Filter lines for specific operation type
            operation_lines = []
            for line in lines:
                if f"[{operation_type.value.upper()}]" in line:
                    operation_lines.append(line.strip())
            
            if limit:
                operation_lines = operation_lines[-limit:]
            
            return operation_lines
        except Exception as e:
            self.log_message(LogLevel.ERROR, f"Failed to read operation logs: {e}")
            return []    def cleanup_old_logs(self, days_to_keep: int = 30):
        """
        Clean up log files older than specified days
        
        Args:
            days_to_keep: Number of days to keep logs
        """
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_to_keep)
        
        # For single file logging, we'll just archive the current log if it's old
        try:
            if self.main_log_file.exists() and self.main_log_file.stat().st_mtime < cutoff_date.timestamp():
                # Archive old log file instead of deleting
                archive_name = f"{self.main_log_file.stem}-{datetime.datetime.fromtimestamp(self.main_log_file.stat().st_mtime).strftime('%Y%m%d')}.log.old"
                archive_path = self.main_log_file.parent / archive_name
                self.main_log_file.rename(archive_path)
                self.log_message(LogLevel.INFO, f"Archived old log file: {self.main_log_file.name} -> {archive_name}")
        except Exception as e:
            self.log_message(LogLevel.WARNING, f"Failed to cleanup log file {self.main_log_file}: {e}")

# Global logger instance
_logger_instance: Optional[ZFSLogger] = None

def get_logger() -> ZFSLogger:
    """Get the global logger instance"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = ZFSLogger()
    return _logger_instance

def log_info(message: str, details: Optional[Dict[str, Any]] = None):
    """Convenience function to log info message"""
    get_logger().log_message(LogLevel.INFO, message, details)

def log_error(message: str, details: Optional[Dict[str, Any]] = None):
    """Convenience function to log error message"""
    get_logger().log_message(LogLevel.ERROR, message, details)

def log_success(message: str, details: Optional[Dict[str, Any]] = None):
    """Convenience function to log success message"""
    get_logger().log_message(LogLevel.SUCCESS, message, details)

def log_warning(message: str, details: Optional[Dict[str, Any]] = None):
    """Convenience function to log warning message"""
    get_logger().log_message(LogLevel.WARNING, message, details)
